from datetime import datetime
from pyrogram import Client, filters
from database import db
from utils.permissions import is_admin

LOG_CATEGORIES = ["settings", "admin", "user", "automated", "reports", "other"]


# =========================================================
# LOG CHANNEL COMMANDS
# =========================================================

@Client.on_message(filters.command("logchannel") & filters.group)
async def logchannel_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    chat = await db.get_chat(message.chat.id)
    cid = chat.get("log_channel", 0)
    if cid:
        await message.reply_text(f"📋 <b>Log Channel:</b> <code>{cid}</code>")
    else:
        await message.reply_text("❌ No log channel set. Use /setlog")


@Client.on_message(filters.command("setlog") & filters.group)
async def setlog_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")

    # Option 1: ID diya
    if len(message.command) > 1:
        try:
            cid = int(message.command[1])
        except ValueError:
            return await message.reply_text("❌ Invalid chat ID.")
        await db.set_chat_field(message.chat.id, "log_channel", cid)
        try:
            await client.send_message(cid, "✅ Log channel connected.")
            return await message.reply_text(f"✅ Log channel set: <code>{cid}</code>")
        except Exception as e:
            return await message.reply_text(
                f"⚠️ Set but cannot post: {e}\n"
                f"Make bot admin with Post permission in that channel."
            )

    # Option 2: Forwarded from channel
    if message.forward_from_chat:
        cid = message.forward_from_chat.id
        await db.set_chat_field(message.chat.id, "log_channel", cid)
        try:
            await client.send_message(
                cid, f"✅ Log channel set for group: <code>{message.chat.id}</code>")
        except Exception as e:
            return await message.reply_text(f"❌ Bot cannot post in channel: {e}")
        return await message.reply_text(f"✅ Log channel set: <code>{cid}</code>")

    # No ID, no forward
    await message.reply_text(
        "📋 <b>How to set log channel:</b>\n\n"
        "<b>Option 1:</b> Direct ID\n"
        "<code>/setlog -1001234567890</code>\n\n"
        "<b>Option 2:</b> Forward\n"
        "1. Add bot as admin in channel\n"
        "2. Send /setlog in channel\n"
        "3. Forward that message to this group"
    )


@Client.on_message(filters.command("unsetlog") & filters.group)
async def unsetlog_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    await db.set_chat_field(message.chat.id, "log_channel", 0)
    await message.reply_text("✅ Log channel removed.")


@Client.on_message(filters.command("log") & filters.group)
async def log_enable_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    if len(message.command) < 2:
        return await message.reply_text(
            "Usage: /log <category>\n"
            "Categories: " + ", ".join(LOG_CATEGORIES)
        )
    cat = message.command[1].lower()
    if cat not in LOG_CATEGORIES:
        return await message.reply_text("❌ Invalid category.")
    await db.set_chat_field(message.chat.id, f"log_{cat}", True)
    await message.reply_text(f"✅ Logging: <code>{cat}</code> ON")


@Client.on_message(filters.command("nolog") & filters.group)
async def nolog_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    if len(message.command) < 2:
        return await message.reply_text("Usage: /nolog <category>")
    cat = message.command[1].lower()
    if cat not in LOG_CATEGORIES:
        return await message.reply_text("❌ Invalid category.")
    await db.set_chat_field(message.chat.id, f"log_{cat}", False)
    await message.reply_text(f"✅ Logging: <code>{cat}</code> OFF")


@Client.on_message(filters.command("logcategories") & filters.group)
async def logcategories_cmd(client, message):
    await message.reply_text(
        "📋 <b>Log Categories:</b>\n\n"
        "• <code>settings</code> — Settings changes\n"
        "• <code>admin</code> — Admin actions\n"
        "• <code>user</code> — User actions\n"
        "• <code>automated</code> — Auto actions\n"
        "• <code>reports</code> — Reports\n"
        "• <code>other</code> — Other\n\n"
        "Enable: /log admin\n"
        "Disable: /nolog admin"
    )


# =========================================================
# SILENT ACTIONS
# =========================================================

@Client.on_message(filters.command("silentactions") & filters.group)
async def silentactions_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    if len(message.command) < 2 or message.command[1].lower() not in (
        "yes", "no", "on", "off"
    ):
        chat = await db.get_chat(message.chat.id)
        state = chat.get("silentactions", False)
        log = chat.get("log_channel", 0)
        return await message.reply_text(
            f"📋 <b>Silent Actions:</b> {'ON' if state else 'OFF'}\n"
            f"📊 <b>Log Channel:</b> {'Set' if log else 'Not set'}\n"
            f"⚠️ Log channel required for silent actions.\n"
            f"Usage: /silentactions yes|no"
        )
    state = message.command[1].lower() in ("yes", "on")
    await db.set_chat_field(message.chat.id, "silentactions", state)
    await message.reply_text(f"✅ Silent Actions: {'ON' if state else 'OFF'}")


# =========================================================
# LOG_ACTION — Call this from any command
# =========================================================

async def log_action(client, chat_id, category, action,
                     user=None, target=None, reason="", extra=""):
    """Centralized log helper. Call from ban/mute/kick/etc."""
    try:
        chat = await db.get_chat(chat_id)
        if not chat.get(f"log_{category}", False):
            print(f"[LOG] Category '{category}' not enabled")
            return
        log_channel = chat.get("log_channel", 0)
        if not log_channel:
            print(f"[LOG] No log channel set")
            return

        text = f"📋 <b>Log — {category.upper()}</b>\n\n"
        text += f"⚡ <b>Action:</b> <code>{action}</code>\n"
        if user:
            mention = user.mention if hasattr(user, "mention") else str(user)
            text += f"👤 <b>By:</b> {mention}\n"
        if target:
            mention = target.mention if hasattr(target, "mention") else str(target)
            text += f"🎯 <b>Target:</b> {mention}\n"
        if reason:
            text += f"📝 <b>Reason:</b> {reason}\n"
        if extra:
            text += f"ℹ️ {extra}\n"
        text += f"🕐 <b>Time:</b> {datetime.now().strftime('%d %b %Y %H:%M:%S')}"

        await client.send_message(log_channel, text)
        print(f"[LOG] Sent to {log_channel}")
    except Exception as e:
        print(f"[LOG ERROR] {e}")
