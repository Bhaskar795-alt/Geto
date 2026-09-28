from pyrogram import Client, filters
from database import db
from utils.permissions import is_admin


# =========================================================
# DEL — Delete replied message
# =========================================================

@Client.on_message(filters.command(["del", "delete"]) & filters.group)
async def del_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    if not message.reply_to_message:
        return await message.reply_text("❌ Reply to a message to delete it.")
    try:
        await message.reply_to_message.delete()
        await message.delete()
    except Exception as e:
        await message.reply_text(f"❌ {e}")


# =========================================================
# PURGE — Delete from replied to current
# =========================================================

@Client.on_message(filters.command("purge") & filters.group)
async def purge_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    if not message.reply_to_message:
        return await message.reply_text(
            "❌ Reply to a message to purge from.\n"
            "Usage: /purge or /purge <count>"
        )

    start_id = message.reply_to_message.id
    end_id = message.id

    # /purge X — delete X messages after reply
    if len(message.command) > 1 and message.command[1].isdigit():
        count = int(message.command[1])
        end_id = start_id + count

    ids = list(range(start_id, end_id + 1))
    try:
        for i in range(0, len(ids), 100):
            await client.delete_messages(message.chat.id, ids[i:i+100])
    except Exception as e:
        await message.reply_text(f"❌ {e}")
        return

    try:
        confirm = await message.reply_text(f"🗑️ Purged <code>{len(ids)}</code> messages.")
        import asyncio
        await asyncio.sleep(3)
        await confirm.delete()
    except Exception:
        pass


# =========================================================
# SPURGE — Silent purge (no final message)
# =========================================================

@Client.on_message(filters.command("spurge") & filters.group)
async def spurge_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    if not message.reply_to_message:
        return await message.reply_text("❌ Reply to a message to purge from.")

    start_id = message.reply_to_message.id
    end_id = message.id

    if len(message.command) > 1 and message.command[1].isdigit():
        count = int(message.command[1])
        end_id = start_id + count

    ids = list(range(start_id, end_id + 1))
    try:
        for i in range(0, len(ids), 100):
            await client.delete_messages(message.chat.id, ids[i:i+100])
    except Exception:
        pass


# =========================================================
# PURGEFROM — Mark start message
# =========================================================

@Client.on_message(filters.command("purgefrom") & filters.group)
async def purgefrom_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    if not message.reply_to_message:
        return await message.reply_text("❌ Reply to the FIRST message to purge from.")

    start_id = message.reply_to_message.id
    await db.set_chat_field(message.chat.id, "purge_from_id", start_id)
    try:
        await message.delete()
    except Exception:
        pass

    try:
        confirm = await message.reply_text(
            f"📌 Marked start message: <code>{start_id}</code>\n"
            f"Now reply to the end message with /purgeto"
        )
        import asyncio
        await asyncio.sleep(5)
        await confirm.delete()
    except Exception:
        pass


# =========================================================
# PURGETO — Delete between purgefrom and purgeto
# =========================================================

@Client.on_message(filters.command("purgeto") & filters.group)
async def purgeto_cmd(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    if not message.reply_to_message:
        return await message.reply_text("❌ Reply to the LAST message to purge to.")

    chat = await db.get_chat(message.chat.id)
    start_id = chat.get("purge_from_id")
    if not start_id:
        return await message.reply_text("❌ No /purgefrom marked. Use /purgefrom first.")

    end_id = message.reply_to_message.id
    if end_id < start_id:
        start_id, end_id = end_id, start_id

    ids = list(range(start_id, end_id + 1))
    try:
        for i in range(0, len(ids), 100):
            await client.delete_messages(message.chat.id, ids[i:i+100])
    except Exception as e:
        await message.reply_text(f"❌ {e}")
        return

    await db.set_chat_field(message.chat.id, "purge_from_id", None)

    try:
        confirm = await message.reply_text(f"🗑️ Purged <code>{len(ids)}</code> messages.")
        import asyncio
        await asyncio.sleep(3)
        await confirm.delete()
    except Exception:
        pass
