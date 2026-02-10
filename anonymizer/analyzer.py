from presidio_analyzer import AnalyzerEngine, RecognizerRegistry, PatternRecognizer, Pattern
from presidio_analyzer.nlp_engine import NlpEngineProvider
from .recognizers import FrenchLicensePlateRecognizer, FrenchInsuranceRecognizer
import yaml
import os
import re

class FrenchAnalyzer:
    # Common words in French documents that should not be redacted
    GLOBAL_ALLOW_LIST = [
        "euro", "euros", "tva", "TVA", "ttc", "TTC", "ht", "HT",
        "total", "Total", "montant", "Montant", "prix", "Prix", "quantité", "Quantité"
    ]

    DOC_SPECIFIC_ALLOW_LISTS = {
        "quittance": ["loyer", "Loyer", "charges", "Charges", "quittance", "Quittance", "location", "Location", "bail", "Bail"],
        "facture": ["facture", "Facture", "client", "Client", "commande", "Commande", "article", "Article"],
        "devis": ["devis", "Devis", "prestation", "Prestation", "estimation", "Estimation"],
        "constat": ["constat", "Constat", "amiable", "Amiable", "véhicule", "Véhicule", "conducteur", "Conducteur", "choc", "Choc", "témoin", "Témoin", "assurance", "Assurance", "accident", "Accident"]
    }

    def __init__(self, custom_recognizers_path=None):
        configuration = {
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "fr", "model_name": "fr_core_news_md"}],
        }
        provider = NlpEngineProvider(nlp_configuration=configuration)
        nlp_engine = provider.create_engine()

        registry = RecognizerRegistry()
        registry.load_predefined_recognizers(nlp_engine=nlp_engine, languages=["fr"])

        registry.add_recognizer(FrenchLicensePlateRecognizer())
        registry.add_recognizer(FrenchInsuranceRecognizer())

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
                    context=rec_config.get('context'),
                    supported_language="fr"
                )
                registry.add_recognizer(recognizer)

    def detect_doc_type(self, text, filename=""):
        combined_source = (filename + " " + text).lower()

        scores = {doc_type: 0 for doc_type in self.DOC_SPECIFIC_ALLOW_LISTS}

        for doc_type, keywords in self.DOC_SPECIFIC_ALLOW_LISTS.items():
            for keyword in keywords:
                if keyword.lower() in combined_source:
                    # Give more weight to keywords found in filename
                    if keyword.lower() in filename.lower():
                        scores[doc_type] += 5
                    else:
                        scores[doc_type] += 1

        best_type = max(scores, key=scores.get)
        if scores[best_type] > 0:
            return best_type
        return None

    def analyze(self, text, entities=None, doc_type=None, extra_allow_list=None):
        allow_list = self.GLOBAL_ALLOW_LIST.copy()

        if doc_type and doc_type in self.DOC_SPECIFIC_ALLOW_LISTS:
            allow_list.extend(self.DOC_SPECIFIC_ALLOW_LISTS[doc_type])

        if extra_allow_list:
            allow_list.extend(extra_allow_list)

        return self.engine.analyze(
            text=text,
            language="fr",
            entities=entities,
            allow_list=list(set(allow_list)) # Remove duplicates
        )
