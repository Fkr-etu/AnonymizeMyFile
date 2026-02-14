import unittest
from unittest.mock import MagicMock, patch
from anonymizer.pipeline import AnonymizationPipeline
import os
import shutil

class TestPipelineMode(unittest.TestCase):
    def setUp(self):
        self.output_dir = "test_output"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def tearDown(self):
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)

    @patch("anonymizer.pipeline.FrenchAnalyzer")
    @patch("anonymizer.pipeline.FrenchImageRedactor")
    @patch("anonymizer.pipeline.PDFProcessor")
    def test_pipeline_ocr_mode(self, mock_pdf, mock_redactor, mock_analyzer):
        pipeline = AnonymizationPipeline(self.output_dir, mode="ocr")
        self.assertEqual(pipeline.mode, "ocr")
        mock_redactor.assert_called_once()
        # Ensure it's FrenchImageRedactor and not VLMImageRedactor
        self.assertEqual(mock_redactor.call_args[0][0], mock_analyzer.return_value)

    @patch("anonymizer.pipeline.VLMEngine")
    @patch("anonymizer.pipeline.VLMImageRedactor")
    @patch("anonymizer.pipeline.FrenchAnalyzer")
    @patch("anonymizer.pipeline.PDFProcessor")
    def test_pipeline_vlm_mode(self, mock_pdf, mock_analyzer, mock_vlm_redactor, mock_vlm_engine):
        pipeline = AnonymizationPipeline(self.output_dir, mode="vlm")
        self.assertEqual(pipeline.mode, "vlm")
        mock_vlm_redactor.assert_called_once()
        mock_vlm_engine.assert_called_once()

if __name__ == "__main__":
    unittest.main()
