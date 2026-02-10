import fitz  # PyMuPDF
from .analyzer import FrenchAnalyzer
from .redactor import FrenchImageRedactor
import os
from PIL import Image
import io

class PDFProcessor:
    def __init__(self, analyzer: FrenchAnalyzer, image_redactor: FrenchImageRedactor):
        self.analyzer = analyzer
        self.image_redactor = image_redactor

    def process(self, input_path, output_path):
        """
        Processes a PDF: detects PII and performs physical redaction.
        Supports both native and scanned PDFs.
        """
        doc = fitz.open(input_path)
        audit_results = []

        # We will create a new PDF to store results if we encounter scanned pages
        # or just modify the current one.

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()

            if text.strip():
                # Native PDF with text
                results = self.analyzer.analyze(text)
                audit_results.extend(results)

                for res in results:
                    target_text = text[res.start:res.end]
                    if not target_text.strip():
                        continue

                    # Search for the text to get its coordinates
                    # Note: this can have false positives if the same text appears elsewhere
                    areas = page.search_for(target_text)
                    for area in areas:
                        page.add_redact_annot(area, fill=(0, 0, 0))

                page.apply_redactions()
            else:
                # Scanned PDF or page with no text
                # Convert page to image
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) # Higher resolution
                img_data = pix.tobytes("png")

                # Temp path for image redactor
                temp_img_in = f"temp_page_{page_num}.png"
                temp_img_out = f"temp_page_{page_num}_out.png"

                with open(temp_img_in, "wb") as f:
                    f.write(img_data)

                try:
                    # This uses Tesseract OCR
                    results = self.image_redactor.redact(temp_img_in, temp_img_out)
                    audit_results.extend(results)

                    # Replace page content with redacted image
                    # We create a new page with the image size
                    redacted_pix = fitz.Pixmap(temp_img_out)
                    page.insert_image(page.rect, pixmap=redacted_pix)
                    # We also need to remove any hidden text if it was just poorly OCRed
                    page.add_redact_annot(page.rect)
                    page.apply_redactions()
                    page.insert_image(page.rect, pixmap=redacted_pix)
                except Exception as e:
                    print(f"Warning: Could not OCR page {page_num}: {e}")
                finally:
                    if os.path.exists(temp_img_in): os.remove(temp_img_in)
                    if os.path.exists(temp_img_out): os.remove(temp_img_out)

        doc.save(output_path)
        doc.close()
        return audit_results
