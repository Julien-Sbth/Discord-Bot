import discord
from discord import Embed

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