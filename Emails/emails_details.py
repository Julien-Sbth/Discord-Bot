from googleapiclient.discovery import build
from typing import Dict, List, Optional

from Emails.extract_email_body import extract_email_body


def get_email_details(service: build, message_id: str) -> Optional[Dict]:
    try:
        msg = service.users().messages().get(
            userId="me",
            id=message_id,
            format="full"
        ).execute()

        payload = msg.get("payload", {})
        headers = payload.get("headers", [])

        sender = next((h["value"] for h in headers if h["name"] == "From"), "Inconnu")
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "Sans sujet")

        body = extract_email_body(payload)

        return {
            "sender": sender,
            "subject": subject,
            "body": body or "Aucun contenu"
        }
    except Exception as e:
        print(f"❌ Erreur lors de la récupération de l'email {message_id}: {e}")
        return None