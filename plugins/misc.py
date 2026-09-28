import random
from pyrogram import Client, filters
from pyrogram.enums import ChatType
from config import Config
from database import db


# =========================================================
# /runs — Random "run away" string
# =========================================================

RUN_MESSAGES = [
    "Run away! 🏃‍♂️💨",
    "Quick, run! 😱",
    "Run for your life! 🏃",
    "Run fast! 💨",
    "Escape! 🏃‍♀️💨",
    "Run, Forest, run! 🌳",
    "Better run! ⚡",
    "Just run! 🏃‍♂️",
]


@Client.on_message(filters.command("runs"))
async def runs_cmd(client, message):
    await message.reply_text(random.choice(RUN_MESSAGES))


# =========================================================
# /id — Get ID
# =========================================================

@Client.on_message(filters.command("id"))
async def id_cmd(client, message):
    text = f"👤 <b>Your ID:</b> <code>{message.from_user.id}</code>\n"
    if message.chat.type != ChatType.PRIVATE:
        text += f"💬 <b>Chat ID:</b> <code>{message.chat.id}</code>\n"
    if message.reply_to_message and message.reply_to_message.from_user:
        text += f"↩️ <b>Replied:</b> <code>{message.reply_to_message.from_user.id}</code>"
    await message.reply_text(text)


# =========================================================
# /info — User info
# =========================================================

@Client.on_message(filters.command("info"))
async def info_cmd(client, message):
    user = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    try:
        full = await client.get_users(user.id)
    except Exception:
        full = user

    text = (
        f"👤 <b>User Info</b>\n\n"
        f"🆔 <b>ID:</b> <code>{full.id}</code>\n"
        f"📛 <b>First:</b> {full.first_name or ''}\n"
        f"📛 <b>Last:</b> {full.last_name or 'None'}\n"
        f"🔗 <b>Username:</b> @{full.username or 'None'}\n"
        f"🤖 <b>Bot:</b> {full.is_bot}\n"
        f"⭐ <b>Premium:</b> {getattr(full, 'is_premium', False)}\n"
        f"🌐 <b>Language:</b> {getattr(full, 'language_code', 'Unknown')}"
    )
    await message.reply_text(text)


# =========================================================
# /donate — Donate info
# =========================================================

@Client.on_message(filters.command("donate"))
async def donate_cmd(client, message):
    await message.reply_text(
        f"💖 <b>Support {Config.BOT_NAME}</b>\n\n"
        f"If you like the bot and want to support the creator:\n\n"
        f"👑 <b>Owner:</b> @{Config.OWNER_USERNAME}\n\n"
        f"Your support keeps the bot alive! Thank you 💖"
    )


# =========================================================
# /markdownhelp — Markdown guide (PM only)
# =========================================================

@Client.on_message(filters.command("markdownhelp") & filters.private)
async def markdownhelp_cmd(client, message):
    await message.reply_text(
        "📝 <b>Markdown Guide</b>\n\n"
        "<b>Supported Formatting:</b>\n"
        "<code>*bold*</code> → <b>bold</b>\n"
        "<code>_italic_</code> → <i>italic</i>\n"
        "<code>__underline__</code> → <u>underline</u>\n"
        "<code>~strike~</code> → <s>strike</s>\n"
        "<code>`code`</code> → <code>code</code>\n"
        "<code>||spoiler||</code> → spoiler\n"
        "<code>&gt; quote</code> → quote\n\n"
        "<b>Buttons:</b>\n"
        "<code>[Label](buttonurl://URL)</code>\n"
        "<code>[Btn1](url1) | [Btn2](url2)</code>\n\n"
        "<b>Fillings:</b>\n"
        "<code>{mention}</code>, <code>{first}</code>, <code>{last}</code>\n"
        "<code>{fullname}</code>, <code>{username}</code>, <code>{id}</code>\n"
        "<code>{chatname}</code>, <code>{count}</code>, <code>{date}</code>, <code>{time}</code>\n\n"
        "<b>Links:</b>\n"
        "<code>[Google](https://google.com)</code>"
    )


# =========================================================
# /limits — Bot limits
# =========================================================

@Client.on_message(filters.command("limits"))
async def limits_cmd(client, message):
    await message.reply_text(
        f"📊 <b>{Config.BOT_NAME} Limits</b>\n\n"
        f"💬 <b>Max Message:</b> 4096 characters\n"
        f"📷 <b>Max Caption:</b> 1024 characters\n"
        f"🔘 <b>Max Buttons:</b> 100 per message\n"
        f"📋 <b>Max Filters:</b> Unlimited\n"
        f"📝 <b>Max Notes:</b> Unlimited\n"
        f"👥 <b>Max Admins:</b> Unlimited\n"
        f"⏱️ <b>Flood Wait:</b> Handled automatically\n"
        f"🗑️ <b>Purge Limit:</b> 100 messages per request\n"
        f"📢 <b>Broadcast:</b> Auto-handled with FloodWait"
    )
