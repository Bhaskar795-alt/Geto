from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import ChatPermissions, ChatPrivileges
from database import db
from utils.helpers import resolve_user, parse_duration, mention_html
from utils.permissions import is_admin

MUTE_PERMS = ChatPermissions(can_send_messages=False, can_send_media_messages=False,
    can_send_other_messages=False, can_add_web_page_previews=False, can_send_polls=False)
UNMUTE_PERMS = ChatPermissions(can_send_messages=True, can_send_media_messages=True,
    can_send_other_messages=True, can_add_web_page_previews=True, can_send_polls=True)


# ---------- BAN ----------

@Client.on_message(filters.command("ban") & filters.group)
async def ban_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    uid, name, _ = await resolve_user(client, message)
    if not uid:
        return await message.reply_text("❌ Reply or give a user.")
    reason = " ".join(message.command[2:]) or "No reason"
    try:
        await client.ban_chat_member(message.chat.id, uid)
        await message.reply_text(f"🔨 <b>Banned</b> {mention_html(uid, name)}\n📝 {reason}")
    except Exception as e:
        await message.reply_text(f"❌ {e}")


@Client.on_message(filters.command("tban") & filters.group)
async def tban_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    if len(message.command) < 3:
        return await message.reply_text("Usage: /tban <user> <duration>")
    uid, name, _ = await resolve_user(client, message)
    if not uid:
        return await message.reply_text("❌ Give a user.")
    secs = parse_duration(message.command[2])
    if secs == 0:
        return await message.reply_text("❌ Invalid duration (e.g. 1h).")
    until = datetime.now() + timedelta(seconds=secs)
    try:
        await client.ban_chat_member(message.chat.id, uid, until_date=until)
        await message.reply_text(f"🔨 Temp-Ban {mention_html(uid, name)} for {message.command[2]}")
    except Exception as e:
        await message.reply_text(f"❌ {e}")


@Client.on_message(filters.command("unban") & filters.group)
async def unban_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    uid, name, _ = await resolve_user(client, message)
    if not uid:
        return await message.reply_text("❌ Give a user.")
    try:
        await client.unban_chat_member(message.chat.id, uid)
        await message.reply_text(f"✅ Unbanned {mention_html(uid, name)}")
    except Exception as e:
        await message.reply_text(f"❌ {e}")


@Client.on_message(filters.command("kick") & filters.group)
async def kick_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    uid, name, _ = await resolve_user(client, message)
    if not uid:
        return await message.reply_text("❌ Give a user.")
    try:
        await client.ban_chat_member(message.chat.id, uid)
        await client.unban_chat_member(message.chat.id, uid)
        await message.reply_text(f"👢 Kicked {mention_html(uid, name)}")
    except Exception as e:
        await message.reply_text(f"❌ {e}")


# ---------- MUTE ----------

@Client.on_message(filters.command("mute") & filters.group)
async def mute_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    uid, name, _ = await resolve_user(client, message)
    if not uid:
        return await message.reply_text("❌ Give a user.")
    try:
        await client.restrict_chat_member(message.chat.id, uid, MUTE_PERMS)
        await db.mute_user(message.chat.id, uid, 0, "permanent")
        await message.reply_text(f"🔇 Muted {mention_html(uid, name)}")
    except Exception as e:
        await message.reply_text(f"❌ {e}")


@Client.on_message(filters.command("tmute") & filters.group)
async def tmute_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    if len(message.command) < 3:
        return await message.reply_text("Usage: /tmute <user> <duration>")
    uid, name, _ = await resolve_user(client, message)
    if not uid:
        return await message.reply_text("❌ Give a user.")
    secs = parse_duration(message.command[2])
    if secs == 0:
        return await message.reply_text("❌ Invalid duration.")
    until = datetime.now() + timedelta(seconds=secs)
    try:
        await client.restrict_chat_member(message.chat.id, uid, MUTE_PERMS, until_date=until)
        await db.mute_user(message.chat.id, uid, int(until.timestamp()), message.command[2])
        await message.reply_text(f"🔇 Temp-Mute {mention_html(uid, name)} for {message.command[2]}")
    except Exception as e:
        await message.reply_text(f"❌ {e}")


@Client.on_message(filters.command("unmute") & filters.group)
async def unmute_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    uid, name, _ = await resolve_user(client, message)
    if not uid:
        return await message.reply_text("❌ Give a user.")
    try:
        await client.restrict_chat_member(message.chat.id, uid, UNMUTE_PERMS)
        await db.unmute_user(message.chat.id, uid)
        await message.reply_text(f"🔊 Unmuted {mention_html(uid, name)}")
    except Exception as e:
        await message.reply_text(f"❌ {e}")


@Client.on_message(filters.command("mutelist") & filters.group)
async def mutelist_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    import time
    lines = ["<b>🔇 Active Mutes:</b>\n"]
    async for d in db.get_mutelist(message.chat.id):
        until = d.get("until", 0)
        if until:
            rem = max(0, until - int(time.time()))
            lines.append(f"• <code>{d['user_id']}</code> — {rem}s left")
        else:
            lines.append(f"• <code>{d['user_id']}</code> — permanent")
    if len(lines) == 1:
        lines.append("<i>No active mutes.</i>")
    await message.reply_text("\n".join(lines))


# ---------- PROMOTE / DEMOTE ----------

@Client.on_message(filters.command("promote") & filters.group)
async def promote_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    uid, name, _ = await resolve_user(client, message)
    if not uid:
        return await message.reply_text("❌ Give a user.")
    try:
        await client.promote_chat_member(
            chat_id=message.chat.id,
            user_id=uid,
            privileges=ChatPrivileges(
                can_delete_messages=True,
                can_restrict_members=True,
                can_pin_messages=True,
                can_invite_users=True,
                can_manage_video_chats=True,
                can_change_info=True,
                can_manage_chat=True,
                can_promote_members=False,
            )
        )
        await message.reply_text(f"⬆️ Promoted {mention_html(uid, name)}")
    except Exception as e:
        await message.reply_text(f"❌ {e}")


@Client.on_message(filters.command("demote") & filters.group)
async def demote_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    uid, name, _ = await resolve_user(client, message)
    if not uid:
        return await message.reply_text("❌ Give a user.")
    try:
        await client.promote_chat_member(
            chat_id=message.chat.id,
            user_id=uid,
            privileges=ChatPrivileges(
                can_delete_messages=False,
                can_restrict_members=False,
                can_pin_messages=False,
                can_invite_users=False,
                can_manage_video_chats=False,
                can_change_info=False,
                can_manage_chat=False,
                can_promote_members=False,
            )
        )
        await message.reply_text(f"⬇️ Demoted {mention_html(uid, name)}")
    except Exception as e:
        await message.reply_text(f"❌ {e}")


# ---------- ADMIN LIST (FIXED) ----------

@Client.on_message(filters.command("admins") & filters.group)
async def admins_cmd(client, message):
    lines = ["<b>👮 Admins:</b>\n"]
    try:
        async for m in client.get_chat_members(message.chat.id, filter="administrators"):
            status = str(m.status).replace("ChatMemberStatus.", "")
            role = "👑 Owner" if "OWNER" in status else "🛡️ Admin"
            lines.append(f"{role} — {m.user.mention} (<code>{m.user.id}</code>)")
    except Exception as e:
        return await message.reply_text(f"❌ {e}")
    await message.reply_text("\n".join(lines))


@Client.on_message(filters.command("adminlist") & filters.group)
async def adminlist_cmd(client, message):
    lines = ["<b>👮 Admin List:</b>\n"]
    try:
        async for m in client.get_chat_members(message.chat.id, filter="administrators"):
            status = str(m.status).replace("ChatMemberStatus.", "")
            role = "👑" if "OWNER" in status else "🛡️"
            lines.append(f"{role} {m.user.mention} — <code>{m.user.id}</code>")
    except Exception as e:
        return await message.reply_text(f"❌ {e}")
    await message.reply_text("\n".join(lines))


@Client.on_message(filters.command("admincache") & filters.group)
async def admincache_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    try:
        import time
        admins = []
        async for m in client.get_chat_members(message.chat.id, filter="administrators"):
            admins.append({
                "user_id": m.user.id,
                "name": m.user.first_name or "",
                "username": m.user.username or "",
                "status": str(m.status).replace("ChatMemberStatus.", ""),
            })
        await db.set_chat_field(message.chat.id, "admins_cache", admins)
        await db.set_chat_field(message.chat.id, "admin_cache_time", int(time.time()))
        await message.reply_text(
            f"✅ <b>Admin cache updated.</b>\n"
            f"👥 Total admins: <code>{len(admins)}</code>"
        )
    except Exception as e:
        await message.reply_text(f"❌ {e}")


@Client.on_message(filters.command("anonadmin") & filters.group)
async def anonadmin_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    if len(message.command) < 2:
        chat = await db.get_chat(message.chat.id)
        state = chat.get("anonadmin", False)
        return await message.reply_text(
            f"📋 <b>Anonymous Admin:</b> {'ON' if state else 'OFF'}\n"
            f"Usage: /anonadmin yes|no"
        )
    val = message.command[1].lower()
    if val in ("yes", "on", "true", "1"):
        await db.set_chat_field(message.chat.id, "anonadmin", True)
        await message.reply_text("✅ Anonymous admin: ON")
    elif val in ("no", "off", "false", "0"):
        await db.set_chat_field(message.chat.id, "anonadmin", False)
        await message.reply_text("✅ Anonymous admin: OFF")
    else:
        await message.reply_text("❌ Usage: /anonadmin yes|no")


@Client.on_message(filters.command("adminerror") & filters.group)
async def adminerror_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    if len(message.command) < 2:
        chat = await db.get_chat(message.chat.id)
        state = chat.get("adminerror", True)
        return await message.reply_text(
            f"📋 <b>Admin Error Messages:</b> {'ON' if state else 'OFF'}\n"
            f"Usage: /adminerror yes|no"
        )
    val = message.command[1].lower()
    if val in ("yes", "on", "true", "1"):
        await db.set_chat_field(message.chat.id, "adminerror", True)
        await message.reply_text("✅ Admin error messages: ON")
    elif val in ("no", "off", "false", "0"):
        await db.set_chat_field(message.chat.id, "adminerror", False)
        await message.reply_text("✅ Admin error messages: OFF")
    else:
        await message.reply_text("❌ Usage: /adminerror yes|no")
