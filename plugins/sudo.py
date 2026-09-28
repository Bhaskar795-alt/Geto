from pyrogram import Client, filters
from config import Config
from database import db


@Client.on_message(filters.command("addsudo") & filters.user(Config.OWNER_ID))
async def addsudo(client, message):
    if len(message.command) < 2 and not message.reply_to_message:
        return await message.reply_text("Usage: /addsudo <user_id>")
    uid = message.reply_to_message.from_user.id if message.reply_to_message else int(message.command[1])
    await db.add_sudo(uid)
    await message.reply_text(f"✅ Sudo added: <code>{uid}</code>")


@Client.on_message(filters.command("rmsudo") & filters.user(Config.OWNER_ID))
async def rmsudo(client, message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /rmsudo <user_id>")
    await db.remove_sudo(int(message.command[1]))
    await message.reply_text("✅ Removed.")


@Client.on_message(filters.command("sudolist") & filters.user(Config.OWNER_ID))
async def sudolist(client, message):
    out = []
    async for d in db.get_sudo_list():
        out.append(f"• <code>{d['user_id']}</code>")
    if not out: return await message.reply_text("No sudo users.")
    await message.reply_text("<b>👑 Sudo Users:</b>\n" + "\n".join(out))
