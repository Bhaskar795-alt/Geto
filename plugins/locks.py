import re
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

    # Handle "all ###" reset
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

    txt = f"🔒 Locked: <code>{', '.join(types)}</code>"
    if reason:
        txt += f"\n📝 {reason}"
    if custom_action:
        txt += f"\n⚡ Action: {custom_action}"
    await message.reply_text(txt)


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

    args = [a.lower() for a in message.command[1:]] if len(message.command) > 1 else []
    if "list" in args:
        await message.reply_text(
            "🔒 <b>Active Locks:</b>\n\n" +
            "\n".join(f"• <code>{x}</code>" for x in active)
        )
    else:
        await message.reply_text(
            "🔒 <b>Active Locks:</b>\n" +
            ", ".join(f"<code>{x}</code>" for x in active)
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
            await message.reply_text(
                f"⚠️ {message.from_user.mention} warned — {reason or 'Locked content'}"
            )

        elif action == "mute":
            await client.restrict_chat_member(message.chat.id, uid, MUTE_PERMS)
            await db.mute_user(message.chat.id, uid, 0, "lock")
            await message.reply_text(
                f"🔇 {message.from_user.mention} muted — {reason or 'Locked content'}"
            )

        elif action == "ban":
            await client.ban_chat_member(message.chat.id, uid)
            await message.reply_text(
                f"🔨 {message.from_user.mention} banned — {reason or 'Locked content'}"
            )

        elif action == "kick":
            await client.ban_chat_member(message.chat.id, uid)
            await client.unban_chat_member(message.chat.id, uid)
            await message.reply_text(
                f"👢 {message.from_user.mention} kicked — {reason or 'Locked content'}"
            )
    except Exception:
        pass


# =========================================================
# LOCK WATCHER — FULL
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

    def is_allowed_content():
        return any(a in text_lower for a in allows)

    matched_type = None

    # ALL
    if locked("all"):
        matched_type = "all"

    # MEDIA
    if not matched_type:
        if locked("photo") and message.photo:
            matched_type = "photo"
        elif locked("video") and message.video:
            matched_type = "video"
        elif locked("audio") and message.audio:
            matched_type = "audio"
        elif locked("voice") and message.voice:
            matched_type = "voice"
        elif locked("document") and message.document:
            matched_type = "document"
        elif locked("gif") and message.animation:
            matched_type = "gif"
        elif locked("sticker") and message.sticker:
            pack = message.sticker.set_name
            if pack and f"stickerpack:{pack.lower()}" in allows:
                pass
            else:
                matched_type = "sticker"
        elif locked("stickeranimated") and message.sticker and message.sticker.is_animated:
            matched_type = "stickeranimated"
        elif locked("stickerpremium") and message.sticker and getattr(message.sticker, "is_premium", False):
            matched_type = "stickerpremium"
        elif locked("videonote") and message.video_note:
            matched_type = "videonote"
        elif locked("contact") and message.contact:
            matched_type = "contact"
        elif locked("location") and message.location:
            matched_type = "location"
        elif locked("poll") and message.poll:
            matched_type = "poll"
        elif locked("album") and message.media_group_id:
            matched_type = "album"

    # TEXT
    if not matched_type and text:
        if locked("email") and re.search(r"\S+@\S+\.\S+", text):
            matched_type = "email"
        elif locked("phone") and re.search(r"\+?\d{10,}", text):
            matched_type = "phone"
        elif locked("cashtag") and re.search(r"\$[A-Z]{2,}", text):
            matched_type = "cashtag"
        elif locked("url") and re.search(r"(https?://|www\.)", text_lower):
            if not is_allowed_content():
                matched_type = "url"
        elif locked("invitelink") and re.search(r"(t\.me/|telegram\.me/)", text_lower):
            if not is_allowed_content():
                matched_type = "invitelink"
        elif locked("botlink") and re.search(r"@\w*bot\b", text_lower):
            matched_type = "botlink"
        elif locked("command") and text_lower.startswith("/"):
            if not is_allowed_content():
                matched_type = "command"
        elif locked("text"):
            matched_type = "text"
        elif locked("spoiler") and message.entities:
            for e in message.entities:
                if str(e.type) == "MessageEntityType.SPOILER":
                    matched_type = "spoiler"
                    break

    # EMOJI
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

    # FORWARD
    if not matched_type:
        if locked("forward") and message.forward_date:
            matched_type = "forward"
        elif locked("forwarduser") and message.forward_from:
            matched_type = "forwarduser"
        elif locked("forwardchannel") and message.forward_from_chat:
            matched_type = "forwardchannel"

    # BOT
    if not matched_type:
        if locked("bot") and message.from_user and message.from_user.is_bot:
            matched_type = "bot"
        if locked("inline") and message.via_bot:
            matched_type = "inline"
        if locked("guestbot") and message.via_bot:
            matched_type = "guestbot"

    # BUTTON
    if not matched_type and locked("button") and message.reply_markup:
        matched_type = "button"

    # RTL / CJK / CYRILLIC
    if not matched_type and text:
        if locked("rtl") and re.search(r"[\u0590-\u08FF]", text):
            matched_type = "rtl"
        elif locked("cjk") and re.search(r"[\u4E00-\u9FFF\u3040-\u30FF\uAC00-\uD7AF]", text):
            matched_type = "cjk"
        elif locked("cyrillic") and re.search(r"[\u0400-\u04FF]", text):
            matched_type = "cyrillic"
        elif locked("zalgo") and re.search(r"[\u0300-\u036F]{3,}", text):
            matched_type = "zalgo"

    if not matched_type:
        return

    # Delete
    try:
        await message.delete()
    except Exception:
        pass

    # Apply custom action
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
