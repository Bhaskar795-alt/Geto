import requests
import re
from config import Config


def send_with_colored_buttons(
    chat_id,
    text,
    buttons_text,
    parse_mode="HTML",
    reply_to_message_id=None
):
    """
    Send message with colored buttons using direct Telegram Bot API.

    buttons_text format:
        [Label](buttonurl#primary://URL)
        [Label](buttonurl#danger://URL)
        [Label](buttonurl#success://URL)
        [Label](buttonurl://URL)           (default style)
        [Btn2](buttonurl#primary://URL2:same)  (same row)
    """
    if not buttons_text:
        buttons_text = ""

    # Pattern: [Label](buttonurl#style://URL)
    pattern = r"\[([^\]]+)\]\(buttonurl(?:#(\w+))?://([^\)]+?)(?::same)?\)"

    rows = []
    current_row = []

    for m in re.finditer(pattern, buttons_text):
        label = m.group(1)
        style = m.group(2)  # primary/danger/success or None
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

    # Clean text
    clean = re.sub(pattern, "", text or "")
    clean = "\n".join(line for line in clean.split("\n") if line.strip())

    # If no buttons, just send text
    if not rows:
        url_api = f"https://api.telegram.org/bot{Config.BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": clean or text or "…",
            "parse_mode": parse_mode,
        }
        if reply_to_message_id:
            payload["reply_to_message_id"] = reply_to_message_id
        try:
            return requests.post(url_api, json=payload, timeout=10).json()
        except Exception as e:
            print(f"[COLORED] {e}")
            return None

    url_api = f"https://api.telegram.org/bot{Config.BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": clean or "…",
        "parse_mode": parse_mode,
        "reply_markup": {"inline_keyboard": rows},
    }
    if reply_to_message_id:
        payload["reply_to_message_id"] = reply_to_message_id

    try:
        response = requests.post(url_api, json=payload, timeout=10)
        result = response.json()
        if not result.get("ok"):
            print(f"[COLORED] API error: {result}")
        return result
    except Exception as e:
        print(f"[COLORED] {e}")
        return None


def send_photo_with_colored_buttons(
    chat_id,
    file_id,
    caption,
    buttons_text,
    parse_mode="HTML",
    reply_to_message_id=None
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
        return requests.post(url_api, json=payload, timeout=10).json()
    except Exception as e:
        print(f"[COLORED PHOTO] {e}")
        return None


def send_video_with_colored_buttons(
    chat_id,
    file_id,
    caption,
    buttons_text,
    parse_mode="HTML",
    reply_to_message_id=None
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
        return requests.post(url_api, json=payload, timeout=10).json()
    except Exception as e:
        print(f"[COLORED VIDEO] {e}")
        return None
