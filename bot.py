import os
import logging
import re
from collections import defaultdict
from datetime import datetime, timedelta

from telegram import Update, ChatPermissions
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters,
)

# ================= CONFIG =================
BOT_TOKEN = os.environ.get("6346466600:AAGZvgfzWWKimBEPqJoh1qyvOvjYJGY5zwA")

SPAM_LIMIT = 6
SPAM_TIME = 8
MUTE_TIME = 120
MAX_WARNINGS = 3
# ==========================================

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable not set!")

logging.basicConfig(level=logging.INFO)

user_messages = defaultdict(list)
user_warnings = defaultdict(int)

# ===== SIMPLE AI-LIKE SPAM CHECK =====
SPAM_WORDS = [
    "free money",
    "bitcoin",
    "crypto",
    "giveaway",
    "win cash",
    "investment offer",
]

DMCA_KEYWORDS = [
    "full movie download",
    "watch movie free",
    "mp3 download",
    "cracked software",
    "torrent link",
    "camrip",
    "hd print",
]

# ===== START COMMAND =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛡 AI Protection Bot Active\n"
        "Spam Filter | DMCA Scanner | Flood Control"
    )

# ===== WARNING SYSTEM =====
async def warn_user(update, context, user_id, reason):
    chat_id = update.message.chat_id

    user_warnings[user_id] += 1
    warnings = user_warnings[user_id]

    if warnings >= MAX_WARNINGS:
        await context.bot.restrict_chat_member(
            chat_id,
            user_id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=datetime.now() + timedelta(seconds=MUTE_TIME),
        )
        await context.bot.send_message(
            chat_id,
            f"🚫 User muted for violations.\nReason: {reason}"
        )
        user_warnings[user_id] = 0
    else:
        await context.bot.send_message(
            chat_id,
            f"⚠ Warning {warnings}/{MAX_WARNINGS}\nReason: {reason}"
        )

# ===== MESSAGE HANDLER =====
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    text = update.message.text.lower()
    now = datetime.now()

    # ===== FLOOD CHECK =====
    user_messages[user_id].append(now)
    user_messages[user_id] = [
        t for t in user_messages[user_id]
        if now - t < timedelta(seconds=SPAM_TIME)
    ]

    if len(user_messages[user_id]) > SPAM_LIMIT:
        await update.message.delete()
        await warn_user(update, context, user_id, "Flooding messages")
        return

    # ===== LINK BLOCK =====
    if re.search(r"(https?://|t\.me/|www\.)", text):
        await update.message.delete()
        await warn_user(update, context, user_id, "Links not allowed")
        return

    # ===== SPAM WORD CHECK =====
    for word in SPAM_WORDS:
        if word in text:
            await update.message.delete()
            await warn_user(update, context, user_id, "Spam detected")
            return

    # ===== DMCA SCAN =====
    for keyword in DMCA_KEYWORDS:
        if keyword in text:
            await update.message.delete()
            await warn_user(update, context, user_id, "Copyright risk content")
            return

# ===== MAIN =====
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler))

    print("Bot running successfully...")
    app.run_polling()

if __name__ == "__main__":
    main()
