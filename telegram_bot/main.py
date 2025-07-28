import json
import logging
import os
from telegram import Update

from telegram_bot.dispatcher import get_application

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("Missing TELEGRAM_BOT_TOKEN environment variable.")
ALLOWED_USER_IDS = {int(uid.strip()) for uid in os.getenv("ALLOWED_USER_IDS", "").split(",") if uid.strip()}


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)



def run_bot():
    logger.info("Creating the bot...")
    application = get_application(
        token=BOT_TOKEN, allowed_user_ids=ALLOWED_USER_IDS
    )
    logger.info("Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    run_bot()
