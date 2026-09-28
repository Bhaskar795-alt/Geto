import secrets
import string

@Client.on_message(filters.command("pass"))
async def pass_cmd(client, message):
    length = 16
    if len(message.command) > 1 and message.command[1].isdigit():
        length = min(int(message.command[1]), 64)
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    pw = "".join(secrets.choice(chars) for _ in range(length))
    await message.reply_text(f"🔐 <code>{pw}</code>")
