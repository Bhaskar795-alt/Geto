import re
import random
import logging
import aiohttp
from html import escape
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import Config

log = logging.getLogger("GETO")


# =========================================================
# TELEGRAM API
# =========================================================

async def _send_telegram_api(endpoint, payload):
    url = f"https://api.telegram.org/bot{Config.BOT_TOKEN}/{endpoint}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=15) as resp:
                result = await resp.json()
                if not result.get("ok"):
                    log.error(f"[API ERROR] {endpoint}: {result.get('description', 'unknown')}")
                return result
    except Exception as e:
        log.error(f"[API EXCEPTION] {endpoint}: {e}")
        return {"ok": False, "description": str(e)}


# =========================================================
# COLORED BUTTONS
# =========================================================

def _parse_button_rows(buttons_text):
    pattern = r"\[([^\]]+)\]\(buttonurl(?:#(\w+))?://([^\)]+?)(?::same)?\)"
    rows = []
    current_row = []

    for m in re.finditer(pattern, buttons_text or ""):
        label = m.group(1)
        style = m.group(2)
        url = m.group(3)
        same = ":same" in m.group(0)

        btn = {"text": label, "url": url}
        if style and style in ("primary", "danger", "success"):
            btn["style"] = style

        if same and current_row:
            current_row.append(btn)
        else:
            if current_row:
                rows.append(current_row)
            current_row = [btn]

    if current_row:
        rows.append(current_row)
    return rows


def _clean_text(text):
    pattern = r"\[([^\]]+)\]\(buttonurl(?:#(\w+))?://([^\)]+?)(?::same)?\)"
    clean = re.sub(pattern, "", text or "")
    clean = "\n".join(line for line in clean.split("\n") if line.strip())
    return clean


async def _send_with_fallback(endpoint, payload, rows):
    """Try multiple combinations of style/parse_mode."""

    # Try 1: with style + parse_mode
    result = await _send_telegram_api(endpoint, payload)
    if result and result.get("ok"):
        log.info(f"[COLORED] Sent with style ✅")
        return result

    # Try 2: without style + parse_mode
    for row in rows:
        for btn in row:
            btn.pop("style", None)
    payload["reply_markup"] = {"inline_keyboard": rows}
    result = await _send_telegram_api(endpoint, payload)
    if result and result.get("ok"):
        log.info("[COLORED] Sent without style ✅")
        return result

    # Try 3: no parse_mode
    payload.pop("parse_mode", None)
    result = await _send_telegram_api(endpoint, payload)
    if result and result.get("ok"):
        log.info("[COLORED] Sent as plain text ✅")
        return result

    log.error(f"[COLORED] All attempts failed: {result}")
    return result


async def send_with_colored_buttons(
    chat_id, text, buttons_text,
    parse_mode="HTML", reply_to_message_id=None
):
    rows = _parse_button_rows(buttons_text)
    clean = _clean_text(text)

    payload = {
        "chat_id": chat_id,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    }
    # Only add text if not empty
    if clean:
        payload["text"] = clean
    else:
        payload["text"] = " "  # space (Telegram requires non-empty)

    if rows:
        payload["reply_markup"] = {"inline_keyboard": rows}
    if reply_to_message_id:
        payload["reply_to_message_id"] = reply_to_message_id

    log.info(f"[COLORED] Sending text: {clean[:80]}...")
    return await _send_with_fallback("sendMessage", payload, rows)


async def send_photo_with_colored_buttons(
    chat_id, file_id, caption, buttons_text,
    parse_mode="HTML", reply_to_message_id=None
):
    rows = _parse_button_rows(buttons_text)
    clean = _clean_text(caption)

    payload = {
        "chat_id": chat_id,
        "photo": file_id,
        "parse_mode": parse_mode,
    }
    # Only add caption if not empty (no "..." placeholder)
    if clean:
        payload["caption"] = clean

    if rows:
        payload["reply_markup"] = {"inline_keyboard": rows}
    if reply_to_message_id:
        payload["reply_to_message_id"] = reply_to_message_id

    log.info(f"[COLORED PHOTO] Sending. Caption: {clean[:80]}...")
    return await _send_with_fallback("sendPhoto", payload, rows)


async def send_video_with_colored_buttons(
    chat_id, file_id, caption, buttons_text,
    parse_mode="HTML", reply_to_message_id=None
):
    rows = _parse_button_rows(buttons_text)
    clean = _clean_text(caption)

    payload = {
        "chat_id": chat_id,
        "video": file_id,
        "parse_mode": parse_mode,
    }
    if clean:
        payload["caption"] = clean

    if rows:
        payload["reply_markup"] = {"inline_keyboard": rows}
    if reply_to_message_id:
        payload["reply_to_message_id"] = reply_to_message_id

    log.info(f"[COLORED VIDEO] Sending. Caption: {clean[:80]}...")
    return await _send_with_fallback("sendVideo", payload, rows)


# =========================================================
# PARSER
# =========================================================

def parse_buttons(text, bot_username="GetoBot"):
    if not text:
        return "", None
    pattern = r"\[([^\]]+)\]\(buttonurl(#[a-z]+)?://([^\)]+?)(:same)?\)"
    rows = []
    current_row = []
    for m in re.finditer(pattern, text):
        label = m.group(1)
        style = m.group(2)
        url = m.group(3)
        same = m.group(4)
        if url.startswith("#"):
            url = f"https://t.me/{bot_username}?start=note_{url[1:]}"
        try:
            if style:
                btn = InlineKeyboardButton(label, url=url, style=style[1:])
            else:
                btn = InlineKeyboardButton(label, url=url)
        except Exception:
            btn = InlineKeyboardButton(label, url=url)
        if same and current_row:
            current_row.append(btn)
        else:
            if current_row:
                rows.append(current_row)
            current_row = [btn]
    if current_row:
        rows.append(current_row)
    clean = re.sub(pattern, "", text)
    clean = "\n".join(line for line in clean.split("\n") if line.strip())
    if not rows:
        return clean.strip(), None
    return clean.strip(), InlineKeyboardMarkup(rows)


# =========================================================
# FILLINGS — With HTML ESCAPE
# =========================================================

def replace_fillings(text, user=None, chat=None, count=0,
                     rules="", rules_button=False, extra=None):
    from datetime import datetime
    if not text:
        return ""

    if "%%%" in text:
        parts = [p.strip() for p in text.split("%%%") if p.strip()]
        if parts:
            text = random.choice(parts)

    if user:
        first = escape(user.first_name or "")
        last = escape(user.last_name or "")
        fullname = (first + " " + last).strip() or first
        username = getattr(user, "username", None)
        mention = f'<a href="tg://user?id={user.id}">{first}</a>'
        text = (text
            .replace("{first}", first)
            .replace("{last}", last)
            .replace("{fullname}", fullname)
            .replace("{name}", first)
            .replace("{mention}", mention)
            .replace("{id}", str(user.id))
            .replace("{user_id}", str(user.id))
            .replace("{username}", f"@{username}" if username else mention))

    if chat:
        safe_title = escape(chat.title or "")
        text = (text
            .replace("{chatname}", safe_title)
            .replace("{chat_id}", str(chat.id)))

    text = (text
        .replace("{count}", str(count))
        .replace("{members}", str(count))
        .replace("{rules}", rules or "No rules"))

    now = datetime.now()
    text = (text
        .replace("{date}", now.strftime("%d %b %Y"))
        .replace("{time}", now.strftime("%H:%M:%S")))

    if rules_button and "{rules}" in text:
        text = text.replace("{rules}", "")

    if extra:
        for k, v in extra.items():
            text = text.replace("{" + k + "}", str(v))

    return text


# =========================================================
# PERMISSIONS
# =========================================================

def check_permissions(text, is_admin_user=False, is_bot=False):
    if "{admin}" in text and not is_admin_user:
        return False
    if "{user}" in text and is_admin_user:
        return False
    if "{allow_bot}" in text and not is_bot:
        return False
    return True


def clean_permission_tags(text):
    return (text
        .replace("{admin}", "")
        .replace("{user}", "")
        .replace("{allow_bot}", "")
        .strip())


# =========================================================
# MARKDOWN
# =========================================================

def convert_markdown(text):
    if not text:
        return text
    text = re.sub(r"```(\w+)?\n(.*?)```",
                  lambda m: f"<pre>{m.group(2)}</pre>",
                  text, flags=re.DOTALL)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\|\|(.+?)\|\|", r"<tg-spoiler>\1</tg-spoiler>", text)
    text = re.sub(r"__(.+?)__", r"<u>\1</u>", text)
    text = re.sub(r"(?<!_)_([^_]+)_(?!_)", r"<i>\1</i>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<b>\1</b>", text)
    text = re.sub(r"~([^~]+)~", r"<s>\1</s>", text)
    text = re.sub(r"\[([^\]]+)\]\((?!#|buttonurl)([^\)]+)\)",
                  r'<a href="\2">\1</a>', text)
    return text


# =========================================================
# FULL PIPELINE
# =========================================================

def format_message(text, user=None, chat=None, count=0,
                   rules="", is_admin_user=False, is_bot=False,
                   bot_username="GetoBot"):
    if not text:
        return "", None
    if not check_permissions(text, is_admin_user, is_bot):
        return None, None
    text = clean_permission_tags(text)
    text = replace_fillings(text, user=user, chat=chat, count=count, rules=rules)
    clean, markup = parse_buttons(text, bot_username)
    clean = convert_markdown(clean)
    return clean, markup
