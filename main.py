import asyncio
import logging
import os
import re
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.types import ChatPermissions
from aiogram.filters import Command
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# ============ CONFIG ============
SPAM_LIMIT = 5  # messages
SPAM_TIME = 10  # seconds
MUTE_TIME = 60  # seconds mute

user_messages = {}
# =================================

def is_link(text):
    url_pattern = re.compile(r"https?://|www\.")
    return url_pattern.search(text)

async def mute_user(chat_id, user_id):
    await bot.restrict_chat_member(
        chat_id,
        user_id,
        permissions=ChatPermissions(can_send_messages=False),
        until_date=datetime.utcnow() + timedelta(seconds=MUTE_TIME)
    )

# ============ START COMMAND ============
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.reply("🤖 Protection Bot Active!\nGroup is protected.")

# ============ ANTI-SPAM ============
@dp.message(F.text)
async def anti_spam(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    now = datetime.utcnow()

    if user_id not in user_messages:
        user_messages[user_id] = []

    user_messages[user_id] = [
        msg_time for msg_time in user_messages[user_id]
        if (now - msg_time).seconds < SPAM_TIME
    ]

    user_messages[user_id].append(now)

    if len(user_messages[user_id]) > SPAM_LIMIT:
        await message.delete()
        await mute_user(chat_id, user_id)
        await message.answer(
            f"🚫 {message.from_user.first_name} muted for spamming!"
        )

    # Anti-Link
    if message.text and is_link(message.text):
        await message.delete()
        await mute_user(chat_id, user_id)
        await message.answer(
            f"🔗 Links are not allowed!"
        )

# ============ ANTI-FORWARD ============
@dp.message(F.forward_from)
async def delete_forward(message: types.Message):
    await message.delete()

# ============ COPYRIGHT PROTECTION ============
@dp.message(F.photo | F.video | F.document)
async def media_protection(message: types.Message):
    await message.delete()
    await mute_user(message.chat.id, message.from_user.id)
    await message.answer(
        "📵 Media sharing is restricted to protect from copyright issues."
    )

# ============ ADMIN COMMAND ============
@dp.message(Command("unmute"))
async def unmute_user(message: types.Message):
    if not message.reply_to_message:
        return await message.reply("Reply to a user to unmute.")

    member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in ["administrator", "creator"]:
        return

    target_id = message.reply_to_message.from_user.id

    await bot.restrict_chat_member(
        message.chat.id,
        target_id,
        permissions=ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_other_messages=True
        )
    )

    await message.reply("✅ User unmuted.")

# ============ RUN ============
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
