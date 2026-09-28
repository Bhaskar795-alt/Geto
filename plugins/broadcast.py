import asyncio
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from config import Config
from database import db


@Client.on_message(filters.command("broadcast") & filters.user(Config.OWNER_ID))
async def broadcast_users(client, message):
    if not message.reply_to_message:
        return await message.reply_text("Reply to a message to broadcast.")
    sent, failed = 0, 0
    status = await message.reply_text("📢 Broadcasting...")
    async for u in db.all_users():
        try:
            await message.reply_to_message.copy(u["user_id"])
            sent += 1
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except Exception:
            failed += 1
    await status.edit_text(f"✅ Broadcast done.\n📤 Sent: {sent}\n❌ Failed: {failed}")


@Client.on_message(filters.command("gbroadcast") & filters.user(Config.OWNER_ID))
async def broadcast_groups(client, message):
    if not message.reply_to_message:
        return await message.reply_text("Reply to a message.")
    sent, failed = 0, 0
    status = await message.reply_text("📢 Broadcasting to groups...")
    async for c in db.all_chats():
        try:
            await message.reply_to_message.copy(c["chat_id"])
            sent += 1
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except Exception:
            failed += 1
    await status.edit_text(f"✅ Done.\n📤 {sent}\n❌ {failed}")
