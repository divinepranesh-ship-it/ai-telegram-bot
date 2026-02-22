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

# AI imports
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB

# ================= CONFIG =================
BOT_TOKEN = "YOUR_BOT_TOKEN"
SPAM_LIMIT = 6
SPAM_TIME = 8
MUTE_TIME = 120
MAX_WARNINGS = 3
# ==========================================

logging.basicConfig(level=logging.INFO)

user_messages = defaultdict(list)
user_warnings = defaultdict(int)

# ===== SIMPLE AI SPAM MODEL =====
training_texts = [
    "Win free money now",
    "Click this crypto link",
    "Free bitcoin giveaway",
    "Normal group discussion",
    "How are you guys",
    "Let's meet tomorrow",
]

labels = [1, 1, 1, 0, 0, 0]  # 1 = spam, 0 = normal

vectorizer = CountVectorizer()
X = vectorizer.fit_transform(training_texts)

model = MultinomialNB()
model.fit(X, labels)


# ===== DMCA KEYWORD LIST =====
DMCA_KEYWORDS = [
    "full movie download",
    "watch movie free",
    "mp3 download free",
    "cracked software",
    "pirated",
    "torrent link",
    "hd print movie",
    "camrip",
]


# ===== START =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛡 AI Protection Bot Active\n"
        "AI Spam Detection | DMCA Scanner | Anti-Link | Safe Mode"
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


# ===== AI SPAM DETECTION =====
async def ai_spam_check(update, context):
    if update.message.text:
        text = update.message.text
        transformed = vectorizer.transform([text])
        prediction = model.predict(transformed)

        if prediction[0] == 1:
            await update.message.delete()
            await warn_user(update, context,
                            update.message.from_user.id,
                            "AI detected spam")


# ===== FLOOD DETECTION =====
async def flood_check(update, context):
    user_id = update.message.from_user.id
    now = datetime.now()

    user_messages[user_id].append(now)
    user_messages[user_id] = [
        t for t in user_messages[user_id]
        if now - t < timedelta(seconds=SPAM_TIME)
    ]

    if len(user_messages[user_id]) > SPAM_LIMIT:
        await update.message.delete()
        await warn_user(update, context, user_id, "Message flooding")


# ===== DMCA SCANNER =====
async def dmca_scan(update, context):
    if update.message.text:
        text = update.message.text.lower()
        for keyword in DMCA_KEYWORDS:
            if keyword in text:
                await update.message.delete()
                await warn_user(update, context,
                                update.message.from_user.id,
                                "Copyright risk content detected")
                break


# ===== LINK BLOCK =====
async def link_block(update, context):
    if update.message.text:
        pattern = r"(https?://|t\.me/|www\.)"
        if re.search(pattern, update.message.text):
            await update.message.delete()
            await warn_user(update, context,
                            update.message.from_user.id,
                            "Links not allowed")


# ===== MAIN =====
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), ai_spam_check))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), flood_check))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), dmca_scan))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), link_block))

    print("AI Secure Bot Running...")
    app.run_polling()


if __name__ == "__main__":
    main()
