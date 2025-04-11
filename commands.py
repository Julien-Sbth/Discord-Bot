import os
from dbm import sqlite3

from discord import app_commands
import discord
from discord.ext import commands
import asyncio
from apify_client import ApifyClient
import time
from Emails.Gmail import get_gmail_service
from utils.config import MAX_RESULTS
from Emails.search_emails import search_emails
from Emails.emails_details import get_email_details
from Emails.display_email import display_email
from Emails.format_email_embed import format_email_embed
from Emails.is_rejection_email import is_rejection_email
from utils.utils import load_posted_offer_ids, log_message
import sqlite3
from odf.opendocument import OpenDocumentText
from odf.table import Table, TableColumn, TableRow, TableCell
from odf.text import P
from odf.style import Style, TableCellProperties
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
apify_client = ApifyClient(os.getenv("APIFY_API_KEY"))
posted_offer_ids = load_posted_offer_ids()
log_message("Le bot démarre...")

def setup_commands(bot):

    @bot.tree.command(name="clear_posted_offers", description="Vide la liste des offres déjà postées")
    async def clear_posted_offers(interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("❌ Permission refusée.", ephemeral=True)
            return
        try:
            with open("posted_offers/posted_offers.txt", "w", encoding="utf-8") as file:
                file.write("")
            posted_offer_ids.clear()
            await interaction.response.send_message("✅ Liste des offres postées vidée.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Erreur : {e}", ephemeral=True)

    @bot.tree.command(name="purge", description="Supprime tous les messages du canal actuel")
    @app_commands.describe(confirm="Confirmez la suppression en écrivant 'oui'")
    async def purge(interaction: discord.Interaction, confirm: str):
        if confirm.lower() != "oui":
            await interaction.response.send_message("❌ La suppression a été annulée.", ephemeral=True)
            return
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("❌ Permission refusée.", ephemeral=True)
            return
        await interaction.response.send_message("🗑️ Suppression en cours...", ephemeral=True)
        try:
            await interaction.channel.purge()
            with open("posted_offers/posted_offers.txt", "w", encoding="utf-8") as file:
                file.write("")
            posted_offer_ids.clear()
            await interaction.followup.send("✅ Messages supprimés et liste des offres postées vidée.", ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send("❌ Permissions insuffisantes.", ephemeral=True)
        except discord.HTTPException as e:
            await interaction.followup.send(f"❌ Erreur : {e}", ephemeral=True)

    @bot.tree.command(name="run_apify", description="Exécute l'Apify Actor pour récupérer des offres d'emploi")
    @app_commands.describe(platform="Choisissez une plateforme : indeed ou linkedin")
    @app_commands.choices(platform=[
        discord.app_commands.Choice(name="Indeed", value="indeed"),
        discord.app_commands.Choice(name="LinkedIn", value="linkedin")
    ])
    async def run_apify(interaction: discord.Interaction, platform: discord.app_commands.Choice[str]):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("❌ Permission refusée.", ephemeral=True)
            return

        await interaction.response.send_message(f"🔍 Recherche sur {platform.value.capitalize()} en cours...", ephemeral=True)

        if platform.value == "linkedin":
            run_input = {
                "title": "",
                "location": "United States",
                "companyName": [""],
                "companyId": [""],
                "publishedAt": "",
                "rows": 50,
                "proxy": {
                    "useApifyProxy": True,
                    "apifyProxyGroups": ["RESIDENTIAL"],
                },
                "source": "linkedin"
            }
            actor_id = "BHzefUZlZRKWxkTck"
        elif platform.value == "indeed":
            run_input = {
                "position": "web developer",
                "country": "US",
                "location": "San Francisco",
                "maxItems": 50,
                "parseCompanyDetails": False,
                "saveOnlyUniqueItems": True,
                "followApplyRedirects": False
            }
            actor_id = "hMvNSpz3JnHgl5jkh"
        else:
            await interaction.followup.send("❌ Plateforme inconnue.", ephemeral=True)
            return

        try:
            run = await asyncio.to_thread(apify_client.actor(actor_id).call, run_input)
            dataset = apify_client.dataset(run["defaultDatasetId"])
            items = await asyncio.to_thread(lambda: list(dataset.iterate_items()))

            if items:
                for item in items:
                    offer_message = (
                        f"**Titre:** {item.get('title', item.get('position', 'N/A'))}\n"
                        f"**Entreprise:** {item.get('companyName', 'N/A')}\n"
                        f"**Localisation:** {item.get('location', 'N/A')}\n"
                        f"**Description:** {item.get('description', 'N/A')[:200]}...\n"
                        f"**Lien:** {item.get('jobUrl', 'N/A')}\n"
                    )
                    await interaction.followup.send(offer_message, ephemeral=True)
                    await asyncio.sleep(1)
            else:
                await interaction.followup.send("✅ Aucune nouvelle offre trouvée.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Erreur lors de l'exécution de l'Apify Actor : {e}", ephemeral=True)

    @bot.tree.command(name="suivi_candidatures", description="Exporte le suivi des candidatures au format ODT")
    async def slash_suivi_candidatures(interaction: discord.Interaction):
        await interaction.response.defer()
        file_path = lister_candidatures()
        if file_path:
            await interaction.followup.send("📊 Voici le suivi des candidatures :", file=discord.File(file_path))
            os.remove(file_path)
        else:
            await interaction.followup.send("❌ Erreur lors de la génération du fichier ODT.")

    def lister_candidatures():
        db_path = "Database/bot_offres.db"
        table_name = "candidatures"
        output_file = "candidatures.odt"

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            if not cursor.fetchone():
                raise ValueError(f"La table {table_name} n'existe pas")

            cursor.execute(f"SELECT * FROM {table_name}")
            colonnes = [description[0] for description in cursor.description]
            resultats = cursor.fetchall()

            doc = OpenDocumentText()

            cell_style = Style(name="TableCellStyle", family="table-cell")
            cell_props = TableCellProperties(
                border="0.5pt solid #000000",
                padding="1mm"
            )
            cell_style.addElement(cell_props)
            doc.automaticstyles.addElement(cell_style)

            header_style = Style(name="HeaderCellStyle", family="table-cell")
            header_props = TableCellProperties(
                border="0.5pt solid #000000",
                padding="1mm",
                backgroundcolor="#D3D3D3"
            )
            header_style.addElement(header_props)
            doc.automaticstyles.addElement(header_style)

            table = Table()

            for _ in colonnes:
                table.addElement(TableColumn())

            header_row = TableRow()
            for col in colonnes:
                cell = TableCell(stylename=header_style)
                cell.addElement(P(text=col))
                header_row.addElement(cell)
            table.addElement(header_row)

            for row in resultats:
                table_row = TableRow()
                for cell_data in row:
                    cell = TableCell(stylename=cell_style)
                    cell.addElement(P(text=str(cell_data)))
                    table_row.addElement(cell)
                table.addElement(table_row)

            doc.text.addElement(table)
            doc.save(output_file)

            return output_file

        except Exception as e:
            print(f"Erreur lors de la génération du rapport: {str(e)}")
            return None

    @bot.tree.command(name="emails", description="Recherche les derniers emails Gmail selon un filtre")
    async def emails(interaction: discord.Interaction, query: str = "label:Candidatures"):
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
                            display_email(email_data)
                            embed = format_email_embed(email_data)
                            embeds.append(embed)

                        if i % 5 == 0:
                            time.sleep(0.1)

                    except Exception as e:
                        print(f"Erreur lors du traitement de l'email {msg.get('id')} : {e}")
                        continue

                if embeds:
                    await interaction.followup.send(
                        f"📬 **{len(embeds)} e-mails trouvés** - Libellé : `Candidatures` (filtre : `{query}`)")
                    for embed in embeds:
                        await interaction.channel.send(embed=embed)
                else:
                    await interaction.followup.send("Aucun e-mail exploitable trouvé.")

                return

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

setup_commands(bot)
