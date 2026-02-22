import os
import re
import logging
from collections import defaultdict
from datetime import datetime, timedelta

from flask import Flask
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters,
)

# ---------------- CONFIG ----------------

TOKEN = os.environ.get("BOT_TOKEN")

DMCA_KEYWORDS = [
    "movie download",
    "free netflix",
    "cracked software",
    "pirated",
    "torrent link",
    "mod apk",
    "premium hack"
]

SPAM_LIMIT = 5
SPAM_TIME = 10  # seconds

# ----------------------------------------

logging.basicConfig(level=logging.INFO)

user_messages = defaultdict(list)

# Flask app (keeps Render alive)
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

# ---------------- SPAM CHECK ----------------

def is_spam(text: str) -> bool:
    text = text.lower()

    # DMCA keyword scan
    for word in DMCA_KEYWORDS:
        if word in text:
            return True

    # Link spam detection
    if len(re.findall(r"http[s]?://", text)) > 2:
        return True

    return False

async def moderate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    user_id = message.from_user.id
    text = message.text or ""

    now = datetime.now()

    # Flood control
    user_messages[user_id] = [
        t for t in user_messages[user_id]
        if now - t < timedelta(seconds=SPAM_TIME)
    ]
    user_messages[user_id].append(now)

    if len(user_messages[user_id]) > SPAM_LIMIT:
        await message.delete()
        return

    # Keyword spam check
    if is_spam(text):
        await message.delete()
        return

# ---------------- START BOT ----------------

def start_bot():
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, moderate)
    )

    application.run_polling()

if __name__ == "__main__":
    import threading
    threading.Thread(target=start_bot).start()
    app.run(host="0.0.0.0", port=10000)
