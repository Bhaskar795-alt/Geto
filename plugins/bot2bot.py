from pyrogram import Client, filters
from database import db
from utils.permissions import is_admin


@Client.on_message(filters.command("bot2bot") & filters.group)
async def bot2bot_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    if len(message.command) < 2 or message.command[1].lower() not in ("off", "admin", "all"):
        chat = await db.get_chat(message.chat.id)
        current = chat.get("bot2bot", "off")
        return await message.reply_text(
            f"📋 <b>Bot to Bot:</b> <code>{current}</code>\n"
            f"Options: off / admin / all\n"
            f"Usage: /bot2bot &lt;mode&gt;"
        )
    mode = message.command[1].lower()
    await db.set_chat_field(message.chat.id, "bot2bot", mode)
    await message.reply_text(f"✅ Bot to Bot: <code>{mode}</code>")


@Client.on_message(filters.command("bot2botskipreview") & filters.group)
async def bot2botskipreview_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    if len(message.command) < 2 or message.command[1].lower() not in (
        "yes", "no", "on", "off"
    ):
        chat = await db.get_chat(message.chat.id)
        state = chat.get("bot2bot_skipreview", False)
        return await message.reply_text(
            f"📋 <b>Skip Review:</b> {'ON' if state else 'OFF'}\n"
            f"Usage: /bot2botskipreview yes|no"
        )
    state = message.command[1].lower() in ("yes", "on")
    await db.set_chat_field(message.chat.id, "bot2bot_skipreview", state)
    await message.reply_text(f"✅ Skip Review: {'ON' if state else 'OFF'}")
