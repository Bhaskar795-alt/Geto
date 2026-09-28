from pyrogram import Client, filters
from database import db
from utils.permissions import is_admin

LOG_CATEGORIES = [
    "settings", "admin", "user", "automated", "reports", "other"
]


@Client.on_message(filters.command("logchannel") & filters.group)
async def logchannel_cmd(client, message):
    chat = await db.get_chat(message.chat.id)
    cid = chat.get("log_channel", 0)
    if cid:
        await message.reply_text(f"📋 <b>Log Channel:</b> <code>{cid}</code>")
    else:
        await message.reply_text("❌ No log channel set.")


@Client.on_message(filters.command("setlog") & filters.private)
async def setlog_pm(client, message):
    """Step 1: User sends /setlog in the channel (bot's PM context)."""
    await message.reply_text(
        "📋 Now forward this /setlog command to the group where you want to log.\n"
        "Make sure the bot is admin in that group."
    )


@Client.on_message(filters.command("setlog") & filters.group)
async def setlog_group(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")

    # If forwarded from channel
    if message.forward_from_chat and message.forward_from_chat.type == "channel":
        cid = message.forward_from_chat.id
        await db.set_chat_field(message.chat.id, "log_channel", cid)
        try:
            await client.send_message(cid, f"✅ Log channel set for group: <code>{message.chat.id}</code>")
        except Exception:
            pass
        return await message.reply_text(f"✅ Log channel set: <code>{cid}</code>")

    await message.reply_text(
        "📋 <b>How to set log channel:</b>\n"
        "1. Add bot as admin in your channel\n"
        "2. Send /setlog in that channel\n"
        "3. Forward that command to this group\n"
        "4. Done!"
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
        "• <code>admin</code> — Admin actions (ban/mute/kick)\n"
        "• <code>user</code> — User actions\n"
        "• <code>automated</code> — Automated actions (flood/blocklist)\n"
        "• <code>reports</code> — Reports\n"
        "• <code>other</code> — Other\n\n"
        "Enable: /log settings\n"
        "Disable: /nolog settings"
    )


async def send_log(client, chat_id, category, text):
    """Helper to send log message."""
    chat = await db.get_chat(chat_id)
    if not chat.get(f"log_{category}", False):
        return
    log_channel = chat.get("log_channel", 0)
    if not log_channel:
        return
    try:
        await client.send_message(log_channel, text)
    except Exception:
        pass
