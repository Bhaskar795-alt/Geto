from pyrogram import Client, filters
from config import Config
from database import db
from utils.permissions import is_admin


@Client.on_message(filters.command("setlog") & filters.group)
async def setlog_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    if len(message.command) < 2:
        return await message.reply_text("Usage: /setlog <channel_id>")
    try:
        cid = int(message.command[1])
    except ValueError:
        return await message.reply_text("❌ Invalid channel ID.")
    await db.set_chat_field(message.chat.id, "log_channel", cid)
    await message.reply_text(f"✅ Log channel set: {cid}")


@Client.on_message(filters.command("nolog") & filters.group)
async def nolog_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    await db.set_chat_field(message.chat.id, "log_channel", 0)
    await message.reply_text("✅ Logs disabled.")


async def send_log(client, chat_id, text):
    log_chat = await db.get_log_chat(chat_id)
    if not log_chat: return
    try:
        await client.send_message(log_chat, text)
    except Exception:
        pass
