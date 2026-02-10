# Projet d'Anonymisation de Documents (Images et PDF)

Ce projet utilise Microsoft Presidio pour détecter et anonymiser des informations personnelles (PII) dans des documents français (factures, devis, constats automobiles, etc.).

## Fonctionnalités

- **Support Multi-format** : Traitement des images (JPG, PNG, TIFF) et des fichiers PDF (natifs et scannés).
- **Rédaction Physique Sécurisée** :
  - Utilise `PyMuPDF` (fitz) pour les PDF, garantissant la suppression définitive des données textuelles sous-jacentes (rédaction physique).
  - Support des **PDF scannés** via une conversion automatique en images et un traitement OCR.
- **Extraction intelligente** :
  - Utilise `PyMuPDF` pour l'extraction de texte natif.
  - Utilise `Tesseract OCR` via `presidio-image-redactor` pour les images et PDF scannés.
- **Détection spécialisée pour la France** :
  - Intégration du modèle spaCy `fr_core_news_md`.
  - Reconnaisseurs personnalisés pour les plaques d'immatriculation (nouveaux et anciens formats).
  - Reconnaisseurs pour les numéros de police d'assurance.
- **Piste d'Audit** : Génère un fichier JSON détaillé pour chaque document traité, listant les entités détectées et masquées.
- **Extensibilité** : Possibilité d'ajouter facilement de nouveaux types d'entités via un fichier YAML.

## Installation

### Dépendances système

Le projet nécessite Tesseract OCR installé sur votre système :

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-fra libtesseract-dev
```

### Installation Python

```bash
pip install -r requirements.txt
python -m spacy download fr_core_news_md
```

## Utilisation

Placez vos documents dans le dossier `input/` puis lancez :

```bash
python main.py --input input --output output
```

Les documents anonymisés et leurs logs d'audit seront disponibles dans le dossier `output/`.

### Ajout de reconnaisseurs personnalisés

Vous pouvez ajouter de nouvelles entités sans modifier le code via le fichier `custom_recognizers.yaml` :

```yaml
recognizers:
  - entity: "FR_CONTRACT_NUMBER"
    patterns:
      - name: "contract_number"
        regex: "CN-\\d{6}"
        score: 0.9
    context: ["contrat", "numéro"]
```

## Structure du projet

- `main.py` : Point d'entrée de la ligne de commande (CLI).
- `anonymizer/` :
    - `analyzer.py` : Moteur de détection configuré pour le français.
    - `recognizers.py` : Définition des reconnaisseurs spécifiques (plaques, assurance).
    - `pdf_processor.py` : Logique de traitement des PDF (natifs et scannés).
    - `redactor.py` : Logique de masquage des images.
    - `pipeline.py` : Orchestration globale.
    - `utils.py` : Gestion des logs d'audit.
- `tests/` : Tests unitaires.

## Tests

Pour lancer les tests :

```bash
python -m unittest discover tests
```
