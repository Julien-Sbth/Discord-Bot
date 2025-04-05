from typing import Dict, List, Optional
from googleapiclient.discovery import build

from config import MAX_RESULTS


def search_emails(service: build, query: str = "") -> List[Dict]:
    try:
        results = service.users().messages().list(
            userId="me",
            q=query,
            maxResults=MAX_RESULTS
        ).execute()
        return results.get("messages", [])
    except Exception as e:
        print(f"❌ Erreur lors de la recherche des emails: {e}")
        return []