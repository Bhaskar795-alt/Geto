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
    value = getattr(status, "value", None)

    if value is not None:
        status = value

    status = str(status).lower().replace(
        "chatmemberstatus.", ""
    )

    if status in ("owner", "creator"):
        return "👑", "Owner"

    if status in ("administrator", "admin"):
        return "🛡️", "Admin"

    return "👤", "Member"


async def is_user_admin(client, chat_id, user_id):
    """Check if user is already admin."""
    try:
        member = await client.get_chat_member(
            chat_id,
            user_id
        )

        status = str(
            getattr(member.status, "value", member.status)
        ).lower()

        return (
            "administrator" in status
            or "owner" in status
            or "creator" in status
        )

    except Exception:
        return False


# =========================================================
# LOG HELPER
# =========================================================

async def send_log(
    client,
    message,
    action,
    target=None,
    reason=""
):
    try:
        from plugins.logs import log_action

        if target is None:
            target = message.from_user

        await log_action(
            client,
            message.chat.id,
            "admin",
            action,
            message.from_user,
            target,
            reason
        )

    except Exception as e:
        print(f"[LOG] {e}")


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
        return await message.reply_text(
            "❌ Admin only."
        )

    uid, name, _ = await resolve_user(
        client,
        message
    )

    if not uid:
        return await message.reply_text(
            "❌ Reply to a user or give a valid user."
        )

    reason = " ".join(
        message.command[2:]
    ) or "No reason"

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

        try:
            target = await client.get_users(uid)
        except Exception:
            target = uid

        await send_log(
            client,
            message,
            "ban",
            target,
            reason
        )

    except Exception as e:
        await message.reply_text(
            f"❌ {e}"
        )


@Client.on_message(filters.command("dban") & filters.group)
async def dban_cmd(client, message):

    if not await is_admin(
        client,
        message.chat.id,
        message.from_user.id
    ):
        return await message.reply_text(
            "❌ Admin only."
        )

    if not message.reply_to_message:
        return await message.reply_text(
            "❌ Reply to a user's message."
        )

    target = message.reply_to_message.from_user

    try:
        await message.reply_to_message.delete()

        await client.ban_chat_member(
            message.chat.id,
            target.id
        )

        await message.reply_text(
            f"🔨 <b>Banned + Deleted</b> "
            f"{mention_html(target.id, target.first_name)}"
        )

        await send_log(
            client,
            message,
            "dban",
            target,
            "with message deleted"
        )

    except Exception as e:
        await message.reply_text(
            f"❌ {e}"
        )


@Client.on_message(filters.command("sban") & filters.group)
async def sban_cmd(client, message):

    if not await is_admin(
        client,
        message.chat.id,
        message.from_user.id
    ):
        return await message.reply_text(
            "❌ Admin only."
        )

    uid, name, _ = await resolve_user(
        client,
        message
    )

    if not uid:
        return await message.reply_text(
            "❌ Reply to a user or give a valid user."
        )

    try:
        await message.delete()
    except Exception:
        pass

    try:
        await client.ban_chat_member(
            message.chat.id,
            uid
        )

        await client.send_message(
            message.chat.id,
            f"🔨 <b>Silently banned</b> "
            f"{mention_html(uid, name)}"
        )

        try:
            target = await client.get_users(uid)
        except Exception:
            target = uid

        await send_log(
            client,
            message,
            "sban",
            target,
            "silent"
        )

    except Exception as e:
        await message.reply_text(
            f"❌ {e}"
        )


@Client.on_message(filters.command("tban") & filters.group)
async def tban_cmd(client, message):

    if not await is_admin(
        client,
        message.chat.id,
        message.from_user.id
    ):
        return await message.reply_text(
            "❌ Admin only."
        )

    if len(message.command) < 3:
        return await message.reply_text(
            "Usage: /tban <user> <duration>"
        )

    uid, name, _ = await resolve_user(
        client,
        message
    )

    if not uid:
        return await message.reply_text(
            "❌ Reply to a user or give a valid user."
        )

    secs = parse_duration(
        message.command[2]
    )

    if secs == 0:
        return await message.reply_text(
            "❌ Invalid duration."
        )

    until = datetime.now() + timedelta(
        seconds=secs
    )

    try:
        await client.ban_chat_member(
            message.chat.id,
            uid,
            until_date=until
        )

        await message.reply_text(
            f"🔨 <b>Temp-Ban</b> "
            f"{mention_html(uid, name)}\n"
            f"⏱️ {message.command[2]}"
        )

        try:
            target = await client.get_users(uid)
        except Exception:
            target = uid

        await send_log(
            client,
            message,
            "tban",
            target,
            f"for {message.command[2]}"
        )

    except Exception as e:
        await message.reply_text(
            f"❌ {e}"
        )


@Client.on_message(filters.command("unban") & filters.group)
async def unban_cmd(client, message):

    if not await is_admin(
        client,
        message.chat.id,
        message.from_user.id
    ):
        return await message.reply_text(
            "❌ Admin only."
        )

    uid, name, _ = await resolve_user(
        client,
        message
    )

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

        try:
            target = await client.get_users(uid)
        except Exception:
            target = uid

        await send_log(
            client,
            message,
            "unban",
            target,
            ""
        )

    except Exception as e:
        await message.reply_text(
            f"❌ {e}"
        )


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
        return await message.reply_text(
            "❌ Admin only."
        )

    uid, name, _ = await resolve_user(
        client,
        message
    )

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

        try:
            target = await client.get_users(uid)
        except Exception:
            target = uid

        await send_log(
            client,
            message,
            "mute",
            target,
            "permanent"
        )

    except Exception as e:
        await message.reply_text(
            f"❌ {e}"
        )


@Client.on_message(filters.command("dmute") & filters.group)
async def dmute_cmd(client, message):

    if not await is_admin(
        client,
        message.chat.id,
        message.from_user.id
    ):
        return await message.reply_text(
            "❌ Admin only."
        )

    if not message.reply_to_message:
        return await message.reply_text(
            "❌ Reply to a user's message."
        )

    target = message.reply_to_message.from_user

    try:
        await message.reply_to_message.delete()

        await client.restrict_chat_member(
            message.chat.id,
            target.id,
            MUTE_PERMS
        )

        await db.mute_user(
            message.chat.id,
            target.id,
            0,
            "permanent"
        )

        await message.reply_text(
            f"🔇 <b>Muted + Deleted</b> "
            f"{mention_html(target.id, target.first_name)}"
        )

        await send_log(
            client,
            message,
            "dmute",
            target,
            "with message deleted"
        )

    except Exception as e:
        await message.reply_text(
            f"❌ {e}"
        )


@Client.on_message(filters.command("smute") & filters.group)
async def smute_cmd(client, message):

    if not await is_admin(
        client,
        message.chat.id,
        message.from_user.id
    ):
        return await message.reply_text(
            "❌ Admin only."
        )

    uid, name, _ = await resolve_user(
        client,
        message
    )

    if not uid:
        return await message.reply_text(
            "❌ Reply to a user or give a valid user."
        )

    try:
        await message.delete()
    except Exception:
        pass

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

        await client.send_message(
            message.chat.id,
            f"🔇 <b>Silently muted</b> "
            f"{mention_html(uid, name)}"
        )

        try:
            target = await client.get_users(uid)
        except Exception:
            target = uid

        await send_log(
            client,
            message,
            "smute",
            target,
            "silent"
        )

    except Exception as e:
        await message.reply_text(
            f"❌ {e}"
        )


@Client.on_message(filters.command("tmute") & filters.group)
async def tmute_cmd(client, message):

    if not await is_admin(
        client,
        message.chat.id,
        message.from_user.id
    ):
        return await message.reply_text(
            "❌ Admin only."
        )

    if len(message.command) < 3:
        return await message.reply_text(
            "Usage: /tmute <user> <duration>"
        )

    uid, name, _ = await resolve_user(
        client,
        message
    )

    if not uid:
        return await message.reply_text(
            "❌ Reply to a user or give a valid user."
        )

    secs = parse_duration(
        message.command[2]
    )

    if secs == 0:
        return await message.reply_text(
            "❌ Invalid duration."
        )

    until = datetime.now() + timedelta(
        seconds=secs
    )

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
            f"⏱️ {message.command[2]}"
        )

        try:
            target = await client.get_users(uid)
        except Exception:
            target = uid

        await send_log(
            client,
            message,
            "tmute",
            target,
            f"for {message.command[2]}"
        )

    except Exception as e:
        await message.reply_text(
            f"❌ {e}"
        )


@Client.on_message(filters.command("unmute") & filters.group)
async def unmute_cmd(client, message):

    if not await is_admin(
        client,
        message.chat.id,
        message.from_user.id
    ):
        return await message.reply_text(
            "❌ Admin only."
        )

    uid, name, _ = await resolve_user(
        client,
        message
    )

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

        try:
            target = await client.get_users(uid)
        except Exception:
            target = uid

        await send_log(
            client,
            message,
            "unmute",
            target,
            ""
        )

    except Exception as e:
        await message.reply_text(
            f"❌ {e}"
        )


@Client.on_message(filters.command("mutelist") & filters.group)
async def mutelist_cmd(client, message):

    if not await is_admin(
        client,
        message.chat.id,
        message.from_user.id
    ):
        return await message.reply_text(
            "❌ Admin only."
        )

    import time

    lines = [
        "<b>🔇 Active Mutes:</b>\n"
    ]

    async for d in db.get_mutelist(
        message.chat.id
    ):
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
# KICK
# =========================================================

@Client.on_message(filters.command("kick") & filters.group)
async def kick_cmd(client, message):

    if not await is_admin(
        client,
        message.chat.id,
        message.from_user.id
    ):
        return await message.reply_text(
            "❌ Admin only."
        )

    uid, name, _ = await resolve_user(
        client,
        message
    )

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

        try:
            target = await client.get_users(uid)
        except Exception:
            target = uid

        await send_log(
            client,
            message,
            "kick",
            target,
            ""
        )

    except Exception as e:
        await message.reply_text(
            f"❌ {e}"
        )


@Client.on_message(filters.command("dkick") & filters.group)
async def dkick_cmd(client, message):

    if not await is_admin(
        client,
        message.chat.id,
        message.from_user.id
    ):
        return await message.reply_text(
            "❌ Admin only."
        )

    if not message.reply_to_message:
        return await message.reply_text(
            "❌ Reply to a user's message."
        )

    target = message.reply_to_message.from_user

    try:
        await message.reply_to_message.delete()

        await client.ban_chat_member(
            message.chat.id,
            target.id
        )

        await client.unban_chat_member(
            message.chat.id,
            target.id
        )

        await message.reply_text(
            f"👢 <b>Kicked + Deleted</b> "
            f"{mention_html(target.id, target.first_name)}"
        )

        await send_log(
            client,
            message,
            "dkick",
            target,
            "with message deleted"
        )

    except Exception as e:
        await message.reply_text(
            f"❌ {e}"
        )


@Client.on_message(filters.command("skick") & filters.group)
async def skick_cmd(client, message):

    if not await is_admin(
        client,
        message.chat.id,
        message.from_user.id
    ):
        return await message.reply_text(
            "❌ Admin only."
        )

    uid, name, _ = await resolve_user(
        client,
        message
    )

    if not uid:
        return await message.reply_text(
            "❌ Reply to a user or give a valid user."
        )

    try:
        await message.delete()
    except Exception:
        pass

    try:
        await client.ban_chat_member(
            message.chat.id,
            uid
        )

        await client.unban_chat_member(
            message.chat.id,
            uid
        )

        await client.send_message(
            message.chat.id,
            f"👢 <b>Silently kicked</b> "
            f"{mention_html(uid, name)}"
        )

        try:
            target = await client.get_users(uid)
        except Exception:
            target = uid

        await send_log(
            client,
            message,
            "skick",
            target,
            "silent"
        )

    except Exception as e:
        await message.reply_text(
            f"❌ {e}"
        )


@Client.on_message(filters.command("kickme") & filters.group)
async def kickme_cmd(client, message):

    try:
        await client.ban_chat_member(
            message.chat.id,
            message.from_user.id
        )

        await client.unban_chat_member(
            message.chat.id,
            message.from_user.id
        )

        await message.reply_text(
            f"👋 {message.from_user.mention} "
            f"kicked themselves."
        )

    except Exception as e:
        await message.reply_text(
            f"❌ {e}"
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
        return await message.reply_text(
            "❌ Admin only."
        )

    uid, name, _ = await resolve_user(
        client,
        message
    )

    if not uid:
        return await message.reply_text(
            "❌ Reply to a user or give a valid user."
        )

    custom_title = " ".join(
        message.command[2:]
    )[:16] or ""

    already_admin = await is_user_admin(
        client,
        message.chat.id,
        uid
    )

    if already_admin:
        try:
            target_user = await client.get_users(uid)

            return await message.reply_text(
                f"ℹ️ {target_user.mention} "
                f"is <b>already an admin</b> "
                f"in this group."
            )

        except Exception:
            return await message.reply_text(
                "ℹ️ User is already an admin."
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

        if custom_title:
            try:
                await client.set_administrator_title(
                    chat_id=message.chat.id,
                    user_id=uid,
                    title=custom_title
                )
            except Exception:
                pass

        title_text = (
            f"\n👑 Title: <b>{custom_title}</b>"
            if custom_title
            else ""
        )

        await message.reply_text(
            f"⬆️ <b>Promoted</b> "
            f"{mention_html(uid, name)}"
            f"{title_text}"
        )

        try:
            target = await client.get_users(uid)
        except Exception:
            target = uid

        await send_log(
            client,
            message,
            "promote",
            target,
            custom_title or ""
        )

    except Exception as e:

        error_str = str(e)

        if (
            "CHAT_ADMIN_REQUIRED" in error_str
            or "not enough rights" in error_str.lower()
        ):
            await message.reply_text(
                "❌ <b>Cannot promote this user</b>\n\n"
                "⚠️ <b>Bot ko ye permissions chahiye:</b>\n"
                "• ✅ Add New Admins\n"
                "• ✅ Ban Users\n"
                "• ✅ Delete Messages\n\n"
                "📋 <b>Fix:</b>\n"
                "1. Group → Manage → Administrators\n"
                "2. Bot → Add New Admins → ON\n"
                "3. Save karo\n"
                "4. Phir se try karo"
            )

        else:
            await message.reply_text(
                f"❌ {error_str}"
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
        return await message.reply_text(
            "❌ Admin only."
        )

    uid, name, _ = await resolve_user(
        client,
        message
    )

    if not uid:
        return await message.reply_text(
            "❌ Reply to a user or give a valid user."
        )

    is_admin_user = await is_user_admin(
        client,
        message.chat.id,
        uid
    )

    if not is_admin_user:
        try:
            target_user = await client.get_users(uid)

            return await message.reply_text(
                f"ℹ️ {target_user.mention} "
                f"is <b>not an admin</b> "
                f"in this group."
            )

        except Exception:
            return await message.reply_text(
                "ℹ️ User is not an admin."
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

        try:
            target = await client.get_users(uid)
        except Exception:
            target = uid

        await send_log(
            client,
            message,
            "demote",
            target,
            ""
        )

    except Exception as e:

        error_str = str(e)

        if "CHAT_ADMIN_REQUIRED" in error_str:
            await message.reply_text(
                "❌ <b>Cannot demote this user</b>\n\n"
                "Bot ko <b>Add New Admins</b> "
                "permission chahiye."
            )

        else:
            await message.reply_text(
                f"❌ {error_str}"
            )


# =========================================================
# ADMINS — COMPLETE ADMIN LIST
# =========================================================

@Client.on_message(filters.command("admins") & filters.group)
async def admins_cmd(client, message):

    try:
        admin_list = []

        async for member in client.get_chat_members(
            message.chat.id,
            filter="administrators"
        ):
            admin_list.append(member)

        if not admin_list:
            return await message.reply_text(
                "❌ <b>Admin list nahi mili.</b>"
            )

        lines = [
            "👑 <b>GROUP ADMINS</b>",
            "",
            f"👥 <b>Total Admins:</b> "
            f"<code>{len(admin_list)}</code>",
            ""
        ]

        for i, member in enumerate(
            admin_list,
            1
        ):

            user = member.user

            # Full name
            name = user.first_name or "Unknown"

            if user.last_name:
                name += f" {user.last_name}"

            # Username / mention
            if user.username:
                user_text = f"@{user.username}"
            else:
                user_text = user.mention

            # Status
            status = str(
                getattr(
                    member.status,
                    "value",
                    member.status
                )
            ).lower()

            if (
                "owner" in status
                or "creator" in status
            ):
                role = "👑 <b>Owner</b>"
            else:
                role = "🛡️ <b>Admin</b>"

            lines.append(
                f"{i}. {role}\n"
                f"   👤 {name}\n"
                f"   🔗 {user_text}\n"
                f"   🆔 <code>{user.id}</code>\n"
            )

        await message.reply_text(
            "\n".join(lines),
            disable_web_page_preview=True
        )

    except Exception as e:

        await message.reply_text(
            "❌ <b>Admin list error:</b>\n"
            f"<code>{e}</code>"
        )


# =========================================================
# ADMIN LIST — SHORT VERSION
# =========================================================

@Client.on_message(filters.command("adminlist") & filters.group)
async def adminlist_cmd(client, message):

    lines = [
        "<b>👮 Admin List:</b>\n"
    ]

    try:
        async for member in client.get_chat_members(
            message.chat.id,
            filter="administrators"
        ):

            icon, role = get_admin_role(
                member.status
            )

            lines.append(
                f"{icon} <b>{role}</b> "
                f"{member.user.mention} — "
                f"<code>{member.user.id}</code>"
            )

    except Exception as e:

        return await message.reply_text(
            f"❌ {e}"
        )

    await message.reply_text(
        "\n".join(lines),
        disable_web_page_preview=True
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

        async for member in client.get_chat_members(
            message.chat.id,
            filter="administrators"
        ):

            status = getattr(
                member.status,
                "value",
                member.status
            )

            admins.append({
                "user_id": member.user.id,
                "name": member.user.first_name or "",
                "username": member.user.username or "",
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

# =========================================================
# ADMINS — COMPLETE ADMIN LIST
# =========================================================

@Client.on_message(filters.command("admins") & filters.group)
async def admins_cmd(client, message):

    try:
        admin_list = []

        async for member in client.get_chat_members(
            message.chat.id,
            filter="administrators"
        ):
            admin_list.append(member)

        if not admin_list:
            return await message.reply_text(
                "❌ <b>Admin list nahi mili.</b>"
            )

        lines = [
            "👑 <b>GROUP ADMINS</b>",
            "",
            f"👥 <b>Total Admins:</b> "
            f"<code>{len(admin_list)}</code>",
            ""
        ]

        for i, member in enumerate(admin_list, 1):

            user = member.user

            # =================================================
            # FULL NAME
            # =================================================

            first_name = user.first_name or ""
            last_name = user.last_name or ""

            name = f"{first_name} {last_name}".strip()

            if not name:
                name = "Unknown"

            # =================================================
            # USERNAME / MENTION
            # =================================================

            if user.username:
                user_text = f"@{user.username}"
            else:
                user_text = (
                    f'<a href="tg://user?id={user.id}">'
                    f'{name}</a>'
                )

            # =================================================
            # STATUS
            # IMPORTANT:
            # Pyrogram version ke according member.status
            # string ya enum dono ho sakta hai.
            # =================================================

            status = getattr(member, "status", "")

            if hasattr(status, "value"):
                status = status.value

            status = str(status).lower()

            # Remove enum prefix if present
            status = status.replace(
                "chatmemberstatus.",
                ""
            )

            # =================================================
            # ROLE
            # =================================================

            if status in (
                "owner",
                "creator"
            ):
                role = "👑 <b>Owner</b>"

            elif status in (
                "administrator",
                "admin"
            ):
                role = "🛡️ <b>Admin</b>"

            else:
                # Safety fallback
                if (
                    "owner" in status
                    or "creator" in status
                ):
                    role = "👑 <b>Owner</b>"
                else:
                    role = "🛡️ <b>Admin</b>"

            # =================================================
            # ADD ADMIN TO LIST
            # =================================================

            lines.append(
                f"<b>{i}.</b> {role}\n"
                f"   👤 {name}\n"
                f"   🔗 {user_text}\n"
                f"   🆔 <code>{user.id}</code>\n"
            )

        # =====================================================
        # SEND RESULT
        # =====================================================

        await message.reply_text(
            "\n".join(lines),
            disable_web_page_preview=True
        )

    except Exception as e:

        await message.reply_text(
            "❌ <b>Admin list error:</b>\n"
            f"<code>{e}</code>"
        )
