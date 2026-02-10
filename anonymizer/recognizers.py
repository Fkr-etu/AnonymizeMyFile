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
                regex=r"\b\d{1,4}\s[A-Z]{1,2}\s\d{2,3}\b",
                score=0.8
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
