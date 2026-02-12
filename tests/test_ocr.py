import unittest
from anonymizer.ocr import HybridOCR
from PIL import Image
import os
from unittest.mock import MagicMock, patch

class TestHybridOCR(unittest.TestCase):
    @patch('anonymizer.ocr.TesseractOCR')
    def test_switch_engine(self, mock_tesseract):
        mock_tesseract_instance = mock_tesseract.return_value
        mock_tesseract_instance.perform_ocr.return_value = {"text": ["hello"], "left": [0], "top": [0], "width": [1], "height": [1], "conf": [100]}

        ocr = HybridOCR()
        ocr.tesseract = mock_tesseract_instance

        img = Image.new('RGB', (10, 10))
        img_path = "test_ocr.png"
        img.save(img_path)

        # Test Tesseract (default)
        res = ocr.perform_ocr(img_path)
        self.assertEqual(res["text"], ["hello"])
        mock_tesseract_instance.perform_ocr.assert_called_once()

        if os.path.exists(img_path): os.remove(img_path)

if __name__ == '__main__':
    unittest.main()
