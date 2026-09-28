import re
import random
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


# =========================================================
# BUTTON PARSER
# =========================================================

def parse_buttons(text, bot_username="GetoBot"):
    """
    Rose-style button parser.
    Supports:
      [Label](buttonurl://URL)
      [Label](buttonurl://URL:same)
      [Label](buttonurl#primary://URL)
      [Label](buttonurl#danger://URL)
      [Label](buttonurl#success://URL)
      [Label](buttonurl://#notename)
    """
    if not text:
        return "", None

    # Match button syntax
    pattern = r"\[([^\]]+)\]\(buttonurl(#[a-z]+)?://([^\)]+?)(:same)?\)"

    rows = []
    current_row = []

    for m in re.finditer(pattern, text):
        label = m.group(1)
        style = m.group(2)
        url = m.group(3)
        same = m.group(4)

        # Note link
        if url.startswith("#"):
            url = f"https://t.me/{bot_username}?start=note_{url[1:]}"

        # Try styled button (Pyrogram may not support)
        try:
            if style:
                btn = InlineKeyboardButton(
                    label, url=url, style=style[1:]
                )
            else:
                btn = InlineKeyboardButton(label, url=url)
        except Exception:
            btn = InlineKeyboardButton(label, url=url)

        # Same row or new row
        if same and current_row:
            current_row.append(btn)
        else:
            if current_row:
                rows.append(current_row)
            current_row = [btn]

    if current_row:
        rows.append(current_row)

    # Clean text
    clean = re.sub(pattern, "", text)
    clean = "\n".join(line for line in clean.split("\n") if line.strip())

    if not rows:
        return clean.strip(), None
    return clean.strip(), InlineKeyboardMarkup(rows)


# =========================================================
# FILLINGS (variables)
# =========================================================

def replace_fillings(text, user=None, chat=None, count=0,
                     rules="", rules_button=False, extra=None):
    """
    Replace Rose-style fillings in text.
    Handles: {first}, {last}, {fullname}, {username}, {mention},
             {id}, {chatname}, {count}, {rules}, {date}, {time},
             and random content via %%%.
    """
    from datetime import datetime

    if not text:
        return ""

    # Random content
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

    # Rules button
    if rules_button and "{rules}" in text:
        text = text.replace("{rules}", "")

    if extra:
        for k, v in extra.items():
            text = text.replace("{" + k + "}", str(v))

    return text


# =========================================================
# PERMISSION TAGS
# =========================================================

def check_permissions(text, is_admin_user=False, is_bot=False):
    """
    Check if text has {admin}/{user}/{allow_bot} and if user qualifies.
    Returns False if the user shouldn't trigger this message.
    """
    if "{admin}" in text and not is_admin_user:
        return False
    if "{user}" in text and is_admin_user:
        return False
    if "{allow_bot}" in text and not is_bot:
        return False
    return True


def clean_permission_tags(text):
    """Remove {admin}, {user}, {allow_bot} tags."""
    return (text
        .replace("{admin}", "")
        .replace("{user}", "")
        .replace("{allow_bot}", "")
        .strip())


# =========================================================
# MARKDOWN CONVERTER (Rosé style)
# =========================================================

def convert_markdown(text):
    """
    Convert Rose-style markdown to Telegram HTML.
    Since we use HTML mode, convert Rose markdown syntax to HTML.
    
    Rose syntax → HTML:
      *bold*        → <b>bold</b>
      _italic_      → <i>italic</i>
      __underline__ → <u>underline</u>
      ~strike~      → <s>strike</s>
      ||spoiler||   → <tg-spoiler>spoiler</tg-spoiler>
      `code`        → <code>code</code>
      ```...```     → <pre>...</pre>
      > quote       → <blockquote>quote</blockquote>
      [link](url)   → <a href="url">link</a>
    """
    if not text:
        return text

    # Code blocks (triple backtick)
    text = re.sub(
        r"```(\w+)?\n(.*?)```",
        lambda m: f"<pre>{m.group(2)}</pre>",
        text, flags=re.DOTALL
    )

    # Inline code
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)

    # Spoiler
    text = re.sub(r"\|\|(.+?)\|\|", r"<tg-spoiler>\1</tg-spoiler>", text)

    # Underline
    text = re.sub(r"__(.+?)__", r"<u>\1</u>", text)

    # Italic
    text = re.sub(r"(?<!_)_([^_]+)_(?!_)", r"<i>\1</i>", text)

    # Bold
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<b>\1</b>", text)

    # Strikethrough
    text = re.sub(r"~([^~]+)~", r"<s>\1</s>", text)

    # Hyperlinks (excluding button syntax)
    text = re.sub(
        r"\[([^\]]+)\]\((?!#|buttonurl)([^\)]+)\)",
        r'<a href="\2">\1</a>',
        text
    )

    # Blockquote
    lines = text.split("\n")
    new_lines = []
    in_quote = False
    for line in lines:
        if line.startswith("&gt;") or line.startswith(">"):
            if not in_quote:
                new_lines.append("<blockquote>")
                in_quote = True
            new_lines.append(line.lstrip("&gt;").lstrip(">").strip())
        else:
            if in_quote:
                new_lines.append("</blockquote>")
                in_quote = False
            new_lines.append(line)
    if in_quote:
        new_lines.append("</blockquote>")
    text = "\n".join(new_lines)

    return text


# =========================================================
# FULL FORMAT PIPELINE
# =========================================================

def format_message(text, user=None, chat=None, count=0,
                   rules="", is_admin_user=False, is_bot=False,
                   bot_username="GetoBot"):
    """
    Full pipeline: permissions → fillings → markdown → buttons.
    Returns (clean_text, markup or None).
    """
    if not text:
        return "", None

    # 1. Check permissions
    if not check_permissions(text, is_admin_user, is_bot):
        return None, None

    # 2. Clean permission tags
    text = clean_permission_tags(text)

    # 3. Replace fillings
    text = replace_fillings(text, user=user, chat=chat,
                            count=count, rules=rules)

    # 4. Parse buttons (before markdown so buttons are preserved)
    clean, markup = parse_buttons(text, bot_username)

    # 5. Convert markdown (careful with HTML entities)
    # Do not convert inside button labels — buttons already parsed out
    clean = convert_markdown(clean)

    return clean, markup
