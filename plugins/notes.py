from pyrogram import Client, filters
from database import db
from utils.permissions import is_admin


@Client.on_message(filters.command("save") & filters.group)
async def save_note(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    if len(message.command) < 2:
        return await message.reply_text("Usage: /save <name> (reply)")
    name = message.command[1]
    r = message.reply_to_message
    if not r: return await message.reply_text("Reply to a message.")
    text = r.text or r.caption or ""
    msg_type, file_id = "text", ""
    if r.photo: msg_type, file_id = "photo", r.photo.file_id
    elif r.video: msg_type, file_id = "video", r.video.file_id
    await db.save_note(message.chat.id, name, text, msg_type, file_id)
    await message.reply_text(f"✅ Note saved: <code>{name}</code>")


@Client.on_message(filters.command("get") & filters.group)
async def get_note(client, message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /get <name>")
    doc = await db.get_note(message.chat.id, message.command[1])
    if not doc: return await message.reply_text("❌ Not found.")
    if doc["msg_type"] == "text":
        await message.reply_text(doc["reply"] or "…")
    elif doc["msg_type"] == "photo":
        await message.reply_photo(doc["file_id"], caption=doc["reply"] or "")
    elif doc["msg_type"] == "video":
        await message.reply_video(doc["file_id"], caption=doc["reply"] or "")


@Client.on_message(filters.command("notes") & filters.group)
async def list_notes(client, message):
    out = []
    async for d in db.get_all_notes(message.chat.id):
        out.append(f"• <code>{d['name']}</code>")
    if not out: return await message.reply_text("No notes.")
    await message.reply_text("<b>📝 Notes:</b>\n" + "\n".join(out))


@Client.on_message(filters.command("clear") & filters.group)
async def clear_note(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    if len(message.command) < 2:
        return await message.reply_text("Usage: /clear <name>")
    await db.delete_note(message.chat.id, message.command[1])
    await message.reply_text("🗑️ Deleted.")


@Client.on_message(filters.command("clearall") & filters.group)
async def clear_all_notes(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    await db.delete_all_notes(message.chat.id)
    await message.reply_text("🗑️ All notes deleted.")
