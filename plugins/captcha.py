import random
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database import db
from utils.permissions import is_admin


@Client.on_message(filters.command("captcha") & filters.group)
async def captcha_toggle(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    chat = await db.get_chat(message.chat.id)
    state = not chat.get("captcha", False)
    await db.set_chat_field(message.chat.id, "captcha", state)
    await message.reply_text(f"✅ Captcha: {'ON' if state else 'OFF'}")


@Client.on_message(filters.command("captchamode") & filters.group)
async def captcha_mode(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    if len(message.command) < 2 or message.command[1] not in ("button", "text", "math"):
        return await message.reply_text("Usage: /captchamode button|text|math")
    await db.set_chat_field(message.chat.id, "captcha_mode", message.command[1])
    await message.reply_text(f"✅ Captcha mode: {message.command[1]}")


@Client.on_message(filters.new_chat_members & filters.group, group=2)
async def send_captcha(client, message):
    chat = await db.get_chat(message.chat.id)
    if not chat.get("captcha", False): return
    mode = chat.get("captcha_mode", "button")
    for user in message.new_chat_members:
        if user.is_bot: continue
        if mode == "button":
            buttons = InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ I'm not a robot",
                    callback_data=f"captcha_verify:{message.chat.id}:{user.id}")
            ]])
            await message.reply_text(
                f"👋 {user.mention}, please verify you're human.",
                reply_markup=buttons)
        elif mode == "math":
            a, b = random.randint(2, 9), random.randint(2, 9)
            await db.save_captcha(message.chat.id, user.id, str(a + b))
            await message.reply_text(f"🧮 {user.mention}, what is <b>{a} + {b}</b>?")


@Client.on_callback_query(filters.regex(r"^captcha_verify:"))
async def captcha_verify_cb(client, cb):
    _, chat_id, user_id = cb.data.split(":")
    chat_id, user_id = int(chat_id), int(user_id)
    if cb.from_user.id != user_id:
        return await cb.answer("❌ Not your captcha.", show_alert=True)
    await cb.message.edit_text(f"✅ {cb.from_user.mention} verified!")
    await cb.answer("Verified!")


@Client.on_message(filters.group & filters.text & ~filters.service, group=20)
async def captcha_text_check(client, message):
    if not message.from_user: return
    doc = await db.get_captcha(message.chat.id, message.from_user.id)
    if not doc: return
    if message.text.strip() == str(doc["answer"]):
        await db.delete_captcha(message.chat.id, message.from_user.id)
        await message.reply_text(f"✅ {message.from_user.mention} verified!")
    else:
        try:
            await message.delete()
        except Exception:
            pass
