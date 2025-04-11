from database import init_db
from discordbot import bot
from utils.config import TOKEN

if __name__ == "__main__":
    init_db()
    bot.run(TOKEN)
