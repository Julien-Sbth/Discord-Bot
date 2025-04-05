import re
from typing import Dict


def is_rejection_email(email_data: Dict) -> bool:
    if not email_data:
        return False

    subject = email_data.get('subject', '').lower()
    body = email_data.get('body', '').lower()
    full_text = f"{subject} {body}"

    strong_rejection_keywords = [
        "n'a pas été retenue", "non retenue", "pas retenu",
        "ne donnerons pas suite", "refus", "regret",
        "malheureusement", "not selected", "unfortunately"
    ]

    if any(keyword in full_text for keyword in strong_rejection_keywords):
        return True

    is_forwarded_application = (
            subject.startswith(("tr:", "fw:", "re:")) and
            any(term in full_text for term in ["candidature", "application", "postule"])
    )

    if is_forwarded_application and "votre candidature" in subject:
        return True

    if "équipe de recrutement" in full_text or "recruitment team" in full_text:
        return True

    rejection_patterns = [
        r"(candidature|application).*(pas|non).*(retenu|sélectionné|abouti)",
        r"(ne|n') pas (retenu|sélectionné|abouti)",
        r"(malheureusement|regret).*(candidature|postuler)"
    ]

    if any(re.search(pattern, full_text) for pattern in rejection_patterns):
        return True

    return False