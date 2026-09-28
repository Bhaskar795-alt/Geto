from pyrogram import Client, filters
from database import db
from utils.permissions import is_admin

LOCK_TYPES = ["links", "url", "invitelink", "photo", "video", "audio", "voice",
    "document", "sticker", "gif", "animation", "contact", "location",
    "poll", "game", "forward", "bot", "button", "inline", "channel"]


@Client.on_message(filters.command("lock") & filters.group)
async def lock_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    if len(message.command) < 2:
        return await message.reply_text("Usage: /lock <type>")
    lt = message.command[1].lower()
    if lt not in LOCK_TYPES:
        return await message.reply_text(f"❌ Unknown lock: {lt}")
    await db.set_lock(message.chat.id, lt, True)
    await message.reply_text(f"🔒 Locked <code>{lt}</code>")


@Client.on_message(filters.command("unlock") & filters.group)
async def unlock_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    if len(message.command) < 2:
        return await message.reply_text("Usage: /unlock <type>")
    lt = message.command[1].lower()
    await db.set_lock(message.chat.id, lt, False)
    await message.reply_text(f"🔓 Unlocked <code>{lt}</code>")


@Client.on_message(filters.command("locks") & filters.group)
async def locks_cmd(client, message):
    doc = await db.get_locks(message.chat.id)
    active = [k for k, v in doc.items() if k not in ("_id", "chat_id") and v]
    if not active:
        return await message.reply_text("No active locks.")
    await message.reply_text("🔒 <b>Active Locks:</b>\n" + "\n".join(f"• {x}" for x in active))


@Client.on_message(filters.command("locktypes"))
async def locktypes_cmd(client, message):
    await message.reply_text("<b>Lock types:</b>\n" + ", ".join(LOCK_TYPES))
