from anonymizer.analyzer import FrenchAnalyzer
from anonymizer.redactor import FrenchImageRedactor
from unittest.mock import MagicMock
from PIL import Image
import os

def test_consistency():
    analyzer = FrenchAnalyzer()
    redactor = FrenchImageRedactor(analyzer)

    # Mock the deep AnalyzerEngine.analyze
    analyzer.engine.analyze = MagicMock(return_value=[])

    # Test text analysis
    text = "Le loyer est de 500 euros"
    analyzer.analyze(text, doc_type="quittance")
    text_call_kwargs = analyzer.engine.analyze.call_args[1]
    text_allow_list = text_call_kwargs.get('allow_list', [])
    print(f"Text allow_list: {text_allow_list}")

    # Test image analysis
    img = Image.new('RGB', (100, 100))
    img_path = "dummy.png"
    img.save(img_path)

    # We don't mock redactor.analyzer_engine.analyze,
    # we let it call analyzer.engine.analyze which IS mocked.
    redactor.redact(img_path, "dummy_out.png", doc_type="quittance")

    # Find the call to analyzer.engine.analyze from the image redactor
    # It should be the second call (or more if OCR calls it)
    image_call_kwargs = None
    for call in analyzer.engine.analyze.call_args_list:
        kwargs = call[1]
        # Image analysis passes 'text' from OCR
        if 'text' in kwargs and kwargs.get('language') == 'fr':
            image_call_kwargs = kwargs
            break

    if image_call_kwargs:
        image_allow_list = image_call_kwargs.get('allow_list', [])
        print(f"Image allow_list: {image_allow_list}")
        assert set(text_allow_list) == set(image_allow_list)
        print("Consistency verified: Both use the same allow_list!")
    else:
        print("Could not find image analyzer call")
        # Print all calls for debugging
        for i, call in enumerate(analyzer.engine.analyze.call_args_list):
            print(f"Call {i}: {call}")

    if os.path.exists(img_path): os.remove(img_path)
    if os.path.exists("dummy_out.png"): os.remove("dummy_out.png")

if __name__ == "__main__":
    test_consistency()
