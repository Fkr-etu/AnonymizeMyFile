import unittest
from anonymizer.recognizers import FrenchLicensePlateRecognizer, FrenchInsuranceRecognizer
from presidio_analyzer import RecognizerResult

class TestRecognizers(unittest.TestCase):
    def test_license_plate_new(self):
        rec = FrenchLicensePlateRecognizer()
        results = rec.analyze("Ma plaque est AA-123-BB", ["FR_LICENSE_PLATE"])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].entity_type, "FR_LICENSE_PLATE")
        self.assertEqual(results[0].start, 14)
        self.assertEqual(results[0].end, 23)

    def test_license_plate_old(self):
        rec = FrenchLicensePlateRecognizer()
        results = rec.analyze("Ancienne plaque 1234 AB 75", ["FR_LICENSE_PLATE"])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].entity_type, "FR_LICENSE_PLATE")

    def test_insurance_number(self):
        rec = FrenchInsuranceRecognizer()
        results = rec.analyze("Mon contrat AA 12345678", ["FR_INSURANCE_NUMBER"])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].entity_type, "FR_INSURANCE_NUMBER")

if __name__ == '__main__':
    unittest.main()
