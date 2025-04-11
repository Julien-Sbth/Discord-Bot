import re
from typing import Dict, List, Optional
from dataclasses import dataclass
import sqlite3
import logging
from Emails.is_rejection_email import is_rejection_email
logging.basicConfig(level=logging.DEBUG, format="📘 [%(levelname)s] %(message)s")

PREVIEW_LENGTH = 150
DEBUG_MODE = True

@dataclass
class EmailDisplayConfig:
    max_preview_length: int = PREVIEW_LENGTH
    debug_mode: bool = DEBUG_MODE
    truncate_after: int = 50


def clean_text(text: str, max_length: Optional[int] = None) -> str:
    logging.debug("Fonction clean_text appelée")
    text = text.strip()
    if not text:
        return "(contenu vide ou non textuel)"

    text = ' '.join(text.split())

    if max_length and len(text) > max_length:
        return f"{text[:max_length]}..."
    return text


def get_rejection_reasons(email_data: Dict) -> List[str]:
    logging.debug("Fonction get_rejection_reasons appelée")
    full_text = f"{email_data.get('subject', '')} {email_data.get('body', '')}".lower()

    rejection_patterns = [
        ("Email transféré concernant une candidature", r"^(tr:|fw:|re:).*(candidature|application|postule)"),
        ("Termes de candidature détectés", r"candidature|application|postule|recrutement"),
        ("Mots-clés de refus identifiés", r"pas retenu|non retenu|refus|regret|malheureusement|not selected")
    ]

    return [
        label for label, pattern in rejection_patterns
        if re.search(pattern, full_text, re.IGNORECASE)
    ]


def extract_url_from_body(body: str) -> Optional[str]:
    logging.debug("Fonction extract_url_from_body appelée")
    url_pattern = r"https?://[^\s]+"
    match = re.search(url_pattern, body)
    if match:
        logging.debug(f"URL extraite du corps : {match.group(0)}")
        return match.group(0)
    return None


def find_application_id_by_company_or_url(entreprise: str, url: Optional[str]) -> Optional[int]:
    logging.debug("Fonction find_application_id_by_company_or_url appelée")
    try:
        conn = sqlite3.connect("../Database/bot_offres.db")
        cursor = conn.cursor()

        if url:
            logging.debug(f"Recherche par URL : {url}")
            cursor.execute("SELECT id FROM candidatures WHERE offre_url = ?", (url,))
            result = cursor.fetchone()
            if result:
                logging.debug(f"ID trouvé par URL : {result[0]}")
                return result[0]

        cleaned_entreprise = entreprise.strip().lower()
        logging.debug(f"Recherche dans entreprise pour : {cleaned_entreprise}")

        cursor.execute("SELECT id FROM candidatures WHERE entreprise LIKE ?", ('%' + cleaned_entreprise + '%',))
        result = cursor.fetchone()
        if result:
            logging.debug(f"ID trouvé par entreprise : {result[0]}")
            return result[0]
    except sqlite3.Error as e:
        logging.error(f"Erreur lors de la recherche de la candidature : {e}")
    finally:
        conn.close()

    logging.debug("Aucune candidature trouvée")
    return None


def find_application_ids_by_position(position: str) -> List[int]:
    logging.debug(f"Recherche de candidatures pour: {position}")
    try:
        conn = sqlite3.connect("../Database/bot_offres.db")
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id FROM candidatures 
            WHERE entreprise LIKE ? OR offre_url LIKE ?
            """, (f'%{position}%', f'%{position}%'))

        return [row[0] for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logging.error(f"Erreur lors de la recherche: {e}")
        return []
    finally:
        conn.close()

def update_application_status(candidature_ids: List[int], status: str, url: Optional[str] = None) -> None:
    logging.debug("Fonction update_application_status appelée")
    if not candidature_ids:
        logging.warning("Aucun ID de candidature fourni pour la mise à jour")
        return

    try:
        conn = sqlite3.connect("../Database/bot_offres.db")
        cursor = conn.cursor()

        placeholders = ','.join(['?'] * len(candidature_ids))
        cursor.execute(
            f"UPDATE candidatures SET statut = ? WHERE id IN ({placeholders})",
            [status] + candidature_ids
        )

        if url:
            cursor.execute("SELECT 1 FROM offres WHERE url = ?", (url,))
            if cursor.fetchone():
                cursor.execute(
                    f"UPDATE candidatures SET offre_url = ? WHERE id IN ({placeholders})",
                    [url] + candidature_ids
                )

        conn.commit()
        logging.info(f"✅ Statut mis à jour pour {len(candidature_ids)} candidature(s)")
    except sqlite3.Error as e:
        logging.error(f"Erreur lors de la mise à jour : {e}")
    finally:
        if 'conn' in locals():
            conn.close()


def find_application_ids_by_url(url: str) -> List[int]:
    logging.debug(f"Recherche de candidatures par URL: {url}")
    try:
        conn = sqlite3.connect("../Database/bot_offres.db")
        cursor = conn.cursor()

        domain_parts = url.replace("https://", "").replace("http://", "").split("/")[0].split(".")
        if len(domain_parts) > 1:
            main_domain = ".".join(domain_parts[-2:])
        else:
            main_domain = domain_parts[0]

        cursor.execute("""
            SELECT id FROM candidatures 
            WHERE offre_url LIKE ?
            """, (f'%{main_domain}%',))

        return [row[0] for row in cursor.fetchall()]

    except sqlite3.Error as e:
        logging.error(f"Erreur lors de la recherche par URL: {e}")
        return []
    finally:
        conn.close()


def normalize_url(url: str) -> str:
    if not url:
        return ''
    return (url.lower()
            .replace('https://', '')
            .replace('http://', '')
            .split('?')[0]
            .split('#')[0]
            .rstrip('/'))

def display_email(email_data: Dict, config: EmailDisplayConfig = EmailDisplayConfig()) -> None:
    logging.debug("Fonction display_email appelée")

    if not email_data:
        logging.warning("Email vide ou None passé à display_email")
        return

    sender = clean_text(email_data.get('sender', 'Expéditeur inconnu'), config.truncate_after)
    subject = clean_text(email_data.get('subject', 'Sans sujet'), config.truncate_after)
    body_preview = clean_text(email_data.get('body', '')[:config.max_preview_length])
    entreprise = clean_text(email_data.get('entreprise', 'Entreprise non spécifiée'), config.truncate_after)

    if entreprise == 'Entreprise non spécifiée':
        logging.warning("Entreprise non spécifiée dans l'email. Recherche basée sur l'URL uniquement.")

    is_rejection = is_rejection_email(email_data)
    status = "❌ REFUS" if is_rejection else "✅ ACCEPTÉ"

    email_display = [
        f"\n{status} - 📧 De : {sender}",
        f"📌 Sujet : {subject}",
        f"📜 Extrait : {body_preview}",
        f"🏢 Entreprise : {entreprise}"
    ]
    print('\n'.join(email_display))

    url_offre = extract_url_from_body(email_data.get('body', ''))
    if entreprise != 'Entreprise non spécifiée':
        candidature_id = find_application_id_by_company_or_url(entreprise, url_offre)
    else:
        candidature_id = find_application_id_by_company_or_url('', url_offre)

    if candidature_id:
        update_application_status(candidature_id, "refusé" if is_rejection else "accepté", url_offre)
    else:
        logging.warning(f"❗ Aucun ID de candidature trouvé pour l'entreprise : {entreprise} ou l'URL : {url_offre}")

    if config.debug_mode and is_rejection:
        reasons = get_rejection_reasons(email_data)
        if reasons:
            print("\n🔍 Raisons du classement :")
            print('\n'.join(f" - {r}" for r in reasons))
        else:
            print("\n🔍 Détection basée sur l'analyse contextuelle")

    print("-" * 80)