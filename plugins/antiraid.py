import time
from pyrogram import Client, filters
from database import db
from utils.permissions import is_admin


@Client.on_message(filters.command("antiraid") & filters.group)
async def antiraid_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    chat = await db.get_chat(message.chat.id)
    state = not chat.get("antiraid", False)
    await db.set_chat_field(message.chat.id, "antiraid", state)
    await message.reply_text(f"✅ AntiRaid: {'ON' if state else 'OFF'}")


@Client.on_message(filters.command("setantiraid") & filters.group)
async def setantiraid_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    if len(message.command) < 2:
        return await message.reply_text("Usage: /setantiraid <threshold>")
    try:
        n = int(message.command[1])
    except ValueError:
        return await message.reply_text("❌ Must be a number.")
    await db.set_chat_field(message.chat.id, "antiraid_threshold", n)
    await message.reply_text(f"✅ AntiRaid threshold: {n}")


@Client.on_message(filters.new_chat_members & filters.group, group=1)
async def raid_watcher(client, message):
    chat = await db.get_chat(message.chat.id)
    if not chat.get("antiraid", False): return
    threshold = chat.get("antiraid_threshold", 10)
    await db.add_flood(message.chat.id, 0)
    count = await db.get_flood(message.chat.id, 0)
    if count >= threshold:
        await message.reply_text("🚨 <b>Raid detected!</b>")
        await db.reset_flood(message.chat.id, 0)
