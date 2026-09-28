from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import ChatPermissions
from database import db
from utils.helpers import resolve_user, mention_html
from utils.permissions import is_admin

MUTE_PERMS = ChatPermissions(can_send_messages=False, can_send_media_messages=False,
    can_send_other_messages=False, can_add_web_page_previews=False, can_send_polls=False)


@Client.on_message(filters.command("warn") & filters.group)
async def warn_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    uid, name, _ = await resolve_user(client, message)
    if not uid: return await message.reply_text("❌ Give a user.")
    reason = " ".join(message.command[2:]) or "No reason"
    count = await db.add_warn(message.chat.id, uid, reason)
    chat = await db.get_chat(message.chat.id)
    limit = chat.get("warn_limit", 3)
    action = chat.get("warn_action", "mute")
    await message.reply_text(
        f"⚠️ <b>Warned</b> {mention_html(uid, name)}\n"
        f"📝 {reason}\n"
        f"🔢 <b>Total:</b> {count}/{limit}")
    if count >= limit:
        try:
            if action == "mute":
                await client.restrict_chat_member(message.chat.id, uid, MUTE_PERMS)
                await db.mute_user(message.chat.id, uid, 0, f"Warn limit reached ({limit})")
                await message.reply_text(f"🔇 Auto-muted {mention_html(uid, name)} (warn limit reached)")
            elif action == "ban":
                await client.ban_chat_member(message.chat.id, uid)
                await message.reply_text(f"🔨 Auto-banned {mention_html(uid, name)} (warn limit reached)")
            elif action == "kick":
                await client.ban_chat_member(message.chat.id, uid)
                await client.unban_chat_member(message.chat.id, uid)
                await message.reply_text(f"👢 Auto-kicked {mention_html(uid, name)}")
        except Exception as e:
            await message.reply_text(f"❌ Auto action failed: {e}")


@Client.on_message(filters.command("unwarn") & filters.group)
async def unwarn_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    uid, name, _ = await resolve_user(client, message)
    if not uid: return await message.reply_text("❌ Give a user.")
    count = await db.remove_last_warn(message.chat.id, uid)
    await message.reply_text(f"✅ Unwarned {mention_html(uid, name)}\n🔢 Now: {count}")


@Client.on_message(filters.command("warns") & filters.group)
async def warns_cmd(client, message):
    uid, name, _ = await resolve_user(client, message)
    if not uid:
        uid = message.from_user.id
        name = message.from_user.first_name
    count = await db.get_warns(message.chat.id, uid)
    reasons = await db.get_warn_reasons(message.chat.id, uid)
    txt = f"⚠️ <b>Warns for</b> {mention_html(uid, name)}: <b>{count}</b>\n"
    for i, r in enumerate(reasons, 1):
        txt += f"{i}. {r}\n"
    await message.reply_text(txt)


@Client.on_message(filters.command("resetwarns") & filters.group)
async def resetwarns_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    uid, name, _ = await resolve_user(client, message)
    if not uid: return await message.reply_text("❌ Give a user.")
    await db.reset_warns(message.chat.id, uid)
    await message.reply_text(f"✅ Reset warns for {mention_html(uid, name)}")


@Client.on_message(filters.command("setwarnlimit") & filters.group)
async def setwarnlimit_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    if len(message.command) < 2:
        return await message.reply_text("Usage: /setwarnlimit <number>")
    try:
        n = int(message.command[1])
    except ValueError:
        return await message.reply_text("❌ Must be a number.")
    await db.set_chat_field(message.chat.id, "warn_limit", n)
    await message.reply_text(f"✅ Warn limit set to {n}")


@Client.on_message(filters.command("setwarnmode") & filters.group)
async def setwarnmode_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    if len(message.command) < 2 or message.command[1] not in ("mute", "ban", "kick"):
        return await message.reply_text("Usage: /setwarnmode mute|ban|kick")
    await db.set_chat_field(message.chat.id, "warn_action", message.command[1])
    await message.reply_text(f"✅ Warn action: {message.command[1]}")
