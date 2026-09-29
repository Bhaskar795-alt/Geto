import re
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

try:
    from pyrogram.enums import ButtonStyle
except ImportError:
    ButtonStyle = None


BUTTON_PATTERNS = [
    # [Label](buttonurl://https://link)
    (
        r"\[([^\]]+)\]\(buttonurl://([^\)]+)\)",
        "url"
    ),

    # [Label](buttonurl#primary://https://link)
    # [Label](buttonurl#success://https://link)
    # [Label](buttonurl#danger://https://link)
    (
        r"\[([^\]]+)\]\(buttonurl#(\w+)://([^\)]+)\)",
        "url_styled"
    ),

    # [Label](buttonuser://USER_ID)
    (
        r"\[([^\]]+)\]\(buttonuser://(\d+)\)",
        "user"
    ),

    # [Label](buttoncallback://DATA)
    (
        r"\[([^\]]+)\]\(buttoncallback://([^\)]+)\)",
        "callback"
    ),

    # [Label](buttoncallback#primary://DATA)
    # [Label](buttoncallback#success://DATA)
    # [Label](buttoncallback#danger://DATA)
    (
        r"\[([^\]]+)\]\(buttoncallback#(\w+)://([^\)]+)\)",
        "callback_styled"
    ),
]


def get_button_style(style_name):
    """
    Convert style name into Pyrogram ButtonStyle.
    Supported:
        primary
        success
        danger
        default
    """

    if not ButtonStyle:
        return None

    styles = {
        "primary": ButtonStyle.PRIMARY,
        "success": ButtonStyle.SUCCESS,
        "danger": ButtonStyle.DANGER,
        "default": ButtonStyle.DEFAULT,
    }

    return styles.get(style_name.lower())


def make_button(label, button_type, value, style=None):
    """
    Creates an InlineKeyboardButton safely.
    """

    kwargs = {
        "text": label,
    }

    if button_type == "url":
        kwargs["url"] = value

    elif button_type == "user":
        kwargs["url"] = f"tg://user?id={value}"

    elif button_type == "callback":
        kwargs["callback_data"] = value

    if style:
        button_style = get_button_style(style)

        if button_style is not None:
            kwargs["style"] = button_style

    return InlineKeyboardButton(**kwargs)


def parse_buttons(text: str):
    """
    Parse inline buttons from text.

    Supported:

    [Google](buttonurl://https://google.com)

    [Google](buttonurl#primary://https://google.com)

    [Success](buttonurl#success://https://google.com)

    [Delete](buttonurl#danger://https://google.com)

    [User](buttonuser://123456789)

    [Click](buttoncallback://hello)

    [Click](buttoncallback#primary://hello)

    Multiple buttons in same row:

    [One](buttoncallback://one) | [Two](buttoncallback://two)

    Each new line creates a new row.

    Returns:
        (clean_text, InlineKeyboardMarkup or None)
    """

    rows = []
    button_lines = []

    for line in text.splitlines():
        row_buttons = []

        # Multiple buttons in one row
        parts = re.split(r"\s*\|\s*", line)

        for part in parts:
            part = part.strip()

            for pattern, btype in BUTTON_PATTERNS:
                m = re.fullmatch(pattern, part)

                if not m:
                    continue

                if btype == "url":
                    label = m.group(1)
                    value = m.group(2)

                    row_buttons.append(
                        make_button(
                            label,
                            "url",
                            value
                        )
                    )

                elif btype == "url_styled":
                    label = m.group(1)
                    style = m.group(2)
                    value = m.group(3)

                    row_buttons.append(
                        make_button(
                            label,
                            "url",
                            value,
                            style
                        )
                    )

                elif btype == "user":
                    label = m.group(1)
                    value = m.group(2)

                    row_buttons.append(
                        make_button(
                            label,
                            "user",
                            value
                        )
                    )

                elif btype == "callback":
                    label = m.group(1)
                    value = m.group(2)

                    row_buttons.append(
                        make_button(
                            label,
                            "callback",
                            value
                        )
                    )

                elif btype == "callback_styled":
                    label = m.group(1)
                    style = m.group(2)
                    value = m.group(3)

                    row_buttons.append(
                        make_button(
                            label,
                            "callback",
                            value,
                            style
                        )
                    )

                break

        if row_buttons:
            rows.append(row_buttons)
            button_lines.append(line)

    if not rows:
        return text, None

    # Remove only button lines from message text
    clean_lines = []

    for line in text.splitlines():
        if line in button_lines:
            continue

        clean_lines.append(line)

    clean_text = "\n".join(clean_lines).strip()

    return clean_text, InlineKeyboardMarkup(rows)

Ab Geto mein aise use karna

Text + emoji + buttons:

text = """
😀 Hello 👋

[Help](buttoncallback#primary://help) | [Settings](buttoncallback#success://settings)
[Close](buttoncallback#danger://close)
"""

clean_text, buttons = parse_buttons(text)

await message.reply_text(
    clean_text,
    reply_markup=buttons
)

Photo + buttons:

clean_text, buttons = parse_buttons(caption)

await message.reply_photo(
    photo,
    caption=clean_text,
    reply_markup=buttons
)

Sticker + buttons:

clean_text, buttons = parse_buttons(text)

await message.reply_sticker(
    sticker,
    reply_markup=buttons
)

Format

[🌐 Website](buttonurl#primary://https://example.com)
[💚 Support](buttonurl#success://https://example.com)
[❌ Close](buttoncallback#danger://close)

Ya same row:

[🌐 Website](buttonurl#primary://https://example.com) | [💚 Support](buttonurl#success://https://example.com)

Note: "primary/success/danger" Telegram ke supported button styles hain; arbitrary button color jaise "#FF0000" set nahi kiya ja sakta.
