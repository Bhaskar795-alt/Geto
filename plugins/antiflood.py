import time
from pyrogram import Client, filters
from pyrogram.types import ChatPermissions
from database import db
from utils.permissions import is_admin
from utils.helpers import resolve_user, parse_duration

MUTE_PERMS = ChatPermissions(can_send_messages=False, can_send_media_messages=False,
    can_send_other_messages=False, can_add_web_page_previews=False, can_send_polls=False)


@Client.on_message(filters.command("flood") & filters.group)
async def flood_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    chat = await db.get_chat(message.chat.id)
    enabled = chat.get("antiflood", False)
    limit = chat.get("flood_limit", 7)
    action = chat.get("flood_action", "mute")
    action_dur = chat.get("flood_action_duration", "")
    timed = chat.get("flood_timed", False)
    time_count = chat.get("flood_time_count", 10)
    time_sec = chat.get("flood_time_sec", 30)
    clear = chat.get("flood_clear", False)

    text = (
        f"🚨 <b>Antiflood Settings</b>\n\n"
        f"<b>Status:</b> {'ON' if enabled else 'OFF'}\n"
        f"<b>Limit:</b> <code>{limit}</code> messages\n"
        f"<b>Action:</b> <code>{action}</code>"
    )
    if action_dur:
        text += f" ({action_dur})"
    text += "\n"
    if timed:
        text += f"<b>Timed:</b> <code>{time_count}</code> msgs in <code>{time_sec}s</code>\n"
    text += f"<b>Delete flood messages:</b> {'ON' if clear else 'OFF'}"
    await message.reply_text(text)


@Client.on_message(filters.command("setflood") & filters.group)
async def setflood_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    if len(message.command) < 2:
        return await message.reply_text("Usage: /setflood <number|off>")
    val = message.command[1].lower()

    if val in ("off", "no", "0"):
        await db.set_chat_field(message.chat.id, "antiflood", False)
        return await message.reply_text("✅ Antiflood <b>disabled</b>.")

    if not val.isdigit():
        return await message.reply_text("❌ Must be a number or 'off'.")

    n = int(val)
    await db.set_chat_field(message.chat.id, "antiflood", True)
    await db.set_chat_field(message.chat.id, "flood_limit", n)
    await message.reply_text(f"✅ Antiflood set to trigger after <code>{n}</code> messages.")


@Client.on_message(filters.command("setfloodtimer") & filters.group)
async def setfloodtimer_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    if len(message.command) < 2:
        return await message.reply_text("Usage: /setfloodtimer <count> <duration> | off")

    val = message.command[1].lower()
    if val in ("off", "no"):
        await db.set_chat_field(message.chat.id, "flood_timed", False)
        return await message.reply_text("✅ Timed antiflood <b>disabled</b>.")

    if len(message.command) < 3:
        return await message.reply_text("Usage: /setfloodtimer <count> <duration>")

    try:
        count = int(message.command[1])
    except ValueError:
        return await message.reply_text("❌ Count must be a number.")

    secs = parse_duration(message.command[2])
    if secs == 0:
        return await message.reply_text("❌ Invalid duration (e.g. 30s, 1m).")

    await db.set_chat_field(message.chat.id, "flood_timed", True)
    await db.set_chat_field(message.chat.id, "flood_time_count", count)
    await db.set_chat_field(message.chat.id, "flood_time_sec", secs)
    await message.reply_text(
        f"✅ Timed antiflood: <code>{count}</code> messages in <code>{secs}s</code>."
    )


@Client.on_message(filters.command("floodmode") & filters.group)
async def floodmode_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    if len(message.command) < 2:
        return await message.reply_text(
            "Usage: /floodmode <ban|mute|kick|tban|tmute> [duration]\n"
            "Example: /floodmode tban 3d"
        )
    action = message.command[1].lower()
    if action not in ("ban", "mute", "kick", "tban", "tmute"):
        return await message.reply_text("❌ Invalid action.")

    duration_str = ""
    if action in ("tban", "tmute"):
        if len(message.command) < 3:
            return await message.reply_text("❌ Need duration (e.g. 3d, 12h).")
        secs = parse_duration(message.command[2])
        if secs == 0:
            return await message.reply_text("❌ Invalid duration.")
        duration_str = message.command[2]

    await db.set_chat_field(message.chat.id, "flood_action", action)
    await db.set_chat_field(message.chat.id, "flood_action_duration", duration_str)
    await message.reply_text(f"✅ Flood action: <code>{action}</code> {duration_str}".strip())


@Client.on_message(filters.command("clearflood") & filters.group)
async def clearflood_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    if len(message.command) < 2 or message.command[1].lower() not in ("yes", "no", "on", "off"):
        chat = await db.get_chat(message.chat.id)
        state = chat.get("flood_clear", False)
        return await message.reply_text(
            f"📋 <b>Delete flood messages:</b> {'ON' if state else 'OFF'}\n"
            f"Usage: /clearflood yes|no"
        )
    val = message.command[1].lower()
    state = val in ("yes", "on")
    await db.set_chat_field(message.chat.id, "flood_clear", state)
    await message.reply_text(f"✅ Delete flood messages: {'ON' if state else 'OFF'}")


# ---------- FLOOD WATCHER ----------

@Client.on_message(filters.group & ~filters.service, group=10)
async def flood_watcher(client, message):
    if not message.from_user:
        return
    chat = await db.get_chat(message.chat.id)
    if not chat.get("antiflood", False):
        return
    if await is_admin(client, message.chat.id, message.from_user.id):
        return

    limit = chat.get("flood_limit", 7)
    action = chat.get("flood_action", "mute")
    action_dur = chat.get("flood_action_duration", "")
    clear = chat.get("flood_clear", False)
    timed = chat.get("flood_timed", False)
    time_count = chat.get("flood_time_count", 10)
    time_sec = chat.get("flood_time_sec", 30)

    uid = message.from_user.id
    now = int(time.time())

    # --- Timed antiflood ---
    if timed:
        key = f"flood_timed_{uid}"
        data = chat.get(key) or {"first": now, "count": 0}
        if now - data["first"] > time_sec:
            # Reset window
            data = {"first": now, "count": 1}
        else:
            data["count"] += 1
        await db.set_chat_field(message.chat.id, key, data)
        if data["count"] >= time_count:
            await _apply_action(client, message, uid, action, action_dur, clear)
            await db.set_chat_field(message.chat.id, key, {"first": now, "count": 0})
            return

    # --- Consecutive messages ---
    count = await db.add_flood(message.chat.id, uid)
    if count >= limit:
        await _apply_action(client, message, uid, action, action_dur, clear)
        await db.reset_flood(message.chat.id, uid)


async def _apply_action(client, message, uid, action, action_dur, clear):
    from datetime import datetime, timedelta
    try:
        if clear:
            try:
                await message.delete()
            except Exception:
                pass

        if action == "mute":
            await client.restrict_chat_member(message.chat.id, uid, MUTE_PERMS)
            await db.mute_user(message.chat.id, uid, 0, "flood")
            await message.reply_text(f"🔇 {message.from_user.mention} muted for flooding.")

        elif action == "ban":
            await client.ban_chat_member(message.chat.id, uid)
            await message.reply_text(f"🔨 {message.from_user.mention} banned for flooding.")

        elif action == "kick":
            await client.ban_chat_member(message.chat.id, uid)
            await client.unban_chat_member(message.chat.id, uid)
            await message.reply_text(f"👢 {message.from_user.mention} kicked for flooding.")

        elif action == "tban":
            secs = parse_duration(action_dur) if action_dur else 3600
            until = datetime.now() + timedelta(seconds=secs)
            await client.ban_chat_member(message.chat.id, uid, until_date=until)
            await message.reply_text(
                f"🔨 {message.from_user.mention} temp-banned for {action_dur} (flood)."
            )

        elif action == "tmute":
            secs = parse_duration(action_dur) if action_dur else 3600
            until = datetime.now() + timedelta(seconds=secs)
            await client.restrict_chat_member(message.chat.id, uid, MUTE_PERMS, until_date=until)
            await db.mute_user(message.chat.id, uid, int(until.timestamp()), action_dur)
            await message.reply_text(
                f"🔇 {message.from_user.mention} temp-muted for {action_dur} (flood)."
            )
    except Exception as e:
        try:
            await message.reply_text(f"❌ Flood action error: {e}")
        except Exception:
            pass
