from presidio_analyzer import AnalyzerEngine, RecognizerRegistry, PatternRecognizer, Pattern
from presidio_analyzer.nlp_engine import NlpEngineProvider
from .recognizers import FrenchLicensePlateRecognizer, FrenchInsuranceRecognizer
import yaml
import os
import re
import logging

logger = logging.getLogger(__name__)

class FrenchAnalyzer:
    # Common words in French documents that should not be redacted
    GLOBAL_ALLOW_LIST = [
        "euro", "euros", "tva", "TVA", "ttc", "TTC", "ht", "HT",
        "total", "Total", "montant", "Montant", "prix", "Prix", "quantité", "Quantité"
    ]

    DOC_SPECIFIC_ALLOW_LISTS = {
        "facture": ["facture", "client", "commande", "article", "fournisseur", "achat", "réparation"],
        "devis": ["devis", "prestation", "estimation", "matériaux", "main-d'oeuvre"],
        "etat_perte": ["perte", "état", "liste", "objets", "valeur", "sinistre"],
        "courrier_assureur": ["assureur", "adverse", "compagnie", "sinistre", "réclamation", "indemnisation"],
        "plainte": ["plainte", "dépôt", "procès-verbal", "commissariat", "gendarmerie", "infraction", "victime"],
        "constat_auto": ["constat", "amiable", "véhicule", "conducteur", "choc", "témoin", "assurance", "accident", "circonstances"],
        "constat_habitation": ["dégât", "eaux", "fuite", "robinet", "joint", "plafond", "infiltration", "sinistre"],
        "expertise": ["expert", "rapport", "vétusté", "dommages", "indemnisation", "conclusions", "convocation"],
        "bail_location": ["bail", "location", "contrat", "preneur", "bailleur", "loyer", "dépôt", "garantie", "locataire", "quittance"],
        "extrait_compte": ["compte", "solde", "débit", "crédit", "opération", "relevé", "virement", "prélèvement", "bancaire"],
        "avis_imposition": ["impôts", "imposition", "revenus", "fiscal", "déclaration", "avis"],
        "bulletin_salaire": ["salaire", "bulletin", "paie", "brut", "net", "cotisations", "employeur", "congés", "retraite"],
        "bulletin_hospitalisation": ["hospitalisation", "hôpital", "admis", "sortie", "soins", "bulletin", "situation"],
        "arret_travail": ["arrêt", "travail", "médical", "prolongation", "incapacité", "attestation"],
        "releve_social": ["sécurité", "sociale", "social", "allocations", "caf", "relevé", "prestations", "ameli", "organisme"],
        "certificat_medical": ["certificat", "médical", "examen", "aptitude", "santé", "docteur", "médecin", "ordonnance", "pathologie"],
        "identite": ["carte", "identité", "passeport", "titre", "séjour", "naissance", "nationalité"],
        "carte_grise": ["immatriculation", "certificat", "préfecture", "marque", "modèle", "titulaire"],
        "permis_conduire": ["permis", "conduire", "catégorie", "validité", "préfecture"],
        "rib": ["banque", "iban", "bic", "compte", "titulaire", "relevé", "identité"]
    }

    def __init__(self, custom_recognizers_path=None, allow_lists_path=None):
        logger.info("Initializing FrenchAnalyzer...")
        configuration = {
            "nlp_engine_name": "spacy",
            "models": [
                {"lang_code": "en", "model_name": "en_core_web_sm"},
                {"lang_code": "fr", "model_name": "fr_core_news_md"}
            ],
        }
        logger.debug(f"NLP configuration: {configuration}")
        provider = NlpEngineProvider(nlp_configuration=configuration)
        nlp_engine = provider.create_engine()
        logger.info("NLP engine created with models: en (lightweight), fr")

        registry = RecognizerRegistry()
        registry.load_predefined_recognizers(nlp_engine=nlp_engine, languages=["en", "fr"])
        logger.info("Predefined recognizers loaded for English and French")

        registry.add_recognizer(FrenchLicensePlateRecognizer())
        registry.add_recognizer(FrenchInsuranceRecognizer())
        logger.info("French custom recognizers added")

        if custom_recognizers_path and os.path.exists(custom_recognizers_path):
            logger.info(f"Loading custom recognizers from: {custom_recognizers_path}")
            self._load_custom_recognizers(registry, custom_recognizers_path)
        else:
            logger.debug(f"No custom recognizers file: {custom_recognizers_path}")

        self.global_allow_list = self.GLOBAL_ALLOW_LIST.copy()
        self.doc_specific_allow_lists = self.DOC_SPECIFIC_ALLOW_LISTS.copy()
        logger.info(f"Allow lists initialized: {len(self.global_allow_list)} global items")

        if allow_lists_path and os.path.exists(allow_lists_path):
            logger.info(f"Loading custom allow lists from: {allow_lists_path}")
            self._load_allow_lists(allow_lists_path)
        else:
            logger.debug(f"No custom allow lists file: {allow_lists_path}")

        # Store the registry for later access
        self.registry = registry
        
        # Create the analyzer engine with the configured registry
        logger.info("Creating AnalyzerEngine...")
        self.engine = AnalyzerEngine(
            nlp_engine=nlp_engine,
            registry=registry,
            default_score_threshold=0.4
        )
        logger.info("FrenchAnalyzer initialization complete")

    def _load_custom_recognizers(self, registry, path):
        logger.debug(f"Loading custom recognizers from {path}")
        try:
            with open(path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                count = 0
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
                    count += 1
                logger.info(f"Loaded {count} custom recognizers")
        except Exception as e:
            logger.error(f"Error loading custom recognizers: {e}", exc_info=True)

    def _load_allow_lists(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            if 'global' in config:
                self.global_allow_list.extend(config['global'])
            if 'document_specific' in config:
                for doc_type, terms in config['document_specific'].items():
                    if doc_type in self.doc_specific_allow_lists:
                        self.doc_specific_allow_lists[doc_type].extend(terms)
                    else:
                        self.doc_specific_allow_lists[doc_type] = terms

            # Clean up duplicates
            self.global_allow_list = list(set(self.global_allow_list))
            for doc_type in self.doc_specific_allow_lists:
                self.doc_specific_allow_lists[doc_type] = list(set(self.doc_specific_allow_lists[doc_type]))

    def detect_doc_type(self, text, filename=""):
        logger.debug(f"Detecting document type for: {filename}")
        combined_source = (filename + " " + text).lower()

        scores = {doc_type: 0 for doc_type in self.doc_specific_allow_lists}

        for doc_type, keywords in self.doc_specific_allow_lists.items():
            for keyword in keywords:
                # Count occurrences of keywords
                occurrences = combined_source.count(keyword.lower())
                if occurrences > 0:
                    # More weight to filename matches
                    if keyword.lower() in filename.lower():
                        scores[doc_type] += 10 * occurrences
                    else:
                        scores[doc_type] += 1 * occurrences

        best_type = max(scores, key=scores.get)
        if scores[best_type] > 0:
            logger.debug(f"Detected doc type: {best_type} (score: {scores[best_type]})")
            return best_type
        logger.debug("Could not detect document type")
        return None

    def get_allow_list(self, doc_type=None, extra_allow_list=None):
        allow_list = self.global_allow_list.copy()
        if doc_type and doc_type in self.doc_specific_allow_lists:
            allow_list.extend(self.doc_specific_allow_lists[doc_type])
        if extra_allow_list:
            allow_list.extend(extra_allow_list)
        result = list(set(allow_list))
        logger.debug(f"get_allow_list for doc_type '{doc_type}': {len(result)} items")
        return result

    def analyze(self, text, entities=None, doc_type=None, extra_allow_list=None):
        logger.info(f"Analyzing text (doc_type: {doc_type}, text_length: {len(text)})")
        allow_list = self.get_allow_list(doc_type, extra_allow_list)

        # Make the allow_list case-insensitive by adding lowercased and capitalized versions
        extended_allow_list = set()
        for term in allow_list:
            extended_allow_list.add(term)
            extended_allow_list.add(term.lower())
            extended_allow_list.add(term.upper())
            extended_allow_list.add(term.capitalize())

        results = self.engine.analyze(
            text=text,
            language="fr",
            entities=entities,
            allow_list=list(extended_allow_list)
        )
        logger.info(f"Analysis complete: found {len(results)} entities before filtering")
        
        # Apply doc_type specific filtering and confidence adjustments
        filtered_results = self._filter_by_doc_type(results, doc_type)
        logger.info(f"After doc_type filtering: {len(filtered_results)} entities")
        
        return filtered_results

    def _filter_by_doc_type(self, results, doc_type):
        """Filter and adjust results based on document type"""
        if not doc_type:
            return results
        
        min_score_threshold = 0.5  # Default minimum score
        entities_to_exclude = []
        
        # Configure filtering by document type
        if doc_type == "facture":
            min_score_threshold = 0.75  # Higher threshold for invoices
            # Exclude license plates and money amounts from invoice analysis (not sensitive in this context)
            entities_to_exclude = ["MONEY"]
            logger.debug(f"Invoice mode: min_score={min_score_threshold}, excluding {entities_to_exclude}")
        
        elif doc_type in ["constat_auto", "constat_habitation"]:
            min_score_threshold = 0.7
            logger.debug(f"Report mode: min_score={min_score_threshold}")
        
        elif doc_type == "extrait_compte":
            min_score_threshold = 0.8  # Very high for bank statements (sensitive)
            logger.debug(f"Bank statement mode: min_score={min_score_threshold}")
        
        elif doc_type == "bulletin_salaire":
            min_score_threshold = 0.75
            logger.debug(f"Payroll mode: min_score={min_score_threshold}")
        
        # Apply filtering
        filtered_results = []
        for result in results:
            # Exclude certain entity types based on doc_type
            if result.entity_type in entities_to_exclude:
                logger.debug(f"Excluding {result.entity_type} (not relevant for {doc_type})")
                continue
            
            # Apply minimum score threshold
            if result.score < min_score_threshold:
                logger.debug(f"Filtering {result.entity_type} with score {result.score} < {min_score_threshold}")
                continue
            
            filtered_results.append(result)
        
        return filtered_results
