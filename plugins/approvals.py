from pyrogram import Client, filters
from database import db
from utils.helpers import resolve_user, mention_html
from utils.permissions import is_admin


@Client.on_message(filters.command("approve") & filters.group)
async def approve_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    uid, name, _ = await resolve_user(client, message)
    if not uid: return await message.reply_text("❌ Give a user.")
    reason = " ".join(message.command[2:]) or ""
    await db.approve_user(message.chat.id, uid, reason)
    await message.reply_text(f"✅ Approved {mention_html(uid, name)}")


@Client.on_message(filters.command("unapprove") & filters.group)
async def unapprove_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    uid, name, _ = await resolve_user(client, message)
    if not uid: return await message.reply_text("❌ Give a user.")
    await db.unapprove_user(message.chat.id, uid)
    await message.reply_text(f"✅ Unapproved {mention_html(uid, name)}")


@Client.on_message(filters.command("approved") & filters.group)
async def approved_list(client, message):
    lines = ["<b>✅ Approved Users:</b>\n"]
    async for d in db.get_approved_list(message.chat.id):
        lines.append(f"• <code>{d['user_id']}</code> — {d.get('reason','')}")
    if len(lines) == 1: lines.append("<i>None</i>")
    await message.reply_text("\n".join(lines))


@Client.on_message(filters.command("unapproveall") & filters.group)
async def unapprove_all(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    await db.unapprove_all(message.chat.id)
    await message.reply_text("✅ All unapproved.")
