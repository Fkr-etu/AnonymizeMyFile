from presidio_image_redactor import ImageRedactorEngine, ImageAnalyzerEngine
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)

class FrenchImageRedactor:
    def __init__(self, french_analyzer):
        self.french_analyzer = french_analyzer
        self.analyzer_engine = ImageAnalyzerEngine(analyzer_engine=french_analyzer.engine)
        self.image_redactor_engine = ImageRedactorEngine(image_analyzer_engine=self.analyzer_engine)

    def redact(self, image_path, output_path, entities_to_ignore=None, doc_type=None):
        logger.info(f"Starting image redaction: {image_path}")
        try:
            image = Image.open(image_path)
            logger.debug(f"Image opened successfully: {image.size}, {image.format}")
        except Exception as e:
            logger.error(f"Failed to open image {image_path}: {e}", exc_info=True)
            raise

        # 1. Get allow list
        try:
            allow_list = self.french_analyzer.get_allow_list(doc_type)
            logger.debug(f"Allow list for doc_type '{doc_type}': {len(allow_list)} items")
        except Exception as e:
            logger.error(f"Failed to get allow list: {e}", exc_info=True)
            raise

        # 2. Prepare extended allow list (case-insensitive versions)
        extended_allow_list = set()
        for term in allow_list:
            extended_allow_list.add(term)
            extended_allow_list.add(term.lower())
            extended_allow_list.add(term.upper())
            extended_allow_list.add(term.capitalize())

        # 3. Analyze for audit logging
        try:
            logger.info("Starting image analysis...")
            # ImageAnalyzerEngine.analyze() may not support all parameters
            # Try with minimal parameters first
            analysis_results = self.analyzer_engine.analyze(image, language="fr")
            logger.info(f"Image analysis completed. Found {len(analysis_results)} entities")
        except Exception as e:
            logger.error(f"Error during image analysis: {e}", exc_info=True)
            analysis_results = []

        # 4. Filter out ignored entities and allow-listed items
        filtered_results = []
        ignored_count = 0
        allow_listed_count = 0
        duplicate_count = 0
        
        # Track seen entities to avoid duplicates (same location)
        seen_locations = set()
        
        for res in analysis_results:
            # Skip ignored entity types
            if entities_to_ignore and res.entity_type in entities_to_ignore:
                ignored_count += 1
                logger.debug(f"Ignored entity (type): {res.entity_type}")
                continue
            
            # Deduplicate: skip if we've already seen an entity at this exact location
            location_key = (res.start, res.end, res.entity_type)
            if location_key in seen_locations:
                duplicate_count += 1
                logger.debug(f"Duplicate entity at location {res.start}-{res.end}: {res.entity_type}")
                continue
            seen_locations.add(location_key)
            
            # Get the text value from the result (could be 'value' or 'text' depending on result type)
            text_value = getattr(res, 'value', getattr(res, 'text', ''))
            
            # Skip items in the allow list (case-insensitive)
            if text_value and (text_value in extended_allow_list or text_value.lower() in {t.lower() for t in extended_allow_list}):
                allow_listed_count += 1
                logger.debug(f"Ignored entity (allow-list): {text_value}")
                continue
            
            filtered_results.append(res)
        
        logger.info(f"Filtered results: {len(filtered_results)} to redact, {ignored_count} ignored by type, {allow_listed_count} ignored by allow-list, {duplicate_count} duplicates")

        # 5. Redact the image
        try:
            logger.info("Starting image redaction...")
            redacted_image = self.image_redactor_engine.redact(
                image, 
                fill=(0, 0, 0)
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

