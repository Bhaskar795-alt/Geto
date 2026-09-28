import re
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database import db
from utils.permissions import is_admin


def parse_buttons(text):
    """Parse [Label](buttonurl://URL) style buttons."""
    if not text:
        return "", None
    pattern = r"\[([^\]]+)\]\(buttonurl://([^\)]+)\)"
    rows = []
    for line in text.split("\n"):
        row = []
        for m in re.finditer(pattern, line):
            row.append(InlineKeyboardButton(m.group(1), url=m.group(2)))
        if row:
            rows.append(row)
    clean = re.sub(pattern, "", text)
    clean = "\n".join(line for line in clean.split("\n") if line.strip())
    if not rows:
        return clean.strip(), None
    return clean.strip(), InlineKeyboardMarkup(rows)


@Client.on_message(filters.command("filter") & filters.group)
async def add_filter(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    if len(message.command) < 2:
        return await message.reply_text(
            "📝 <b>Usage:</b>\n"
            "/filter &lt;keyword&gt; (reply to a message)\n"
            "Or: /filter &lt;keyword&gt; &lt;text&gt;"
        )
    keyword = message.command[1]

    # Case 1: Reply to a message
    if message.reply_to_message:
        r = message.reply_to_message
        text = r.caption or r.text or ""
        msg_type, file_id = "text", ""
        if r.photo:
            msg_type, file_id = "photo", r.photo.file_id
        elif r.video:
            msg_type, file_id = "video", r.video.file_id
        elif r.sticker:
            msg_type, file_id = "sticker", r.sticker.file_id
        elif r.document:
            msg_type, file_id = "document", r.document.file_id
        elif r.animation:
            msg_type, file_id = "animation", r.animation.file_id
    # Case 2: Direct text
    elif len(message.command) > 2:
        text = message.text.split(None, 2)[2]
        msg_type, file_id = "text", ""
    else:
        return await message.reply_text("❌ Reply to a message or provide text.")

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
    if not keys:
        return await message.reply_text("No filters.")
    await message.reply_text("<b>🔥 Filters:</b>\n" + "\n".join(keys))


@Client.on_message(filters.group & ~filters.service, group=5)
async def filter_watcher(client, message):
    if not message.text and not message.caption:
        return
    text = (message.text or message.caption).lower()
    for word in text.split():
        doc = await db.get_filter(message.chat.id, word)
        if not doc:
            continue
        reply = doc.get("reply") or ""
        clean, markup = parse_buttons(reply)
        try:
            if doc["msg_type"] == "text":
                await message.reply_text(clean or "…", reply_markup=markup)
            elif doc["msg_type"] == "photo":
                await message.reply_photo(doc["file_id"], caption=clean or "", reply_markup=markup)
            elif doc["msg_type"] == "video":
                await message.reply_video(doc["file_id"], caption=clean or "", reply_markup=markup)
            elif doc["msg_type"] == "sticker":
                await message.reply_sticker(doc["file_id"])
                if clean:
                    await message.reply_text(clean, reply_markup=markup)
            elif doc["msg_type"] == "document":
                await message.reply_document(doc["file_id"], caption=clean or "", reply_markup=markup)
            elif doc["msg_type"] == "animation":
                await message.reply_animation(doc["file_id"], caption=clean or "", reply_markup=markup)
        except Exception:
            try:
                await message.reply_text(clean or "…", reply_markup=markup)
            except Exception:
                pass
        break
