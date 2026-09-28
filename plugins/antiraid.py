import time
from datetime import datetime, timedelta
from pyrogram import Client, filters
from database import db
from utils.permissions import is_admin
from utils.helpers import parse_duration


@Client.on_message(filters.command("antiraid") & filters.group)
async def antiraid_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")

    # Toggle off
    if len(message.command) > 1:
        val = message.command[1].lower()
        if val in ("off", "no"):
            await db.set_chat_field(message.chat.id, "antiraid", False)
            await db.set_chat_field(message.chat.id, "antiraid_until", 0)
            return await message.reply_text("✅ AntiRaid <b>disabled</b>.")

        # Enable with duration
        secs = parse_duration(val)
        if secs == 0:
            return await message.reply_text("❌ Invalid duration (e.g. 3h, 1d).")
        until = int(time.time()) + secs
        await db.set_chat_field(message.chat.id, "antiraid", True)
        await db.set_chat_field(message.chat.id, "antiraid_until", until)
        return await message.reply_text(f"🚨 AntiRaid enabled for <code>{val}</code>.")

    # Toggle
    chat = await db.get_chat(message.chat.id)
    state = not chat.get("antiraid", False)
    if state:
        # Use default raidtime
        raid_time = chat.get("raid_time", 6 * 3600)
        until = int(time.time()) + raid_time
        await db.set_chat_field(message.chat.id, "antiraid", True)
        await db.set_chat_field(message.chat.id, "antiraid_until", until)
        await message.reply_text(f"🚨 AntiRaid <b>ON</b> for {raid_time // 3600}h.")
    else:
        await db.set_chat_field(message.chat.id, "antiraid", False)
        await db.set_chat_field(message.chat.id, "antiraid_until", 0)
        await message.reply_text("✅ AntiRaid <b>OFF</b>.")


@Client.on_message(filters.command("raidtime") & filters.group)
async def raidtime_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")

    chat = await db.get_chat(message.chat.id)
    if len(message.command) < 2:
        current = chat.get("raid_time", 6 * 3600)
        return await message.reply_text(
            f"⏱️ <b>Raid time:</b> <code>{current // 3600}h</code>\n"
            f"Usage: /raidtime <duration>"
        )

    secs = parse_duration(message.command[1])
    if secs == 0:
        return await message.reply_text("❌ Invalid duration.")
    await db.set_chat_field(message.chat.id, "raid_time", secs)
    await message.reply_text(f"✅ Raid time set to <code>{message.command[1]}</code>.")


@Client.on_message(filters.command("raidactiontime") & filters.group)
async def raidactiontime_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")

    chat = await db.get_chat(message.chat.id)
    if len(message.command) < 2:
        current = chat.get("raid_action_time", 3600)
        return await message.reply_text(
            f"⏱️ <b>Raid action time:</b> <code>{current // 60}m</code>\n"
            f"Usage: /raidactiontime <duration>"
        )

    secs = parse_duration(message.command[1])
    if secs == 0:
        return await message.reply_text("❌ Invalid duration.")
    await db.set_chat_field(message.chat.id, "raid_action_time", secs)
    await message.reply_text(f"✅ Raid action time set to <code>{message.command[1]}</code>.")


@Client.on_message(filters.command("autoantiraid") & filters.group)
async def autoantiraid_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")

    chat = await db.get_chat(message.chat.id)
    if len(message.command) < 2:
        current = chat.get("autoantiraid", 0)
        if current == 0:
            return await message.reply_text("📋 <b>Auto AntiRaid:</b> OFF")
        return await message.reply_text(
            f"📋 <b>Auto AntiRaid:</b> <code>{current}</code> joins/min"
        )

    val = message.command[1].lower()
    if val in ("off", "no", "0"):
        await db.set_chat_field(message.chat.id, "autoantiraid", 0)
        return await message.reply_text("✅ Auto AntiRaid <b>OFF</b>.")

    if not val.isdigit():
        return await message.reply_text("❌ Must be a number or 'off'.")

    n = int(val)
    await db.set_chat_field(message.chat.id, "autoantiraid", n)
    await message.reply_text(f"✅ Auto AntiRaid: <code>{n}</code> joins/min")


# ---------- RAID WATCHER ----------

@Client.on_message(filters.new_chat_members & filters.group, group=1)
async def raid_watcher(client, message):
    chat = await db.get_chat(message.chat.id)
    if not chat.get("antiraid", False):
        return

    raid_time = chat.get("raid_time", 6 * 3600)
    action_time = chat.get("raid_action_time", 3600)
    now = int(time.time())
    until_raid = chat.get("antiraid_until", 0)

    # If antiraid duration expired, disable
    if until_raid and now > until_raid:
        await db.set_chat_field(message.chat.id, "antiraid", False)
        await db.set_chat_field(message.chat.id, "antiraid_until", 0)
        return

    # Temp-ban new joins
    from datetime import datetime, timedelta
    ban_until = datetime.now() + timedelta(seconds=action_time)

    for user in message.new_chat_members:
        if user.is_bot:
            continue
        try:
            await client.ban_chat_member(
                chat_id=message.chat.id,
                user_id=user.id,
                until_date=ban_until
            )
        except Exception:
            pass

    try:
        await message.reply_text(
            f"🚨 <b>Raid detected!</b> New joins are temporarily banned "
            f"for {action_time // 60} minutes."
        )
    except Exception:
        pass


# ---------- AUTO ANTIRAID WATCHER ----------

@Client.on_message(filters.new_chat_members & filters.group, group=2)
async def auto_raid_watcher(client, message):
    chat = await db.get_chat(message.chat.id)
    threshold = chat.get("autoantiraid", 0)
    if threshold == 0:
        return

    # Count joins in last 60 seconds
    now = int(time.time())
    key = "auto_raid_log"
    log = chat.get(key) or []
    log = [t for t in log if now - t < 60]
    log.extend([now] * len(message.new_chat_members))
    await db.set_chat_field(message.chat.id, key, log)

    if len(log) >= threshold:
        raid_time = chat.get("raid_time", 6 * 3600)
        until = now + raid_time
        await db.set_chat_field(message.chat.id, "antiraid", True)
        await db.set_chat_field(message.chat.id, "antiraid_until", until)
        try:
            await message.reply_text(
                f"🚨 <b>Auto AntiRaid triggered!</b>\n"
                f"<code>{len(log)}</code> joins in 60s (threshold: {threshold})\n"
                f"AntiRaid enabled for {raid_time // 3600}h."
            )
        except Exception:
            pass
