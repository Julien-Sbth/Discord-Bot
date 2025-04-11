from discord import Embed
from typing import Dict

from Emails.is_rejection_email import is_rejection_email


def format_email_embed(email_data: Dict) -> Embed:
    sender = email_data.get("sender", "Inconnu")
    subject = email_data.get("subject", "(Sans sujet)")
    body = email_data.get("body", "(Contenu vide)")
    snippet = (body[:200] + "...") if len(body) > 200 else body

    status = "🟡 En attente"
    if is_rejection_email(email_data):
        status = "❌ Refusé"

    embed = Embed(title=subject, description=snippet, color=0xFFD700)
    embed.add_field(name="📤 Expéditeur", value=sender, inline=False)
    embed.add_field(name="📌 Statut", value=status, inline=False)

    return embed