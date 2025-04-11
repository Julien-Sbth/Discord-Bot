import hashlib
from commands import setup_commands
from file_processor import process_new_files, global_accepted_offers
from utils.utils import save_posted_offer_ids, load_posted_offer_ids, log_message
import json
import asyncio
import sqlite3
from typing import Dict, Optional
from googleapiclient.discovery import build
from utils.config import load_dotenv, VALIDATE_JSON_INDEED, VALIDATE_JSON_LINKEDIN
import os
import logging
from Emails.extract_email_body import extract_email_body
import discord
from datetime import datetime
from discord.ext import commands, tasks
from utils.config import CHANNEL_ID, TOKEN
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
load_dotenv()
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

            view = OffreView(offer_url=offer[4], entreprise=offer[5])
            await channel.send(embed=embed, view=view)
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
    def __init__(self, *, offer_url: str = "", entreprise: str = "Entreprise non spécifiée", commentaires: str = ""):
        super().__init__(timeout=None)
        self.url = offer_url
        self.entreprise = entreprise
        self.commentaires = commentaires

        if offer_url:
            button_custom_id = f"postuler_{hashlib.md5(offer_url.encode()).hexdigest()[:16]}"
            self.add_item(discord.ui.Button(
                label="J'ai postulé",
                style=discord.ButtonStyle.green,
                custom_id=button_custom_id
            ))


    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        print(f"Bouton cliqué - Custom ID: {interaction.data['custom_id']}")
        try:
            await interaction.response.defer(ephemeral=True)

            with sqlite3.connect("Database/bot_offres.db") as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT OR IGNORE INTO candidatures 
                    (offre_url, entreprise, statut, commentaires, date_postulation)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    self.url,
                    self.entreprise,
                    "en attente",
                    self.commentaires,
                    f"Le {datetime.now().strftime('%d/%m/%Y')}"
                ))
                conn.commit()

            await interaction.message.delete()

            await interaction.followup.send(
                f"✅ Candidature chez {self.entreprise} enregistrée !\n"
                f"Lien : {self.url}",
                ephemeral=True
            )

        except Exception as e:
            logging.error(f"Erreur dans postuler_callback: {str(e)}")
            await interaction.followup.send(
                "❌ Une erreur est survenue lors de l'enregistrement",
                ephemeral=True
            )
        return False

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

@bot.event
async def setup_hook():
    bot.add_view(OffreView(offer_url=""))
@bot.event
async def on_ready():
    if not hasattr(bot, 'persistent_views_registered'):
        print(f"✅ Initialisation des vues persistantes pour {bot.user}")

        view = OffreView(offer_url="")
        bot.add_view(view)

        bot.persistent_views_registered = True

    print(f"🔄 Bot prêt (Ping: {round(bot.latency * 1000)}ms)")

    try:
        synced = await bot.tree.sync()
        print(f"🔗 Commandes synchronisées: {len(synced)}")
    except Exception as e:
        print(f"❌ Erreur de sync: {e}")

    if not check_new_files.is_running():
        check_new_files.start()

@tasks.loop(minutes=5)
async def check_new_files():
    await process_new_files()
    if global_accepted_offers:
        await send_offers_to_discord(global_accepted_offers)
        global_accepted_offers.clear()

setup_commands(bot)

bot.run(TOKEN)