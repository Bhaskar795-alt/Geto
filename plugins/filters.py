import re
import random
from pyrogram import Client, filters
from database import db
from utils.permissions import is_admin
from utils.formatting import (
    parse_buttons, replace_fillings, check_permissions, clean_permission_tags
)


def parse_triggers(raw):
    raw = raw.strip()
    mode = "word"
    if raw.startswith('"exact:') or raw.startswith("'exact:"):
        return [raw[7:-1].lower()], "exact"
    if raw.startswith('"prefix:') or raw.startswith("'prefix:"):
        return [raw[8:-1].lower()], "prefix"
    if raw.startswith('"') and raw.endswith('"'):
        return [raw[1:-1].lower()], "phrase"
    if raw.startswith("(") and raw.endswith(")"):
        inner = raw[1:-1]
        parts = [p.strip().strip('"').strip("'").lower() for p in inner.split(",")]
        return [p for p in parts if p], "word"
    return [raw.lower()], "word"


@Client.on_message(filters.command("filter") & filters.group)
async def add_filter(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    if len(message.command) < 2:
        return await message.reply_text(
            "📝 <b>Usage:</b>\n/filter &lt;trigger&gt; (reply to a message)\n"
            "Or: /filter &lt;trigger&gt; &lt;text&gt;"
        )

    raw_text = message.text.split(None, 1)[1]
    trigger_match = re.match(r'("[^"]+"|\([^)]+\)|\S+)', raw_text)
    if not trigger_match:
        return await message.reply_text("❌ Invalid trigger.")
    raw_trigger = trigger_match.group(1)
    triggers, mode = parse_triggers(raw_trigger)
    if not triggers:
        return await message.reply_text("❌ Invalid trigger.")
    keyword = triggers[0]

    if message.reply_to_message:
        r = message.reply_to_message
        text = r.caption or r.text or ""
        msg_type, file_id = "text", ""
        if r.photo:
            msg_type, file_id = "photo", r.photo.file_id
        elif r.video:
            msg_type, file_id = "video", r.video.file_id
        elif r.sticker:
            msg_type, file_id = "sticker", r.sticker.file_id
        elif r.document:
            msg_type, file_id = "document", r.document.file_id
        elif r.animation:
            msg_type, file_id = "animation", r.animation.file_id
    else:
        rest = raw_text[len(raw_trigger):].strip()
        text = rest
        msg_type, file_id = "text", ""

    await db.save_filter(message.chat.id, keyword, text, msg_type, file_id)
    await db.set_chat_field(message.chat.id, f"filter_mode_{keyword}", mode)
    await db.set_chat_field(message.chat.id, f"filter_triggers_{keyword}", triggers)
    await message.reply_text(f"✅ Filter saved: <code>{keyword}</code> (mode: {mode})")


@Client.on_message(filters.command("stop") & filters.group)
async def stop_filter(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    if len(message.command) < 2:
        return await message.reply_text("Usage: /stop <keyword>")
    await db.delete_filter(message.chat.id, message.command[1])
    await message.reply_text(f"🗑️ Removed: <code>{message.command[1]}</code>")


@Client.on_message(filters.command("stopall") & filters.group)
async def stopall_filter(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    await db.delete_all_filters(message.chat.id)
    await message.reply_text("🗑️ All filters removed.")


@Client.on_message(filters.command("filters") & filters.group)
async def list_filters(client, message):
    keys = []
    async for d in db.get_all_filters(message.chat.id):
        keys.append(f"• <code>{d['keyword']}</code>")
    if not keys:
        return await message.reply_text("No filters.")
    await message.reply_text("<b>🔥 Filters:</b>\n" + "\n".join(keys))


@Client.on_message(filters.group & ~filters.service, group=5)
async def filter_watcher(client, message):
    if not message.text and not message.caption:
        return

    text = (message.text or message.caption).lower()
    chat = await db.get_chat(message.chat.id)
    rules_text = chat.get("rules") or "No rules."

    async for fdoc in db.get_all_filters(message.chat.id):
        keyword = fdoc["keyword"]
        mode = chat.get(f"filter_mode_{keyword}", "word")
        triggers = chat.get(f"filter_triggers_{keyword}", [keyword])

        matched = False
        for t in triggers:
            if mode == "exact":
                if text.strip() == t:
                    matched = True
            elif mode == "prefix":
                if text.startswith(t):
                    matched = True
            elif mode == "phrase":
                if t in text:
                    matched = True
            else:
                if t in text.split():
                    matched = True
            if matched:
                break

        if not matched:
            continue

        reply = fdoc.get("reply") or ""
        is_bot = message.from_user.is_bot if message.from_user else False
        is_admin_user = await is_admin(client, message.chat.id,
                                        message.from_user.id) if message.from_user else False

        if not check_permissions(reply, is_admin_user, is_bot):
            continue

        reply = clean_permission_tags(reply)

        if "%%%" in reply:
            parts = [p.strip() for p in reply.split("%%%") if p.strip()]
            reply = random.choice(parts) if parts else ""

        reply = replace_fillings(reply, user=message.from_user,
                                 chat=message.chat, count=0, rules=rules_text)

        clean, markup = parse_buttons(reply)

        try:
            if fdoc["msg_type"] == "text":
                await message.reply_text(clean or "…", reply_markup=markup)
            elif fdoc["msg_type"] == "photo":
                await message.reply_photo(fdoc["file_id"], caption=clean or "", reply_markup=markup)
            elif fdoc["msg_type"] == "video":
                await message.reply_video(fdoc["file_id"], caption=clean or "", reply_markup=markup)
            elif fdoc["msg_type"] == "sticker":
                await message.reply_sticker(fdoc["file_id"])
                if clean:
                    await message.reply_text(clean, reply_markup=markup)
            elif fdoc["msg_type"] == "document":
                await message.reply_document(fdoc["file_id"], caption=clean or "", reply_markup=markup)
            elif fdoc["msg_type"] == "animation":
                await message.reply_animation(fdoc["file_id"], caption=clean or "", reply_markup=markup)
        except Exception:
            try:
                await message.reply_text(clean or "…", reply_markup=markup)
            except Exception:
                pass
        break
