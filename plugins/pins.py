from pyrogram import Client, filters
from pyrogram.types import Message
from utils.permissions import is_admin


@Client.on_message(filters.command("pin") & filters.group)
async def pin_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    if not message.reply_to_message:
        return await message.reply_text("Reply to a message.")
    try:
        await message.reply_to_message.pin(disable_notification=False)
        await message.reply_text("📌 Pinned.")
    except Exception as e:
        await message.reply_text(f"❌ {e}")


@Client.on_message(filters.command("unpin") & filters.group)
async def unpin_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    try:
        await client.unpin_chat_message(message.chat.id)
        await message.reply_text("📌 Unpinned.")
    except Exception as e:
        await message.reply_text(f"❌ {e}")


@Client.on_message(filters.command("pinned") & filters.group)
async def pinned_cmd(client, message):
    try:
        p = await client.get_chat(message.chat.id)
        if p.pinned_message:
            await p.pinned_message.forward(message.chat.id)
        else:
            await message.reply_text("No pinned message.")
    except Exception as e:
        await message.reply_text(f"❌ {e}")
