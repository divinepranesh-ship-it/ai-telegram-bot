import os
import re
from flask import Flask, request
from collections import defaultdict
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL")

if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable not set!")

if not RENDER_URL:
    raise ValueError("RENDER_EXTERNAL_URL not set!")

app = Flask(__name__)
telegram_app = ApplicationBuilder().token(TOKEN).build()

# ===== SETTINGS =====
MAX_WARNINGS = 3
BLOCKED_KEYWORDS = [
    "movie download",
    "free movie",
    "torrent",
    "crack",
    "pirated",
]

user_warnings = defaultdict(int)


# ===== START COMMAND =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Group Protection Bot Active!")


# ===== MESSAGE MONITOR =====
async def monitor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.lower()
    user_id = update.message.from_user.id
    chat_id = update.message.chat.id

    # Block links
    if "http://" in text or "https://" in text:
        await punish(update, context, "Links not allowed")
        return

    # Keyword scan
    for word in BLOCKED_KEYWORDS:
        if word in text:
            await punish(update, context, "Copyright content not allowed")
            return


async def punish(update: Update, context: ContextTypes.DEFAULT_TYPE, reason):
    user_id = update.message.from_user.id
    chat_id = update.message.chat.id

    user_warnings[user_id] += 1

    try:
        await update.message.delete()
    except:
        pass

    if user_warnings[user_id] >= MAX_WARNINGS:
        await context.bot.ban_chat_member(chat_id, user_id)
        await context.bot.send_message(
            chat_id,
            f"🚫 User banned.\nReason: {reason}"
        )
    else:
        await context.bot.send_message(
            chat_id,
            f"⚠ Warning {user_warnings[user_id]}/{MAX_WARNINGS}\nReason: {reason}"
        )


telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, monitor))


# ===== WEBHOOK ROUTES =====
@app.route("/")
def home():
    return "Bot Running"

@app.route(f"/{TOKEN}", methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    await telegram_app.process_update(update)
    return "OK"


# ===== START SERVER =====
if __name__ == "__main__":
    telegram_app.bot.set_webhook(f"{RENDER_URL}/{TOKEN}")
    app.run(host="0.0.0.0", port=10000)
