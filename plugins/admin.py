from datetime import datetime, timedelta

from pyrogram import Client, filters
from pyrogram.types import ChatPermissions, ChatPrivileges

from database import db
from utils.helpers import resolve_user, parse_duration, mention_html
from utils.permissions import is_admin


# =========================================================
# MUTE PERMISSIONS
# =========================================================

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
# ADMIN STATUS HELPER
# =========================================================

def get_admin_role(status):
    """
    Safely handles Pyrogram status as either:
    - enum/object with .value
    - plain string
    """

    # Some Pyrogram versions return an enum,
    # others may return a string.
    value = getattr(status, "value", None)

    if value is not None:
        status = value

    status = str(status).lower()

    # Remove enum prefix if present.
    status = status.replace("chatmemberstatus.", "")

    if status in ("owner", "creator"):
        return "👑", "Owner"

    if status in ("administrator", "admin"):
        return "🛡️", "Admin"

    return "👤", "Member"


# =========================================================
# BAN
# =========================================================

@Client.on_message(filters.command("ban") & filters.group)
async def ban_cmd(client, message):

    if not await is_admin(
        client,
        message.chat.id,
        message.from_user.id
    ):
        return await message.reply_text("❌ Admin only.")

    uid, name, _ = await resolve_user(client, message)

    if not uid:
        return await message.reply_text(
            "❌ Reply to a user or give a valid username/ID."
        )

    reason = " ".join(message.command[2:]) or "No reason"

    try:
        await client.ban_chat_member(
            message.chat.id,
            uid
        )

        await message.reply_text(
            f"🔨 <b>Banned</b> "
            f"{mention_html(uid, name)}\n"
            f"📝 {reason}"
        )

    except Exception as e:
        await message.reply_text(f"❌ {e}")


# =========================================================
# TEMP BAN
# =========================================================

@Client.on_message(filters.command("tban") & filters.group)
async def tban_cmd(client, message):

    if not await is_admin(
        client,
        message.chat.id,
        message.from_user.id
    ):
        return await message.reply_text("❌ Admin only.")

    if len(message.command) < 3:
        return await message.reply_text(
            "Usage: /tban <user> <duration>"
        )

    uid, name, _ = await resolve_user(client, message)

    if not uid:
        return await message.reply_text(
            "❌ Reply to a user or give a valid user."
        )

    secs = parse_duration(message.command[2])

    if secs == 0:
        return await message.reply_text(
            "❌ Invalid duration.\nExample: `1h`, `30m`, `2d`"
        )

    until = datetime.now() + timedelta(seconds=secs)

    try:
        await client.ban_chat_member(
            message.chat.id,
            uid,
            until_date=until
        )

        await message.reply_text(
            f"🔨 <b>Temp-Ban</b> "
            f"{mention_html(uid, name)}\n"
            f"⏱️ Duration: <code>{message.command[2]}</code>"
        )

    except Exception as e:
        await message.reply_text(f"❌ {e}")


# =========================================================
# UNBAN
# =========================================================

@Client.on_message(filters.command("unban") & filters.group)
async def unban_cmd(client, message):

    if not await is_admin(
        client,
        message.chat.id,
        message.from_user.id
    ):
        return await message.reply_text("❌ Admin only.")

    uid, name, _ = await resolve_user(client, message)

    if not uid:
        return await message.reply_text(
            "❌ Reply to a user or give a valid user."
        )

    try:
        await client.unban_chat_member(
            message.chat.id,
            uid
        )

        await message.reply_text(
            f"✅ <b>Unbanned</b> "
            f"{mention_html(uid, name)}"
        )

    except Exception as e:
        await message.reply_text(f"❌ {e}")


# =========================================================
# KICK
# =========================================================

@Client.on_message(filters.command("kick") & filters.group)
async def kick_cmd(client, message):

    if not await is_admin(
        client,
        message.chat.id,
        message.from_user.id
    ):
        return await message.reply_text("❌ Admin only.")

    uid, name, _ = await resolve_user(client, message)

    if not uid:
        return await message.reply_text(
            "❌ Reply to a user or give a valid user."
        )

    try:
        await client.ban_chat_member(
            message.chat.id,
            uid
        )

        await client.unban_chat_member(
            message.chat.id,
            uid
        )

        await message.reply_text(
            f"👢 <b>Kicked</b> "
            f"{mention_html(uid, name)}"
        )

    except Exception as e:
        await message.reply_text(f"❌ {e}")


# =========================================================
# MUTE
# =========================================================

@Client.on_message(filters.command("mute") & filters.group)
async def mute_cmd(client, message):

    if not await is_admin(
        client,
        message.chat.id,
        message.from_user.id
    ):
        return await message.reply_text("❌ Admin only.")

    uid, name, _ = await resolve_user(client, message)

    if not uid:
        return await message.reply_text(
            "❌ Reply to a user or give a valid user."
        )

    try:
        await client.restrict_chat_member(
            message.chat.id,
            uid,
            MUTE_PERMS
        )

        await db.mute_user(
            message.chat.id,
            uid,
            0,
            "permanent"
        )

        await message.reply_text(
            f"🔇 <b>Muted</b> "
            f"{mention_html(uid, name)}"
        )

    except Exception as e:
        await message.reply_text(f"❌ {e}")


# =========================================================
# TEMP MUTE
# =========================================================

@Client.on_message(filters.command("tmute") & filters.group)
async def tmute_cmd(client, message):

    if not await is_admin(
        client,
        message.chat.id,
        message.from_user.id
    ):
        return await message.reply_text("❌ Admin only.")

    if len(message.command) < 3:
        return await message.reply_text(
            "Usage: /tmute <user> <duration>"
        )

    uid, name, _ = await resolve_user(client, message)

    if not uid:
        return await message.reply_text(
            "❌ Reply to a user or give a valid user."
        )

    secs = parse_duration(message.command[2])

    if secs == 0:
        return await message.reply_text(
            "❌ Invalid duration.\nExample: `1h`, `30m`, `2d`"
        )

    until = datetime.now() + timedelta(seconds=secs)

    try:
        await client.restrict_chat_member(
            message.chat.id,
            uid,
            MUTE_PERMS,
            until_date=until
        )

        await db.mute_user(
            message.chat.id,
            uid,
            int(until.timestamp()),
            message.command[2]
        )

        await message.reply_text(
            f"🔇 <b>Temp-Mute</b> "
            f"{mention_html(uid, name)}\n"
            f"⏱️ Duration: <code>{message.command[2]}</code>"
        )

    except Exception as e:
        await message.reply_text(f"❌ {e}")


# =========================================================
# UNMUTE
# =========================================================

@Client.on_message(filters.command("unmute") & filters.group)
async def unmute_cmd(client, message):

    if not await is_admin(
        client,
        message.chat.id,
        message.from_user.id
    ):
        return await message.reply_text("❌ Admin only.")

    uid, name, _ = await resolve_user(client, message)

    if not uid:
        return await message.reply_text(
            "❌ Reply to a user or give a valid user."
        )

    try:
        await client.restrict_chat_member(
            message.chat.id,
            uid,
            UNMUTE_PERMS
        )

        await db.unmute_user(
            message.chat.id,
            uid
        )

        await message.reply_text(
            f"🔊 <b>Unmuted</b> "
            f"{mention_html(uid, name)}"
        )

    except Exception as e:
        await message.reply_text(f"❌ {e}")


# =========================================================
# MUTE LIST
# =========================================================

@Client.on_message(filters.command("mutelist") & filters.group)
async def mutelist_cmd(client, message):

    if not await is_admin(
        client,
        message.chat.id,
        message.from_user.id
    ):
        return await message.reply_text("❌ Admin only.")

    import time

    lines = [
        "<b>🔇 Active Mutes:</b>\n"
    ]

    async for d in db.get_mutelist(message.chat.id):

        until = d.get("until", 0)

        if until:
            rem = max(
                0,
                until - int(time.time())
            )

            lines.append(
                f"• <code>{d['user_id']}</code> "
                f"— {rem}s left"
            )

        else:
            lines.append(
                f"• <code>{d['user_id']}</code> "
                f"— permanent"
            )

    if len(lines) == 1:
        lines.append(
            "<i>No active mutes.</i>"
        )

    await message.reply_text(
        "\n".join(lines)
    )


# =========================================================
# PROMOTE
# =========================================================

@Client.on_message(filters.command("promote") & filters.group)
async def promote_cmd(client, message):

    if not await is_admin(
        client,
        message.chat.id,
        message.from_user.id
    ):
        return await message.reply_text("❌ Admin only.")

    uid, name, _ = await resolve_user(
        client,
        message
    )

    if not uid:
        return await message.reply_text(
            "❌ Reply to a user or give a valid user."
        )

    try:

        privileges = ChatPrivileges(
            can_delete_messages=True,
            can_restrict_members=True,
            can_pin_messages=True,
            can_invite_users=True,
            can_manage_video_chats=True,
            can_change_info=True,
            can_manage_chat=True,
            can_promote_members=False
        )

        await client.promote_chat_member(
            chat_id=message.chat.id,
            user_id=uid,
            privileges=privileges
        )

        await message.reply_text(
            f"⬆️ <b>Promoted</b> "
            f"{mention_html(uid, name)}"
        )

    except Exception as e:
        await message.reply_text(
            f"❌ {e}"
        )


# =========================================================
# DEMOTE
# =========================================================

@Client.on_message(filters.command("demote") & filters.group)
async def demote_cmd(client, message):

    if not await is_admin(
        client,
        message.chat.id,
        message.from_user.id
    ):
        return await message.reply_text("❌ Admin only.")

    uid, name, _ = await resolve_user(
        client,
        message
    )

    if not uid:
        return await message.reply_text(
            "❌ Reply to a user or give a valid user."
        )

    try:

        privileges = ChatPrivileges(
            can_delete_messages=False,
            can_restrict_members=False,
            can_pin_messages=False,
            can_invite_users=False,
            can_manage_video_chats=False,
            can_change_info=False,
            can_manage_chat=False,
            can_promote_members=False
        )

        await client.promote_chat_member(
            chat_id=message.chat.id,
            user_id=uid,
            privileges=privileges
        )

        await message.reply_text(
            f"⬇️ <b>Demoted</b> "
            f"{mention_html(uid, name)}"
        )

    except Exception as e:
        await message.reply_text(
            f"❌ {e}"
        )


# =========================================================
# ADMINS
# =========================================================

@Client.on_message(filters.command("admins") & filters.group)
async def admins_cmd(client, message):

    lines = [
        "<b>👮 Admins:</b>\n"
    ]

    try:

        async for m in client.get_chat_members(
            message.chat.id,
            filter="administrators"
        ):

            icon, role = get_admin_role(
                m.status
            )

            lines.append(
                f"{icon} <b>{role}</b> — "
                f"{m.user.mention} "
                f"(<code>{m.user.id}</code>)"
            )

    except Exception as e:
        return await message.reply_text(
            f"❌ {e}"
        )

    await message.reply_text(
        "\n".join(lines)
    )


# =========================================================
# ADMIN LIST
# =========================================================

@Client.on_message(filters.command("adminlist") & filters.group)
async def adminlist_cmd(client, message):

    lines = [
        "<b>👮 Admin List:</b>\n"
    ]

    try:

        async for m in client.get_chat_members(
            message.chat.id,
            filter="administrators"
        ):

            icon, role = get_admin_role(
                m.status
            )

            lines.append(
                f"{icon} <b>{role}</b> "
                f"{m.user.mention} "
                f"— <code>{m.user.id}</code>"
            )

    except Exception as e:
        return await message.reply_text(
            f"❌ {e}"
        )

    await message.reply_text(
        "\n".join(lines)
    )


# =========================================================
# ADMIN CACHE
# =========================================================

@Client.on_message(filters.command("admincache") & filters.group)
async def admincache_cmd(client, message):

    if not await is_admin(
        client,
        message.chat.id,
        message.from_user.id
    ):
        return await message.reply_text(
            "❌ Admin only."
        )

    try:

        import time

        admins = []

        async for m in client.get_chat_members(
            message.chat.id,
            filter="administrators"
        ):

            status = getattr(
                m.status,
                "value",
                m.status
            )

            admins.append({
                "user_id": m.user.id,
                "name": m.user.first_name or "",
                "username": m.user.username or "",
                "status": str(status)
            })

        await db.set_chat_field(
            message.chat.id,
            "admins_cache",
            admins
        )

        await db.set_chat_field(
            message.chat.id,
            "admin_cache_time",
            int(time.time())
        )

        await message.reply_text(
            f"✅ <b>Admin cache updated.</b>\n"
            f"👥 Total admins: "
            f"<code>{len(admins)}</code>"
        )

    except Exception as e:
        await message.reply_text(
            f"❌ {e}"
        )


# =========================================================
# ANONYMOUS ADMIN
# =========================================================

@Client.on_message(filters.command("anonadmin") & filters.group)
async def anonadmin_cmd(client, message):

    if not await is_admin(
        client,
        message.chat.id,
        message.from_user.id
    ):
        return await message.reply_text(
            "❌ Admin only."
        )

    if len(message.command) < 2:

        chat = await db.get_chat(
            message.chat.id
        )

        state = chat.get(
            "anonadmin",
            False
        )

        return await message.reply_text(
            f"📋 <b>Anonymous Admin:</b> "
            f"{'ON' if state else 'OFF'}\n"
            f"Usage: /anonadmin yes|no"
        )

    val = message.command[1].lower()

    if val in (
        "yes",
        "on",
        "true",
        "1"
    ):

        await db.set_chat_field(
            message.chat.id,
            "anonadmin",
            True
        )

        await message.reply_text(
            "✅ Anonymous admin: ON"
        )

    elif val in (
        "no",
        "off",
        "false",
        "0"
    ):

        await db.set_chat_field(
            message.chat.id,
            "anonadmin",
            False
        )

        await message.reply_text(
            "✅ Anonymous admin: OFF"
        )

    else:

        await message.reply_text(
            "❌ Usage: /anonadmin yes|no"
        )


# =========================================================
# ADMIN ERROR
# =========================================================

@Client.on_message(filters.command("adminerror") & filters.group)
async def adminerror_cmd(client, message):

    if not await is_admin(
        client,
        message.chat.id,
        message.from_user.id
    ):
        return await message.reply_text(
            "❌ Admin only."
        )

    if len(message.command) < 2:

        chat = await db.get_chat(
            message.chat.id
        )

        state = chat.get(
            "adminerror",
            True
        )

        return await message.reply_text(
            f"📋 <b>Admin Error Messages:</b> "
            f"{'ON' if state else 'OFF'}\n"
            f"Usage: /adminerror yes|no"
        )

    val = message.command[1].lower()

    if val in (
        "yes",
        "on",
        "true",
        "1"
    ):

        await db.set_chat_field(
            message.chat.id,
            "adminerror",
            True
        )

        await message.reply_text(
            "✅ Admin error messages: ON"
        )

    elif val in (
        "no",
        "off",
        "false",
        "0"
    ):

        await db.set_chat_field(
            message.chat.id,
            "adminerror",
            False
        )

        await message.reply_text(
            "✅ Admin error messages: OFF"
        )

    else:

        await message.reply_text(
            "❌ Usage: /adminerror yes|no"
        )

Main fix: "get_admin_role()" ab ".value" ko blindly access nahi karta. Agar "m.status" string hai to string hi use karega; agar enum hai to ".value" safely lega.

Ek aur cheez: agar "/adminlist" ke baad bhi error aaye, exact new error paste kar dena. Us case mein problem status nahi, "get_chat_members()"/Pyrogram version compatibility mein hogi.
