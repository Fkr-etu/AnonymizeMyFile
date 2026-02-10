import argparse
import os
from anonymizer.pipeline import AnonymizationPipeline

def main():
    parser = argparse.ArgumentParser(description="Anonymisation de documents (Images et PDF) - Français")
    parser.add_argument("--input", default="input", help="Dossier contenant les fichiers à traiter")
    parser.add_argument("--output", default="output", help="Dossier où sauvegarder les fichiers anonymisés")
    parser.add_argument("--custom-recognizers", default="custom_recognizers.yaml", help="Fichier YAML des reconnaisseurs personnalisés")

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Le dossier d'entrée '{args.input}' n'existe pas.")
        return

    if not os.path.exists(args.output):
        os.makedirs(args.output)

    custom_rec_path = args.custom_recognizers if os.path.exists(args.custom_recognizers) else None

    pipeline = AnonymizationPipeline(args.output, custom_recognizers=custom_rec_path)

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
