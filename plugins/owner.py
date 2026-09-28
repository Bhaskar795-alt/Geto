from pyrogram import Client, filters
from config import Config


@Client.on_message(filters.command("owner"))
async def owner_cmd(client, message):
    await message.reply_text(f"👑 <a href='tg://user?id={Config.OWNER_ID}'>Owner</a>")


@Client.on_message(filters.command("restart") & filters.user(Config.OWNER_ID))
async def restart_cmd(client, message):
    await message.reply_text("🔄 Restarting...")
    import os, sys
    os.execl(sys.executable, sys.executable, *sys.argv)


@Client.on_message(filters.command("leaves") & filters.user(Config.OWNER_ID))
async def leave_cmd(client, message):
    if len(message.command) < 2: return
    try:
        await client.leave_chat(int(message.command[1]))
        await message.reply_text("👋 Left.")
    except Exception as e:
        await message.reply_text(f"❌ {e}")
