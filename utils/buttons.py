import re
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


BUTTON_PATTERNS = [
    # [Label](buttonurl://https://link)
    (r"\[([^\]]+)\]\(buttonurl://([^\)]+)\)", "url"),
    # [Label](buttonurl#primary://https://link)
    (r"\[([^\]]+)\]\(buttonurl#(\w+)://([^\)]+)\)", "url_styled"),
    # [Label](buttonuser://USER_ID)
    (r"\[([^\]]+)\]\(buttonuser://(\d+)\)", "user"),
    # [Label](buttoncallback://DATA)
    (r"\[([^\]]+)\]\(buttoncallback://([^\)]+)\)", "callback"),
]


def parse_buttons(text: str):
    """
    Returns (clean_text, markup_or_None)
    Handles multi-row buttons using || separator
    """
    rows = []
    for line in text.split("\n"):
        row_buttons = []
        # Split multi-buttons per row with " | "
        parts = re.split(r"\s*\|\s*", line)
        for part in parts:
            for pattern, btype in BUTTON_PATTERNS:
                m = re.match(pattern, part.strip())
                if m:
                    label = m.group(1)
                    if btype == "url":
                        row_buttons.append(InlineKeyboardButton(label, url=m.group(2)))
                    elif btype == "url_styled":
                        # style hint: primary/success/danger
                        row_buttons.append(InlineKeyboardButton(label, url=m.group(3)))
                    elif btype == "user":
                        row_buttons.append(InlineKeyboardButton(label, url=f"tg://user?id={m.group(2)}"))
                    elif btype == "callback":
                        row_buttons.append(InlineKeyboardButton(label, callback_data=m.group(2)))
                    break
        if row_buttons:
            rows.append(row_buttons)

    if not rows:
        return text, None

    # Remove button lines from text
    clean = re.sub(r"\[[^\]]+\]\(button\w+[^\)]*\)\s*(\|\s*\[[^\]]+\]\(button\w+[^\)]*\))*\n?", "", text)
    return clean.strip(), InlineKeyboardMarkup(rows)
