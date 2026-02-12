import unittest
from anonymizer.ocr import HybridOCR
from PIL import Image
import os
from unittest.mock import MagicMock, patch

class TestHybridOCR(unittest.TestCase):
    @patch('anonymizer.ocr.TesseractOCR')
    def test_switch_engine(self, mock_tesseract):
        mock_tesseract_instance = mock_tesseract.return_value
        mock_tesseract_instance.perform_ocr.return_value = {"text": ["hello"]}

        ocr = HybridOCR()
        # Mocking tesseract attribute directly because it's initialized in __init__
        ocr.tesseract = mock_tesseract_instance

        # Create dummy image
        img = Image.new('RGB', (10, 10))
        img.save("test.png")

        # Test Tesseract (default)
        res = ocr.perform_ocr("test.png")
        self.assertEqual(res["text"], ["hello"])
        mock_tesseract_instance.perform_ocr.assert_called_once()

        if os.path.exists("test.png"): os.remove("test.png")

if __name__ == '__main__':
    unittest.main()
