import re
import fnmatch
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import ChatPermissions
from database import db
from utils.permissions import is_admin

MUTE_PERMS = ChatPermissions(
    can_send_messages=False,
    can_send_media_messages=False,
    can_send_other_messages=False,
    can_add_web_page_previews=False,
    can_send_polls=False
)


# =========================================================
# PATTERN MATCHING
# =========================================================

def wildcard_match(pattern, text):
    """
    Rose-style wildcards:
      ?  = any single non-whitespace char
      *  = any number of non-whitespace chars
      ** = any number of any chars (including spaces)
    """
    pattern = pattern.lower()
    text = text.lower()

    # Convert to regex-safe
    # Escape regex special chars first
    regex = ""
    i = 0
    while i < len(pattern):
        c = pattern[i]
        if c == "*" and i + 1 < len(pattern) and pattern[i + 1] == "*":
            regex += ".*"
            i += 2
            continue
        if c == "*":
            regex += r"\S*"
        elif c == "?":
            regex += r"\S"
        else:
            regex += re.escape(c)
        i += 1

    try:
        return re.search(regex, text) is not None
    except re.error:
        return False


# =========================================================
# ADD BLOCKLIST
# =========================================================

@Client.on_message(filters.command("addblocklist") & filters.group)
async def add_blocklist_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")

    if len(message.command) < 2:
        return await message.reply_text(
            "📝 <b>Usage:</b>\n"
            "/addblocklist &lt;trigger&gt; [reason]\n\n"
            "Examples:\n"
            "/addblocklist \"bad word\" This is not allowed\n"
            "/addblocklist *.exe Executable files not allowed\n"
            "/addblocklist bad?word"
        )

    # Parse trigger — support quoted
    raw = message.text.split(None, 1)[1]
    trigger_match = re.match(r'("[^"]+"|\S+)', raw)
    if not trigger_match:
        return await message.reply_text("❌ Invalid trigger.")

    raw_trigger = trigger_match.group(1)
    if raw_trigger.startswith('"') and raw_trigger.endswith('"'):
        trigger = raw_trigger[1:-1]
        reason = raw[len(raw_trigger):].strip()
    else:
        trigger = raw_trigger
        reason = raw[len(raw_trigger):].strip()

    # Save
    await db.blocklist.update_one(
        {"chat_id": message.chat.id, "trigger": trigger.lower()},
        {"$set": {
            "chat_id": message.chat.id,
            "trigger": trigger.lower(),
            "reason": reason or "Blocked"
        }},
        upsert=True
    )
    await message.reply_text(
        f"✅ Blocklist added:\n"
        f"🔹 <code>{trigger}</code>\n"
        f"📝 Reason: {reason or 'Blocked'}"
    )


# =========================================================
# REMOVE BLOCKLIST
# =========================================================

@Client.on_message(filters.command("rmblocklist") & filters.group)
async def rm_blocklist_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    if len(message.command) < 2:
        return await message.reply_text("📝 Usage: /rmblocklist <trigger>")

    raw = message.text.split(None, 1)[1]
    if raw.startswith('"') and raw.endswith('"'):
        trigger = raw[1:-1]
    else:
        trigger = raw.split()[0]

    result = await db.blocklist.delete_one({
        "chat_id": message.chat.id,
        "trigger": trigger.lower()
    })
    if result.deleted_count > 0:
        await message.reply_text(f"🗑️ Removed: <code>{trigger}</code>")
    else:
        await message.reply_text(f"❌ Not found: <code>{trigger}</code>")


# =========================================================
# REMOVE ALL BLOCKLIST (owner only)
# =========================================================

@Client.on_message(filters.command("unblocklistall") & filters.group)
async def unblocklistall_cmd(client, message):
    # Chat creator only
    try:
        member = await client.get_chat_member(message.chat.id, message.from_user.id)
        is_creator = str(member.status).lower().endswith("owner")
    except Exception:
        is_creator = False

    if not is_creator:
        return await message.reply_text("❌ Chat owner only.")

    if len(message.command) < 2 or message.command[1].lower() not in ("yes", "confirm"):
        return await message.reply_text(
            "⚠️ <b>Warning:</b> This will remove ALL blocklist triggers.\n"
            "Type <code>/unblocklistall yes</code> to confirm."
        )

    await db.blocklist.delete_many({"chat_id": message.chat.id})
    await message.reply_text("✅ All blocklist triggers removed.")


# =========================================================
# LIST BLOCKLIST
# =========================================================

@Client.on_message(filters.command("blocklist") & filters.group)
async def list_blocklist_cmd(client, message):
    lines = ["<b>🚫 Blocklist:</b>\n"]
    count = 0
    async for d in db.blocklist.find({"chat_id": message.chat.id}):
        count += 1
        trigger = d.get("trigger", "")
        reason = d.get("reason", "")
        lines.append(f"• <code>{trigger}</code> — {reason}")
    if count == 0:
        lines.append("<i>No blocklist triggers.</i>")
    lines.append(f"\n<b>Total:</b> <code>{count}</code>")
    await message.reply_text("\n".join(lines))


# =========================================================
# BLOCKLIST MODE
# =========================================================

@Client.on_message(filters.command("blocklistmode") & filters.group)
async def blocklistmode_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")

    if len(message.command) < 2:
        chat = await db.get_chat(message.chat.id)
        current = chat.get("blocklist_mode", "nothing")
        return await message.reply_text(
            f"📋 <b>Blocklist Mode:</b> <code>{current}</code>\n\n"
            f"Available: nothing / ban / mute / kick / warn / tban / tmute\n"
            f"Usage: /blocklistmode &lt;mode&gt;"
        )

    mode = message.command[1].lower()
    if mode not in ("nothing", "ban", "mute", "kick", "warn", "tban", "tmute"):
        return await message.reply_text("❌ Invalid mode.")

    # If tban/tmute, need duration
    duration = ""
    if mode in ("tban", "tmute"):
        if len(message.command) < 3:
            return await message.reply_text(
                f"📝 For <code>{mode}</code>, provide duration.\n"
                f"Example: /blocklistmode {mode} 2h"
            )
        duration = message.command[2]

    await db.set_chat_field(message.chat.id, "blocklist_mode", mode)
    await db.set_chat_field(message.chat.id, "blocklist_duration", duration)
    await message.reply_text(
        f"✅ Blocklist mode set to <code>{mode}</code>"
        + (f" ({duration})" if duration else "")
    )


# =========================================================
# BLOCKLIST DELETE (on/off)
# =========================================================

@Client.on_message(filters.command("blocklistdelete") & filters.group)
async def blocklistdelete_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")

    if len(message.command) < 2 or message.command[1].lower() not in ("yes", "no", "on", "off"):
        chat = await db.get_chat(message.chat.id)
        state = chat.get("blocklist_delete", True)
        return await message.reply_text(
            f"📋 <b>Delete blocklisted messages:</b> {'ON' if state else 'OFF'}\n"
            f"Usage: /blocklistdelete yes|no"
        )

    val = message.command[1].lower()
    state = val in ("yes", "on")
    await db.set_chat_field(message.chat.id, "blocklist_delete", state)
    await message.reply_text(f"✅ Delete blocklisted messages: {'ON' if state else 'OFF'}")


# =========================================================
# SET DEFAULT REASON
# =========================================================

@Client.on_message(filters.command("setblocklistreason") & filters.group)
async def setblocklistreason_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")

    if len(message.command) < 2:
        return await message.reply_text("📝 Usage: /setblocklistreason <reason>")

    reason = message.text.split(None, 1)[1]
    await db.set_chat_field(message.chat.id, "blocklist_reason", reason)
    await message.reply_text(f"✅ Default reason set:\n📝 {reason}")


@Client.on_message(filters.command("resetblocklistreason") & filters.group)
async def resetblocklistreason_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    await db.set_chat_field(message.chat.id, "blocklist_reason", None)
    await message.reply_text("✅ Blocklist reason reset.")


# =========================================================
# BLOCKLIST WATCHER
# =========================================================

@Client.on_message(filters.group & ~filters.service, group=12)
async def blocklist_watcher(client, message):
    if not message.text and not message.caption:
        return
    chat = await db.get_chat(message.chat.id)

    # Skip admins
    if message.from_user:
        if await is_admin(client, message.chat.id, message.from_user.id):
            return
        # Skip approved users
        if await db.is_approved(message.chat.id, message.from_user.id):
            return

    text = (message.text or message.caption).lower()

    # Check each blocklist trigger
    matched_trigger = None
    async for d in db.blocklist.find({"chat_id": message.chat.id}):
        trigger = d.get("trigger", "")
        if wildcard_match(trigger, text):
            matched_trigger = d
            break

    if not matched_trigger:
        return

    # Delete message if enabled
    delete_flag = chat.get("blocklist_delete", True)
    if delete_flag:
        try:
            await message.delete()
        except Exception:
            pass

    # Get reason
    reason = matched_trigger.get("reason") or chat.get("blocklist_reason") or "Blocked word"
    mode = chat.get("blocklist_mode", "nothing")
    duration = chat.get("blocklist_duration", "")

    if mode == "nothing":
        return

    uid = message.from_user.id if message.from_user else None
    if not uid:
        return

    try:
        if mode == "warn":
            count = await db.add_warn(message.chat.id, uid, f"Blocklist: {reason}")
            await message.reply_text(
                f"⚠️ <b>Warned</b> {message.from_user.mention}\n"
                f"📝 {reason}\n🔢 Total: {count}"
            )

        elif mode == "mute":
            await client.restrict_chat_member(message.chat.id, uid, MUTE_PERMS)
            await db.mute_user(message.chat.id, uid, 0, "blocklist")
            await message.reply_text(
                f"🔇 {message.from_user.mention} muted.\n📝 {reason}"
            )

        elif mode == "ban":
            await client.ban_chat_member(message.chat.id, uid)
            await message.reply_text(
                f"🔨 {message.from_user.mention} banned.\n📝 {reason}"
            )

        elif mode == "kick":
            await client.ban_chat_member(message.chat.id, uid)
            await client.unban_chat_member(message.chat.id, uid)
            await message.reply_text(
                f"👢 {message.from_user.mention} kicked.\n📝 {reason}"
            )

        elif mode == "tban":
            from utils.helpers import parse_duration
            secs = parse_duration(duration) if duration else 3600
            until = datetime.now() + timedelta(seconds=secs)
            await client.ban_chat_member(message.chat.id, uid, until_date=until)
            await message.reply_text(
                f"🔨 {message.from_user.mention} temp-banned for {duration}.\n📝 {reason}"
            )

        elif mode == "tmute":
            from utils.helpers import parse_duration
            secs = parse_duration(duration) if duration else 3600
            until = datetime.now() + timedelta(seconds=secs)
            await client.restrict_chat_member(
                message.chat.id, uid, MUTE_PERMS, until_date=until
            )
            await db.mute_user(message.chat.id, uid, int(until.timestamp()), duration)
            await message.reply_text(
                f"🔇 {message.from_user.mention} temp-muted for {duration}.\n📝 {reason}"
            )

    except Exception as e:
        try:
            await message.reply_text(f"❌ Blocklist action error: {e}")
        except Exception:
            pass
