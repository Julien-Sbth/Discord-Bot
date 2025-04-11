from Gmail import get_gmail_service
from bot.core import get_email_details
from search_emails import search_emails
from display_email import display_email
import time
from datetime import datetime


def display_filtered_emails(query: str = 'in:inbox', max_retries: int = 3) -> None:

    def log_message(message: str, level: str = "INFO") -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level} - {message}")

    service = None
    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            if not service:
                service = get_gmail_service()
                if not service:
                    raise RuntimeError("Échec de l'initialisation du service Gmail")

            start_time = time.time()
            messages = search_emails(service, query)
            elapsed_time = time.time() - start_time

            if not messages:
                log_message("Aucun email trouvé dans la boîte de réception.")
                return

            log_message(f"{len(messages)} emails trouvés (temps: {elapsed_time:.2f}s)")

            processed_count = 0
            for index, msg in enumerate(messages, 1):
                try:
                    email_data = get_email_details(service, msg["id"])
                    if email_data:
                        display_email(email_data)
                        processed_count += 1

                    if index % 5 == 0:
                        time.sleep(0.1)

                except Exception as e:
                    log_message(f"Erreur lors du traitement de l'email {msg.get('id', 'inconnu')}: {str(e)}", "WARNING")
                    continue

            log_message(f"Traitement terminé. {processed_count}/{len(messages)} emails analysés avec succès.")
            return

        except Exception as e:
            last_error = e
            wait_time = attempt * 2

            if attempt < max_retries:
                log_message(f"Tentative {attempt}/{max_retries} échouée. Nouvelle tentative dans {wait_time}s...",
                            "WARNING")
                time.sleep(wait_time)

                service = None
            else:
                log_message(f"Échec après {max_retries} tentatives", "ERROR")
                raise RuntimeError(f"Erreur critique persistante: {str(last_error)}") from last_error