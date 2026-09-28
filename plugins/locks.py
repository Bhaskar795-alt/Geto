import re
from pyrogram import Client, filters
from database import db
from utils.permissions import is_admin

# =========================================================
# ALL LOCK TYPES
# =========================================================

LOCK_TYPES = [
    "all", "album", "anonchannel", "audio", "bot", "botlink", "button",
    "cashtag", "checklist", "cjk", "collage", "command", "comment",
    "contact", "cyrillic", "document", "email", "emoji", "emojicustom",
    "emojigame", "emojionly", "externalreply", "forward", "forwardbot",
    "forwardchannel", "forwardstory", "forwarduser", "game", "gif",
    "guestbot", "inline", "invitelink", "location", "outsidereaction",
    "phone", "photo", "poll", "reaction", "richmessage", "rtl",
    "slideshow", "spoiler", "sticker", "stickeranimated",
    "stickerpremium", "text", "url", "video", "videonote", "voice", "zalgo",
]


@Client.on_message(filters.command("lock") & filters.group)
async def lock_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")

    if len(message.command) < 2:
        return await message.reply_text(
            "📝 Usage: /lock <type1> [type2...]\n"
            "See: /locktypes"
        )

    # Parse types (before ###)
    raw = message.text.split(None, 1)[1]
    reason = ""
    custom_action = ""

    if "###" in raw:
        types_part, rest = raw.split("###", 1)
        rest = rest.strip()
        # Parse custom action {ban}, {mute}, {kick}, {warn}
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

    for t in types:
        await db.set_lock(message.chat.id, t, True)
        if reason:
            await db.set_chat_field(message.chat.id, f"lock_reason_{t}", reason)
        if custom_action:
            await db.set_chat_field(message.chat.id, f"lock_action_{t}", custom_action)

    await message.reply_text(f"🔒 Locked: <code>{', '.join(types)}</code>")


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

    await message.reply_text(f"🔓 Unlocked: <code>{', '.join(types)}</code>")


@Client.on_message(filters.command("locks") & filters.group)
async def locks_cmd(client, message):
    doc = await db.get_locks(message.chat.id)
    active = [k for k, v in doc.items()
              if k not in ("_id", "chat_id") and v is True]
    if not active:
        return await message.reply_text("🔓 No active locks.")
    await message.reply_text(
        "🔒 <b>Active Locks:</b>\n" + ", ".join(f"<code>{x}</code>" for x in active)
    )


@Client.on_message(filters.command("locktypes"))
async def locktypes_cmd(client, message):
    await message.reply_text(
        "<b>🔒 Available Lock Types:</b>\n\n"
        + ", ".join(f"<code>{t}</code>" for t in LOCK_TYPES)
    )


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
        # Show current
        lines = ["<b>✅ Allowlist:</b>\n"]
        async for d in db.get_allows(message.chat.id):
            lines.append(f"• <code>{d['value']}</code>")
        if len(lines) == 1:
            lines.append("<i>Empty</i>")
        return await message.reply_text("\n".join(lines))

    added = []
    for val in message.command[1:]:
        await db.add_allow(message.chat.id, val.lower())
        added.append(val)
    await message.reply_text(f"✅ Allowlisted: {', '.join(added)}")


@Client.on_message(filters.command("rmallowlist") & filters.group)
async def rmallowed_cmd(client, message):
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
# LOCK WATCHER
# =========================================================

@Client.on_message(filters.group & ~filters.service, group=40)
async def lock_watcher(client, message):
    chat = await db.get_chat(message.chat.id)
    locks = await db.get_locks(message.chat.id)

    # Skip admins & approved
    if message.from_user:
        if await is_admin(client, message.chat.id, message.from_user.id):
            return
        if await db.is_approved(message.chat.id, message.from_user.id):
            return

    # Allowlist check
    allows = [d["value"] async for d in db.get_allows(message.chat.id)]
    text = (message.text or message.caption or "").lower()
    is_allowed = any(a in text for a in allows)

    def locked(key):
        return locks.get(key, False)

    delete = False

    # All types check
    if locked("all"):
        delete = True
    if locked("text") and (message.text or message.caption):
        delete = True
    if locked("photo") and message.photo:
        delete = True
    if locked("video") and message.video:
        delete = True
    if locked("audio") and message.audio:
        delete = True
    if locked("voice") and message.voice:
        delete = True
    if locked("document") and message.document:
        delete = True
    if locked("sticker") and message.sticker:
        delete = True
    if locked("gif") and message.animation:
        delete = True
    if locked("contact") and message.contact:
        delete = True
    if locked("location") and message.location:
        delete = True
    if locked("poll") and message.poll:
        delete = True
    if locked("video") and message.video_note:
        delete = True

    # Forward
    if locked("forward") and message.forward_date:
        delete = True
    if locked("forwarduser") and message.forward_from:
        delete = True
    if locked("forwardchannel") and message.forward_from_chat:
        delete = True

    # Bot
    if locked("bot") and message.from_user and message.from_user.is_bot:
        delete = True

    # Inline
    if locked("inline") and message.via_bot:
        delete = True

    # Command
    if locked("command") and message.text and message.text.startswith("/"):
        delete = True

    # URL
    if locked("url") and not is_allowed:
        if message.text and ("http://" in message.text or "https://" in message.text):
            delete = True
        if message.caption and ("http://" in message.caption or "https://" in message.caption):
            delete = True

    # Invite link
    if locked("invitelink") and not is_allowed:
        if message.text and ("t.me/" in message.text or "telegram.me/" in message.text):
            delete = True
        if message.caption and ("t.me/" in message.caption or "telegram.me/" in message.caption):
            delete = True

    # Emoji only
    if locked("emojionly") and message.text:
        # Check if only emoji
        stripped = re.sub(r"[\U0001F300-\U0001F9FF]", "", message.text).strip()
        if not stripped and len(message.text) > 0:
            delete = True

    if not delete:
        return

    try:
        await message.delete()
    except Exception:
        pass

    # Warn if enabled
    lock_warns = chat.get("lock_warns", False)
    if lock_warns and message.from_user:
        try:
            await message.reply_text(
                f"⚠️ {message.from_user.mention}, that item is locked in this chat."
            )
        except Exception:
            pass
