import unittest
from anonymizer.analyzer import FrenchAnalyzer

class TestNewDocTypes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Use default allow_lists.yaml if it exists
        cls.analyzer = FrenchAnalyzer(allow_lists_path="allow_lists.yaml")

    def test_detection_facture_achat(self):
        text = "Facture d'achat pour un ordinateur portable."
        doc_type = self.analyzer.detect_doc_type(text)
        self.assertEqual(doc_type, "facture")

    def test_detection_bulletin_salaire(self):
        text = "Ceci est un bulletin de salaire pour le mois de Janvier."
        doc_type = self.analyzer.detect_doc_type(text)
        self.assertEqual(doc_type, "bulletin_salaire")

    def test_detection_certificat_medical(self):
        text = "Certificat médical d'aptitude au sport."
        doc_type = self.analyzer.detect_doc_type(text)
        self.assertEqual(doc_type, "certificat_medical")

    def test_allow_list_from_config(self):
        # 'CARREFOUR' is in the allow-list for 'extrait_compte' in allow_lists.yaml
        text = "Paiement CARREFOUR le 12/01."

        allow_list = self.analyzer.get_allow_list(doc_type="extrait_compte")
        self.assertIn("CARREFOUR", allow_list)

        # Test analysis with allow_list
        results = self.analyzer.analyze(text, doc_type="extrait_compte")
        # Check that CARREFOUR is NOT in results (meaning it was allowed)
        for res in results:
            self.assertNotEqual(text[res.start:res.end], "CARREFOUR")

    def test_new_doc_types_detection(self):
        test_cases = [
            ("avis d'imposition 2023", "avis_imposition"),
            ("relevé de compte bancaire", "extrait_compte"),
            ("contrat de location appartement", "bail_location"),
            ("convocation à une expertise médicale", "expertise"),
            ("déclaration de dépôt de plainte", "plainte"),
            ("état de perte suite au sinistre", "etat_perte"),
            ("courrier de l'assureur adverse", "courrier_assureur"),
            ("bulletin de situation hospitalière", "bulletin_hospitalisation"),
            ("attestation d'arrêt de travail", "arret_travail"),
            ("relevé de l'organisme social", "releve_social"),
        ]

        for text, expected_type in test_cases:
            with self.subTest(text=text):
                doc_type = self.analyzer.detect_doc_type(text)
                self.assertEqual(doc_type, expected_type)

if __name__ == '__main__':
    unittest.main()
