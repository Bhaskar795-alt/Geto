import re
import random
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def parse_buttons(text):
    """Rose-style button parser."""
    if not text:
        return "", None

    pattern = r"\[([^\]]+)\]\(buttonurl(#[a-z]+)?://([^\)]+?)(:same)?\)"
    rows = []
    current_row = []

    for m in re.finditer(pattern, text):
        label = m.group(1)
        url = m.group(3)
        same = m.group(4)

        if url.startswith("#"):
            url = f"https://t.me/YourBotUsername?start=note_{url[1:]}"

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


def replace_fillings(text, user=None, chat=None, count=0, rules="", extra=None):
    from datetime import datetime
    if not text:
        return ""

    if "%%%" in text:
        parts = [p.strip() for p in text.split("%%%") if p.strip()]
        text = random.choice(parts) if parts else text

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

    if extra:
        for k, v in extra.items():
            text = text.replace("{" + k + "}", str(v))

    return text


def check_permissions(text, is_admin_user=False, is_bot=False):
    if "{admin}" in text and not is_admin_user:
        return False
    if "{user}" in text and is_admin_user:
        return False
    if "{allow_bot}" in text and not is_bot:
        return False
    return True


def clean_permission_tags(text):
    return text.replace("{admin}", "").replace("{user}", "").replace("{allow_bot}", "").strip()
