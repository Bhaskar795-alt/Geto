from pyrogram import Client, filters
from utils.permissions import is_admin


@Client.on_message(filters.command("pin") & filters.group)
async def pin_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    if not message.reply_to_message:
        return await message.reply_text("❌ Reply to a message to pin it.")
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
        if message.reply_to_message:
            await client.unpin_chat_message(
                chat_id=message.chat.id,
                message_id=message.reply_to_message.id
            )
            await message.reply_text("📌 Unpinned.")
        else:
            chat = await client.get_chat(message.chat.id)
            if chat.pinned_message:
                await client.unpin_chat_message(
                    chat_id=message.chat.id,
                    message_id=chat.pinned_message.id
                )
                await message.reply_text("📌 Latest pinned message unpinned.")
            else:
                await message.reply_text("❌ No pinned message found.")
    except Exception as e:
        await message.reply_text(f"❌ {e}")


@Client.on_message(filters.command("pinned") & filters.group)
async def pinned_cmd(client, message):
    try:
        chat = await client.get_chat(message.chat.id)
        if chat.pinned_message:
            await chat.pinned_message.forward(message.chat.id)
        else:
            await message.reply_text("❌ No pinned message.")
    except Exception as e:
        await message.reply_text(f"❌ {e}")
