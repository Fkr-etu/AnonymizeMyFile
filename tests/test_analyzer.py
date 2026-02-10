import unittest
from anonymizer.analyzer import FrenchAnalyzer

class TestAnalyzer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.analyzer = FrenchAnalyzer()

    def test_french_pii(self):
        text = "Je m'appelle Jean Dupont et j'habite à Paris."
        results = self.analyzer.analyze(text)
        entities = [r.entity_type for r in results]
        print(f"Entities found for PII test: {entities}")
        self.assertTrue(any(e in ["PERSON", "PER"] for e in entities))
        self.assertTrue(any(e in ["LOCATION", "LOC"] for e in entities))

    def test_custom_recognizer_integration(self):
        text = "Voici ma plaque : AB-123-CD"
        # Try explicitly requesting the entity
        results = self.analyzer.analyze(text, entities=["FR_LICENSE_PLATE"])
        entities = [r.entity_type for r in results]
        print(f"Entities found for license plate (explicit): {entities}")
        self.assertIn("FR_LICENSE_PLATE", entities)

if __name__ == '__main__':
    unittest.main()
