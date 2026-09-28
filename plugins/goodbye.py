from pyrogram import Client, filters
from database import db
from utils.permissions import is_admin
from utils.helpers import format_text


@Client.on_message(filters.command("setgoodbye") & filters.group)
async def setgoodbye_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    if message.reply_to_message:
        text = message.reply_to_message.text or message.reply_to_message.caption or ""
    elif len(message.command) > 1:
        text = message.text.split(None, 1)[1]
    else:
        return await message.reply_text("❌ Reply or provide text.")
    await db.set_chat_field(message.chat.id, "goodbye", text)
    await message.reply_text("✅ Goodbye saved.")


@Client.on_message(filters.command("resetgoodbye") & filters.group)
async def resetgoodbye_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    await db.set_chat_field(message.chat.id, "goodbye", None)
    await message.reply_text("✅ Goodbye reset.")


@Client.on_message(filters.command("goodbye") & filters.group)
async def goodbye_toggle(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    chat = await db.get_chat(message.chat.id)
    state = not chat.get("goodbye_enabled", True)
    await db.set_chat_field(message.chat.id, "goodbye_enabled", state)
    await message.reply_text(f"✅ Goodbye: {'ON' if state else 'OFF'}")


@Client.on_message(filters.left_chat_member & filters.group)
async def on_leave(client, message):
    chat = await db.get_chat(message.chat.id)
    if not chat.get("goodbye_enabled", True): return
    tmpl = chat.get("goodbye")
    if not tmpl: return
    user = message.left_chat_member
    if user.is_bot: return
    txt = format_text(tmpl, user=user, chat=message.chat)
    try:
        await message.reply_text(txt)
    except Exception:
        pass
