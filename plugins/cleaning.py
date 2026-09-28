from pyrogram import Client, filters
from utils.permissions import is_admin


@Client.on_message(filters.command(["del", "delete"]) & filters.group)
async def del_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    if message.reply_to_message:
        try:
            await message.reply_to_message.delete()
            await message.delete()
        except Exception as e:
            await message.reply_text(f"❌ {e}")


@Client.on_message(filters.command("purge") & filters.group)
async def purge_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    if not message.reply_to_message:
        return await message.reply_text("Reply to a message to purge from.")
    start_id = message.reply_to_message.id
    end_id = message.id
    ids = list(range(start_id, end_id + 1))
    try:
        for i in range(0, len(ids), 100):
            await client.delete_messages(message.chat.id, ids[i:i+100])
    except Exception as e:
        await message.reply_text(f"❌ {e}")
