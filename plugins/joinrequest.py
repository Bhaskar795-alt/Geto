from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import Config
from database import db
from utils.permissions import is_admin


@Client.on_chat_join_request()
async def on_join_request(client, request):
    chat = await db.get_chat(request.chat.id)
    if not chat.get("joinrequest_notify", True): return
    user = request.from_user
    text = (f"📨 <b>New Join Request</b>\n\n"
            f"👤 <b>Name:</b> {user.first_name or ''}\n"
            f"🔗 <b>Username:</b> @{user.username or 'None'}\n"
            f"🆔 <b>ID:</b> <code>{user.id}</code>\n"
            f"💬 <b>Chat:</b> {request.chat.title}")
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🟢 ACCEPT", callback_data=f"jr_accept:{request.chat.id}:{user.id}"),
         InlineKeyboardButton("🔴 DECLINE", callback_data=f"jr_decline:{request.chat.id}:{user.id}")],
        [InlineKeyboardButton("👤 USER INFO", url=f"tg://user?id={user.id}")]
    ])
    try:
        await client.send_message(request.chat.id, text, reply_markup=buttons)
    except Exception:
        if Config.LOG_CHANNEL:
            await client.send_message(Config.LOG_CHANNEL, text, reply_markup=buttons)


@Client.on_callback_query(filters.regex(r"^jr_(accept|decline):"))
async def jr_action(client, cb):
    _, action, chat_id, user_id = cb.data.split(":")
    chat_id, user_id = int(chat_id), int(user_id)
    if not await is_admin(client, chat_id, cb.from_user.id):
        return await cb.answer("❌ Admin only.", show_alert=True)
    try:
        if action == "accept":
            await client.approve_chat_join_request(chat_id, user_id)
            await cb.edit_message_text(cb.message.text + f"\n\n✅ <b>Approved by</b> {cb.from_user.mention}")
        else:
            await client.decline_chat_join_request(chat_id, user_id)
            await cb.edit_message_text(cb.message.text + f"\n\n❌ <b>Declined by</b> {cb.from_user.mention}")
    except Exception as e:
        return await cb.answer(f"Error: {e}", show_alert=True)
    await cb.answer("Done ✅")


@Client.on_message(filters.command("joinrequests") & filters.group)
async def jr_toggle(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    chat = await db.get_chat(message.chat.id)
    state = not chat.get("joinrequest_notify", True)
    await db.set_chat_field(message.chat.id, "joinrequest_notify", state)
    await message.reply_text(f"✅ Join-request notifications: {'ON' if state else 'OFF'}")


@Client.on_message(filters.command("autoapprove") & filters.group)
async def auto_approve(client, message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Admin only.")
    chat = await db.get_chat(message.chat.id)
    state = not chat.get("auto_approve", False)
    await db.set_chat_field(message.chat.id, "auto_approve", state)
    await message.reply_text(f"✅ Auto-approve: {'ON' if state else 'OFF'}")
