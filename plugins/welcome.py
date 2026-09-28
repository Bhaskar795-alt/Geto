import re
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database import db
from utils.permissions import is_admin
from utils.helpers import format_text


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


@Client.on_message(filters.command("setwelcome") & filters.group)
async def setwelcome_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")

    media_type = None
    file_id = None
    text = ""

    # Case 1: Reply to a media/text message
    if message.reply_to_message:
        r = message.reply_to_message
        if r.photo:
            media_type, file_id = "photo", r.photo.file_id
        elif r.video:
            media_type, file_id = "video", r.video.file_id
        elif r.animation:
            media_type, file_id = "animation", r.animation.file_id
        elif r.document:
            media_type, file_id = "document", r.document.file_id
        elif r.sticker:
            media_type, file_id = "sticker", r.sticker.file_id
        text = r.caption or r.text or ""
        if len(message.command) > 1:
            extra = message.text.split(None, 1)[1]
            if extra:
                text = extra

    # Case 2: Direct text command
    elif len(message.command) > 1:
        text = message.text.split(None, 1)[1]

    # Case 3: Nothing
    else:
        return await message.reply_text(
            "❌ <b>Usage:</b>\n"
            "1. Reply to a photo/video/text with /setwelcome\n"
            "2. Or /setwelcome <text>\n"
            "3. Buttons: [Label](buttonurl://URL)"
        )

    await db.set_chat_field(message.chat.id, "welcome", text)
    await db.set_chat_field(message.chat.id, "welcome_media_type", media_type)
    await db.set_chat_field(message.chat.id, "welcome_file_id", file_id)

    if media_type:
        await message.reply_text(f"✅ Welcome saved ({media_type} + text + buttons).")
    else:
        await message.reply_text("✅ Welcome saved (text + buttons).")


@Client.on_message(filters.command("resetwelcome") & filters.group)
async def resetwelcome_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    await db.set_chat_field(message.chat.id, "welcome", None)
    await db.set_chat_field(message.chat.id, "welcome_media_type", None)
    await db.set_chat_field(message.chat.id, "welcome_file_id", None)
    await message.reply_text("✅ Welcome reset.")


@Client.on_message(filters.command("welcome") & filters.group)
async def welcome_toggle(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    chat = await db.get_chat(message.chat.id)
    state = not chat.get("welcome_enabled", True)
    await db.set_chat_field(message.chat.id, "welcome_enabled", state)
    await message.reply_text(f"✅ Welcome: {'ON' if state else 'OFF'}")


@Client.on_message(filters.command("welcomepreview") & filters.group)
async def welcome_preview(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    chat = await db.get_chat(message.chat.id)
    tmpl = chat.get("welcome")
    media_type = chat.get("welcome_media_type")
    file_id = chat.get("welcome_file_id")

    if not tmpl and not file_id:
        return await message.reply_text("❌ No welcome message set.")

    count = await client.get_chat_members_count(message.chat.id)
    rules_text = chat.get("rules") or "No rules set."
    txt = format_text(tmpl or "", user=message.from_user, chat=message.chat,
                      count=count, extra={"rules": rules_text})
    clean, markup = parse_buttons(txt)

    try:
        if media_type == "photo":
            await message.reply_photo(file_id, caption=clean, reply_markup=markup)
        elif media_type == "video":
            await message.reply_video(file_id, caption=clean, reply_markup=markup)
        elif media_type == "animation":
            await message.reply_animation(file_id, caption=clean, reply_markup=markup)
        elif media_type == "document":
            await message.reply_document(file_id, caption=clean, reply_markup=markup)
        elif media_type == "sticker":
            await message.reply_sticker(file_id)
        else:
            await message.reply_text(clean or "…", reply_markup=markup)
    except Exception as e:
        await message.reply_text(f"❌ Preview error: {e}")


@Client.on_message(filters.new_chat_members & filters.group, group=0)
async def on_new_member(client, message):
    chat = await db.get_chat(message.chat.id)
    if not chat.get("welcome_enabled", True):
        return

    tmpl = chat.get("welcome") or ""
    media_type = chat.get("welcome_media_type")
    file_id = chat.get("welcome_file_id")

    if not tmpl and not file_id:
        return

    count = await client.get_chat_members_count(message.chat.id)
    rules_text = chat.get("rules") or "No rules set."

    for user in message.new_chat_members:
        if user.is_bot:
            continue
        txt = format_text(tmpl, user=user, chat=message.chat, count=count,
                          extra={"rules": rules_text})
        clean, markup = parse_buttons(txt)

        try:
            if media_type == "photo":
                await message.reply_photo(file_id, caption=clean, reply_markup=markup)
            elif media_type == "video":
                await message.reply_video(file_id, caption=clean, reply_markup=markup)
            elif media_type == "animation":
                await message.reply_animation(file_id, caption=clean, reply_markup=markup)
            elif media_type == "document":
                await message.reply_document(file_id, caption=clean, reply_markup=markup)
            elif media_type == "sticker":
                await message.reply_sticker(file_id)
                if clean:
                    await message.reply_text(clean, reply_markup=markup)
            else:
                await message.reply_text(clean or "…", reply_markup=markup)
        except Exception:
            try:
                await message.reply_text(clean or "…", reply_markup=markup)
            except Exception:
                pass
