import os
from .analyzer import FrenchAnalyzer
from .redactor import FrenchImageRedactor
from .pdf_processor import PDFProcessor
from .utils import AuditLogger

class AnonymizationPipeline:
    def __init__(self, output_dir, custom_recognizers=None):
        self.analyzer = FrenchAnalyzer(custom_recognizers_path=custom_recognizers)
        self.image_redactor = FrenchImageRedactor(self.analyzer.engine)
        self.pdf_processor = PDFProcessor(self.analyzer, self.image_redactor)
        self.logger = AuditLogger(output_dir)
        self.output_dir = output_dir

    def process_file(self, file_path):
        filename = os.path.basename(file_path)
        ext = os.path.splitext(filename)[1].lower()
        output_path = os.path.join(self.output_dir, filename)

        print(f"Processing {filename}...")

        results = []
        if ext in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
            results = self.image_redactor.redact(file_path, output_path)
        elif ext == '.pdf':
            results = self.pdf_processor.process(file_path, output_path)
        else:
            print(f"Unsupported file format: {ext}")
            return None

        audit_path = self.logger.log_process(filename, results)
        print(f"Finished processing {filename}. Audit log: {audit_path}")
        return output_path
