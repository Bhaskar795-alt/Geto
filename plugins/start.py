import time
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import Config
from database import db


HELP_TEXT = """🌹 <b>GETO BOT — ULTIMATE MASTER</b>

👑 <b>Owner:</b> <a href="tg://user?id={owner}">Click Here</a>
🤖 <b>Bot:</b> @{bot}

<b>📌 Main Commands</b>
/start — Start
/help — Help menu
/ping — Latency
/id — Get IDs
/info — User info
/stats — Bot stats
"""


@Client.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    await db.add_user(message.from_user.id, message.from_user.first_name)
    btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Me To Group",
            url=f"https://t.me/{Config.BOT_USERNAME}?startgroup=true")],
        [InlineKeyboardButton("📜 Help", callback_data="help_home"),
         InlineKeyboardButton("👑 Owner", url=f"tg://user?id={Config.OWNER_ID}")]
    ])
    await message.reply_text(
        HELP_TEXT.format(owner=Config.OWNER_ID, bot=Config.BOT_USERNAME),
        reply_markup=btn, disable_web_page_preview=True)


@Client.on_message(filters.command("help"))
async def help_cmd(client, message):
    await message.reply_text(
        HELP_TEXT.format(owner=Config.OWNER_ID, bot=Config.BOT_USERNAME),
        disable_web_page_preview=True)


@Client.on_message(filters.command("ping"))
async def ping_cmd(client, message):
    t = time.time()
    m = await message.reply_text("🏓 Pinging...")
    ms = round((time.time() - t) * 1000, 2)
    await m.edit_text(f"🏓 <b>Pong!</b>\n⚡ <code>{ms} ms</code>")


@Client.on_message(filters.command("id"))
async def id_cmd(client, message):
    txt = f"👤 <b>Your ID:</b> <code>{message.from_user.id}</code>\n"
    if message.chat.type != "private":
        txt += f"💬 <b>Chat ID:</b> <code>{message.chat.id}</code>\n"
    if message.reply_to_message and message.reply_to_message.from_user:
        txt += f"↩️ <b>Replied ID:</b> <code>{message.reply_to_message.from_user.id}</code>"
    await message.reply_text(txt)


@Client.on_message(filters.command("stats"))
async def stats_cmd(client, message):
    u = await db.count_users()
    c = await db.count_chats()
    await message.reply_text(
        f"📊 <b>GETO BOT STATS</b>\n\n"
        f"👥 Users: <code>{u}</code>\n💬 Chats: <code>{c}</code>")


@Client.on_message(filters.command("info"))
async def info_cmd(client, message):
    u = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    await message.reply_text(
        f"👤 <b>User Info</b>\n\n"
        f"🆔 <code>{u.id}</code>\n📛 {u.first_name or ''}\n"
        f"🔗 @{u.username or 'None'}")


@Client.on_message(filters.command("about"))
async def about_cmd(client, message):
    await message.reply_text(f"🌹 <b>{Config.BOT_NAME}</b>\n🤖 @{Config.BOT_USERNAME}")


@Client.on_message(filters.command("botinfo"))
async def botinfo_cmd(client, message):
    me = await client.get_me()
    await message.reply_text(
        f"🤖 <b>Bot Info</b>\n\nName: {me.first_name}\n"
        f"Username: @{me.username}\nID: <code>{me.id}</code>")


@Client.on_callback_query(filters.regex("^help_home$"))
async def help_cb(client, cb):
    await cb.message.edit_text(
        HELP_TEXT.format(owner=Config.OWNER_ID, bot=Config.BOT_USERNAME),
        disable_web_page_preview=True)
    await cb.answer()
