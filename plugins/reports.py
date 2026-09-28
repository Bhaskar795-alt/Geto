from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus
from database import db
from utils.permissions import is_admin


# =========================================================
# REPORT TOGGLE
# =========================================================

@Client.on_message(filters.command("reports") & filters.group)
async def reports_toggle_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")

    if len(message.command) < 2 or message.command[1].lower() not in (
        "yes", "no", "on", "off"
    ):
        chat = await db.get_chat(message.chat.id)
        state = chat.get("reports_enabled", True)
        return await message.reply_text(
            f"📋 <b>Reports:</b> {'ON' if state else 'OFF'}\n"
            f"Usage: /reports yes|no"
        )

    val = message.command[1].lower()
    state = val in ("yes", "on")
    await db.set_chat_field(message.chat.id, "reports_enabled", state)
    await message.reply_text(f"✅ Reports: {'ON' if state else 'OFF'}")


# =========================================================
# HELPER — Get all admin mentions
# =========================================================

async def get_admin_mentions(client, chat_id):
    mentions = []
    try:
        async for m in client.get_chat_members(chat_id, filter="administrators"):
            if m.user.is_bot:
                continue
            mentions.append(m.user.mention)
    except Exception:
        pass
    return mentions


async def send_report(client, message):
    """Core report logic — sends notification to admins."""
    chat = await db.get_chat(message.chat.id)

    # Reports disabled?
    if not chat.get("reports_enabled", True):
        return

    if not message.reply_to_message:
        return await message.reply_text(
            "❌ Reply to a message to report it."
        )

    target = message.reply_to_message.from_user
    if not target:
        return await message.reply_text("❌ Cannot report this message.")

    reporter = message.from_user

    # Don't allow admins to report
    if await is_admin(client, message.chat.id, reporter.id):
        return await message.reply_text(
            "❌ Admins don't need to report."
        )

    # Don't allow reporting admins
    if await is_admin(client, message.chat.id, target.id):
        return await message.reply_text(
            "❌ You cannot report an admin."
        )

    # Get admin mentions
    admins = await get_admin_mentions(client, message.chat.id)
    if not admins:
        return await message.reply_text("❌ No admins found.")

    admin_mentions = " ".join(admins[:10])  # Limit to 10

    try:
        await message.reply_to_message.forward(message.chat.id)
    except Exception:
        pass

    await message.reply_text(
        f"🚨 <b>Report</b>\n\n"
        f"👤 <b>Reporter:</b> {reporter.mention}\n"
        f"🎯 <b>Reported:</b> {target.mention}\n"
        f"📝 <b>Message:</b> {message.reply_to_message.text or message.reply_to_message.caption or '[Media]'}\n\n"
        f"👮 <b>Admins Notified:</b>\n{admin_mentions}"
    )


# =========================================================
# /report COMMAND
# =========================================================

@Client.on_message(filters.command("report") & filters.group)
async def report_cmd(client, message):
    await send_report(client, message)


# =========================================================
# @admin MENTION
# =========================================================

@Client.on_message(
    filters.group & filters.regex(r"(?i)@admin\b"),
    group=25
)
async def admin_mention_report(client, message):
    # Avoid double-triggering for /report or command messages
    if message.text and message.text.startswith("/"):
        return
    await send_report(client, message)
