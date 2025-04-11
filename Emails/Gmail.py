import os
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "../token.json"
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service():
    creds = None

    # Vérifie si le token existe et le charge
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "rb") as token:
                creds = pickle.load(token)
        except (pickle.PickleError, EOFError) as e:
            print(f"⚠️ Erreur lors du chargement du token: {e}")
            os.remove(TOKEN_FILE)

    # Si le token est invalide ou expiré, le rafraîchir ou en obtenir un nouveau
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"⚠️ Erreur lors du rafraîchissement du token: {e}")
                creds = None

        if not creds:
            try:
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
            except Exception as e:
                print(f"❌ Erreur d'authentification: {e}")
                raise

        try:
            # Sauvegarde du token pour utilisation future
            with open(TOKEN_FILE, "wb") as token:
                pickle.dump(creds, token)
        except Exception as e:
            print(f"⚠️ Erreur lors de la sauvegarde du token: {e}")

    try:
        return build("gmail", "v1", credentials=creds)
    except Exception as e:
        print(f"❌ Erreur lors de la création du service Gmail: {e}")
        raise
