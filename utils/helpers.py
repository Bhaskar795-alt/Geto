import re
from datetime import datetime
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import Config

DURATION_RE = re.compile(r"^(\d+)([smhdw])$")


def parse_duration(text):
    m = DURATION_RE.match(text.strip().lower())
    if not m:
        return 0
    return int(m.group(1)) * Config.DURATION_MAP[m.group(2)]


def mention_html(user_id, name):
    return f'<a href="tg://user?id={user_id}">{name}</a>'


async def resolve_user(app, message):
    """Resolve user from reply, @username, user ID, or HTML mention."""
    if message.reply_to_message and message.reply_to_message.from_user:
        u = message.reply_to_message.from_user
        return u.id, u.first_name or "User", u.username

    if len(message.command) > 1:
        arg = message.command[1]

        if arg.startswith("@"):
            try:
                u = await app.get_users(arg)
                return u.id, u.first_name or "User", u.username
            except Exception:
                return None, None, None

        if arg.isdigit():
            try:
                u = await app.get_users(int(arg))
                return u.id, u.first_name or "User", u.username
            except Exception:
                return int(arg), f"User {arg}", None

        mention_match = re.search(r"tg://user\?id=(\d+)", arg)
        if mention_match:
            uid = int(mention_match.group(1))
            try:
                u = await app.get_users(uid)
                return u.id, u.first_name or "User", u.username
            except Exception:
                return uid, f"User {uid}", None

    return None, None, None


def build_buttons(button_data):
    if not button_data:
        return None
    rows = []
    for row in button_data:
        rows.append([InlineKeyboardButton(**b) for b in row])
    return InlineKeyboardMarkup(rows)


def format_text(template, user=None, chat=None, count=0, extra=None):
    if not template:
        template = ""
    if user:
        first = user.first_name or ""
        last = user.last_name or ""
        fullname = (first + " " + last).strip() or first
        username = getattr(user, "username", None)
        mention = user.mention if hasattr(user, "mention") else first
        template = (template
            .replace("{first}", first)
            .replace("{last}", last)
            .replace("{fullname}", fullname)
            .replace("{name}", first)
            .replace("{mention}", mention)
            .replace("{id}", str(user.id))
            .replace("{user_id}", str(user.id))
            .replace("{username}", f"@{username}" if username else mention))
    if chat:
        template = (template
            .replace("{chatname}", chat.title or "")
            .replace("{chat_id}", str(chat.id)))
    template = template.replace("{count}", str(count))
    template = template.replace("{members}", str(count))
    now = datetime.now()
    template = (template
        .replace("{date}", now.strftime("%d %b %Y"))
        .replace("{time}", now.strftime("%H:%M:%S")))
    if extra:
        for k, v in extra.items():
            template = template.replace("{" + k + "}", str(v))
    return template
