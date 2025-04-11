import os
from dotenv import load_dotenv
import logging

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join("..", "logs")
POSTED_OFFERS_DIR = os.path.join("..", "posted_offers")


for directory in [LOG_DIR, POSTED_OFFERS_DIR]:
    os.makedirs(directory, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "error.log")
POSTED_OFFERS_FILE = os.path.join(POSTED_OFFERS_DIR, "posted_offers.txt")

MAX_LOG_AGE_DAYS = 30
JSON_FOLDER = "json/offers"
VALIDATE_JSON_LINKEDIN = "json/linkedin"
VALIDATE_JSON_INDEED = "json/indeed"

DEBUG = False
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
MAX_OFFER_AGE_DAYS = 30

TARGET_LOCATIONS = ["toulouse", "colomiers", "blagnac", "labège", "balma", "lyon"]

BANNED_KEYWORDS = [
    "full stack", "développeur", "web", "développement", "development",
    "java", "angular", "data", "UI", "Designer", "DevSecOps", "IA"
]

ID_WIDTH, TITLE_WIDTH, LOCATION_WIDTH, URL_WIDTH, DEPT_WIDTH, COMPANY_WIDTH = 20, 50, 20, 50, 5, 20

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.modify']
TOKEN_FILE = "../token.json"
CREDENTIALS_FILE = "credentials.json"
MAX_RESULTS = 10
PREVIEW_LENGTH = 150

REJECTION_KEYWORDS = [
    "malheureusement", "n'avons pas retenu", "candidature n'a pas été retenue",
    "poste a été attribué", "ne correspond pas", "refus", "retenu un autre candidat",
    "décidé de ne pas retenir", "candidature spontanée", "ne sera pas poursuivie",
    "n'a pas abouti", "nous vous remercions de votre intérêt", "votre profil ne correspond pas",
    "n'avons pas retenu votre candidature", "poste a été pourvu", "candidature n'a pas été sélectionnée",
    "retenu un autre profil", "malheureusement votre candidature", "nous sommes au regret",
    "nous avons le regret", "votre candidature n'a pas été retenue", "n'a pas été sélectionné",
    "au regret de vous informer", "candidature non retenue", "ne correspond pas à nos attentes",
    "n'avons pas sélectionné", "nous ne donnerons pas suite", "ne pas retenir votre candidature",

    "not selected", "unfortunately", "we regret to inform", "we will not proceed",
    "your application was not successful", "we have decided to move forward",
    "position has been filled", "other candidates were more closely aligned"
]
REJECTION_PATTERNS = [
    r"candidature.*n'a pas",
    r"n'avons pas.*retenu",
    r"poste.*pourvu",
    r"ne sera pas poursuivie",
    r"nous avons le regret.*vous informer",
    r"votre candidature.*pas été retenue",
    r"nous ne.*donnerons pas suite",
    r"candidature.*non retenue",
    r"n'a pas été.*sélectionné",
    r"we regret.*inform you",
    r"your application.*not successful",
    r"position.*been filled"
]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_DAYS = 180
BATCH_SIZE = 50
LABEL_NAME = "Candidatures"
KEYWORDS = [
    r'thank you.*application',
    r'recent application',
    r'alternance',
    r'ATC Log analysis',
    r'application',
    r'cv',
    r'curriculum vitae',
    r'job',
    r'position',
    r'offre',
    r'candidature',
    r'recrutement',
    r'interview',
    r'forum',
    r'rencontre',
    r'étudiant',
    r'embauche'
]


BASE_QUERY = """
(subject:("Suite à" OR "Candidature" OR "Thales" OR "Alternance" OR "Forum" OR "Rencontre" OR "Poste" OR "Recrutement" OR "Suite à notre rencontre au forum d'YNOV Toulouse" OR "Application Update" OR "CV" OR "Curriculum Vitae" OR "Lettre de motivation" OR "Interview" OR "Job" OR "Position" OR "Offre" OR "Stage")
OR body:("Suite à" OR "candidature" OR "Thales" OR "alternance" OR "forum" OR "rencontre" OR "poste" OR "recrutement" OR "Due to the high volume of applications we receive" OR "CV" OR "Curriculum Vitae" OR "Lettre de motivation" OR "Interview" OR "Job" OR "Position" OR "Offre" OR "Stage" OR "thank you for your application" OR "status of your application" OR "review your application" OR "career possibilities" OR "job alert"))
-label:Candidatures
"""

def generate_query(keywords, base_query):
    keyword_query = " OR ".join(f"({kw})" for kw in keywords)
    return f"({base_query}) AND ({keyword_query})"

full_query = generate_query(KEYWORDS, BASE_QUERY)
logger.info(f"Requête complète: {full_query}")

EMAIL_QUERY = """
(subject:("Suite à votre candidature" OR "Votre candidature" OR "Alternance" OR "Candidature spontanée"
           OR "Réponse candidature" OR "Votre postulation" OR "Votre demande")
 OR body:("Suite à notre rencontre" OR "entretien" OR "poste" OR "recrutement"
          OR "processus de recrutement" OR "votre profil" OR "nous étudions votre candidature"))
-label:Candidatures
"""

PROCESSING_CONFIG = {
    'days_to_search': 90,
    'batch_size': 100,
    'target_label': "Candidatures"
}