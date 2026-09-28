import re
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import ChatPermissions
from database import db
from utils.permissions import is_admin

# =========================================================
# ALL LOCK TYPES
# =========================================================

# Telegram-native permissions (can be set via ChatPermissions)
NATIVE_LOCKS = {
    "photo": "can_send_media_messages",
    "video": "can_send_media_messages",
    "audio": "can_send_media_messages",
    "document": "can_send_media_messages",
    "voice": "can_send_media_messages",
    "videonote": "can_send_media_messages",
    "sticker": "can_send_other_messages",
    "gif": "can_send_other_messages",
    "animation": "can_send_other_messages",
    "emojigame": "can_send_other_messages",
    "inline": "can_send_other_messages",
    "game": "can_send_other_messages",
    "url": "can_add_web_page_previews",
    "poll": "can_send_polls",
}

# Non-native locks (must be handled by deleting messages)
TEXT_LOCKS = {
    "all", "album", "anonchannel", "bot", "botlink", "button",
    "cashtag", "checklist", "cjk", "collage", "command", "comment",
    "contact", "cyrillic", "email", "emoji", "emojicustom",
    "emojionly", "externalreply", "forward", "forwardbot",
    "forwardchannel", "forwardstory", "forwarduser", "guestbot",
    "invitelink", "location", "outsidereaction", "phone", "reaction",
    "richmessage", "rtl", "slideshow", "spoiler", "stickeranimated",
    "stickerpremium", "text", "zalgo",
}

LOCK_TYPES = list(NATIVE_LOCKS.keys()) + list(TEXT_LOCKS)
LOCK_TYPES = sorted(set(LOCK_TYPES))


# =========================================================
# APPLY NATIVE PERMISSIONS
# =========================================================

async def apply_group_permissions(client, chat_id, locks):
    """
    Apply Telegram native permissions based on current locks.
    Only touches permissions that have native locks.
    """
    # Default permissions (all allowed)
    perms = {
        "can_send_messages": True,
        "can_send_media_messages": True,
        "can_send_other_messages": True,
        "can_add_web_page_previews": True,
        "can_send_polls": True,
        "can_change_info": False,
        "can_invite_users": True,
        "can_pin_messages": False,
    }

    # Apply native locks (disable the permission)
    for lock_type, perm in NATIVE_LOCKS.items():
        if locks.get(lock_type, False):
            perms[perm] = False

    # Special: all → disable everything
    if locks.get("all", False):
        perms["can_send_messages"] = False

    # Special: text → disable text messages
    if locks.get("text", False):
        perms["can_send_messages"] = False

    # Build ChatPermissions
    chat_perms = ChatPermissions(
        can_send_messages=perms["can_send_messages"],
        can_send_media_messages=perms["can_send_media_messages"],
        can_send_other_messages=perms["can_send_other_messages"],
        can_add_web_page_previews=perms["can_add_web_page_previews"],
        can_send_polls=perms["can_send_polls"],
        can_change_info=perms["can_change_info"],
        can_invite_users=perms["can_invite_users"],
        can_pin_messages=perms["can_pin_messages"],
    )

    try:
        await client.set_chat_permissions(chat_id, chat_perms)
        return True
    except Exception as e:
        print(f"Failed to set permissions: {e}")
        return False


# =========================================================
# LOCK
# =========================================================

@Client.on_message(filters.command("lock") & filters.group)
async def lock_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")

    if len(message.command) < 2:
        return await message.reply_text(
            "📝 Usage: /lock <type1> [type2...]\n"
            "See: /locktypes"
        )

    raw = message.text.split(None, 1)[1]
    reason = ""
    custom_action = ""

    if "###" in raw:
        types_part, rest = raw.split("###", 1)
        rest = rest.strip()
        action_match = re.search(r"\{(\w+)\}", rest)
        if action_match:
            custom_action = action_match.group(1).lower()
            rest = rest.replace(action_match.group(0), "").strip()
        reason = rest
    else:
        types_part = raw

    types = [t.strip().lower() for t in types_part.split() if t.strip()]

    invalid = [t for t in types if t not in LOCK_TYPES]
    if invalid:
        return await message.reply_text(f"❌ Invalid types: {', '.join(invalid)}")

    # Special: reset all custom actions
    if "all" in types and not reason and not custom_action and "###" in raw:
        for t in LOCK_TYPES:
            await db.set_chat_field(message.chat.id, f"lock_reason_{t}", None)
            await db.set_chat_field(message.chat.id, f"lock_action_{t}", None)
        return await message.reply_text("✅ All custom lock actions reset.")

    for t in types:
        await db.set_lock(message.chat.id, t, True)
        if reason:
            await db.set_chat_field(message.chat.id, f"lock_reason_{t}", reason)
        if custom_action:
            await db.set_chat_field(message.chat.id, f"lock_action_{t}", custom_action)

    # Apply native permissions
    locks = await db.get_locks(message.chat.id)
    applied = await apply_group_permissions(client, message.chat.id, locks)

    txt = f"🔒 Locked: <code>{', '.join(types)}</code>"
    if reason:
        txt += f"\n📝 {reason}"
    if custom_action:
        txt += f"\n⚡ Action: {custom_action}"

    # Inform about native vs text locks
    native_types = [t for t in types if t in NATIVE_LOCKS]
    text_types = [t for t in types if t in TEXT_LOCKS and t != "all"]

    if native_types and not applied:
        txt += f"\n\n⚠️ <i>Could not update group permissions. Check bot admin rights.</i>"
    elif native_types:
        txt += f"\n\n✅ <i>Group permissions updated for: {', '.join(native_types)}</i>"
    if text_types:
        txt += f"\n\n🗑️ <i>Messages will be deleted for: {', '.join(text_types)}</i>"

    await message.reply_text(txt)


# =========================================================
# UNLOCK
# =========================================================

@Client.on_message(filters.command("unlock") & filters.group)
async def unlock_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")

    if len(message.command) < 2:
        return await message.reply_text("📝 Usage: /unlock <type1> [type2...]")

    types = [t.strip().lower() for t in message.command[1:] if t.strip()]
    invalid = [t for t in types if t not in LOCK_TYPES]
    if invalid:
        return await message.reply_text(f"❌ Invalid types: {', '.join(invalid)}")

    for t in types:
        await db.set_lock(message.chat.id, t, False)

    # Reapply native permissions
    locks = await db.get_locks(message.chat.id)
    await apply_group_permissions(client, message.chat.id, locks)

    await message.reply_text(f"🔓 Unlocked: <code>{', '.join(types)}</code>")


# =========================================================
# LIST LOCKS
# =========================================================

@Client.on_message(filters.command("locks") & filters.group)
async def locks_cmd(client, message):
    doc = await db.get_locks(message.chat.id)
    active = [k for k, v in doc.items()
              if k not in ("_id", "chat_id") and v is True]
    if not active:
        return await message.reply_text("🔓 No active locks.")

    native = [x for x in active if x in NATIVE_LOCKS]
    text = [x for x in active if x in TEXT_LOCKS]

    txt = "🔒 <b>Active Locks:</b>\n\n"
    if native:
        txt += f"<b>Group Permissions:</b>\n"
        txt += ", ".join(f"<code>{x}</code>" for x in native) + "\n\n"
    if text:
        txt += f"<b>Message Delete:</b>\n"
        txt += ", ".join(f"<code>{x}</code>" for x in text)

    await message.reply_text(txt)


# =========================================================
# LOCK TYPES
# =========================================================

@Client.on_message(filters.command("locktypes"))
async def locktypes_cmd(client, message):
    txt = "<b>🔒 Lock Types</b>\n\n"
    txt += "<b>🛡️ Group Permission Locks:</b>\n"
    txt += ", ".join(f"<code>{t}</code>" for t in sorted(NATIVE_LOCKS.keys())) + "\n\n"
    txt += "<b>🗑️ Message Delete Locks:</b>\n"
    txt += ", ".join(f"<code>{t}</code>" for t in sorted(TEXT_LOCKS))
    await message.reply_text(txt)


# =========================================================
# LOCK WARNS
# =========================================================

@Client.on_message(filters.command("lockwarns") & filters.group)
async def lockwarns_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    if len(message.command) < 2 or message.command[1].lower() not in (
        "yes", "no", "on", "off"
    ):
        chat = await db.get_chat(message.chat.id)
        state = chat.get("lock_warns", False)
        return await message.reply_text(
            f"📋 <b>Lock Warns:</b> {'ON' if state else 'OFF'}\n"
            f"Usage: /lockwarns yes|no"
        )
    state = message.command[1].lower() in ("yes", "on")
    await db.set_chat_field(message.chat.id, "lock_warns", state)
    await message.reply_text(f"✅ Lock warns: {'ON' if state else 'OFF'}")


# =========================================================
# ALLOWLIST
# =========================================================

@Client.on_message(filters.command("allowlist") & filters.group)
async def allowlist_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")

    if len(message.command) < 2:
        lines = ["<b>✅ Allowlist:</b>\n"]
        count = 0
        async for d in db.get_allows(message.chat.id):
            count += 1
            lines.append(f"• <code>{d['value']}</code>")
        if count == 0:
            lines.append("<i>Empty</i>")
        return await message.reply_text("\n".join(lines))

    added = []
    for val in message.command[1:]:
        await db.add_allow(message.chat.id, val.lower())
        added.append(val)
    await message.reply_text(f"✅ Allowlisted: {', '.join(added)}")


@Client.on_message(filters.command("rmallowlist") & filters.group)
async def rmallowlist_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    if len(message.command) < 2:
        return await message.reply_text("Usage: /rmallowlist <item>")
    removed = []
    for val in message.command[1:]:
        await db.remove_allow(message.chat.id, val.lower())
        removed.append(val)
    await message.reply_text(f"🗑️ Removed: {', '.join(removed)}")


@Client.on_message(filters.command("rmallowlistall") & filters.group)
async def rmallowlistall_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    await db.clear_allows(message.chat.id)
    await message.reply_text("🗑️ Allowlist cleared.")


# =========================================================
# APPLY CUSTOM LOCK ACTION
# =========================================================

async def apply_lock_action(client, message, action, reason):
    if not message.from_user:
        return
    uid = message.from_user.id
    try:
        if action == "warn":
            await db.add_warn(message.chat.id, uid, reason or "Locked content")
        elif action == "mute":
            await client.restrict_chat_member(
                message.chat.id, uid,
                ChatPermissions(can_send_messages=False)
            )
            await db.mute_user(message.chat.id, uid, 0, "lock")
        elif action == "ban":
            await client.ban_chat_member(message.chat.id, uid)
        elif action == "kick":
            await client.ban_chat_member(message.chat.id, uid)
            await client.unban_chat_member(message.chat.id, uid)
    except Exception:
        pass


# =========================================================
# LOCK WATCHER — Only for NON-native locks
# =========================================================

@Client.on_message(filters.group & ~filters.service, group=40)
async def lock_watcher(client, message):
    chat = await db.get_chat(message.chat.id)
    locks = await db.get_locks(message.chat.id)

    if message.from_user:
        if await is_admin(client, message.chat.id, message.from_user.id):
            return
        if await db.is_approved(message.chat.id, message.from_user.id):
            return

    allows = [d["value"] async for d in db.get_allows(message.chat.id)]
    text = (message.text or message.caption or "")
    text_lower = text.lower()

    def locked(key):
        return locks.get(key, False)

    def is_allowed():
        return any(a in text_lower for a in allows)

    matched_type = None

    # ===== NON-NATIVE LOCKS (message delete) =====

    # all / text
    if locked("all"):
        matched_type = "all"
    elif locked("text") and (message.text or message.caption):
        matched_type = "text"

    # Forward
    if not matched_type:
        if locked("forward") and message.forward_date:
            matched_type = "forward"
        elif locked("forwarduser") and message.forward_from:
            matched_type = "forwarduser"
        elif locked("forwardchannel") and message.forward_from_chat:
            matched_type = "forwardchannel"
        elif locked("forwardbot") and message.forward_from and message.forward_from.is_bot:
            matched_type = "forwardbot"

    # Bot messages
    if not matched_type:
        if locked("bot") and message.from_user and message.from_user.is_bot:
            matched_type = "bot"
        if locked("guestbot") and message.via_bot:
            matched_type = "guestbot"

    # Patterns
    if not matched_type and text:
        if locked("email") and re.search(r"\S+@\S+\.\S+", text):
            matched_type = "email"
        elif locked("phone") and re.search(r"\+?\d{10,}", text):
            matched_type = "phone"
        elif locked("cashtag") and re.search(r"\$[A-Z]{2,}", text):
            matched_type = "cashtag"
        elif locked("url") and re.search(r"(https?://|www\.)", text_lower):
            if not is_allowed():
                matched_type = "url"
        elif locked("invitelink") and re.search(r"(t\.me/|telegram\.me/)", text_lower):
            if not is_allowed():
                matched_type = "invitelink"
        elif locked("botlink") and re.search(r"@\w*bot\b", text_lower):
            matched_type = "botlink"
        elif locked("command") and text_lower.startswith("/"):
            if not is_allowed():
                matched_type = "command"

    # Emoji
    if not matched_type and text:
        if locked("emojionly"):
            stripped = re.sub(r"[\U0001F300-\U0001F9FF\U0001F600-\U0001F64F]", "", text).strip()
            if not stripped and len(text) > 0:
                matched_type = "emojionly"
        if locked("emojicustom") and message.entities:
            for ent in message.entities:
                if str(ent.type) == "MessageEntityType.CUSTOM_EMOJI":
                    matched_type = "emojicustom"
                    break

    # Language / script
    if not matched_type and text:
        if locked("rtl") and re.search(r"[\u0590-\u08FF]", text):
            matched_type = "rtl"
        elif locked("cjk") and re.search(r"[\u4E00-\u9FFF\u3040-\u30FF\uAC00-\uD7AF]", text):
            matched_type = "cjk"
        elif locked("cyrillic") and re.search(r"[\u0400-\u04FF]", text):
            matched_type = "cyrillic"
        elif locked("zalgo") and re.search(r"[\u0300-\u036F]{3,}", text):
            matched_type = "zalgo"

    # Others
    if not matched_type:
        if locked("contact") and message.contact:
            matched_type = "contact"
        elif locked("location") and message.location:
            matched_type = "location"
        elif locked("spoiler") and message.entities:
            for e in message.entities:
                if str(e.type) == "MessageEntityType.SPOILER":
                    matched_type = "spoiler"
                    break
        elif locked("button") and message.reply_markup:
            matched_type = "button"

    if not matched_type:
        return

    # Delete
    try:
        await message.delete()
    except Exception:
        pass

    # Custom action
    action = chat.get(f"lock_action_{matched_type}") or chat.get("lock_action_all")
    reason = chat.get(f"lock_reason_{matched_type}") or chat.get("lock_reason_all")

    if action:
        await apply_lock_action(client, message, action, reason)
    elif chat.get("lock_warns", False) and message.from_user:
        try:
            await message.reply_text(
                f"⚠️ {message.from_user.mention}, that item is locked: <code>{matched_type}</code>"
            )
        except Exception:
            pass
