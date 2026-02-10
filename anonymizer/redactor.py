from presidio_image_redactor import ImageRedactorEngine, ImageAnalyzerEngine
from PIL import Image, ImageChops, ImageDraw
import io

class FrenchImageRedactor:
    def __init__(self, french_analyzer):
        self.french_analyzer = french_analyzer
        self.analyzer_engine = ImageAnalyzerEngine(analyzer_engine=french_analyzer.engine)
        self.engine = ImageRedactorEngine(image_analyzer_engine=self.analyzer_engine)

    def redact(self, image_path, output_path, entities_to_ignore=None, doc_type=None):
        image = Image.open(image_path)

        # 1. Get allow list
        allow_list = self.french_analyzer.get_allow_list(doc_type)

        # 2. Analyze for audit
        # Keyword arguments (except image and ocr_kwargs) are passed to text analyzer's analyze method
        analysis_results = self.analyzer_engine.analyze(
            image,
            language="fr",
            allow_list=allow_list
        )

        # 3. Filter out ignored entities
        filtered_results = []
        for res in analysis_results:
            if entities_to_ignore and res.entity_type in entities_to_ignore:
                continue
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
