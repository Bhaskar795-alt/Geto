# 🌹 GETO BOT

Ultimate Telegram group manager bot.

## Features
- Full moderation (ban/mute/kick/promote)
- Warnings with auto-action
- Filters, Notes, Locks, Blocklist, Allowlist
- Anti-flood, Anti-raid
- CAPTCHA verification
- Join Request approval with buttons
- Welcome/Goodbye/Rules
- Premium/Custom Emoji support
- Federation, Broadcast, Logs
- Sudo & Owner system

## Deploy on Render

1. Fork this repo
2. Create MongoDB Atlas cluster
3. Create a **Background Worker** on Render
4. Build: `pip install -r requirements.txt`
5. Start: `python bot.py`
6. Add env variables (see `.env.example`)

## Env Variables
- `API_ID`, `API_HASH` — from my.telegram.org
- `BOT_TOKEN` — from @BotFather
- `MONGO_URI` — MongoDB connection string
- `OWNER_ID` — your Telegram user ID
- `LOG_CHANNEL` — optional log channel ID
- `BOT_NAME`, `BOT_USERNAME`

## Commands
See `/help` in bot.

## Owner
Set your Telegram ID in `OWNER_ID`.
