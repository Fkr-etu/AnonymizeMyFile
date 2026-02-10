from anonymizer.analyzer import FrenchAnalyzer
from anonymizer.redactor import FrenchImageRedactor
from unittest.mock import MagicMock
from PIL import Image
import os

def test_consistency():
    analyzer = FrenchAnalyzer()
    redactor = FrenchImageRedactor(analyzer)

    # Mock the analyzer engine to see what it receives
    analyzer.engine.analyze = MagicMock(return_value=[])

    # Test text analysis
    text = "Le loyer est de 500 euros"
    analyzer.analyze(text, doc_type="quittance")

    # Get the allow_list passed to text analyzer
    text_allow_list = analyzer.engine.analyze.call_args[1]['allow_list']
    print(f"Text allow_list: {text_allow_list}")

    # Test image analysis
    # We mock the analyzer_engine inside redactor
    redactor.analyzer_engine.analyze = MagicMock(return_value=[])

    # Create a dummy image
    img = Image.new('RGB', (100, 100))
    img_path = "dummy.png"
    img.save(img_path)

    redactor.redact(img_path, "dummy_out.png", doc_type="quittance")

    # Check what was passed to ImageAnalyzerEngine.analyze
    # In redactor.py we call: analyze(image, language="fr", allow_list=allow_list)
    image_kwargs = redactor.analyzer_engine.analyze.call_args[1]
    image_allow_list = image_kwargs.get('allow_list', [])

    print(f"Image allow_list: {image_allow_list}")
    assert set(text_allow_list) == set(image_allow_list)
    assert image_kwargs.get('language') == 'fr'

    print("Consistency verified: Both use the same allow_list and language!")

    if os.path.exists(img_path): os.remove(img_path)
    if os.path.exists("dummy_out.png"): os.remove("dummy_out.png")

if __name__ == "__main__":
    test_consistency()
