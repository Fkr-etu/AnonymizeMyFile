import unittest
import os
import json
import shutil
from anonymizer.utils import AuditLogger
from presidio_analyzer import RecognizerResult

class TestAuditLogger(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_output"
        if not os.path.exists(self.test_dir):
            os.makedirs(self.test_dir)
        self.logger = AuditLogger(self.test_dir)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_log_process(self):
        results = [
            RecognizerResult(entity_type="PERSON", start=0, end=4, score=0.9)
        ]
        audit_path = self.logger.log_process("test.pdf", results)

        self.assertTrue(os.path.exists(audit_path))
        with open(audit_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertEqual(data["filename"], "test.pdf")
            self.assertEqual(len(data["detections"]), 1)
            self.assertEqual(data["detections"][0]["entity_type"], "PERSON")

if __name__ == '__main__':
    unittest.main()
