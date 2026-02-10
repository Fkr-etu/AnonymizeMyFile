from presidio_image_redactor import ImageRedactorEngine, ImageAnalyzerEngine
from PIL import Image, ImageChops, ImageDraw
import io

class FrenchImageRedactor:
    def __init__(self, analyzer_engine):
        self.engine = ImageRedactorEngine(image_analyzer_engine=analyzer_engine)
        self.analyzer_engine = ImageAnalyzerEngine(analyzer_engine=analyzer_engine)

    def redact(self, image_path, output_path, entities_to_keep=None, doc_type=None):
        image = Image.open(image_path)

        # 1. Analyze for audit
        # Note: Presidio's ImageAnalyzerEngine doesn't easily support allow_list
        # because it's built on OCR + Analyzer.
        # For simplicity, we filter the results after analysis.
        analysis_results = self.analyzer_engine.analyze(image, language="fr")

        # 2. Filter results
        filtered_results = []
        for res in analysis_results:
            if entities_to_keep and res.entity_type in entities_to_keep:
                continue

            # Since we don't have the text easily from ImageAnalyzerEngine results
            # without re-OCR or more complex logic, the allow_list is harder to apply
            # here than in text-based PDF.
            # But most false positives (Loyer, Total) are better handled in text.
            filtered_results.append(res)

        # 3. Redact using bbox processor to avoid re-calling OCR/analyzer
        analyzer_bboxes = self.engine.bbox_processor.get_bboxes_from_analyzer_results(
            filtered_results
        )

        redacted_image = ImageChops.duplicate(image)
        draw = ImageDraw.Draw(redacted_image)

        for box in analyzer_bboxes:
            x0 = box["left"]
            y0 = box["top"]
            x1 = x0 + box["width"]
            y1 = y0 + box["height"]
            draw.rectangle([x0, y0, x1, y1], fill=(0, 0, 0))

        redacted_image.save(output_path)
        return filtered_results
