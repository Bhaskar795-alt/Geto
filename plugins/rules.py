from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database import db
from utils.permissions import is_admin
from utils.formatting import parse_buttons, replace_fillings


# =========================================================
# SET RULES
# =========================================================

@Client.on_message(filters.command("setrules") & filters.group)
async def setrules_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")

    if message.reply_to_message:
        text = message.reply_to_message.text or message.reply_to_message.caption or ""
    elif len(message.command) > 1:
        text = message.text.split(None, 1)[1]
    else:
        return await message.reply_text(
            "📝 Usage:\n"
            "• /setrules <text>\n"
            "• Reply to a message with /setrules"
        )

    await db.set_chat_field(message.chat.id, "rules", text)
    await message.reply_text("✅ Rules saved.")


# =========================================================
# RESET RULES
# =========================================================

@Client.on_message(filters.command("resetrules") & filters.group)
async def resetrules_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    await db.set_chat_field(message.chat.id, "rules", None)
    await message.reply_text("✅ Rules reset.")


# =========================================================
# PRIVATE RULES
# =========================================================

@Client.on_message(filters.command("privaterules") & filters.group)
async def privaterules_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")

    if len(message.command) < 2 or message.command[1].lower() not in (
        "yes", "no", "on", "off"
    ):
        chat = await db.get_chat(message.chat.id)
        state = chat.get("private_rules", False)
        return await message.reply_text(
            f"📋 <b>Private Rules:</b> {'ON' if state else 'OFF'}\n"
            f"Usage: /privaterules yes|no"
        )

    val = message.command[1].lower()
    state = val in ("yes", "on")
    await db.set_chat_field(message.chat.id, "private_rules", state)
    await message.reply_text(f"✅ Private rules: {'ON' if state else 'OFF'}")


# =========================================================
# RULES BUTTON NAME
# =========================================================

@Client.on_message(filters.command("setrulesbutton") & filters.group)
async def setrulesbutton_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")

    if len(message.command) < 2:
        chat = await db.get_chat(message.chat.id)
        current = chat.get("rules_button", "📜 Rules")
        return await message.reply_text(
            f"📋 <b>Rules button:</b> {current}\n"
            f"Usage: /setrulesbutton <text>"
        )

    text = message.text.split(None, 1)[1]
    await db.set_chat_field(message.chat.id, "rules_button", text)
    await message.reply_text(f"✅ Rules button: {text}")


@Client.on_message(filters.command("resetrulesbutton") & filters.group)
async def resetrulesbutton_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    await db.set_chat_field(message.chat.id, "rules_button", None)
    await message.reply_text("✅ Rules button reset.")


# =========================================================
# SHOW RULES
# =========================================================

@Client.on_message(filters.command("rules"))
async def rules_cmd(client, message):
    if message.chat.type == "private":
        return await message.reply_text(
            "❌ This command only works in groups."
        )

    chat = await db.get_chat(message.chat.id)
    rules = chat.get("rules")
    private = chat.get("private_rules", False)
    button_name = chat.get("rules_button") or "📜 Rules"

    # Check noformat flag
    noformat = len(message.command) > 1 and message.command[1].lower() == "noformat"

    if not rules:
        return await message.reply_text("📋 No rules set for this chat.")

    if noformat:
        return await message.reply_text(f"<b>Rules (raw):</b>\n\n<code>{rules}</code>")

    # Private rules
    if private:
        try:
            await client.send_message(
                message.from_user.id,
                f"📜 <b>{message.chat.title} — Rules</b>\n\n"
            )
            # Use helper to send with buttons
            txt = replace_fillings(rules, user=message.from_user, chat=message.chat,
                                   rules=rules)
            clean, markup = parse_buttons(txt)
            await client.send_message(
                message.from_user.id,
                clean or "…",
                reply_markup=markup
            )
            await message.reply_text("📩 Rules sent in PM.")
        except Exception:
            await message.reply_text(
                "❌ Cannot send PM. Please start the bot first: @" + 
                (await client.get_me()).username
            )
        return

    # Public rules
    txt = replace_fillings(rules, user=message.from_user, chat=message.chat,
                           rules=rules)
    clean, markup = parse_buttons(txt)

    # Build rules button row if not present
    if not markup:
        rules_btn = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                button_name,
                url=f"https://t.me/{(await client.get_me()).username}?start=rules_{message.chat.id}"
            )
        ]])
        await message.reply_text(clean or "…", reply_markup=rules_btn)
    else:
        await message.reply_text(clean or "…", reply_markup=markup)


# =========================================================
# RULES BUTTON CALLBACK (from PM link)
# =========================================================

@Client.on_message(filters.command("start") & filters.private & filters.regex(r"^/start rules_"))
async def rules_pm_view(client, message):
    try:
        cid = int(message.text.split("rules_")[1])
    except Exception:
        return
    chat = await db.get_chat(cid)
    rules = chat.get("rules")
    if not rules:
        return await message.reply_text("📋 No rules set.")
    txt = replace_fillings(rules, user=message.from_user, chat=chat, rules=rules)
    clean, markup = parse_buttons(txt)
    await message.reply_text(
        f"📜 <b>{chat.get('title', 'Group')} — Rules</b>\n\n{clean}",
        reply_markup=markup
    )
