import unittest
from unittest.mock import MagicMock, patch
from anonymizer.vlm_engine import VLMEngine
from anonymizer.analyzer import FrenchAnalyzer
import os

class TestVLMEngine(unittest.TestCase):
    def setUp(self):
        # Mock API key to avoid initialization error
        self.vlm = VLMEngine(api_key="fake_key")
        self.analyzer = FrenchAnalyzer()

    def test_generate_prompt(self):
        prompt = self.vlm.generate_prompt(self.analyzer)
        self.assertIn("Vous êtes un expert en anonymisation", prompt)
        self.assertIn("facture", prompt) # One of the doc types
        self.assertIn("euro", prompt) # One of the global allow list terms
        self.assertIn("JSON", prompt)

    def test_get_redaction_boxes(self):
        gemini_result = {
            "document_type": "facture",
            "entities": [
                {
                    "entity_type": "PERSON",
                    "text": "Jean Dupont",
                    "box_2d": [100, 200, 150, 400] # [ymin, xmin, ymax, xmax]
                }
            ]
        }
        # Image 1000x1000 for easy math
        boxes = self.vlm.get_redaction_boxes(gemini_result, 1000, 1000)

        self.assertEqual(len(boxes), 1)
        # Gemini [ymin, xmin, ymax, xmax] -> [100, 200, 150, 400]
        # Pixel (left, top, right, bottom)
        # left = xmin * 1000 / 1000 = 200
        # top = ymin * 1000 / 1000 = 100
        # right = xmax * 1000 / 1000 = 400
        # bottom = ymax * 1000 / 1000 = 150
        self.assertEqual(boxes[0]["box"], (200.0, 100.0, 400.0, 150.0))
        self.assertEqual(boxes[0]["entity_type"], "PERSON")
        self.assertEqual(boxes[0]["text"], "Jean Dupont")

    @patch("google.generativeai.GenerativeModel.generate_content")
    def test_analyze_image_success(self, mock_generate):
        # Mock response from Gemini
        mock_response = MagicMock()
        mock_response.text = '{"document_type": "facture", "entities": []}'
        mock_generate.return_value = mock_response

        # Create a real small image file
        from PIL import Image
        img = Image.new('RGB', (10, 10), color='red')
        img.save("test_image.png")

        try:
            result = self.vlm.analyze_image("test_image.png", "fake prompt")
            self.assertEqual(result["document_type"], "facture")
            self.assertEqual(result["entities"], [])
        finally:
            if os.path.exists("test_image.png"):
                os.remove("test_image.png")

if __name__ == "__main__":
    unittest.main()
