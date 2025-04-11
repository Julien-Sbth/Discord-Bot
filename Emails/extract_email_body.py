import base64
import re
from typing import Dict, List, Optional


def extract_email_body(payload: Dict) -> str:
    body = ""

    def extract_from_part(part):
        if part['mimeType'] in ['text/plain', 'text/html']:
            body_data = part['body'].get('data', '')
            if body_data:
                try:
                    return base64.urlsafe_b64decode(body_data).decode('utf-8', 'ignore')
                except (base64.binascii.Error, UnicodeDecodeError):
                    return ""
        elif 'parts' in part:
            for subpart in part['parts']:
                content = extract_from_part(subpart)
                if content:
                    return content
        return ""

    if 'parts' in payload:
        for part in payload['parts']:
            content = extract_from_part(part)
            if content:
                body = content
                break
    elif 'body' in payload and 'data' in payload['body']:
        try:
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', 'ignore')
        except (base64.binascii.Error, UnicodeDecodeError):
            pass

    if "forwarded message" in body.lower() or "original message" in body.lower():
        parts = re.split(r'(?i)-{2,}.*original message.*-{2,}', body)
        if len(parts) > 1:
            body = parts[-1]

        parts = re.split(r'(?i)begin forwarded message:', body)
        if len(parts) > 1:
            body = parts[-1]

    return body.strip() or "Aucun contenu"