# Requires: pip install nsfw-detector  (or similar)
# Simple keyword-based version:
from pyrogram import Client, filters
from database import db
from utils.permissions import is_admin
NSFW_WORDS = ["porn", "xxx", "nsfw", "sex", "nude"]  # extend karo

@Client.on_message(filters.group & filters.text, group=15)
async def antinsfw(client, message):
    chat = await db.get_chat(message.chat.id)
    if not chat.get("antinsfw", False): return
    text = message.text.lower()
    for w in NSFW_WORDS:
        if w in text:
            try: await message.delete()
            except: pass
            await message.reply_text(f"🚫 NSFW content removed.")
            return


@Client.on_message(filters.command("antinsfw") & filters.group)
async def antinsfw_toggle(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return
    chat = await db.get_chat(message.chat.id)
    state = not chat.get("antinsfw", False)
    await db.set_chat_field(message.chat.id, "antinsfw", state)
    await message.reply_text(f"✅ Anti-NSFW: {'ON' if state else 'OFF'}")
