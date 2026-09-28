from pyrogram import Client, filters
from database import db
from utils.permissions import is_admin
from utils.formatting import parse_buttons, replace_fillings


@Client.on_message(filters.command("setwelcome") & filters.group)
async def setwelcome_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")

    media_type = None
    file_id = None
    text = ""

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
    elif len(message.command) > 1:
        text = message.text.split(None, 1)[1]
    else:
        return await message.reply_text("❌ Reply or provide text.")

    await db.set_chat_field(message.chat.id, "welcome", text)
    await db.set_chat_field(message.chat.id, "welcome_media_type", media_type)
    await db.set_chat_field(message.chat.id, "welcome_file_id", file_id)
    await message.reply_text(f"✅ Welcome saved{' (' + media_type + ')' if media_type else ''}.")


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
    txt = replace_fillings(tmpl or "", user=message.from_user, chat=message.chat,
                           count=count, rules=rules_text)
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
            if clean or markup:
                await message.reply_text(clean or "📎", reply_markup=markup)
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
        txt = replace_fillings(tmpl, user=user, chat=message.chat,
                               count=count, rules=rules_text)
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
                sent = await message.reply_sticker(file_id)
                if clean or markup:
                    await sent.reply_text(clean or "📎", reply_markup=markup)
            else:
                await message.reply_text(clean or "…", reply_markup=markup)
        except Exception:
            try:
                await message.reply_text(clean or "…", reply_markup=markup)
            except Exception:
                pass
