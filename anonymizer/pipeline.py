import os
import logging
from .analyzer import FrenchAnalyzer
from .redactor import FrenchImageRedactor
from .pdf_processor import PDFProcessor
from .utils import AuditLogger
import fitz

logger = logging.getLogger(__name__)

class AnonymizationPipeline:
    def __init__(self, output_dir, custom_recognizers=None, allow_lists=None, entities_to_ignore=None, default_doc_type=None):
        logger.info("Initializing AnonymizationPipeline...")
        try:
            self.analyzer = FrenchAnalyzer(custom_recognizers_path=custom_recognizers, allow_lists_path=allow_lists)
            logger.info("FrenchAnalyzer initialized")
            self.image_redactor = FrenchImageRedactor(self.analyzer)
            logger.info("FrenchImageRedactor initialized")
            self.pdf_processor = PDFProcessor(self.analyzer, self.image_redactor)
            logger.info("PDFProcessor initialized")
            self.logger = AuditLogger(output_dir)
            self.output_dir = output_dir
            self.entities_to_ignore = entities_to_ignore or ["DATE_TIME", "CARDINAL"]
            self.default_doc_type = default_doc_type
            logger.info(f"Pipeline ready. Entities to ignore: {self.entities_to_ignore}")
        except Exception as e:
            logger.error(f"Error initializing pipeline: {e}", exc_info=True)
            raise

    def _extract_sample_text(self, file_path):
        """Extract a sample of text to help identify the document type."""
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.pdf':
            try:
                doc = fitz.open(file_path)
                text = ""
                for i in range(min(2, len(doc))):
                    text += doc[i].get_text()
                doc.close()
                logger.debug(f"Extracted {len(text)} characters from PDF: {os.path.basename(file_path)}")
                return text
            except Exception as e:
                logger.warning(f"Could not extract text from PDF {os.path.basename(file_path)}: {e}")
                return ""
        return ""

    def process_file(self, file_path, manual_doc_type=None):
        filename = os.path.basename(file_path)
        ext = os.path.splitext(filename)[1].lower()
        
        # Skip files without extension
        if not ext:
            print(f"Skipping {filename} (no file extension)")
            return None
        
        output_path = os.path.join(self.output_dir, filename)

        sample_text = self._extract_sample_text(file_path)
        doc_type = manual_doc_type or self.default_doc_type or self.analyzer.detect_doc_type(sample_text, filename)

        if doc_type:
            print(f"Processing {filename} as type: {doc_type}...")
        else:
            print(f"Processing {filename} (unknown type)...")

        results = []
        if ext in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
            results = self.image_redactor.redact(file_path, output_path, entities_to_ignore=self.entities_to_ignore, doc_type=doc_type)
        elif ext == '.pdf':
            results = self.pdf_processor.process(file_path, output_path, entities_to_ignore=self.entities_to_ignore, doc_type=doc_type)
        else:
            print(f"Unsupported file format: {ext}")
            return None

        audit_path = self.logger.log_process(filename, results)
        print(f"Finished processing {filename}. Audit log: {audit_path}")
        return output_path
