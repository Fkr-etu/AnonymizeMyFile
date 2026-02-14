import logging
from PIL import Image, ImageDraw
from .vlm_engine import VLMEngine
from presidio_analyzer import RecognizerResult
import os

logger = logging.getLogger(__name__)

class VLMImageRedactor:
    def __init__(self, analyzer, vlm_engine: VLMEngine):
        self.analyzer = analyzer
        self.vlm_engine = vlm_engine

    def redact(self, image_path, output_path, entities_to_ignore=None, doc_type=None):
        logger.info(f"Starting VLM image redaction: {image_path}")

        # 1. Generate prompt based on analyzer rules
        prompt = self.vlm_engine.generate_prompt(self.analyzer)

        # 2. Analyze image with Gemini
        gemini_result = self.vlm_engine.analyze_image(image_path, prompt)

        # 3. Detect doc type if not provided
        detected_doc_type = gemini_result.get("document_type")
        if not doc_type and detected_doc_type:
            doc_type = detected_doc_type
            logger.info(f"VLM detected document type: {doc_type}")

        # 4. Open image to get dimensions
        try:
            image = Image.open(image_path)
            width, height = image.size
            # Convert to RGB if needed (e.g. for RGBA or palette images)
            if image.mode != "RGB":
                image = image.convert("RGB")
            draw = ImageDraw.Draw(image)
        except Exception as e:
            logger.error(f"Failed to open image {image_path}: {e}")
            raise

        # 5. Process redactions
        redaction_boxes = self.vlm_engine.get_redaction_boxes(gemini_result, width, height)
        results = []

        for item in redaction_boxes:
            entity_type = item["entity_type"]

            # Filter by entities_to_ignore
            if entities_to_ignore and entity_type in entities_to_ignore:
                continue

            box = item["box"] # (left, top, right, bottom)
            text = item["text"]

            # Draw redaction box
            draw.rectangle(box, fill=(0, 0, 0))

            # Create a RecognizerResult-like object for audit logging
            # Note: start/end might not be accurate for VLM but we can use them as placeholders
            results.append(RecognizerResult(
                entity_type=entity_type,
                start=0,
                end=len(text) if text else 0,
                score=1.0 # Gemini's confidence is assumed high if returned
            ))
            # We add a custom attribute for the audit logger if needed,
            # but standard RecognizerResult is better for compatibility.

        # 6. Save redacted image
        try:
            image.save(output_path)
            logger.info(f"Redacted image saved: {output_path}")
        except Exception as e:
            logger.error(f"Error saving redacted image: {e}")
            raise

        return results
