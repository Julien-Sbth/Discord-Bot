import re
from typing import Dict, List, Optional
from dataclasses import dataclass

from is_rejection_email import is_rejection_email

PREVIEW_LENGTH = 150
DEBUG_MODE = True

@dataclass
class EmailDisplayConfig:
    max_preview_length: int = PREVIEW_LENGTH
    debug_mode: bool = DEBUG_MODE
    truncate_after: int = 50


def clean_text(text: str, max_length: Optional[int] = None) -> str:
    text = text.strip()
    if not text:
        return "(contenu vide ou non textuel)"

    text = ' '.join(text.split())

    if max_length and len(text) > max_length:
        return f"{text[:max_length]}..."
    return text


def get_rejection_reasons(email_data: Dict) -> List[str]:
    full_text = f"{email_data.get('subject', '')} {email_data.get('body', '')}".lower()

    rejection_patterns = [
        ("Email transféré concernant une candidature",
         r"^(tr:|fw:|re:).*(candidature|application|postule)"),
        ("Termes de candidature détectés",
         r"candidature|application|postule|recrutement"),
        ("Mots-clés de refus identifiés",
         r"pas retenu|non retenu|refus|regret|malheureusement|not selected")
    ]

    return [
        label for label, pattern in rejection_patterns
        if re.search(pattern, full_text, re.IGNORECASE)
    ]


def display_email(email_data: Dict, config: EmailDisplayConfig = EmailDisplayConfig()) -> None:
    if not email_data:
        return

    sender = clean_text(email_data.get('sender', 'Expéditeur inconnu'), config.truncate_after)
    subject = clean_text(email_data.get('subject', 'Sans sujet'), config.truncate_after)
    body_preview = clean_text(email_data.get('body', '')[:config.max_preview_length])

    is_rejection = is_rejection_email(email_data)
    status = "❌ REFUS" if is_rejection else "✅ Autre"

    email_display = [
        f"\n{status} - 📧 De : {sender}",
        f"📌 Sujet : {subject}",
        f"📜 Extrait : {body_preview}"
    ]

    print('\n'.join(email_display))

    if config.debug_mode and is_rejection:
        reasons = get_rejection_reasons(email_data)
        if reasons:
            print("\n🔍 Raisons du classement :")
            print('\n'.join(f" - {r}" for r in reasons))
        else:
            print("\n🔍 Détection basée sur l'analyse contextuelle")

    print("-" * 80)