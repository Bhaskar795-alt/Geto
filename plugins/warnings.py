import time
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import ChatPermissions
from database import db
from utils.helpers import resolve_user, mention_html, parse_duration
from utils.permissions import is_admin

MUTE_PERMS = ChatPermissions(
    can_send_messages=False,
    can_send_media_messages=False,
    can_send_other_messages=False,
    can_add_web_page_previews=False,
    can_send_polls=False
)


# =========================================================
# WARN
# =========================================================

@Client.on_message(filters.command("warn") & filters.group)
async def warn_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")

    uid, name, _ = await resolve_user(client, message)
    if not uid:
        return await message.reply_text("❌ Reply to a user or give a valid user.")

    reason = " ".join(message.command[2:]) or "No reason"
    await process_warn(client, message, uid, name, reason, delete=False, silent=False)


@Client.on_message(filters.command("dwarn") & filters.group)
async def dwarn_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    if not message.reply_to_message:
        return await message.reply_text("❌ Reply to a user's message.")
    target = message.reply_to_message.from_user
    reason = " ".join(message.command[1:]) or "No reason"
    try:
        await message.reply_to_message.delete()
    except Exception:
        pass
    await process_warn(client, message, target.id, target.first_name, reason,
                       delete=False, silent=False)


@Client.on_message(filters.command("swarn") & filters.group)
async def swarn_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")

    uid, name, _ = await resolve_user(client, message)
    if not uid:
        return await message.reply_text("❌ Give a user.")

    reason = " ".join(message.command[2:]) or "No reason"

    try:
        await message.delete()
    except Exception:
        pass

    await process_warn(client, message, uid, name, reason, delete=False, silent=True)


async def process_warn(client, message, uid, name, reason, delete=False, silent=False):
    """Core warn logic — checks expiry, counts, applies action."""
    chat = await db.get_chat(message.chat.id)
    warn_limit = chat.get("warn_limit", 3)
    warn_action = chat.get("warn_action", "mute")
    warn_time = chat.get("warn_time", 0)

    # Expire old warns
    if warn_time > 0:
        await expire_warns(message.chat.id, uid)

    # Add warn
    count = await db.add_warn(message.chat.id, uid, reason)

    # Warn message
    if not silent:
        try:
            await message.reply_text(
                f"⚠️ <b>Warned</b> {mention_html(uid, name)}\n"
                f"📝 {reason}\n"
                f"🔢 <b>{count}/{warn_limit}</b>"
            )
        except Exception:
            pass

    # Trigger action
    if count >= warn_limit:
        try:
            await apply_warn_action(client, message, uid, warn_action, chat)
        except Exception:
            pass


async def apply_warn_action(client, message, uid, action, chat):
    """Apply configured warn action."""
    try:
        if action == "mute":
            await client.restrict_chat_member(message.chat.id, uid, MUTE_PERMS)
            await db.mute_user(message.chat.id, uid, 0, "warn limit")
            await client.send_message(
                message.chat.id,
                f"🔇 Auto-muted (warn limit reached)."
            )

        elif action == "ban":
            await client.ban_chat_member(message.chat.id, uid)
            await client.send_message(
                message.chat.id,
                f"🔨 Auto-banned (warn limit reached)."
            )

        elif action == "kick":
            await client.ban_chat_member(message.chat.id, uid)
            await client.unban_chat_member(message.chat.id, uid)
            await client.send_message(
                message.chat.id,
                f"👢 Auto-kicked (warn limit reached)."
            )

        elif action == "tban":
            duration = chat.get("warn_time_action", "1h")
            secs = parse_duration(duration) if duration else 3600
            until = datetime.now() + timedelta(seconds=secs)
            await client.ban_chat_member(message.chat.id, uid, until_date=until)
            await client.send_message(
                message.chat.id,
                f"🔨 Auto temp-banned for {duration} (warn limit)."
            )

        elif action == "tmute":
            duration = chat.get("warn_time_action", "1h")
            secs = parse_duration(duration) if duration else 3600
            until = datetime.now() + timedelta(seconds=secs)
            await client.restrict_chat_member(
                message.chat.id, uid, MUTE_PERMS, until_date=until
            )
            await db.mute_user(message.chat.id, uid, int(until.timestamp()), duration)
            await client.send_message(
                message.chat.id,
                f"🔇 Auto temp-muted for {duration} (warn limit)."
            )
    except Exception:
        pass


# =========================================================
# EXPIRY HELPER
# =========================================================

async def expire_warns(chat_id, user_id):
    """Remove expired warns."""
    chat = await db.get_chat(chat_id)
    warn_time = chat.get("warn_time", 0)
    if warn_time <= 0:
        return

    doc = await db.warns.find_one({"chat_id": chat_id, "user_id": user_id})
    if not doc:
        return

    last_warn = doc.get("last_warn_time", 0)
    if last_warn == 0:
        # Set timestamp now
        await db.warns.update_one(
            {"chat_id": chat_id, "user_id": user_id},
            {"$set": {"last_warn_time": int(time.time())}}
        )
        return

    if int(time.time()) - last_warn >= warn_time:
        await db.reset_warns(chat_id, user_id)


# =========================================================
# VIEW WARNS
# =========================================================

@Client.on_message(filters.command("warns") & filters.group)
async def warns_cmd(client, message):
    uid, name, _ = await resolve_user(client, message)
    if not uid:
        uid = message.from_user.id
        name = message.from_user.first_name

    await expire_warns(message.chat.id, uid)

    count = await db.get_warns(message.chat.id, uid)
    reasons = await db.get_warn_reasons(message.chat.id, uid)
    chat = await db.get_chat(message.chat.id)
    limit = chat.get("warn_limit", 3)

    text = (
        f"⚠️ <b>Warns for</b> {mention_html(uid, name)}\n"
        f"🔢 <b>{count}/{limit}</b>\n\n"
    )
    for i, r in enumerate(reasons, 1):
        text += f"{i}. {r}\n"
    if not reasons:
        text += "<i>No warns.</i>"

    await message.reply_text(text)


# =========================================================
# REMOVE LATEST WARN
# =========================================================

@Client.on_message(filters.command("rmwarn") & filters.group)
async def rmwarn_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    uid, name, _ = await resolve_user(client, message)
    if not uid:
        return await message.reply_text("❌ Give a user.")

    count = await db.remove_last_warn(message.chat.id, uid)
    await message.reply_text(
        f"✅ Removed latest warn for {mention_html(uid, name)}\n"
        f"🔢 Now: <code>{count}</code>"
    )


# =========================================================
# RESET WARNS (single user)
# =========================================================

@Client.on_message(filters.command("resetwarn") & filters.group)
async def resetwarn_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    uid, name, _ = await resolve_user(client, message)
    if not uid:
        return await message.reply_text("❌ Give a user.")
    await db.reset_warns(message.chat.id, uid)
    await message.reply_text(f"✅ Reset warns for {mention_html(uid, name)}")


# =========================================================
# RESET ALL WARNS
# =========================================================

@Client.on_message(filters.command("resetallwarns") & filters.group)
async def resetallwarns_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    if len(message.command) < 2 or message.command[1].lower() not in ("yes", "confirm"):
        return await message.reply_text(
            "⚠️ This will reset ALL warns in this chat.\n"
            "Type <code>/resetallwarns yes</code> to confirm."
        )
    await db.warns.delete_many({"chat_id": message.chat.id})
    await message.reply_text("✅ All warns reset.")


# =========================================================
# WARNING SETTINGS
# =========================================================

@Client.on_message(filters.command("warnings") & filters.group)
async def warnings_cmd(client, message):
    chat = await db.get_chat(message.chat.id)
    limit = chat.get("warn_limit", 3)
    action = chat.get("warn_action", "mute")
    wtime = chat.get("warn_time", 0)

    wtime_str = "Never" if wtime == 0 else f"{wtime}s"

    await message.reply_text(
        f"⚠️ <b>Warning Settings</b>\n\n"
        f"🔢 <b>Limit:</b> {limit}\n"
        f"⚡ <b>Action:</b> {action}\n"
        f"⏱️ <b>Warn expiry:</b> {wtime_str}"
    )


# =========================================================
# WARN MODE
# =========================================================

@Client.on_message(filters.command("warnmode") & filters.group)
async def warnmode_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")

    if len(message.command) < 2:
        chat = await db.get_chat(message.chat.id)
        current = chat.get("warn_action", "mute")
        return await message.reply_text(
            f"📋 <b>Warn Mode:</b> <code>{current}</code>\n"
            f"Available: ban / mute / kick / tban / tmute\n"
            f"Usage: /warnmode &lt;mode&gt;"
        )

    mode = message.command[1].lower()
    if mode not in ("ban", "mute", "kick", "tban", "tmute"):
        return await message.reply_text("❌ Invalid mode.")

    await db.set_chat_field(message.chat.id, "warn_action", mode)

    if mode in ("tban", "tmute"):
        if len(message.command) > 2:
            duration = message.command[2]
            await db.set_chat_field(message.chat.id, "warn_time_action", duration)
            return await message.reply_text(
                f"✅ Warn mode: <code>{mode}</code> ({duration})"
            )
        return await message.reply_text(
            f"✅ Warn mode: <code>{mode}</code>\n"
            f"ℹ️ Tip: Add duration like <code>/warnmode {mode} 2h</code>"
        )

    await message.reply_text(f"✅ Warn mode: <code>{mode}</code>")


# =========================================================
# WARN LIMIT
# =========================================================

@Client.on_message(filters.command("warnlimit") & filters.group)
async def warnlimit_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")

    if len(message.command) < 2:
        chat = await db.get_chat(message.chat.id)
        limit = chat.get("warn_limit", 3)
        return await message.reply_text(
            f"🔢 <b>Warn limit:</b> <code>{limit}</code>\n"
            f"Usage: /warnlimit &lt;number&gt;"
        )

    try:
        n = int(message.command[1])
    except ValueError:
        return await message.reply_text("❌ Must be a number.")

    await db.set_chat_field(message.chat.id, "warn_limit", n)
    await message.reply_text(f"✅ Warn limit set to <code>{n}</code>")


# =========================================================
# WARN TIME (expiry)
# =========================================================

@Client.on_message(filters.command("warntime") & filters.group)
async def warntime_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")

    if len(message.command) < 2:
        chat = await db.get_chat(message.chat.id)
        wtime = chat.get("warn_time", 0)
        wtime_str = "Never" if wtime == 0 else f"{wtime}s"
        return await message.reply_text(
            f"⏱️ <b>Warn expiry:</b> {wtime_str}\n"
            f"Usage: /warntime &lt;duration|off&gt;\n"
            f"Example: /warntime 4w"
        )

    val = message.command[1].lower()
    if val in ("off", "no", "0"):
        await db.set_chat_field(message.chat.id, "warn_time", 0)
        return await message.reply_text("✅ Warn expiry: OFF (never expire)")

    secs = parse_duration(val)
    if secs == 0:
        return await message.reply_text("❌ Invalid duration (e.g. 4w, 1d).")

    await db.set_chat_field(message.chat.id, "warn_time", secs)
    await message.reply_text(f"✅ Warn expiry: <code>{val}</code>")
