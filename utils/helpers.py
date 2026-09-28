import re
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from config import Config

DURATION_RE = re.compile(r"^(\d+)([smhdw])$")


def parse_duration(text):
    m = DURATION_RE.match(text.strip().lower())
    if not m: return 0
    return int(m.group(1)) * Config.DURATION_MAP[m.group(2)]


def mention_html(user_id, name):
    return f'<a href="tg://user?id={user_id}">{name}</a>'


async def resolve_user(app, message: Message):
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
    return None, None, None


def build_buttons(button_data):
    if not button_data: return None
    rows = []
    for row in button_data:
        rows.append([InlineKeyboardButton(**b) for b in row])
    return InlineKeyboardMarkup(rows)


def parse_buttons_from_text(text):
    """Parse [Label](buttonurl://link) style buttons."""
    pattern = r"\[([^\]]+)\]\(buttonurl://([^\)]+)\)"
    matches = re.findall(pattern, text)
    if not matches: return None, text
    rows = [[InlineKeyboardButton(label, url=url)] for label, url in matches]
    clean = re.sub(pattern, "", text).strip()
    return InlineKeyboardMarkup(rows), clean


def format_text(template, user=None, chat=None, count=0, extra=None):
    if user:
        template = (template
            .replace("{name}", user.first_name or "")
            .replace("{username}", f"@{user.username}" if getattr(user, "username", None) else "")
            .replace("{mention}", user.mention if hasattr(user, "mention") else "")
            .replace("{user_id}", str(user.id)))
    if chat:
        template = (template
            .replace("{chatname}", chat.title or "")
            .replace("{chat_id}", str(chat.id)))
    template = template.replace("{count}", str(count))
    if extra:
        for k, v in extra.items():
            template = template.replace("{" + k + "}", str(v))
    return template
