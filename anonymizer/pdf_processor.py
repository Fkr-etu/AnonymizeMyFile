import fitz  # PyMuPDF
from .analyzer import FrenchAnalyzer
from .redactor import FrenchImageRedactor
import os

class PDFProcessor:
    def __init__(self, analyzer: FrenchAnalyzer, image_redactor: FrenchImageRedactor):
        self.analyzer = analyzer
        self.image_redactor = image_redactor

    def process(self, input_path, output_path, entities_to_ignore=None, doc_type=None):
        """
        Processes a PDF: detects PII and performs physical redaction.
        Supports both native and scanned PDFs.
        Optimized for output file size.
        """
        doc = fitz.open(input_path)
        audit_results = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()

            if text.strip():
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
                # Scanned PDF or page with no text
                # We use a reasonable resolution for OCR
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                img_data = pix.tobytes("png")

                temp_img_in = f"temp_page_{page_num}.png"
                temp_img_out = f"temp_page_{page_num}_out.png"

                with open(temp_img_in, "wb") as f:
                    f.write(img_data)

                try:
                    results = self.image_redactor.redact(temp_img_in, temp_img_out, entities_to_ignore=entities_to_ignore, doc_type=doc_type)
                    audit_results.extend(results)

                    # Insert the redacted image back.
                    # To optimize size, we could use JPEG but PNG is safer for redaction quality.
                    # However, we'll rely on the overall doc optimization at save time.
                    page.insert_image(page.rect, filename=temp_img_out)
                    page.add_redact_annot(page.rect)
                    page.apply_redactions()
                    page.insert_image(page.rect, filename=temp_img_out)
                except Exception as e:
                    print(f"Warning: Could not OCR page {page_num}: {e}")
                finally:
                    if os.path.exists(temp_img_in): os.remove(temp_img_in)
                    if os.path.exists(temp_img_out): os.remove(temp_img_out)

        # Optimize the output PDF
        doc.save(
            output_path,
            garbage=4,
            deflate=True,
            clean=True
        )
        doc.close()
        return audit_results
