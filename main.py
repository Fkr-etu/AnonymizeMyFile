import argparse
import os
import logging
import traceback
from anonymizer.pipeline import AnonymizationPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('anonymization.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting anonymization process...")
    parser = argparse.ArgumentParser(description="Anonymisation de documents (Images et PDF) - Français")
    parser.add_argument("--input", default="input", help="Dossier contenant les fichiers à traiter")
    parser.add_argument("--output", default="output", help="Dossier où sauvegarder les fichiers anonymisés")
    parser.add_argument("--custom-recognizers", default="custom_recognizers.yaml", help="Fichier YAML des reconnaisseurs personnalisés")
    parser.add_argument("--allow-lists", default="allow_lists.yaml", help="Fichier YAML des listes d'autorisation")
    parser.add_argument("--doc-type", help="Type de document manuel (ex: facture, devis, extrait_compte, bulletin_salaire, etc.)")
    parser.add_argument("--ignore-entities", default="DATE_TIME,CARDINAL", help="Liste d'entités à ignorer (séparées par des virgules)")

    args = parser.parse_args()

    if not os.path.exists(args.input):
        logger.error(f"Input folder '{args.input}' does not exist")
        return

    if not os.path.exists(args.output):
        os.makedirs(args.output)
        logger.info(f"Created output directory: {args.output}")

    custom_rec_path = args.custom_recognizers if os.path.exists(args.custom_recognizers) else None
    allow_lists_path = args.allow_lists if os.path.exists(args.allow_lists) else None
    entities_to_ignore = [e.strip() for e in args.ignore_entities.split(",")] if args.ignore_entities else []

    logger.info(f"Configuration: input={args.input}, output={args.output}")
    logger.info(f"Custom recognizers: {custom_rec_path}, Allow lists: {allow_lists_path}")
    logger.info(f"Entities to ignore: {entities_to_ignore}")

    try:
        pipeline = AnonymizationPipeline(
            args.output,
            custom_recognizers=custom_rec_path,
            allow_lists=allow_lists_path,
            entities_to_ignore=entities_to_ignore,
            default_doc_type=args.doc_type
        )
        logger.info("Pipeline initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize pipeline: {e}", exc_info=True)
        return

    files_to_process = [f for f in os.listdir(args.input) if os.path.isfile(os.path.join(args.input, f))]

    if not files_to_process:
        logger.warning("No files found in input folder")
        return

    logger.info(f"Found {len(files_to_process)} files to process: {files_to_process}")

    success_count = 0
    error_count = 0

    for filename in files_to_process:
        file_path = os.path.join(args.input, filename)
        logger.info(f"\n=== Processing file: {filename} ===")
        try:
            result = pipeline.process_file(file_path)
            if result:
                success_count += 1
                logger.info(f"Successfully processed: {filename}")
            else:
                logger.warning(f"Processing returned no result for: {filename}")
        except Exception as e:
            error_count += 1
            logger.error(f"Error processing {filename}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")

    logger.info(f"\n=== Processing complete ===")
    logger.info(f"Success: {success_count}, Errors: {error_count}, Total: {len(files_to_process)}")

if __name__ == "__main__":
    main()
