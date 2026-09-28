from pyrogram import Client, filters
from config import Config
from database import db


@Client.on_message(filters.command("addemoji") & filters.user(Config.OWNER_ID))
async def add_emoji(client, message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /addemoji <name> (reply with premium emoji)")
    name = message.command[1].upper()
    target = message.reply_to_message
    if not target or not target.entities:
        return await message.reply_text("❌ Reply to a message with a premium emoji.")
    for ent in target.entities:
        if str(ent.type) == "MessageEntityType.CUSTOM_EMOJI":
            emoji_id = ent.custom_emoji_id
            fallback = target.text[ent.offset:ent.offset + ent.length]
            await db.save_emoji(name, emoji_id, fallback, message.from_user.id)
            return await message.reply_text(
                f"✅ Saved\n<b>Name:</b> <code>{name}</code>\n"
                f"<b>ID:</b> <code>{emoji_id}</code>\n<b>Fallback:</b> {fallback}")
    await message.reply_text("❌ No custom emoji found.")


@Client.on_message(filters.command("emoji"))
async def send_emoji(client, message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /emoji <name>")
    doc = await db.get_emoji(message.command[1])
    if not doc:
        return await message.reply_text("❌ Not found.")
    try:
        from pyrogram.types import MessageEntity
        text = doc["fallback"]
        ent = MessageEntity(type="custom_emoji", offset=0, length=len(text),
                            custom_emoji_id=doc["emoji_id"])
        await message.reply_text(text, entities=[ent])
    except Exception:
        await message.reply_text(doc["fallback"])


@Client.on_message(filters.command("emojis"))
async def list_emojis(client, message):
    out = []
    async for d in db.get_all_emojis():
        out.append(f"• <code>{d['name']}</code> — {d['fallback']}")
    if not out: return await message.reply_text("None saved.")
    await message.reply_text("<b>🎨 Saved Emojis:</b>\n" + "\n".join(out))


@Client.on_message(filters.command("delemoji") & filters.user(Config.OWNER_ID))
async def del_emoji(client, message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /delemoji <name>")
    await db.delete_emoji(message.command[1])
    await message.reply_text("🗑️ Deleted.")
