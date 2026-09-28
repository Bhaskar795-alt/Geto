from pyrogram import Client, filters
from database import db
from utils.permissions import is_admin


@Client.on_message(filters.command("addblocklist") & filters.group)
async def add_block_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    if len(message.command) < 2:
        return await message.reply_text("Usage: /addblocklist <word>")
    await db.add_block(message.chat.id, message.command[1])
    await message.reply_text(f"✅ Added: <code>{message.command[1]}</code>")


@Client.on_message(filters.command(["rmblocklist", "removeblocklist"]) & filters.group)
async def rm_block_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    if len(message.command) < 2:
        return await message.reply_text("Usage: /rmblocklist <word>")
    await db.remove_block(message.chat.id, message.command[1])
    await message.reply_text("🗑️ Removed.")


@Client.on_message(filters.command("blocklist") & filters.group)
async def list_blocks(client, message):
    words = []
    async for d in db.get_blocks(message.chat.id):
        words.append(f"• <code>{d['word']}</code>")
    if not words:
        return await message.reply_text("Blocklist empty.")
    await message.reply_text("<b>🚫 Blocklist:</b>\n" + "\n".join(words))


@Client.on_message(filters.command("clearblocklist") & filters.group)
async def clear_blocks(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    await db.clear_blocks(message.chat.id)
    await message.reply_text("🗑️ Blocklist cleared.")
