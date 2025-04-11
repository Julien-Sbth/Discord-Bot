import json
import glob
import os
import logging
from utils.utils import (
    is_offer_valid,
    print_table,
    normalize_location,
    get_department_code,
)
from utils.config import JSON_FOLDER
from models import Offer

unique_offer_ids = set()
global_accepted_offers = []
PROCESSED_FILES = set()

async def process_new_files():
    logging.basicConfig(filename="error.log", level=logging.ERROR)

    files_to_process = glob.glob(os.path.join(JSON_FOLDER, "*.json"))
    files_processed_count = 0

    while len(global_accepted_offers) < 100 and files_processed_count < len(
        files_to_process
    ):
        file_path = files_to_process[files_processed_count]
        files_processed_count += 1

        if file_path in PROCESSED_FILES:
            continue

        print(f"\n📂 Traitement du fichier : {file_path}\n")
        all_alternance_offers = []
        excluded_offers = []

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logging.error(f"Erreur avec le fichier {file_path}: {e}")
            print(
                f"❌ Erreur : Le fichier {file_path} est invalide ou introuvable. Erreur : {e}\n"
            )
            continue

        for offer in data:
            if is_offer_valid(offer):
                offer_id = str(
                    offer.get("id", "ID inconnu")
                )  # Convertir en chaîne pour garantir l'uniformité
                position_name = offer.get(
                    "positionName", offer.get("title", "Titre inconnu")
                )
                location = normalize_location(offer.get("location", ""))
                dept_code = get_department_code(location)
                url = offer.get("url", offer.get("jobUrl", "URL inconnue"))
                company_name = offer.get(
                    "company", offer.get("companyName", "Entreprise inconnue")
                )
                description = offer.get("description", "Aucune description fournie.")

                if offer_id not in unique_offer_ids:
                    all_alternance_offers.append(
                        Offer(
                            offer_id,
                            position_name,
                            location,
                            dept_code,
                            url,
                            company_name,
                            description,
                        )
                    )
                    global_accepted_offers.append(
                        (
                            offer_id,
                            position_name,
                            location,
                            dept_code,
                            url,
                            company_name,
                            description,
                        )
                    )
                    unique_offer_ids.add(offer_id)
            else:
                company_name = offer.get(
                    "company", offer.get("companyName", "Entreprise inconnue")
                )
                excluded_offers.append(
                    (
                        offer.get("id", "ID inconnu"),
                        offer.get("positionName", offer.get("title", "Titre inconnu")),
                        normalize_location(offer.get("location", "")),
                        get_department_code(offer.get("location", "")),
                        offer.get("url", offer.get("jobUrl", "URL inconnue")),
                        company_name,
                    )
                )

        if excluded_offers:
            print_table(excluded_offers, f"Offres Exclues ({file_path})")
        print("\n")

        if all_alternance_offers:
            print_table(
                all_alternance_offers, f"Offres Alternance Acceptées ({file_path})"
            )
        print("\n")

        PROCESSED_FILES.add(file_path)

    if global_accepted_offers:
        print_table(global_accepted_offers, "Offres Alternance Acceptées (Global)")
    print("\n")

    if len(global_accepted_offers) < 100:
        print("⚠️ Attention : Moins de 100 offres uniques ont été trouvées.")
