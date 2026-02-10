from presidio_image_redactor import ImageRedactorEngine, ImageAnalyzerEngine
from PIL import Image
import io

class FrenchImageRedactor:
    def __init__(self, analyzer_engine):
        self.engine = ImageRedactorEngine(image_analyzer_engine=analyzer_engine)
        self.analyzer_engine = ImageAnalyzerEngine(analyzer_engine=analyzer_engine)

    def redact(self, image_path, output_path):
        image = Image.open(image_path)

        # 1. Analyze for audit
        analysis_results = self.analyzer_engine.analyze(image, language="fr")

        # 2. Redact
        # Note: we could pass analysis_results to redact to avoid double work if supported,
        # but presidio's redact usually does its own analysis if not provided.
        # Actually, redact accepts analyzer_results
        redacted_image = self.engine.redact(image, fill=(0, 0, 0), analyzer_results=analysis_results)

        redacted_image.save(output_path)
        return analysis_results
