from presidio_image_redactor import ImageRedactorEngine, ImageAnalyzerEngine
from PIL import Image
from .ocr import HybridOCR
from .image_processing import ImagePreprocessor

class FrenchImageRedactor:
    def __init__(self, french_analyzer):
        self.french_analyzer = french_analyzer
        self.ocr_engine = HybridOCR()
        # Initialize ImageAnalyzerEngine with our custom HybridOCR
        self.analyzer_engine = ImageAnalyzerEngine(
            analyzer_engine=french_analyzer.engine,
            ocr=self.ocr_engine
        )
        self.engine = ImageRedactorEngine(image_analyzer_engine=self.analyzer_engine)

    def redact(self, image_path, output_path, entities_to_ignore=None, doc_type=None):
        image = Image.open(image_path)

        # 1. Image preprocessing (Solution 3)
        # We process a copy for OCR to improve detection
        processed_image = ImagePreprocessor.process_for_ocr(image)

        # 2. Get allow list
        allow_list = self.french_analyzer.get_allow_list(doc_type)

        # 3. Choose OCR engine based on doc_type (Solution 2)
        # Use EasyOCR for constats by default
        ocr_engine = "tesseract"
        if doc_type and "constat" in doc_type:
            ocr_engine = "easyocr"

        # 4. Analyze for audit
        # We use the processed image for analysis
        analysis_results = self.analyzer_engine.analyze(
            processed_image,
            language="fr",
            allow_list=allow_list,
            ocr_engine=ocr_engine # Passed to HybridOCR.perform_ocr
        )

        # 5. Filter out ignored entities
        filtered_results = []
        for res in analysis_results:
            if entities_to_ignore and res.entity_type in entities_to_ignore:
                continue
            filtered_results.append(res)

        # 6. Redact
        # We redact on the ORIGINAL image, using results from the processed one
        redacted_image = self.engine.redact(image, fill=(0, 0, 0), analyzer_results=filtered_results)

        redacted_image.save(output_path)
        return filtered_results
