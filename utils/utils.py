import json
import re
import os
import logging
from datetime import datetime, timedelta
from models import Offer
from utils.config import (
    LOG_DIR,
    LOG_FILE,
    POSTED_OFFERS_FILE,
    MAX_LOG_AGE_DAYS,
    MAX_OFFER_AGE_DAYS,
    TARGET_LOCATIONS,
    BANNED_KEYWORDS,
    ID_WIDTH,
    TITLE_WIDTH,
    LOCATION_WIDTH,
    URL_WIDTH,
    DEPT_WIDTH,
    COMPANY_WIDTH,
)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def log_message(message):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    log_entry = f"{timestamp} {message}\n"

    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        print(f"❌ Erreur lors de l'écriture du log : {e}")


def load_logs():
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                return f.readlines()
        except Exception as e:
            print(f"⚠️ Erreur lors du chargement des logs : {e}")
    return []


def load_file_as_set(filename):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            return {line.strip() for line in file if line.strip()}
    except FileNotFoundError:
        return set()


POSTED_OFFER_IDS = load_file_as_set(POSTED_OFFERS_FILE)

def load_posted_offer_ids():
    if os.path.exists(POSTED_OFFERS_FILE):
        try:
            with open(POSTED_OFFERS_FILE, "r", encoding="utf-8") as f:
                return set(
                    line.strip() for line in f if line.strip()
                )  # Lire chaque ligne et créer un ensemble
        except (IOError, json.JSONDecodeError):
            print(
                "⚠️ Erreur lors du chargement des offres postées, le fichier sera recréé."
            )
            return set()
    return set()


def save_posted_offer_ids(posted_offer_ids):
    try:
        with open(POSTED_OFFERS_FILE, "w", encoding="utf-8") as f:
            for offer_id in posted_offer_ids:
                f.write(f"{offer_id}\n")
    except IOError:
        print("❌ Erreur lors de la sauvegarde des offres postées.")


def clean_old_logs():
    current_time = datetime.now()
    for filename in os.listdir(LOG_DIR):
        file_path = os.path.join(LOG_DIR, filename)
        if os.path.isfile(file_path):
            file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
            file_age = (current_time - file_mtime).days
            if file_age > MAX_LOG_AGE_DAYS:
                os.remove(file_path)
                logger.info(f"Log supprimé : {filename}, vieux de {file_age} jours.")


def print_table(offers, title):
    total_width = (
        sum(
            [
                ID_WIDTH,
                TITLE_WIDTH,
                LOCATION_WIDTH,
                URL_WIDTH,
                DEPT_WIDTH,
                COMPANY_WIDTH,
            ]
        )
        + 14
    )
    SEPARATOR = "+" + "-" * (total_width - 2) + "+"

    TITLE_COLOR, HEADER_COLOR, RESET_COLOR = "\033[1;35m", "\033[1;33m", "\033[0m"

    print(
        f"{SEPARATOR}\n|{TITLE_COLOR} {title.center(total_width - 2)} {RESET_COLOR}|\n{SEPARATOR}"
    )
    print(
        f"| {'#':^2} | {HEADER_COLOR}{'ID':^{ID_WIDTH}}{RESET_COLOR} | {HEADER_COLOR}{'Titre':^{TITLE_WIDTH}}{RESET_COLOR} | "
        f"{HEADER_COLOR}{'Localisation':^{LOCATION_WIDTH}}{RESET_COLOR} | {HEADER_COLOR}{'Département':^{DEPT_WIDTH}}{RESET_COLOR} | "
        f"{HEADER_COLOR}{'Entreprise':^{COMPANY_WIDTH}}{RESET_COLOR} | {HEADER_COLOR}{'URL':^{URL_WIDTH}}{RESET_COLOR} |"
    )
    print(SEPARATOR)

    for idx, offer in enumerate(offers, start=1):
        if isinstance(offer, Offer):
            id_, titre, location, dept_code, url, company_name = (
                offer.id,
                offer.title,
                offer.location,
                offer.dept_code,
                offer.url,
                offer.company_name,
            )
        else:
            id_, titre, location, dept_code, url, company_name = offer[:6]

        def truncate(value, max_length):
            return (value[: max_length - 3] + "…") if len(value) > max_length else value

        print(
            f"| {idx:<2} | {truncate(id_, ID_WIDTH):<{ID_WIDTH}} | {truncate(titre, TITLE_WIDTH):<{TITLE_WIDTH}} | "
            f"{truncate(location, LOCATION_WIDTH):<{LOCATION_WIDTH}} | {dept_code:^{DEPT_WIDTH}} | {truncate(company_name, COMPANY_WIDTH):<{COMPANY_WIDTH}} | "
            f"{truncate(url, URL_WIDTH):<{URL_WIDTH}} |"
        )

    print(SEPARATOR)

def get_department_code(location):
    match = re.search(r"\b(\d{5})\b", location) or re.search(r"\b(\d{2})\b", location)
    if match:
        dept = match.group(1)[:2]
        return (
            "2A"
            if dept == "20" and "2A" in location
            else (
                "2B"
                if dept == "20" and "2B" in location
                else dept if dept.isdigit() and 1 <= int(dept) <= 95 else "N/A"
            )
        )

    #logger.warning(f"Aucun code département trouvé pour : {location}")
    return "N/A"

def normalize_location(location):
    return re.sub(r"[^a-zA-Z0-9\s]", "", location).lower()

def is_offer_valid(offer):
    offer_id = offer.get("id", "ID inconnu")
    position_name = offer.get(
        "positionName", offer.get("title", "Titre inconnu")
    ).lower()
    location = normalize_location(offer.get("location", ""))
    status = offer.get("status", "").lower()
    posting_date_parsed = offer.get("postingDateParsed", offer.get("publishedAt", None))

    #logger.debug(f"🔎 Vérification de l'offre: {position_name} (ID: {offer_id})")

    is_expired = False
    if posting_date_parsed:
        try:
            posting_date = (
                datetime.strptime(posting_date_parsed, "%Y-%m-%dT%H:%M:%S.%fZ")
                if "T" in posting_date_parsed
                else datetime.strptime(posting_date_parsed, "%Y-%m-%d")
            )
            is_expired = datetime.now() - posting_date > timedelta(
                days=MAX_OFFER_AGE_DAYS
            )
        except ValueError:
            logger.error(
                f"Format de date invalide pour l'offre {offer_id}: {posting_date_parsed}"
            )

    is_closed = status == "closed"

    keywords = [
        "alternance",
        "Consultant",
        "apprentissage",
        "contrat pro",
        "alternance ingénieur",
        "cybersécurité",
        "Administrateur Réseau",
        "Analyste",
    ]

    is_alternance = any(keyword.lower() in position_name for keyword in keywords)

    #logger.debug(f"🚨 Mots-clés bannis testés : {BANNED_KEYWORDS}")
    is_banned = any(banned.lower() in position_name for banned in BANNED_KEYWORDS)

    if is_banned:
        logger.debug(
            f"🚫 Offre bannie ({offer_id}) à cause du mot-clé interdit dans: '{position_name}'"
        )

    is_location_valid = any(city in location for city in TARGET_LOCATIONS) or any(
        city in offer.get("location", "").lower() for city in TARGET_LOCATIONS
    )

    is_valid = all(
        [is_alternance, not is_banned, not is_expired, not is_closed, is_location_valid]
    )

    if not is_valid:
        logger.debug(
            f"❌ Offre rejetée : {position_name} (ID: {offer_id}) - Raison : "
            f"Alternance: {is_alternance}, Bannie: {is_banned}, Expirée: {is_expired}, "
            f"Fermée: {is_closed}, Localisation OK: {is_location_valid}"
        )

    return is_valid


clean_old_logs()
