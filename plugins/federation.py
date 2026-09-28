import uuid
from pyrogram import Client, filters
from config import Config
from database import db
from utils.helpers import resolve_user


@Client.on_message(filters.command("newfed") & filters.user(Config.OWNER_ID))
async def newfed(client, message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /newfed <name>")
    fed_id = str(uuid.uuid4())[:8]
    name = " ".join(message.command[1:])
    await db.create_fed(fed_id, name, message.from_user.id)
    await message.reply_text(f"✅ Federation created.\n<b>ID:</b> <code>{fed_id}</code>")


@Client.on_message(filters.command("delfed") & filters.user(Config.OWNER_ID))
async def delfed(client, message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /delfed <fed_id>")
    await db.delete_fed(message.command[1])
    await message.reply_text("✅ Deleted.")


@Client.on_message(filters.command("joinfed") & filters.user(Config.OWNER_ID))
async def joinfed(client, message):
    if len(message.command) < 3:
        return await message.reply_text("Usage: /joinfed <fed_id> <chat_id>")
    await db.join_fed(message.command[1], int(message.command[2]))
    await message.reply_text("✅ Joined.")


@Client.on_message(filters.command("fedinfo") & filters.user(Config.OWNER_ID))
async def fedinfo(client, message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /fedinfo <fed_id>")
    fed = await db.get_fed(message.command[1])
    if not fed: return await message.reply_text("❌ Not found.")
    await message.reply_text(
        f"🌐 <b>Federation</b>\nName: {fed['name']}\n"
        f"ID: <code>{fed['fed_id']}</code>\nOwner: <code>{fed['owner']}</code>")


@Client.on_message(filters.command("fban") & filters.user(Config.OWNER_ID))
async def fban(client, message):
    if len(message.command) < 3:
        return await message.reply_text("Usage: /fban <fed_id> <user>")
    fed_id = message.command[1]
    uid = int(message.command[2]) if message.command[2].isdigit() else None
    if not uid:
        u, _, _ = await resolve_user(client, message)
        uid = u
    if not uid: return await message.reply_text("❌ Invalid user.")
    await db.add_fed_ban(fed_id, uid, " ".join(message.command[3:]))
    fed = await db.get_fed(fed_id)
    for cid in fed.get("chats", []):
        try:
            await client.ban_chat_member(cid, uid)
        except Exception:
            pass
    await message.reply_text(f"🔨 Fed-banned <code>{uid}</code>")


@Client.on_message(filters.command("unfban") & filters.user(Config.OWNER_ID))
async def unfban(client, message):
    if len(message.command) < 3:
        return await message.reply_text("Usage: /unfban <fed_id> <user_id>")
    await db.remove_fed_ban(message.command[1], int(message.command[2]))
    await message.reply_text("✅ Unbanned.")
