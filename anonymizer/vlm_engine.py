import google.generativeai as genai
import os
import json
import logging
import time
from PIL import Image
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class VLMEngine:
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-1.5-flash"):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            logger.error("GOOGLE_API_KEY not found in environment variables")
        else:
            genai.configure(api_key=self.api_key)

        self.model_name = model_name
        self.model = genai.GenerativeModel(model_name)
        logger.info(f"VLMEngine initialized with model: {model_name}")

    def generate_prompt(self, analyzer) -> str:
        """
        Generates a system prompt based on the rules in FrenchAnalyzer.
        """
        doc_types = list(analyzer.doc_specific_allow_lists.keys())
        global_allow_list = analyzer.global_allow_list
        doc_specific_rules = ""
        for doc_type, allow_list in analyzer.doc_specific_allow_lists.items():
            doc_specific_rules += f"- {doc_type} : ne pas anonymiser {', '.join(allow_list)}\n"

        prompt = f"""
Vous êtes un expert en anonymisation de documents français. Votre tâche est d'analyser l'image d'un document fournie et de :
1. Identifier le type de document parmi cette liste : {', '.join(doc_types)}.
2. Détecter toutes les informations personnelles (PII) à anonymiser.

Entités à anonymiser :
- Noms de personnes (PERSON)
- Adresses postales (LOCATION)
- Numéros de téléphone (PHONE_NUMBER)
- Adresses e-mail (EMAIL_ADDRESS)
- Numéros de sécurité sociale (FR_NIR)
- Numéros de comptes bancaires (IBAN/BBAN)
- Plaques d'immatriculation (FR_LICENSE_PLATE)
- Numéros de police d'assurance (FR_INSURANCE_NUMBER)

Règles de protection (NE PAS ANONYMISER) :
- Liste globale : {', '.join(global_allow_list)}.
- Par type de document :
{doc_specific_rules}

Pour chaque entité détectée (qui n'est pas dans les listes de protection), vous devez fournir le texte exact et ses coordonnées sous forme de boîte englobante [ymin, xmin, ymax, xmax] avec des valeurs normalisées de 0 à 1000.

Répondez EXCLUSIVEMENT sous format JSON avec la structure suivante :
{{
  "document_type": "type_détecté",
  "entities": [
    {{
      "entity_type": "TYPE_ENTITE",
      "text": "texte détecté",
      "box_2d": [ymin, xmin, ymax, xmax]
    }}
  ]
}}
"""
        return prompt

    def analyze_image(self, image_path: str, prompt: str) -> Dict[str, Any]:
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY is missing. Please set it in your .env file.")

        logger.info(f"Sending image to Gemini ({self.model_name}): {image_path}")
        try:
            with Image.open(image_path) as img:
                # Using a retry mechanism for API calls
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        response = self.model.generate_content(
                            [prompt, img],
                            generation_config=genai.types.GenerationConfig(
                                candidate_count=1,
                                stop_sequences=[],
                                max_output_tokens=2048,
                                temperature=0.1,
                                response_mime_type="application/json"
                            )
                        )

                        if response.text:
                            result = json.loads(response.text)
                            logger.info(f"Gemini analysis successful. Detected type: {result.get('document_type')}")
                            return result
                        else:
                            logger.warning("Empty response from Gemini")
                    except Exception as e:
                        logger.warning(f"Attempt {attempt + 1} failed: {e}")
                        if attempt < max_retries - 1:
                            time.sleep(2)
                        else:
                            raise e

                return {"document_type": None, "entities": []}

        except Exception as e:
            logger.error(f"Error during Gemini analysis: {e}", exc_info=True)
            return {"document_type": None, "entities": []}

    def get_redaction_boxes(self, gemini_result: Dict[str, Any], img_width: int, img_height: int) -> List[Dict[str, Any]]:
        """
        Converts normalized Gemini boxes [ymin, xmin, ymax, xmax] to pixel coordinates.
        """
        redaction_data = []
        for entity in gemini_result.get("entities", []):
            box = entity.get("box_2d")
            if box and len(box) == 4:
                ymin, xmin, ymax, xmax = box
                # Convert normalized to pixel coordinates
                left = xmin * img_width / 1000
                top = ymin * img_height / 1000
                right = xmax * img_width / 1000
                bottom = ymax * img_height / 1000

                redaction_data.append({
                    "entity_type": entity.get("entity_type"),
                    "text": entity.get("text"),
                    "box": (left, top, right, bottom)
                })
        return redaction_data
