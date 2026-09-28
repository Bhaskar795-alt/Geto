from pyrogram import Client, filters
from database import db
from utils.permissions import is_admin


# =========================================================
# CONNECT
# =========================================================

@Client.on_message(filters.command("connect"))
async def connect_cmd(client, message):
    user_id = message.from_user.id

    # In group: connect to current chat
    if message.chat.type in ("group", "supergroup"):
        if not await is_admin(client, message.chat.id, user_id):
            return await message.reply_text("❌ You must be admin in this chat.")

        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {
                "connected_chat": message.chat.id,
                "connection_history": [message.chat.id]
            }},
            upsert=True
        )
        return await message.reply_text(
            f"✅ <b>Connected</b> to:\n"
            f"💬 {message.chat.title}\n"
            f"🆔 <code>{message.chat.id}</code>"
        )

    # In private: connect by ID or username
    if message.chat.type == "private":
        if len(message.command) < 2:
            # List recent connections
            user = await db.get_user(user_id)
            history = user.get("connection_history", []) if user else []
            if not history:
                return await message.reply_text(
                    "📋 <b>No recent connections.</b>\n\n"
                    "Usage:\n"
                    "• In group: /connect\n"
                    "• In PM: /connect &lt;chat_id&gt;\n"
                    "• In PM: /connect @username"
                )
            lines = ["<b>📋 Recent Connections:</b>\n"]
            for cid in history[:10]:
                try:
                    chat = await client.get_chat(cid)
                    lines.append(f"• {chat.title} — <code>{cid}</code>")
                except Exception:
                    lines.append(f"• <code>{cid}</code> (inaccessible)")
            return await message.reply_text("\n".join(lines))

        target = message.command[1]
        try:
            if target.startswith("-") or target.isdigit():
                cid = int(target)
            else:
                if target.startswith("@"):
                    target = target[1:]
                chat = await client.get_chat(target)
                cid = chat.id

            # Verify admin
            member = await client.get_chat_member(cid, user_id)
            status = str(member.status).lower()
            if "administrator" not in status and "owner" not in status:
                return await message.reply_text("❌ You must be admin in that chat.")

            # Save connection
            user = await db.get_user(user_id)
            history = user.get("connection_history", []) if user else []
            history = [cid] + [c for c in history if c != cid]

            await db.users.update_one(
                {"user_id": user_id},
                {"$set": {
                    "connected_chat": cid,
                    "connection_history": history[:20]
                }},
                upsert=True
            )

            target_chat = await client.get_chat(cid)
            await message.reply_text(
                f"✅ <b>Connected</b> to:\n"
                f"💬 {target_chat.title}\n"
                f"🆔 <code>{cid}</code>"
            )
        except Exception as e:
            await message.reply_text(f"❌ {e}")


# =========================================================
# DISCONNECT
# =========================================================

@Client.on_message(filters.command("disconnect"))
async def disconnect_cmd(client, message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    if not user or not user.get("connected_chat"):
        return await message.reply_text("❌ Not connected to any chat.")

    cid = user.get("connected_chat")
    await db.users.update_one(
        {"user_id": user_id},
        {"$unset": {"connected_chat": ""}}
    )
    await message.reply_text(f"✅ <b>Disconnected</b> from <code>{cid}</code>")


# =========================================================
# RECONNECT
# =========================================================

@Client.on_message(filters.command("reconnect"))
async def reconnect_cmd(client, message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    if not user:
        return await message.reply_text("❌ No connection history.")

    history = user.get("connection_history", [])
    if not history:
        return await message.reply_text("❌ No connection history.")

    cid = history[0]
    try:
        chat = await client.get_chat(cid)
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"connected_chat": cid}}
        )
        await message.reply_text(
            f"✅ <b>Reconnected</b> to:\n"
            f"💬 {chat.title}\n"
            f"🆔 <code>{cid}</code>"
        )
    except Exception as e:
        await message.reply_text(f"❌ {e}")


# =========================================================
# CONNECTION INFO
# =========================================================

@Client.on_message(filters.command("connection"))
async def connection_cmd(client, message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    if not user or not user.get("connected_chat"):
        return await message.reply_text("❌ Not connected to any chat.")

    cid = user["connected_chat"]
    try:
        chat = await client.get_chat(cid)
        history = user.get("connection_history", [])
        history_lines = []
        for h in history[:5]:
            if h == cid:
                continue
            try:
                c = await client.get_chat(h)
                history_lines.append(f"• {c.title} — <code>{h}</code>")
            except Exception:
                history_lines.append(f"• <code>{h}</code>")

        text = (
            f"📋 <b>Current Connection:</b>\n"
            f"💬 {chat.title}\n"
            f"🆔 <code>{cid}</code>\n\n"
        )
        if history_lines:
            text += "<b>Recent:</b>\n" + "\n".join(history_lines)

        await message.reply_text(text)
    except Exception as e:
        await message.reply_text(f"❌ {e}")


# =========================================================
# HELPER — Get Connected Chat (for other plugins)
# =========================================================

async def get_connected_chat(user_id):
    """Returns connected chat_id or None."""
    user = await db.get_user(user_id)
    if not user:
        return None
    return user.get("connected_chat")
