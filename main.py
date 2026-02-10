import argparse
import os
from anonymizer.pipeline import AnonymizationPipeline

def main():
    parser = argparse.ArgumentParser(description="Anonymisation de documents (Images et PDF) - Français")
    parser.add_argument("--input", default="input", help="Dossier contenant les fichiers à traiter")
    parser.add_argument("--output", default="output", help="Dossier où sauvegarder les fichiers anonymisés")
    parser.add_argument("--custom-recognizers", default="custom_recognizers.yaml", help="Fichier YAML des reconnaisseurs personnalisés")
    parser.add_argument("--doc-type", help="Type de document manuel (quittance, facture, devis, constat)")
    parser.add_argument("--ignore-entities", default="DATE_TIME", help="Liste d'entités à ignorer (séparées par des virgules)")

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Le dossier d'entrée '{args.input}' n'existe pas.")
        return

    if not os.path.exists(args.output):
        os.makedirs(args.output)

    custom_rec_path = args.custom_recognizers if os.path.exists(args.custom_recognizers) else None
    entities_to_ignore = [e.strip() for e in args.ignore_entities.split(",")] if args.ignore_entities else []

    pipeline = AnonymizationPipeline(
        args.output,
        custom_recognizers=custom_rec_path,
        entities_to_ignore=entities_to_ignore,
        default_doc_type=args.doc_type
    )

    files_to_process = [f for f in os.listdir(args.input) if os.path.isfile(os.path.join(args.input, f))]

    if not files_to_process:
        print("Aucun fichier trouvé dans le dossier d'entrée.")
        return

    for filename in files_to_process:
        file_path = os.path.join(args.input, filename)
        try:
            pipeline.process_file(file_path)
        except Exception as e:
            print(f"Erreur lors du traitement de {filename}: {e}")

if __name__ == "__main__":
    main()
