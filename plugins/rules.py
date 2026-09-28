from pyrogram import Client, filters
from database import db
from utils.permissions import is_admin


@Client.on_message(filters.command("setrules") & filters.group)
async def setrules_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    if message.reply_to_message:
        text = message.reply_to_message.text or ""
    elif len(message.command) > 1:
        text = message.text.split(None, 1)[1]
    else:
        return await message.reply_text("❌ Reply or provide text.")
    await db.set_chat_field(message.chat.id, "rules", text)
    await message.reply_text("✅ Rules saved.")


@Client.on_message(filters.command("resetrules") & filters.group)
async def resetrules_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    await db.set_chat_field(message.chat.id, "rules", None)
    await message.reply_text("✅ Rules reset.")


@Client.on_message(filters.command("rules"))
async def rules_cmd(client, message):
    if message.chat.type == "private":
        return await message.reply_text("This command is for groups.")
    chat = await db.get_chat(message.chat.id)
    rules = chat.get("rules") or "No rules set."
    await message.reply_text(rules)
