import re
from datetime import datetime
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import Config


# ---------------------------------------------------------
# Duration Parser
# ---------------------------------------------------------

DURATION_RE = re.compile(r"^(\d+)([smhdw])$")


def parse_duration(text):
    if not text:
        return 0

    m = DURATION_RE.match(text.strip().lower())

    if not m:
        return 0

    return int(m.group(1)) * Config.DURATION_MAP[m.group(2)]


# ---------------------------------------------------------
# HTML Mention
# ---------------------------------------------------------

def mention_html(user_id, name):
    name = name or "User"
    return f'<a href="tg://user?id={user_id}">{name}</a>'


# ---------------------------------------------------------
# Resolve Target User
# Supports:
#   Reply
#   @username
#   User ID
#   tg://user?id=123
# ---------------------------------------------------------

async def resolve_user(app, message):
    """Resolve target user safely."""

    # =====================================================
    # 1. REPLY METHOD
    # =====================================================

    if message.reply_to_message:
        target = message.reply_to_message.from_user

        if target:
            return (
                target.id,
                target.first_name or "User",
                target.username
            )


    # =====================================================
    # 2. COMMAND ARGUMENT
    # =====================================================

    if not message.command or len(message.command) < 2:
        return None, None, None

    arg = message.command[1].strip()


    # =====================================================
    # 3. @USERNAME
    # =====================================================

    if arg.startswith("@"):
        try:
            user = await app.get_users(arg)

            return (
                user.id,
                user.first_name or "User",
                user.username
            )

        except Exception:
            return None, None, None


    # =====================================================
    # 4. NUMERIC USER ID
    # =====================================================

    if arg.lstrip("-").isdigit():

        user_id = int(arg)

        try:
            user = await app.get_users(user_id)

            return (
                user.id,
                user.first_name or "User",
                user.username
            )

        except Exception:
            # IMPORTANT:
            # Do NOT return an unresolved ID.
            # Doing that causes PEER_ID_INVALID.
            return None, None, None


    # =====================================================
    # 5. tg://user?id=123
    # =====================================================

    match = re.search(
        r"tg://user\?id=(-?\d+)",
        arg
    )

    if match:

        user_id = int(match.group(1))

        try:
            user = await app.get_users(user_id)

            return (
                user.id,
                user.first_name or "User",
                user.username
            )

        except Exception:
            return None, None, None


    # =====================================================
    # USER NOT FOUND
    # =====================================================

    return None, None, None


# ---------------------------------------------------------
# Inline Keyboard Builder
# ---------------------------------------------------------

def build_buttons(button_data):

    if not button_data:
        return None

    rows = []

    for row in button_data:

        rows.append([
            InlineKeyboardButton(**button)
            for button in row
        ])

    return InlineKeyboardMarkup(rows)


# ---------------------------------------------------------
# Text Formatter
# ---------------------------------------------------------

def format_text(
    template,
    user=None,
    chat=None,
    count=0,
    extra=None
):

    if not template:
        template = ""


    # =====================================================
    # USER VARIABLES
    # =====================================================

    if user:

        first = user.first_name or ""
        last = user.last_name or ""

        fullname = (
            f"{first} {last}".strip()
            or first
            or "User"
        )

        username = getattr(
            user,
            "username",
            None
        )

        mention = (
            user.mention
            if hasattr(user, "mention")
            else first
        )

        template = (
            template
            .replace("{first}", first)
            .replace("{last}", last)
            .replace("{fullname}", fullname)
            .replace("{name}", first)
            .replace("{mention}", mention)
            .replace("{id}", str(user.id))
            .replace("{user_id}", str(user.id))
            .replace(
                "{username}",
                f"@{username}"
                if username
                else mention
            )
        )


    # =====================================================
    # CHAT VARIABLES
    # =====================================================

    if chat:

        template = (
            template
            .replace(
                "{chatname}",
                chat.title or ""
            )
            .replace(
                "{chat_id}",
                str(chat.id)
            )
        )


    # =====================================================
    # COUNT VARIABLES
    # =====================================================

    template = (
        template
        .replace("{count}", str(count))
        .replace("{members}", str(count))
    )


    # =====================================================
    # DATE / TIME
    # =====================================================

    now = datetime.now()

    template = (
        template
        .replace(
            "{date}",
            now.strftime("%d %b %Y")
        )
        .replace(
            "{time}",
            now.strftime("%H:%M:%S")
        )
    )


    # =====================================================
    # CUSTOM VARIABLES
    # =====================================================

    if extra:

        for key, value in extra.items():

            template = template.replace(
                "{" + str(key) + "}",
                str(value)
            )


    return template

⚠️ Ek important baat

Is code se "PEER_ID_INVALID" ko hide nahi kiya gaya hai. Agar Telegram ke paas numeric ID ka peer available hi nahi hai, resolver "None" return karega aur bot clearly bolega:

❌ User not found.

Reply to the user's message and use /ban.

Isliye testing ke liye pehle group mein target user ke message ko reply karke:

/ban

try karo.

Phir "/mute", "/promote" bhi isi resolver ko use kar sakte hain.
