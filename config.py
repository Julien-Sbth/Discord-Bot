import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
BLACKLIST_DIR = os.path.join(BASE_DIR, "blacklist")
POSTED_OFFERS_DIR = os.path.join(BASE_DIR, "posted_offers")

for directory in [LOG_DIR, BLACKLIST_DIR, POSTED_OFFERS_DIR]:
    os.makedirs(directory, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "error.log")
BLACKLIST_FILE = os.path.join(BLACKLIST_DIR, "blacklist.txt")
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

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
TOKEN_FILE = "token.pickle"
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