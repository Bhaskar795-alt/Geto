import random
import time
from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
)
from database import db
from utils.permissions import is_admin
from utils.helpers import parse_duration

MUTE_PERMS = ChatPermissions(
    can_send_messages=False,
    can_send_media_messages=False,
    can_send_other_messages=False,
    can_add_web_page_previews=False,
    can_send_polls=False
)

UNMUTE_PERMS = ChatPermissions(
    can_send_messages=True,
    can_send_media_messages=True,
    can_send_other_messages=True,
    can_add_web_page_previews=True,
    can_send_polls=True
)


# =========================================================
# TOGGLE CAPTCHA
# =========================================================

@Client.on_message(filters.command("captcha") & filters.group)
async def captcha_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")

    chat = await db.get_chat(message.chat.id)

    # Check welcome is enabled
    if not chat.get("welcome_enabled", True):
        return await message.reply_text(
            "⚠️ <b>Welcome messages are OFF.</b>\n"
            "Enable welcome first: /welcome on"
        )

    if len(message.command) < 2 or message.command[1].lower() not in (
        "yes", "no", "on", "off"
    ):
        state = chat.get("captcha", False)
        return await message.reply_text(
            f"📋 <b>CAPTCHA:</b> {'ON' if state else 'OFF'}\n"
            f"Usage: /captcha yes|no"
        )

    val = message.command[1].lower()
    state = val in ("yes", "on")
    await db.set_chat_field(message.chat.id, "captcha", state)
    await message.reply_text(f"✅ CAPTCHA: {'ON' if state else 'OFF'}")


# =========================================================
# CAPTCHA MODE
# =========================================================

@Client.on_message(filters.command("captchamode") & filters.group)
async def captchamode_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")

    if len(message.command) < 2:
        chat = await db.get_chat(message.chat.id)
        mode = chat.get("captcha_mode", "button")
        return await message.reply_text(
            f"📋 <b>CAPTCHA Mode:</b> <code>{mode}</code>\n"
            f"Available: button / math / text / text2\n"
            f"Usage: /captchamode &lt;mode&gt;"
        )

    mode = message.command[1].lower()
    if mode not in ("button", "math", "text", "text2"):
        return await message.reply_text("❌ Invalid mode.")

    await db.set_chat_field(message.chat.id, "captcha_mode", mode)
    await message.reply_text(f"✅ CAPTCHA mode: <code>{mode}</code>")


# =========================================================
# CAPTCHA RULES
# =========================================================

@Client.on_message(filters.command("captcharules") & filters.group)
async def captcharules_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")

    if len(message.command) < 2 or message.command[1].lower() not in (
        "yes", "no", "on", "off"
    ):
        chat = await db.get_chat(message.chat.id)
        state = chat.get("captcha_rules", False)
        return await message.reply_text(
            f"📋 <b>CAPTCHA Rules:</b> {'ON' if state else 'OFF'}\n"
            f"Usage: /captcharules yes|no"
        )

    val = message.command[1].lower()
    state = val in ("yes", "on")
    await db.set_chat_field(message.chat.id, "captcha_rules", state)
    await message.reply_text(f"✅ CAPTCHA rules: {'ON' if state else 'OFF'}")


# =========================================================
# CAPTCHA MUTE TIME
# =========================================================

@Client.on_message(filters.command("captchamutetime") & filters.group)
async def captchamutetime_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")

    if len(message.command) < 2:
        chat = await db.get_chat(message.chat.id)
        secs = chat.get("captcha_mute_time", 0)
        return await message.reply_text(
            f"⏱️ <b>CAPTCHA mute time:</b> <code>{secs}s</code>\n"
            f"Usage: /captchamutetime &lt;duration|off&gt;\n"
            f"Example: /captchamutetime 5m"
        )

    val = message.command[1].lower()
    if val in ("off", "no", "0"):
        await db.set_chat_field(message.chat.id, "captcha_mute_time", 0)
        return await message.reply_text("✅ CAPTCHA mute time: OFF (muted until solved)")

    secs = parse_duration(val)
    if secs == 0:
        return await message.reply_text("❌ Invalid duration (e.g. 5m, 1h).")

    await db.set_chat_field(message.chat.id, "captcha_mute_time", secs)
    await message.reply_text(f"✅ CAPTCHA mute time: <code>{val}</code>")


# =========================================================
# CAPTCHA KICK
# =========================================================

@Client.on_message(filters.command("captchakick") & filters.group)
async def captchakick_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")

    if len(message.command) < 2 or message.command[1].lower() not in (
        "yes", "no", "on", "off"
    ):
        chat = await db.get_chat(message.chat.id)
        state = chat.get("captcha_kick", False)
        return await message.reply_text(
            f"📋 <b>CAPTCHA Kick:</b> {'ON' if state else 'OFF'}\n"
            f"Usage: /captchakick yes|no"
        )

    val = message.command[1].lower()
    state = val in ("yes", "on")
    await db.set_chat_field(message.chat.id, "captcha_kick", state)
    await message.reply_text(f"✅ CAPTCHA kick: {'ON' if state else 'OFF'}")


# =========================================================
# CAPTCHA KICK TIME
# =========================================================

@Client.on_message(filters.command("captchakicktime") & filters.group)
async def captchakicktime_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")

    if len(message.command) < 2:
        chat = await db.get_chat(message.chat.id)
        secs = chat.get("captcha_kick_time", 300)
        return await message.reply_text(
            f"⏱️ <b>CAPTCHA kick time:</b> <code>{secs}s</code>\n"
            f"Usage: /captchakicktime &lt;duration&gt;\n"
            f"Example: /captchakicktime 5m"
        )

    secs = parse_duration(message.command[1])
    if secs == 0:
        return await message.reply_text("❌ Invalid duration.")
    await db.set_chat_field(message.chat.id, "captcha_kick_time", secs)
    await message.reply_text(f"✅ CAPTCHA kick time: <code>{message.command[1]}</code>")


# =========================================================
# SET CAPTCHA TEXT
# =========================================================

@Client.on_message(filters.command("setcaptchatext") & filters.group)
async def setcaptchatext_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")

    if len(message.command) < 2:
        return await message.reply_text(
            "📝 Usage: /setcaptchatext <button text>\n"
            "Example: /setcaptchatext Click to verify ✅"
        )

    text = message.text.split(None, 1)[1]
    await db.set_chat_field(message.chat.id, "captcha_text", text)
    await message.reply_text(f"✅ CAPTCHA button text: {text}")


@Client.on_message(filters.command("resetcaptchatext") & filters.group)
async def resetcaptchatext_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    await db.set_chat_field(message.chat.id, "captcha_text", None)
    await message.reply_text("✅ CAPTCHA button text reset.")


# =========================================================
# NEW MEMBER — SEND CAPTCHA
# =========================================================

@Client.on_message(filters.new_chat_members & filters.group, group=3)
async def send_captcha(client, message):
    chat = await db.get_chat(message.chat.id)
    if not chat.get("captcha", False):
        return
    if not chat.get("welcome_enabled", True):
        return

    mode = chat.get("captcha_mode", "button")
    rules_required = chat.get("captcha_rules", False)
    mute_time = chat.get("captcha_mute_time", 0)
    kick_enabled = chat.get("captcha_kick", False)
    kick_time = chat.get("captcha_kick_time", 300)
    button_text = chat.get("captcha_text") or "✅ Click to verify"

    for user in message.new_chat_members:
        if user.is_bot:
            continue

        # Mute new user
        try:
            await client.restrict_chat_member(message.chat.id, user.id, MUTE_PERMS)
        except Exception:
            pass

        # Send captcha
        if mode == "button":
            buttons = InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    button_text,
                    callback_data=f"captcha_verify:{message.chat.id}:{user.id}"
                )
            ]])
            try:
                await message.reply_text(
                    f"👋 Welcome {user.mention}!\n"
                    f"Please verify you're human to chat.",
                    reply_markup=buttons
                )
            except Exception:
                pass

        elif mode == "math":
            a, b = random.randint(2, 9), random.randint(2, 9)
            answer = str(a + b)
            await db.save_captcha(message.chat.id, user.id, answer)
            try:
                await message.reply_text(
                    f"🧮 {user.mention}, please solve:\n"
                    f"<b>{a} + {b} = ?</b>\n"
                    f"Reply with your answer."
                )
            except Exception:
                pass

        elif mode in ("text", "text2"):
            words = ["rose", "geto", "telegram", "hello", "world", "chat", "admin"]
            answer = random.choice(words)
            await db.save_captcha(message.chat.id, user.id, answer)
            try:
                await message.reply_text(
                    f"📝 {user.mention}, please type:\n"
                    f"<code>{answer}</code>"
                )
            except Exception:
                pass

        # Schedule auto-unmute / kick
        # Store timestamp for background task
        await db.set_chat_field(
            message.chat.id,
            f"captcha_pending_{user.id}",
            {
                "start": int(time.time()),
                "mute_time": mute_time,
                "kick": kick_enabled,
                "kick_time": kick_time,
                "rules_required": rules_required,
            }
        )


# =========================================================
# CAPTCHA VERIFY (BUTTON)
# =========================================================

@Client.on_callback_query(filters.regex(r"^captcha_verify:"))
async def captcha_verify_cb(client, cb):
    try:
        _, chat_id, user_id = cb.data.split(":")
        chat_id, user_id = int(chat_id), int(user_id)
    except Exception:
        return await cb.answer("Invalid captcha data.", show_alert=True)

    if cb.from_user.id != user_id:
        return await cb.answer("❌ This is not your captcha.", show_alert=True)

    # Unmute
    try:
        await client.restrict_chat_member(chat_id, user_id, UNMUTE_PERMS)
    except Exception as e:
        return await cb.answer(f"❌ {e}", show_alert=True)

    # Clear pending
    await db.delete_captcha(chat_id, user_id)

    await cb.message.edit_text(
        f"✅ {cb.from_user.mention} verified successfully!"
    )
    await cb.answer("Verified ✅")


# =========================================================
# CAPTCHA VERIFY (TEXT / MATH)
# =========================================================

@Client.on_message(filters.group & filters.text & ~filters.service, group=20)
async def captcha_text_check(client, message):
    if not message.from_user:
        return
    chat = await db.get_chat(message.chat.id)
    if not chat.get("captcha", False):
        return

    doc = await db.get_captcha(message.chat.id, message.from_user.id)
    if not doc:
        return

    answer = str(doc.get("answer", "")).lower().strip()
    given = message.text.strip().lower()

    # Delete user's message
    try:
        await message.delete()
    except Exception:
        pass

    if given == answer:
        try:
            await client.restrict_chat_member(
                message.chat.id, message.from_user.id, UNMUTE_PERMS
            )
        except Exception:
            pass
        await db.delete_captcha(message.chat.id, message.from_user.id)
        await client.send_message(
            message.chat.id,
            f"✅ {message.from_user.mention} verified successfully!"
        )
    else:
        await client.send_message(
            message.chat.id,
            f"❌ Wrong! Try again."
        )
