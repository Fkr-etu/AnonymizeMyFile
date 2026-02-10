from presidio_analyzer import AnalyzerEngine, RecognizerRegistry, PatternRecognizer, Pattern
from presidio_analyzer.nlp_engine import NlpEngineProvider
from .recognizers import FrenchLicensePlateRecognizer, FrenchInsuranceRecognizer
import yaml
import os

class FrenchAnalyzer:
    def __init__(self, custom_recognizers_path=None):
        # Configure the NLP engine to use the French model
        configuration = {
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "fr", "model_name": "fr_core_news_md"}],
        }
        provider = NlpEngineProvider(nlp_configuration=configuration)
        nlp_engine = provider.create_engine()

        # Initialize the registry and add default recognizers
        registry = RecognizerRegistry()
        registry.load_predefined_recognizers(nlp_engine=nlp_engine, languages=["fr"])

        # Add custom French recognizers (hardcoded)
        registry.add_recognizer(FrenchLicensePlateRecognizer())
        registry.add_recognizer(FrenchInsuranceRecognizer())

        # Load additional recognizers from YAML if provided
        if custom_recognizers_path and os.path.exists(custom_recognizers_path):
            self._load_custom_recognizers(registry, custom_recognizers_path)

        self.engine = AnalyzerEngine(
            nlp_engine=nlp_engine,
            registry=registry,
            default_score_threshold=0.4
        )

    def _load_custom_recognizers(self, registry, path):
        with open(path, 'r') as f:
            config = yaml.safe_load(f)
            for rec_config in config.get('recognizers', []):
                patterns = [
                    Pattern(name=p['name'], regex=p['regex'], score=p.get('score', 0.5))
                    for p in rec_config['patterns']
                ]
                recognizer = PatternRecognizer(
                    supported_entity=rec_config['entity'],
                    patterns=patterns,
                    context=rec_config.get('context')
                )
                registry.add_recognizer(recognizer)

    def analyze(self, text, entities=None):
        return self.engine.analyze(text=text, language="fr", entities=entities)
