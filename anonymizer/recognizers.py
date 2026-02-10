from presidio_analyzer import PatternRecognizer, Pattern

class FrenchLicensePlateRecognizer(PatternRecognizer):
    def __init__(self):
        patterns = [
            Pattern(
                name="license_plate_new",
                regex=r"\b[A-Z]{2}-\d{3}-[A-Z]{2}\b",
                score=0.8
            ),
            Pattern(
                name="license_plate_old",
                # Much stricter regex for the old format:
                # 1 to 4 digits, then 1 to 3 uppercase letters (excluding some common words),
                # then 2 or 3 digits (department code).
                # Added negative lookahead to ensure the letters are not common French words like 'au', 'le', 'et'.
                regex=r"\b\d{1,4}\s(?!(?:AU|LE|LA|DU|DE|EN|UN|ET|AUX|LES)\b)[A-Z]{1,3}\s(?:0[1-9]|[1-8]\d|9[0-5]|2[AB]|97[1-8]|98[4-9])\b",
                score=0.6
            )
        ]
        super().__init__(
            supported_entity="FR_LICENSE_PLATE",
            patterns=patterns,
            context=["plaque", "immatriculation", "véhicule"],
            supported_language="fr"
        )

class FrenchInsuranceRecognizer(PatternRecognizer):
    def __init__(self):
        patterns = [
            Pattern(
                name="insurance_number",
                regex=r"\b[A-Z]{2}\s?\d{8}\b",
                score=0.8
            )
        ]
        super().__init__(
            supported_entity="FR_INSURANCE_NUMBER",
            patterns=patterns,
            context=["assurance", "police", "contrat"],
            supported_language="fr"
        )
