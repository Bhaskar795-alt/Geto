import time
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import Config
from database import db


# =========================================================
# HELP CATEGORIES DATA
# =========================================================

HELP_CATEGORIES = {
    "admin": {
        "title": "🛡️ Admin",
        "desc": "Moderation & admin commands",
        "commands": (
            "<b>🛡️ Admin Commands</b>\n\n"
            "/ban — Ban a user\n"
            "/tban — Temp ban\n"
            "/dban — Ban + delete msg\n"
            "/sban — Silent ban\n"
            "/unban — Unban\n"
            "/kick — Kick\n"
            "/kickme — Kick yourself\n"
            "/mute — Mute\n"
            "/tmute — Temp mute\n"
            "/dmute — Mute + delete\n"
            "/smute — Silent mute\n"
            "/unmute — Unmute\n"
            "/mutelist — Mute list\n"
            "/promote — Promote user\n"
            "/demote — Demote user\n"
            "/admins — Admin list\n"
            "/adminlist — Admin list (short)\n"
            "/admincache — Refresh cache\n"
            "/anonadmin — Toggle anon admin\n"
            "/adminerror — Toggle errors"
        ),
    },
    "antiflood": {
        "title": "🚨 AntiFlood",
        "desc": "Prevent message flooding",
        "commands": (
            "<b>🚨 AntiFlood Commands</b>\n\n"
            "/flood — View settings\n"
            "/setflood <n> — Set limit\n"
            "/setfloodtimer <n> <time> — Timed\n"
            "/floodmode <action> — Set action\n"
            "/clearflood yes/no — Delete msgs"
        ),
    },
    "antiraid": {
        "title": "🚨 AntiRaid",
        "desc": "Stop raid attacks",
        "commands": (
            "<b>🚨 AntiRaid Commands</b>\n\n"
            "/antiraid <time> — Enable\n"
            "/raidtime <time> — Duration\n"
            "/raidactiontime <time> — Ban time\n"
            "/autoantiraid <n> — Auto trigger"
        ),
    },
    "approval": {
        "title": "✅ Approval",
        "desc": "Trusted users system",
        "commands": (
            "<b>✅ Approval Commands</b>\n\n"
            "/approval — Check status\n"
            "/approve — Approve user\n"
            "/unapprove — Unapprove\n"
            "/approved — List approved\n"
            "/unapproveall yes — Reset all"
        ),
    },
    "bans": {
        "title": "🔨 Bans",
        "desc": "Ban & mute users",
        "commands": (
            "<b>🔨 Ban Commands</b>\n\n"
            "/ban — Ban\n"
            "/tban — Temp ban\n"
            "/dban — Ban + delete\n"
            "/sban — Silent ban\n"
            "/unban — Unban\n"
            "/kick — Kick\n"
            "/kickme — Kick yourself"
        ),
    },
    "blocklists": {
        "title": "🚫 Blocklists",
        "desc": "Block bad words/links",
        "commands": (
            "<b>🚫 Blocklist Commands</b>\n\n"
            "/addblocklist <word> — Add\n"
            "/rmblocklist <word> — Remove\n"
            "/blocklist — Show list\n"
            "/unblocklistall yes — Clear\n"
            "/blocklistmode <mode> — Action\n"
            "/blocklistdelete yes/no — Delete\n"
            "/setblocklistreason <r> — Reason\n"
            "/resetblocklistreason — Reset"
        ),
    },
    "captcha": {
        "title": "🤖 CAPTCHA",
        "desc": "Verify new users",
        "commands": (
            "<b>🤖 CAPTCHA Commands</b>\n\n"
            "/captcha yes/no — Toggle\n"
            "/captchamode <mode> — Mode\n"
            "/captcharules yes/no — Rules\n"
            "/captchamutetime <time> — Mute time\n"
            "/captchakick yes/no — Kick\n"
            "/captchakicktime <time> — Kick time\n"
            "/setcaptchatext <text> — Button\n"
            "/resetcaptchatext — Reset"
        ),
    },
    "clean": {
        "title": "🧹 Clean Commands",
        "desc": "Auto-delete commands",
        "commands": (
            "<b>🧹 Clean Commands</b>\n\n"
            "/cleancommand <type> — Set\n"
            "/keepcommand <type> — Unset\n"
            "/cleancommandtypes — Types"
        ),
    },
    "connections": {
        "title": "🔗 Connections",
        "desc": "Manage from PM",
        "commands": (
            "<b>🔗 Connection Commands</b>\n\n"
            "/connect — Connect to chat\n"
            "/disconnect — Disconnect\n"
            "/reconnect — Reconnect\n"
            "/connection — Info"
        ),
    },
    "disabling": {
        "title": "⚙️ Disabling",
        "desc": "Disable commands",
        "commands": (
            "<b>⚙️ Command Disabling</b>\n\n"
            "/disable <command> — Disable\n"
            "/enable <command> — Enable\n"
            "/disabled — List disabled"
        ),
    },
    "federations": {
        "title": "🌐 Federations",
        "desc": "Global ban network",
        "commands": (
            "<b>🌐 Federation Commands</b>\n\n"
            "/newfed <name> — Create\n"
            "/delfed <id> — Delete\n"
            "/joinfed <id> <chat> — Join\n"
            "/leavefed <id> <chat> — Leave\n"
            "/fedinfo <id> — Info\n"
            "/fban <id> <user> — Fed ban\n"
            "/unfban <id> <user> — Unban"
        ),
    },
    "filters": {
        "title": "🔥 Filters",
        "desc": "Auto-replies on keywords",
        "commands": (
            "<b>🔥 Filter Commands</b>\n\n"
            "/filter <word> <reply>\n"
            "/filter (a,b,c) <reply> — Multi\n"
            "/filter \"phrase\" <reply>\n"
            "/filter \"exact:hi\" <reply>\n"
            "/filter \"prefix:hi\" <reply>\n"
            "Reply + /filter <word> — Media\n"
            "/filters — List\n"
            "/stop <word> — Remove\n"
            "/stopall — Remove all"
        ),
    },
    "formatting": {
        "title": "🎨 Formatting",
        "desc": "Markdown & buttons",
        "commands": (
            "<b>🎨 Formatting Guide</b>\n\n"
            "*bold* → <b>bold</b>\n"
            "_italic_ → <i>italic</i>\n"
            "__underline__ → <u>underline</u>\n"
            "~strike~ → <s>strike</s>\n"
            "||spoiler|| → spoiler\n"
            "`code` → code\n"
            "> quote → quote\n\n"
            "<b>Buttons:</b>\n"
            "[Label](buttonurl://URL)\n"
            "[Btn](buttonurl://URL:same)\n"
            "[Btn](buttonurl#primary://URL)"
        ),
    },
    "greetings": {
        "title": "👋 Greetings",
        "desc": "Welcome & goodbye",
        "commands": (
            "<b>👋 Greeting Commands</b>\n\n"
            "/setwelcome <text> — Set\n"
            "Reply + /setwelcome — Media\n"
            "/welcomepreview — Preview\n"
            "/welcome — Toggle\n"
            "/resetwelcome — Reset\n"
            "/setgoodbye <text> — Set\n"
            "/goodbye — Toggle\n"
            "/resetgoodbye — Reset"
        ),
    },
    "locks": {
        "title": "🔒 Locks",
        "desc": "Block content types",
        "commands": (
            "<b>🔒 Lock Commands</b>\n\n"
            "/lock <type> — Lock\n"
            "/lock <t1> <t2> — Multi\n"
            "/lock <t> ### reason — Reason\n"
            "/lock <t> ### reason {ban} — Action\n"
            "/unlock <type> — Unlock\n"
            "/locks — Show active\n"
            "/locktypes — All types\n"
            "/lockwarns yes/no — Warn\n"
            "/allowlist <item> — Whitelist\n"
            "/rmallowlist <item> — Remove\n"
            "/rmallowlistall — Clear"
        ),
    },
    "logs": {
        "title": "📊 Log Channels",
        "desc": "Track all actions",
        "commands": (
            "<b>📊 Log Commands</b>\n\n"
            "/setlog — Set channel\n"
            "/unsetlog — Unset\n"
            "/logchannel — View\n"
            "/log <cat> — Enable category\n"
            "/nolog <cat> — Disable\n"
            "/logcategories — List"
        ),
    },
    "notes": {
        "title": "📝 Notes",
        "desc": "Save snippets",
        "commands": (
            "<b>📝 Note Commands</b>\n\n"
            "/save <name> — Save (reply)\n"
            "/get <name> — Get\n"
            "/notes — List\n"
            "/clear <name> — Delete\n"
            "/clearall — Delete all"
        ),
    },
    "pin": {
        "title": "📌 Pin",
        "desc": "Pin messages",
        "commands": (
            "<b>📌 Pin Commands</b>\n\n"
            "/pin — Pin (reply)\n"
            "/unpin — Unpin\n"
            "/pinned — Show pinned"
        ),
    },
    "purges": {
        "title": "🧹 Purges",
        "desc": "Bulk delete messages",
        "commands": (
            "<b>🧹 Purge Commands</b>\n\n"
            "/del — Delete (reply)\n"
            "/purge — Delete range\n"
            "/purge <n> — Delete n msgs\n"
            "/spurge — Silent purge\n"
            "/purgefrom — Mark start\n"
            "/purgeto — Mark end"
        ),
    },
    "reports": {
        "title": "🚨 Reports",
        "desc": "Report to admins",
        "commands": (
            "<b>🚨 Report Commands</b>\n\n"
            "/report — Report (reply)\n"
            "@admin — Same\n"
            "/reports yes/no — Toggle"
        ),
    },
    "rules": {
        "title": "📜 Rules",
        "desc": "Chat rules",
        "commands": (
            "<b>📜 Rules Commands</b>\n\n"
            "/rules — Show rules\n"
            "/rules noformat — Raw\n"
            "/setrules <text> — Set\n"
            "/resetrules — Reset\n"
            "/privaterules yes/no — PM\n"
            "/setrulesbutton <t> — Button\n"
            "/resetrulesbutton — Reset"
        ),
    },
    "warnings": {
        "title": "⚠️ Warnings",
        "desc": "Warn system",
        "commands": (
            "<b>⚠️ Warning Commands</b>\n\n"
            "/warn <reason> — Warn\n"
            "/dwarn <reason> — Warn + delete\n"
            "/swarn <reason> — Silent\n"
            "/warns — View warns\n"
            "/rmwarn — Remove last\n"
            "/resetwarn — Reset user\n"
            "/resetallwarns yes — Reset all\n"
            "/warnings — Settings\n"
            "/warnmode <mode> — Action\n"
            "/warnlimit <n> — Limit\n"
            "/warntime <time> — Expiry"
        ),
    },
}


# =========================================================
# HELP TEXT
# =========================================================

HELP_TEXT = """🌹 <b>GETO BOT — Help Menu</b>

𝐇ᴇʏ! 𝐈'ᴀᴍ <b>𝐘ᴏᴜʀ</b>, ᴀ 𝐆ʀᴏᴜᴩ 𝐌ᴀɴᴀɢᴇᴍᴇɴᴛ 𝐁ᴏᴛ

𝐈 𝐂ᴀɴ 𝐇ᴇʟᴩ 𝐘ᴏᴜ 𝐖ɪᴛʜ 
• 𝐌ᴏᴅᴇʀᴀᴛɪᴏɴ &𝐀ɴᴛɪ 𝐒ᴩᴀᴍ 
• 𝐖ᴇʟᴄᴏᴍᴇ / 𝐆ᴏᴏᴅʙʏᴇ 𝐌ᴇꜱꜱᴀɢᴇꜱ
• 𝐅ɪʟᴛᴇʀꜱ & 𝐍ᴏᴛᴇꜱ
• 𝐋ᴏᴄᴋ & 𝐁ʟᴏᴄᴋʟɪꜱᴛ
• 𝐑ᴜʟᴇꜱ, 𝐖ᴀʀɴɪɴɢ & 𝐌ᴏʀᴇ

<b>𝐁ᴀꜱɪᴄ 𝐂ᴏᴍᴍᴏɴᴅ</b>
/start — 𝐒ᴛᴀʀᴛ 𝐓ʜᴇ 𝐁ᴏᴛ
/help — 𝐌ᴇɴᴜ

<b>👇 𝐀ʟʟ 𝐂ᴏᴍᴍᴏɴᴅꜱ 𝐂ᴀɴ 𝐁ᴇ 𝐔ꜱᴇᴅ 𝐖ɪᴛʜ 𝐓ʜᴇ 𝐅ᴏʟʟᴏᴡɪɴɢ::</b>
"""


# =========================================================
# HELP KEYBOARD
# =========================================================

def build_help_keyboard():
    """Build the two-column help keyboard."""
    cats = list(HELP_CATEGORIES.keys())
    buttons = []
    for i in range(0, len(cats), 2):
        row = []
        for c in cats[i:i+2]:
            data = HELP_CATEGORIES[c]
            row.append(InlineKeyboardButton(
                data["title"],
                callback_data=f"help_{c}"
            ))
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)


def build_help_back_keyboard():
    """Return keyboard with back button."""
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("◀️ Back to Menu", callback_data="help_home")
    ]])


# =========================================================
# /start COMMAND
# =========================================================

@Client.on_message(filters.command("start"))
async def start_cmd(client, message):
    await db.add_user(message.from_user.id, message.from_user.first_name)
    btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚜️𝐓ᴀᴩ 𝐓ᴏ 𝐒ᴇᴇ 𝐌ᴀɢɪᴄ🫰",
            url=f"https://t.me/{Config.BOT_USERNAME}?startgroup=true")],
        [InlineKeyboardButton("𝐇ᴇʟᴩ", callback_data="help_home"),
         InlineKeyboardButton("👑 𝐎ᴡɴᴇʀ", url=f"https://t.me/{Config.OWNER_USERNAME}")
    ])
    await message.reply_text(
        f"🌹 <b>Welcome to {Config.BOT_NAME}!</b>\n\n"
        f"Hi {message.from_user.mention}!\n\n"
        f"I'm a powerful group management bot.\n"
        f"Use /help to see all my features.",
        reply_markup=btn
    )


# =========================================================
# /help COMMAND
# =========================================================

@Client.on_message(filters.command("help"))
async def help_cmd(client, message):
    args = message.command

    # /help <category> → direct category
    if len(args) > 1:
        cat = args[1].lower()
        if cat in HELP_CATEGORIES:
            data = HELP_CATEGORIES[cat]
            await message.reply_text(
                data["commands"],
                reply_markup=build_help_back_keyboard()
            )
            return
        else:
            await message.reply_text(
                f"❌ Unknown category: <code>{cat}</code>\n\n"
                f"Use /help to see all categories."
            )
            return

    # Default /help → main menu
    await message.reply_text(
        HELP_TEXT,
        reply_markup=build_help_keyboard(),
        disable_web_page_preview=True
    )


# =========================================================
# CALLBACK HANDLERS
# =========================================================

@Client.on_callback_query(filters.regex("^help_home$"))
async def help_home_cb(client, cb):
    await cb.message.edit_text(
        HELP_TEXT,
        reply_markup=build_help_keyboard(),
        disable_web_page_preview=True
    )
    await cb.answer()


@Client.on_callback_query(filters.regex(r"^help_(\w+)$"))
async def help_category_cb(client, cb):
    cat = cb.data.split("_", 1)[1]
    data = HELP_CATEGORIES.get(cat)
    if not data:
        return await cb.answer("❌ Category not found.", show_alert=True)

    try:
        await cb.message.edit_text(
            data["commands"],
            reply_markup=build_help_back_keyboard()
        )
    except Exception:
        pass
    await cb.answer()
