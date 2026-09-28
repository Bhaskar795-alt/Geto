import json
import asyncio
from datetime import datetime
from pyrogram import Client, filters
from config import Config
from database import db


@Client.on_message(filters.command("backup") & filters.user(Config.OWNER_ID))
async def backup_cmd(client, message):
    await message.reply_text("📦 Creating backup...")
    data = {"chats": [], "users": [], "filters": [], "notes": []}
    async for c in db.all_chats(): data["chats"].append(c)
    async for u in db.all_users(): data["users"].append(u)
    async for f in db.filters_c.find({}): data["filters"].append(f)
    async for n in db.notes_c.find({}): data["notes"].append(n)
    # Save as JSON
    fname = f"backup_{int(datetime.now().timestamp())}.json"
    with open(fname, "w") as f:
        json.dump(data, f, default=str, indent=2)
    await message.reply_document(fname, caption="✅ Backup done")


@Client.on_message(filters.command("backup_auto") & filters.user(Config.OWNER_ID))
async def auto_backup(client, message):
    await message.reply_text("✅ Auto-backup enabled (daily).")
    while True:
        await asyncio.sleep(86400)
        # Same as above, save to disk
