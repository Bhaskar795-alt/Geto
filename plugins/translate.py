from pyrogram import Client, filters
from deep_translator import GoogleTranslator


@Client.on_message(filters.command("tr"))
async def tr_cmd(client, message):
    if not message.reply_to_message:
        return await message.reply_text("Reply to a message.")
    if len(message.command) < 2:
        return await message.reply_text("Usage: /tr <lang_code>")
    text = message.reply_to_message.text or message.reply_to_message.caption or ""
    if not text:
        return
    try:
        result = GoogleTranslator(source="auto",
            target=message.command[1]).translate(text)
        await message.reply_text(f"🌐 <b>{message.command[1]}</b>\n{result}")
    except Exception as e:
        await message.reply_text(f"❌ {e}")
