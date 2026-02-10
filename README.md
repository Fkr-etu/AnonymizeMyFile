# Projet d'Anonymisation de Documents (Images et PDF)

Ce projet utilise Microsoft Presidio pour détecter et anonymiser des informations personnelles (PII) dans des documents français (factures, devis, constats automobiles, etc.).

## Fonctionnalités

- **Support Multi-format** : Traitement des images (JPG, PNG, TIFF) et des fichiers PDF (natifs et scannés).
- **Rédaction Physique Sécurisée** :
  - Utilise `PyMuPDF` (fitz) pour les PDF, garantissant la suppression définitive des données textuelles sous-jacentes (rédaction physique).
  - Support des **PDF scannés** via une conversion automatique en images et un traitement OCR.
- **Intelligence Contextuelle** :
  - **Détection automatique du type de document** (Quittance, Facture, Devis, Constat) pour réduire les faux positifs sur les termes techniques (ex: "Loyer", "Total", "Charges").
  - Utilisation d'**allow-lists** globales et spécifiques par type de document.
- **Extraction intelligente** :
  - Utilise `PyMuPDF` pour l'extraction de texte natif.
  - Utilise `Tesseract OCR` via `presidio-image-redactor` pour les images et PDF scannés.
- **Détection spécialisée pour la France** :
  - Intégration du modèle spaCy `fr_core_news_md`.
  - Reconnaisseurs personnalisés pour les plaques d'immatriculation (nouveaux et anciens formats) avec protection contre les faux positifs sur les dates.
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

### Options avancées

- `--doc-type` : Forcer le type de document (`quittance`, `facture`, `devis`, `constat`). Par défaut, le type est deviné automatiquement.
- `--ignore-entities` : Liste d'entités à ne pas masquer, séparées par des virgules (par défaut : `DATE_TIME`).
- `--custom-recognizers` : Chemin vers un fichier YAML de reconnaisseurs personnalisés.

Exemple :
```bash
python main.py --input input --output output --doc-type quittance --ignore-entities DATE_TIME,LOCATION
```

## Structure du projet

- `main.py` : Point d'entrée de la ligne de commande (CLI).
- `anonymizer/` :
    - `analyzer.py` : Moteur de détection configuré pour le français avec gestion du contexte.
    - `recognizers.py` : Définition des reconnaisseurs spécifiques.
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
