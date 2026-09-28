import re
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database import db
from utils.permissions import is_admin
from utils.helpers import format_text


def parse_buttons(text):
    """Parse [Label](buttonurl://URL) style buttons."""
    pattern = r"\[([^\]]+)\]\(buttonurl://([^\)]+)\)"
    rows = []
    for line in text.split("\n"):
        row = []
        for m in re.finditer(pattern, line):
            row.append(InlineKeyboardButton(m.group(1), url=m.group(2)))
        if row:
            rows.append(row)
    if not rows:
        return text, None
    clean = re.sub(pattern, "", text)
    clean = "\n".join(line for line in clean.split("\n") if line.strip())
    return clean, InlineKeyboardMarkup(rows)


@Client.on_message(filters.command("setwelcome") & filters.group)
async def setwelcome_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    if message.reply_to_message:
        text = message.reply_to_message.text or message.reply_to_message.caption or ""
    elif len(message.command) > 1:
        text = message.text.split(None, 1)[1]
    else:
        return await message.reply_text("❌ Reply or provide text.")
    await db.set_chat_field(message.chat.id, "welcome", text)
    await message.reply_text("✅ Welcome saved with buttons.")


@Client.on_message(filters.command("resetwelcome") & filters.group)
async def resetwelcome_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    await db.set_chat_field(message.chat.id, "welcome", None)
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
    if not tmpl:
        return await message.reply_text("❌ No welcome message set.")
    count = await client.get_chat_members_count(message.chat.id)
    txt = format_text(tmpl, user=message.from_user, chat=message.chat, count=count)
    clean, markup = parse_buttons(txt)
    await message.reply_text(f"📋 <b>Preview:</b>\n\n{clean}", reply_markup=markup)


@Client.on_message(filters.new_chat_members & filters.group, group=0)
async def on_new_member(client, message):
    chat = await db.get_chat(message.chat.id)
    if not chat.get("welcome_enabled", True): return
    tmpl = chat.get("welcome")
    if not tmpl: return
    count = await client.get_chat_members_count(message.chat.id)
    for user in message.new_chat_members:
        if user.is_bot: continue
        txt = format_text(tmpl, user=user, chat=message.chat, count=count)
        clean, markup = parse_buttons(txt)
        try:
            await message.reply_text(clean, reply_markup=markup)
        except Exception:
            try:
                await message.reply_text(clean)
            except Exception:
                pass
