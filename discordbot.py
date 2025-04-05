from commands import setup_commands
from display_email import display_email
from file_processor import process_new_files, global_accepted_offers
from is_rejection_email import is_rejection_email
from utils import save_posted_offer_ids, load_posted_offer_ids, log_message
from apify_client import ApifyClient
import logging
import json
import asyncio
import sqlite3
import pickle
import time
from typing import Dict, List, Optional
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from config import *
from extract_email_body import extract_email_body
import discord
from discord import app_commands, Embed
from datetime import datetime
from discord.ext import commands, tasks
from config import CHANNEL_ID, TOKEN
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
load_dotenv()
apify_client = ApifyClient(os.getenv("APIFY_API_KEY"))
posted_offer_ids = load_posted_offer_ids()
log_message("Le bot démarre...")

def save_posted_offers():
    try:
        with open("posted_offers/posted_offers.txt", "w", encoding="utf-8") as file:
            file.writelines(f"{offer_id}\n" for offer_id in posted_offer_ids)
        print("✅ Offres enregistrées dans posted_offers.txt")
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde des offres : {e}")

async def is_offer_already_posted(offer_id):
    return offer_id in posted_offer_ids

async def send_offers_to_discord(offers):
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print("❌ Erreur : Canal Discord introuvable.")
        return

    unique_offers = {offer[0]: offer for offer in offers}.values()

    valid_indeed_offers_file = os.path.join(VALIDATE_JSON_INDEED, "valid_indeed_offers.json")
    valid_linkedin_offers_file = os.path.join(VALIDATE_JSON_LINKEDIN, "valid_linkedin_offers.json")

    valid_indeed_offers = await asyncio.to_thread(load_valid_offers, valid_indeed_offers_file)
    valid_linkedin_offers = await asyncio.to_thread(load_valid_offers, valid_linkedin_offers_file)

    for offer in unique_offers:
        try:
            offer_id = offer[0]

            if await is_offer_already_posted(offer_id):
                print(f"🚫 Offre déjà postée : {offer_id} - {offer[1]}")
                continue

            description = offer[6][:200] + "..." if len(offer[6]) > 200 else offer[6]

            offer_url = offer[4]
            print(f"URL de l'offre : {offer_url}")

            if "linkedin.com" in offer_url:
                thumbnail_url = "https://upload.wikimedia.org/wikipedia/commons/c/ca/LinkedIn_logo_initials.png"
                source = "LinkedIn"
                valid_linkedin_offers.append(offer)
            else:
                thumbnail_url = "https://prod.statics.indeed.com/eml/assets/images/logo/indeed_logo_1200x630.png"
                source = "Indeed"
                valid_indeed_offers.append(offer)

            embed = discord.Embed(
                title=f"🎯 {offer[1]}",
                description=f"**Source:** {source}\n"
                f"**Entreprise:** {offer[5]}\n"
                f"**Localisation:** {offer[2]}\n"
                f"**Département:** {offer[3]}\n"
                f"**ID de l'offre:** `{offer_id}`\n\n"
                f"**Description:**\n{description}",
                color=0x00FF00,
            )
            embed.set_thumbnail(url=thumbnail_url)
            embed.add_field(name="Lien", value=f"[Voir l'offre]({offer[4]})", inline=False)
            embed.timestamp = datetime.now()

            view = OffreView(offer_url=offer[4], entreprise=offer[5])  # offer[4] = URL, offer[5] = entreprise
            await channel.send(embed=embed, view=view)
            print(f"✅ Offre postée : {offer_id} - {offer[1]}")

            await asyncio.to_thread(save_valid_offers, valid_indeed_offers, valid_indeed_offers_file)
            await asyncio.to_thread(save_valid_offers, valid_linkedin_offers, valid_linkedin_offers_file)

            posted_offer_ids.add(offer_id)
            save_posted_offer_ids(posted_offer_ids)

            await asyncio.sleep(2)
        except discord.HTTPException as e:
            print(f"❌ Erreur lors de l'envoi de l'offre {offer_id} : {e}")
        except Exception as e:
            print(f"❌ Erreur inattendue : {e}")

def load_valid_offers(filename):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as file:
                return json.load(file)
        except (json.JSONDecodeError, IOError):
            print(f"⚠️ Erreur lors du chargement des offres valides depuis {filename}.")
            return []
    return []

def save_valid_offers(offers, filename):
    try:
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(offers, file, indent=4, ensure_ascii=False)
        print(f"✅ Offres valides sauvegardées dans {filename}")
    except IOError:
        print(f"❌ Erreur lors de la sauvegarde des offres valides dans {filename}.")

class OffreView(discord.ui.View):
    def __init__(self, offer_url: str, entreprise: str = "Entreprise non spécifiée"):
        super().__init__(timeout=None)
        self.url = offer_url
        self.entreprise = entreprise

    @discord.ui.button(label="J'ai postulé",
                       style=discord.ButtonStyle.green,
                       custom_id="postuler_button")
    async def postuler_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.defer(ephemeral=True)

            with sqlite3.connect("bot_offres.db") as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO candidatures 
                    (offre_url, entreprise, statut, commentaires)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(offre_url) DO UPDATE SET
                        statut = excluded.statut,
                        commentaires = excluded.commentaires
                """, (
                    self.url,
                    self.entreprise,
                    "en attente",
                    f"Le {datetime.now().strftime('%d/%m/%Y')}"

                ))
                conn.commit()

            await interaction.message.delete()
            await interaction.followup.send(
                f"✅ Candidature chez {self.entreprise} enregistrée!\n"
                f"Lien: {self.url}",
                ephemeral=True
            )

        except Exception as e:
            logging.error(f"Erreur dans postuler_callback: {str(e)}")
            await interaction.followup.send(
                "❌ Une erreur est survenue lors de l'enregistrement",
                ephemeral=True
            )
def extract_email_body(payload: Dict) -> str:
    parts = payload.get("parts", [])
    for part in parts:
        if part.get("mimeType") == "text/plain":
            return part.get("body", {}).get("data", "")
    return ""


def get_gmail_service():
    creds = None

    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "rb") as token:
                creds = pickle.load(token)
        except (pickle.PickleError, EOFError) as e:
            print(f"⚠️ Erreur lors du chargement du token: {e}")
            os.remove(TOKEN_FILE)

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
            with open(TOKEN_FILE, "wb") as token:
                pickle.dump(creds, token)
        except Exception as e:
            print(f"⚠️ Erreur lors de la sauvegarde du token: {e}")

    # Création du service Gmail
    try:
        return build("gmail", "v1", credentials=creds)
    except Exception as e:
        print(f"❌ Erreur lors de la création du service Gmail: {e}")
        raise


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

def format_email_embed(email_data: dict, is_reject: bool = False) -> discord.Embed:
    sender = email_data.get("sender", "Inconnu")
    subject = email_data.get("subject", "Sans sujet")
    body = email_data.get("body", "Contenu non lisible")

    color = discord.Color.red() if is_reject else discord.Color.green()
    status = "❌ REFUS" if is_reject else "✅ Autre"

    embed = Embed(
        title=subject[:256],
        description=body[:300] + "..." if len(body) > 300 else body,
        color=color
    )
    embed.set_author(name=sender)
    embed.set_footer(text=status)

    return embed

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
@bot.event
async def on_ready():
    print(f"Bot connecté : {bot.user}")
    try:
        await bot.tree.sync()
        print("Commandes slash synchronisées")
    except Exception as e:
        print(f"Erreur synchronisation: {e}")

@bot.event
async def on_ready():
    print(f"✅ Bot connecté en tant que {bot.user}")
    await bot.tree.sync()
    check_new_files.start()

@bot.tree.command(name="emails", description="Recherche les derniers emails Gmail selon un filtre")
async def emails(interaction: discord.Interaction, query: str = "in:inbox"):
    await interaction.response.defer(thinking=True)

    service = None
    max_retries = 3
    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            if not service:
                service = get_gmail_service()
                if not service:
                    raise RuntimeError("Service Gmail non initialisé.")

            messages = search_emails(service, query)

            if not messages:
                await interaction.followup.send("🔍 Aucun e-mail trouvé avec ce filtre.")
                return

            embeds = []
            for i, msg in enumerate(messages[:MAX_RESULTS]):
                try:
                    email_data = get_email_details(service, msg["id"])

                    if email_data:
                        is_reject = is_rejection_email(email_data)
                        display_email(email_data)  # Affiche dans console pour debug
                        embed = format_email_embed(email_data, is_reject)
                        embeds.append(embed)

                    if i % 5 == 0:
                        time.sleep(0.1)

                except Exception as e:
                    print(f"Erreur lors du traitement de l'email {msg.get('id')} : {e}")
                    continue

            if embeds:
                await interaction.followup.send(f"📬 **{len(embeds)} e-mails trouvés** - Filtre : `{query}`")
                for embed in embeds:
                    await interaction.channel.send(embed=embed)
            else:
                await interaction.followup.send("Aucun e-mail exploitable trouvé.")

        except Exception as e:
            last_error = e
            wait = attempt * 2
            if attempt < max_retries:
                print(f"Tentative {attempt}/{max_retries} échouée. Nouvelle tentative dans {wait}s...")
                time.sleep(wait)
                service = None
            else:
                await interaction.followup.send(f"❌ Échec après {max_retries} tentatives : {last_error}")
                return
@tasks.loop(minutes=5)
async def check_new_files():
    await process_new_files()
    if global_accepted_offers:
        await send_offers_to_discord(global_accepted_offers)
        global_accepted_offers.clear()

setup_commands(bot)

bot.run(TOKEN)