from pyrogram import Client, filters
from database import db
from utils.permissions import is_admin


@Client.on_message(filters.command("disable") & filters.group)
async def disable_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    if len(message.command) < 2:
        return await message.reply_text("Usage: /disable <command>")
    await db.disable_cmd(message.chat.id, message.command[1])
    await message.reply_text(f"🚫 Disabled /{message.command[1]}")


@Client.on_message(filters.command("enable") & filters.group)
async def enable_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    if len(message.command) < 2:
        return await message.reply_text("Usage: /enable <command>")
    await db.enable_cmd(message.chat.id, message.command[1])
    await message.reply_text(f"✅ Enabled /{message.command[1]}")


@Client.on_message(filters.command("disabled") & filters.group)
async def list_disabled(client, message):
    out = []
    async for d in db.get_disabled(message.chat.id):
        out.append(f"• /{d['cmd']}")
    if not out: return await message.reply_text("No disabled commands.")
    await message.reply_text("<b>🚫 Disabled:</b>\n" + "\n".join(out))
