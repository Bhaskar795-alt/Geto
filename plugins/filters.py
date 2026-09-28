from pyrogram import Client, filters
from database import db
from utils.permissions import is_admin


@Client.on_message(filters.command("filter") & filters.group)
async def add_filter(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    if len(message.command) < 2:
        return await message.reply_text("Usage: /filter <keyword>")
    keyword = message.command[1]
    reply_msg = message.reply_to_message or message
    text = reply_msg.text or reply_msg.caption or ""
    if text.startswith("/filter"):
        text = " ".join(message.command[2:])
    msg_type, file_id = "text", ""
    if reply_msg.photo: msg_type, file_id = "photo", reply_msg.photo.file_id
    elif reply_msg.video: msg_type, file_id = "video", reply_msg.video.file_id
    elif reply_msg.sticker: msg_type, file_id = "sticker", reply_msg.sticker.file_id
    elif reply_msg.document: msg_type, file_id = "document", reply_msg.document.file_id
    await db.save_filter(message.chat.id, keyword, text, msg_type, file_id)
    await message.reply_text(f"✅ Filter saved: <code>{keyword}</code>")


@Client.on_message(filters.command("stop") & filters.group)
async def stop_filter(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    if len(message.command) < 2:
        return await message.reply_text("Usage: /stop <keyword>")
    await db.delete_filter(message.chat.id, message.command[1])
    await message.reply_text(f"🗑️ Removed: <code>{message.command[1]}</code>")


@Client.on_message(filters.command("stopall") & filters.group)
async def stopall_filter(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    await db.delete_all_filters(message.chat.id)
    await message.reply_text("🗑️ All filters removed.")


@Client.on_message(filters.command("filters") & filters.group)
async def list_filters(client, message):
    keys = []
    async for d in db.get_all_filters(message.chat.id):
        keys.append(f"• <code>{d['keyword']}</code>")
    if not keys: return await message.reply_text("No filters.")
    await message.reply_text("<b>🔥 Filters:</b>\n" + "\n".join(keys))


@Client.on_message(filters.group & ~filters.service, group=5)
async def filter_watcher(client, message):
    if not message.text and not message.caption: return
    text = (message.text or message.caption).lower()
    for word in text.split():
        doc = await db.get_filter(message.chat.id, word)
        if not doc: continue
        try:
            if doc["msg_type"] == "text":
                await message.reply_text(doc["reply"] or "…")
            elif doc["msg_type"] == "photo":
                await message.reply_photo(doc["file_id"], caption=doc["reply"] or "")
            elif doc["msg_type"] == "video":
                await message.reply_video(doc["file_id"], caption=doc["reply"] or "")
            elif doc["msg_type"] == "sticker":
                await message.reply_sticker(doc["file_id"])
            elif doc["msg_type"] == "document":
                await message.reply_document(doc["file_id"], caption=doc["reply"] or "")
        except Exception:
            pass
        break
