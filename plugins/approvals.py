from pyrogram import Client, filters
from database import db
from utils.helpers import resolve_user, mention_html
from utils.permissions import is_admin


@Client.on_message(filters.command("approval") & filters.group)
async def approval_cmd(client, message):
    """Check a user's approval status."""
    uid, name, _ = await resolve_user(client, message)
    if not uid:
        uid = message.from_user.id
        name = message.from_user.first_name
    doc = await db.is_approved(message.chat.id, uid)
    if doc:
        reason = doc.get("reason") or "No reason"
        await message.reply_text(
            f"✅ {mention_html(uid, name)} is <b>approved</b> in this chat.\n"
            f"📝 Reason: {reason}"
        )
    else:
        await message.reply_text(
            f"❌ {mention_html(uid, name)} is <b>not approved</b> in this chat."
        )


@Client.on_message(filters.command("approve") & filters.group)
async def approve_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    uid, name, _ = await resolve_user(client, message)
    if not uid:
        return await message.reply_text("❌ Reply or give a user.")
    reason = " ".join(message.command[2:]) or ""
    await db.approve_user(message.chat.id, uid, reason)
    await message.reply_text(
        f"✅ Approved {mention_html(uid, name)}\n"
        f"📝 Locks, blocklists, antiflood won't apply to them."
    )


@Client.on_message(filters.command("unapprove") & filters.group)
async def unapprove_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    uid, name, _ = await resolve_user(client, message)
    if not uid:
        return await message.reply_text("❌ Reply or give a user.")
    await db.unapprove_user(message.chat.id, uid)
    await message.reply_text(
        f"✅ Unapproved {mention_html(uid, name)}\n"
        f"📝 They will now be subject to locks, blocklists, antiflood."
    )


@Client.on_message(filters.command("approved") & filters.group)
async def approved_list(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    lines = ["<b>✅ Approved Users:</b>\n"]
    count = 0
    async for d in db.get_approved_list(message.chat.id):
        count += 1
        uid = d["user_id"]
        reason = d.get("reason") or ""
        try:
            u = await client.get_users(uid)
            display = u.mention
        except Exception:
            display = f"<code>{uid}</code>"
        line = f"• {display}"
        if reason:
            line += f" — {reason}"
        lines.append(line)
    if count == 0:
        lines.append("<i>No approved users.</i>")
    lines.append(f"\n<b>Total:</b> <code>{count}</code>")
    await message.reply_text("\n".join(lines))


@Client.on_message(filters.command("unapproveall") & filters.group)
async def unapprove_all(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    # Confirm
    if len(message.command) < 2 or message.command[1].lower() not in ("yes", "confirm"):
        return await message.reply_text(
            "⚠️ <b>Warning:</b> This will unapprove ALL users. Cannot be undone.\n"
            "Type <code>/unapproveall yes</code> to confirm."
        )
    await db.unapprove_all(message.chat.id)
    await message.reply_text("✅ All users unapproved.")
