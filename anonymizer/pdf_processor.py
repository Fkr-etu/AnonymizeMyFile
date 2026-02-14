import fitz  # PyMuPDF
from .analyzer import FrenchAnalyzer
from .redactor import FrenchImageRedactor
import os
import logging

logger = logging.getLogger(__name__)

class PDFProcessor:
    def __init__(self, analyzer: FrenchAnalyzer, image_redactor: FrenchImageRedactor):
        self.analyzer = analyzer
        self.image_redactor = image_redactor

    def process(self, input_path, output_path, entities_to_ignore=None, doc_type=None, force_image_redaction=False):
        """
        Processes a PDF: detects PII and performs physical redaction.
        Supports both native and scanned PDFs.
        Optimized for output file size.
        """
        logger.info(f"Starting PDF processing: {input_path}")
        try:
            doc = fitz.open(input_path)
        except Exception as e:
            logger.error(f"Failed to open PDF {input_path}: {e}", exc_info=True)
            raise

        audit_results = []

        for page_num in range(len(doc)):
            logger.info(f"Processing PDF page {page_num+1}/{len(doc)}")
            page = doc[page_num]
            text = page.get_text()

            if text.strip() and not force_image_redaction:
                logger.debug(f"Page {page_num+1}: native text found")
                # Native PDF with text
                results = self.analyzer.analyze(text, doc_type=doc_type)

                # Filter out ignored entities
                if entities_to_ignore:
                    results = [res for res in results if res.entity_type not in entities_to_ignore]

                audit_results.extend(results)

                for res in results:
                    target_text = text[res.start:res.end]
                    if not target_text.strip():
                        continue

                    areas = page.search_for(target_text)
                    for area in areas:
                        page.add_redact_annot(area, fill=(0, 0, 0))

                page.apply_redactions()
            else:
                if force_image_redaction:
                    logger.info(f"Page {page_num+1}: force_image_redaction is True (VLM mode)")
                else:
                    logger.info(f"Page {page_num+1}: no text found, treating as scan")
                # Scanned PDF or page with no text
                # We use a reasonable resolution for OCR
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                img_data = pix.tobytes("png")

                temp_img_in = f"temp_page_{page_num}.png"
                temp_img_out = f"temp_page_{page_num}_out.png"

                with open(temp_img_in, "wb") as f:
                    f.write(img_data)

                try:
                    # Pass doc_type to redactor (handles handwriting if it's a constat)
                    results = self.image_redactor.redact(temp_img_in, temp_img_out, entities_to_ignore=entities_to_ignore, doc_type=doc_type)
                    audit_results.extend(results)

                    # Insert the redacted image back
                    # We clear existing content first by redacting the whole page
                    page.add_redact_annot(page.rect)
                    page.apply_redactions()
                    page.insert_image(page.rect, filename=temp_img_out)
                except Exception as e:
                    logger.error(f"Error during scanned page {page_num+1} processing: {e}", exc_info=True)
                finally:
                    if os.path.exists(temp_img_in): os.remove(temp_img_in)
                    if os.path.exists(temp_img_out): os.remove(temp_img_out)

        # Optimize the output PDF
        try:
            logger.info(f"Saving optimized PDF to {output_path}")
            doc.save(
                output_path,
                garbage=4,
                deflate=True,
                clean=True
            )
            logger.info("PDF processing complete")
        except Exception as e:
            logger.error(f"Error saving PDF: {e}", exc_info=True)
            raise
        finally:
            doc.close()

        return audit_results
