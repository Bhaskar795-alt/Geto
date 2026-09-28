import time
from pyrogram import Client, filters
from database import db
from config import Config


@Client.on_message(filters.command("afk") & filters.private)
async def afk_cmd(client, message):
    reason = " ".join(message.command[1:]) or "AFK"
    await db.users.update_one(
        {"user_id": message.from_user.id},
        {"$set": {"afk": True, "afk_reason": reason, "afk_time": int(time.time())}},
        upsert=True)
    await message.reply_text(f"💤 AFK set: {reason}")


@Client.on_message(filters.private & ~filters.me, group=1)
async def check_afk(client, message):
    if not message.from_user: return
    # Check if target user is AFK
    if message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user.id
        u = await db.get_user(target)
        if u and u.get("afk"):
            await message.reply_text(
                f"💤 User is AFK: {u.get('afk_reason','')}\n"
                f"Since: <code>{u.get('afk_time',0)}</code>")
    # Remove own afk
    me = await db.get_user(message.from_user.id)
    if me and me.get("afk"):
        await db.users.update_one({"user_id": message.from_user.id},
            {"$unset": {"afk": "", "afk_reason": "", "afk_time": ""}})
        await message.reply_text("✅ Welcome back! AFK removed.")
