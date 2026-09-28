from pyrogram import Client, filters
from database import db
from utils.permissions import is_admin


# =========================================================
# CLEAN COMMAND TYPES
# =========================================================

CLEAN_TYPES = ["all", "admin", "user", "other"]

# Admin commands list
ADMIN_COMMANDS = {
    "ban", "tban", "dban", "sban", "unban", "mute", "tmute", "dmute",
    "smute", "unmute", "kick", "dkick", "skick", "promote", "demote",
    "warn", "unwarn", "resetwarns", "setwarnlimit", "setwarnmode",
    "setwelcome", "resetwelcome", "welcome", "welcomepreview",
    "setgoodbye", "resetgoodbye", "goodbye",
    "setrules", "resetrules", "rules",
    "filter", "stop", "stopall", "filters",
    "save", "clear", "clearall", "notes",
    "lock", "unlock", "locks", "lockwarns", "locktypes",
    "allowlist", "rmallowlist", "rmallowlistall",
    "addblocklist", "rmblocklist", "unblocklistall", "blocklist",
    "blocklistmode", "blocklistdelete", "setblocklistreason",
    "resetblocklistreason",
    "antiflood", "setflood", "setfloodtimer", "floodmode", "clearflood",
    "antiraid", "raidtime", "raidactiontime", "autoantiraid",
    "captcha", "captchamode", "captcharules", "captchamutetime",
    "captchakick", "captchakicktime", "setcaptchatext", "resetcaptchatext",
    "joinrequests", "autoapprove",
    "approve", "unapprove", "approved", "unapproveall",
    "pin", "unpin", "pinned",
    "del", "delete", "purge",
    "disable", "enable", "disabled",
    "connect", "disconnect",
    "log", "nolog", "logchannel", "setlog", "unsetlog", "logcategories",
    "setflood", "flood", "cleancommand", "keepcommand", "cleancommandtypes",
    "adminlist", "admins", "admincache", "anonadmin", "adminerror",
    "setrules", "resetrules",
}

# User commands list
USER_COMMANDS = {
    "id", "info", "userinfo", "chatinfo", "getid",
    "rules", "report", "kickme",
    "get", "notes", "saved",
    "approval", "approved",
    "afk", "weather", "tr", "translate", "qr", "pass", "calc",
    "short", "ip", "whois", "time", "wc", "hash", "b64", "unb64",
    "remind", "meme", "quote", "poll",
}


def get_command_type(command: str):
    """Return command type: admin/user/other."""
    cmd = command.lower().lstrip("/")
    if cmd in ADMIN_COMMANDS:
        return "admin"
    if cmd in USER_COMMANDS:
        return "user"
    return "other"


# =========================================================
# CLEAN COMMAND
# =========================================================

@Client.on_message(filters.command("cleancommand") & filters.group)
async def cleancommand_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")

    if len(message.command) < 2:
        chat = await db.get_chat(message.chat.id)
        types = chat.get("clean_commands", [])
        return await message.reply_text(
            f"🧹 <b>Clean Commands:</b> {', '.join(types) if types else 'OFF'}\n\n"
            f"<b>Available:</b> all / admin / user / other\n"
            f"Usage: /cleancommand &lt;type&gt; [type2...]"
        )

    types_to_add = []
    for arg in message.command[1:]:
        t = arg.lower()
        if t in CLEAN_TYPES:
            types_to_add.append(t)

    if not types_to_add:
        return await message.reply_text("❌ Invalid type.")

    chat = await db.get_chat(message.chat.id)
    current = set(chat.get("clean_commands", []))
    current.update(types_to_add)

    # If "all" is added, clear others
    if "all" in current:
        current = {"all"}

    await db.set_chat_field(message.chat.id, "clean_commands", list(current))
    await message.reply_text(f"✅ Clean commands: <code>{', '.join(current)}</code>")


@Client.on_message(filters.command("keepcommand") & filters.group)
async def keepcommand_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")

    if len(message.command) < 2:
        return await message.reply_text("Usage: /keepcommand <type>")

    types_to_remove = []
    for arg in message.command[1:]:
        t = arg.lower()
        if t in CLEAN_TYPES:
            types_to_remove.append(t)

    if not types_to_remove:
        return await message.reply_text("❌ Invalid type.")

    chat = await db.get_chat(message.chat.id)
    current = set(chat.get("clean_commands", []))

    # If "all" is removed, clear all
    if "all" in types_to_remove:
        current = set()
    else:
        current.difference_update(types_to_remove)

    await db.set_chat_field(message.chat.id, "clean_commands", list(current))
    if not current:
        await message.reply_text("✅ Clean commands: OFF")
    else:
        await message.reply_text(f"✅ Clean commands: <code>{', '.join(current)}</code>")


@Client.on_message(filters.command("cleancommandtypes") & filters.group)
async def cleancommandtypes_cmd(client, message):
    await message.reply_text(
        "🧹 <b>Clean Command Types</b>\n\n"
        "• <code>all</code> — Delete ALL commands\n"
        "• <code>admin</code> — Delete admin commands\n"
        "• <code>user</code> — Delete user commands\n"
        "• <code>other</code> — Delete unknown commands\n\n"
        "<b>Usage:</b>\n"
        "/cleancommand all\n"
        "/cleancommand user other\n"
        "/keepcommand all"
    )


# =========================================================
# CLEAN COMMAND WATCHER
# =========================================================

@Client.on_message(filters.group & filters.text, group=30)
async def clean_command_watcher(client, message):
    if not message.text or not message.text.startswith("/"):
        return

    chat = await db.get_chat(message.chat.id)
    clean_types = chat.get("clean_commands", [])
    if not clean_types:
        return

    # Extract command
    cmd = message.text.split()[0][1:].split("@")[0].lower()
    cmd_type = get_command_type(cmd)

    should_delete = False
    if "all" in clean_types:
        should_delete = True
    elif cmd_type in clean_types:
        should_delete = True

    if should_delete:
        try:
            await message.delete()
        except Exception:
            pass
