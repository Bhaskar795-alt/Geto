import re
import random
import aiohttp
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import Config


# =========================================================
# COLORED BUTTONS — Async (using aiohttp)
# =========================================================

async def send_with_colored_buttons(
    chat_id, text, buttons_text,
    parse_mode="HTML", reply_to_message_id=None
):
    """Send message with colored buttons."""
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

    clean = re.sub(pattern, "", text or "")
    clean = "\n".join(line for line in clean.split("\n") if line.strip())

    url_api = f"https://api.telegram.org/bot{Config.BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": clean or "…",
        "parse_mode": parse_mode,
    }
    if rows:
        payload["reply_markup"] = {"inline_keyboard": rows}
    if reply_to_message_id:
        payload["reply_to_message_id"] = reply_to_message_id

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url_api, json=payload, timeout=10) as resp:
                return await resp.json()
    except Exception as e:
        print(f"[COLORED] {e}")
        return None


async def send_photo_with_colored_buttons(
    chat_id, file_id, caption, buttons_text,
    parse_mode="HTML", reply_to_message_id=None
):
    """Send photo with colored buttons."""
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

    clean = re.sub(pattern, "", caption or "")
    clean = "\n".join(line for line in clean.split("\n") if line.strip())

    url_api = f"https://api.telegram.org/bot{Config.BOT_TOKEN}/sendPhoto"
    payload = {
        "chat_id": chat_id,
        "photo": file_id,
        "caption": clean or "…",
        "parse_mode": parse_mode,
    }
    if rows:
        payload["reply_markup"] = {"inline_keyboard": rows}
    if reply_to_message_id:
        payload["reply_to_message_id"] = reply_to_message_id

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url_api, json=payload, timeout=10) as resp:
                return await resp.json()
    except Exception as e:
        print(f"[COLORED PHOTO] {e}")
        return None


async def send_video_with_colored_buttons(
    chat_id, file_id, caption, buttons_text,
    parse_mode="HTML", reply_to_message_id=None
):
    """Send video with colored buttons."""
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

    clean = re.sub(pattern, "", caption or "")
    clean = "\n".join(line for line in clean.split("\n") if line.strip())

    url_api = f"https://api.telegram.org/bot{Config.BOT_TOKEN}/sendVideo"
    payload = {
        "chat_id": chat_id,
        "video": file_id,
        "caption": clean or "…",
        "parse_mode": parse_mode,
    }
    if rows:
        payload["reply_markup"] = {"inline_keyboard": rows}
    if reply_to_message_id:
        payload["reply_to_message_id"] = reply_to_message_id

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url_api, json=payload, timeout=10) as resp:
                return await resp.json()
    except Exception as e:
        print(f"[COLORED VIDEO] {e}")
        return None


# =========================================================
# PARSER (Pyrogram)
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


def parse_buttons_with_style(text, bot_username="GetoBot"):
    if not text:
        return "", []
    pattern = r"\[([^\]]+)\]\(buttonurl(?:#(\w+))?://([^\)]+?)(?::same)?\)"
    rows = []
    current_row = []
    for m in re.finditer(pattern, text):
        label = m.group(1)
        style = m.group(2)
        url = m.group(3)
        same = ":same" in m.group(0)
        if url.startswith("#"):
            url = f"https://t.me/{bot_username}?start=note_{url[1:]}"
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
    clean = re.sub(pattern, "", text)
    clean = "\n".join(line for line in clean.split("\n") if line.strip())
    return clean.strip(), rows


# =========================================================
# FILLINGS
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
        first = user.first_name or ""
        last = user.last_name or ""
        fullname = (first + " " + last).strip() or first
        username = getattr(user, "username", None)
        mention = user.mention if hasattr(user, "mention") else first
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
        text = (text
            .replace("{chatname}", chat.title or "")
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
