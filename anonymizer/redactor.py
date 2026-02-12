from presidio_image_redactor import ImageRedactorEngine, ImageAnalyzerEngine
from PIL import Image
import io
import logging
from .ocr import HybridOCR
from .image_processing import ImagePreprocessor

logger = logging.getLogger(__name__)

class FrenchImageRedactor:
    def __init__(self, french_analyzer):
        self.french_analyzer = french_analyzer
        self.ocr_engine = HybridOCR()
        # Initialize ImageAnalyzerEngine with our custom HybridOCR
        self.analyzer_engine = ImageAnalyzerEngine(
            analyzer_engine=french_analyzer.engine,
            ocr=self.ocr_engine
        )
        self.image_redactor_engine = ImageRedactorEngine(image_analyzer_engine=self.analyzer_engine)

    def redact(self, image_path, output_path, entities_to_ignore=None, doc_type=None):
        logger.info(f"Starting image redaction: {image_path}")
        try:
            image = Image.open(image_path)
            logger.debug(f"Image opened successfully: {image.size}, {image.format}")
        except Exception as e:
            logger.error(f"Failed to open image {image_path}: {e}", exc_info=True)
            raise

        # 1. Image preprocessing (Solution 3)
        # We process a copy for OCR to improve detection
        try:
            processed_image = ImagePreprocessor.process_for_ocr(image)
        except Exception as e:
            logger.warning(f"Preprocessing failed, using original image: {e}")
            processed_image = image

        # 2. Get allow list
        try:
            allow_list = self.french_analyzer.get_allow_list(doc_type)
            logger.debug(f"Allow list for doc_type '{doc_type}': {len(allow_list)} items")
        except Exception as e:
            logger.error(f"Failed to get allow list: {e}", exc_info=True)
            raise

        # 3. Prepare extended allow list (case-insensitive versions)
        extended_allow_list = set()
        for term in allow_list:
            extended_allow_list.add(term)
            extended_allow_list.add(term.lower())
            extended_allow_list.add(term.upper())
            extended_allow_list.add(term.capitalize())

        # 4. Choose OCR engine based on doc_type (Solution 2)
        # Use EasyOCR for constats by default
        ocr_engine = "tesseract"
        if doc_type and "constat" in doc_type:
            ocr_engine = "easyocr"
            logger.info("Using EasyOCR engine for handwriting support")

        # 5. Analyze for audit logging
        try:
            logger.info(f"Starting image analysis with {ocr_engine}...")
            # Keyword arguments are passed to text analyzer's analyze method in Presidio 0.0.57
            analysis_results = self.analyzer_engine.analyze(
                processed_image,
                language="fr",
                allow_list=allow_list,
                ocr_engine=ocr_engine
            )
            logger.info(f"Image analysis completed. Found {len(analysis_results)} entities")
        except Exception as e:
            logger.error(f"Error during image analysis: {e}", exc_info=True)
            analysis_results = []

        # 6. Filter out ignored entities and allow-listed items
        filtered_results = []
        ignored_count = 0
        allow_listed_count = 0
        duplicate_count = 0

        seen_locations = set()

        for res in analysis_results:
            # Skip ignored entity types
            if entities_to_ignore and res.entity_type in entities_to_ignore:
                ignored_count += 1
                logger.debug(f"Ignored entity (type): {res.entity_type}")
                continue

            # Deduplicate
            location_key = (res.start, res.end, res.entity_type)
            if location_key in seen_locations:
                duplicate_count += 1
                continue
            seen_locations.add(location_key)

            text_value = getattr(res, 'value', getattr(res, 'text', ''))

            # Skip items in the allow list
            if text_value and (text_value in extended_allow_list or text_value.lower() in {t.lower() for t in extended_allow_list}):
                allow_listed_count += 1
                logger.debug(f"Ignored entity (allow-list): {text_value}")
                continue

            filtered_results.append(res)

        logger.info(f"Filtered results: {len(filtered_results)} to redact, {ignored_count} ignored by type, {allow_listed_count} ignored by allow-list, {duplicate_count} duplicates")

        # 7. Redact the image
        # We redact on the ORIGINAL image, using results from the processed one
        try:
            logger.info("Starting physical redaction on original image...")
            redacted_image = self.image_redactor_engine.redact(
                image,
                fill=(0, 0, 0),
                analyzer_results=filtered_results
            )
            logger.info("Image redaction completed")
        except Exception as e:
            logger.error(f"Error during image redaction: {e}", exc_info=True)
            raise

        try:
            redacted_image.save(output_path)
            logger.info(f"Redacted image saved: {output_path}")
        except Exception as e:
            logger.error(f"Error saving redacted image: {e}", exc_info=True)
            raise

        return filtered_results
