from pyrogram import Client, filters
from pyrogram.types import ChatPermissions
from database import db
from utils.permissions import is_admin

MUTE_PERMS = ChatPermissions(can_send_messages=False, can_send_media_messages=False,
    can_send_other_messages=False, can_add_web_page_previews=False, can_send_polls=False)


@Client.on_message(filters.command("antiflood") & filters.group)
async def antiflood_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    chat = await db.get_chat(message.chat.id)
    state = not chat.get("antiflood", False)
    await db.set_chat_field(message.chat.id, "antiflood", state)
    await message.reply_text(f"✅ AntiFlood: {'ON' if state else 'OFF'}")


@Client.on_message(filters.command("setflood") & filters.group)
async def setflood_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    if len(message.command) < 2:
        return await message.reply_text("Usage: /setflood <count>")
    try:
        n = int(message.command[1])
    except ValueError:
        return await message.reply_text("❌ Must be a number.")
    await db.set_chat_field(message.chat.id, "flood_limit", n)
    await message.reply_text(f"✅ Flood limit: {n}")


@Client.on_message(filters.command("setfloodmode") & filters.group)
async def setfloodmode_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    if len(message.command) < 2 or message.command[1] not in ("mute", "ban", "kick"):
        return await message.reply_text("Usage: /setfloodmode mute|ban|kick")
    await db.set_chat_field(message.chat.id, "flood_action", message.command[1])
    await message.reply_text(f"✅ Flood action: {message.command[1]}")


@Client.on_message(filters.command("clearflood") & filters.group)
async def clearflood_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    if message.reply_to_message:
        uid = message.reply_to_message.from_user.id
        await db.reset_flood(message.chat.id, uid)
        await message.reply_text("✅ Flood counter cleared.")


@Client.on_message(filters.group & ~filters.service, group=10)
async def flood_watcher(client, message):
    if not message.from_user: return
    chat = await db.get_chat(message.chat.id)
    if not chat.get("antiflood", False): return
    if await is_admin(client, message.chat.id, message.from_user.id): return
    limit = chat.get("flood_limit", 7)
    action = chat.get("flood_action", "mute")
    count = await db.add_flood(message.chat.id, message.from_user.id)
    if count >= limit:
        try:
            if action == "mute":
                await client.restrict_chat_member(message.chat.id, message.from_user.id, MUTE_PERMS)
                await db.mute_user(message.chat.id, message.from_user.id, 0, "flood")
                await message.reply_text(f"🔇 Muted for flooding.")
            elif action == "ban":
                await client.ban_chat_member(message.chat.id, message.from_user.id)
            elif action == "kick":
                await client.ban_chat_member(message.chat.id, message.from_user.id)
                await client.unban_chat_member(message.chat.id, message.from_user.id)
        except Exception:
            pass
        await db.reset_flood(message.chat.id, message.from_user.id)
