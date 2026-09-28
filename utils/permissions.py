from pyrogram.enums import ChatMemberStatus
from config import Config
from database import db


async def is_admin(app, chat_id, user_id):
    if user_id == Config.OWNER_ID: return True
    if await db.is_sudo(user_id): return True
    try:
        m = await app.get_chat_member(chat_id, user_id)
        return m.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)
    except Exception:
        return False


async def is_owner(app, chat_id, user_id):
    if user_id == Config.OWNER_ID: return True
    try:
        m = await app.get_chat_member(chat_id, user_id)
        return m.status == ChatMemberStatus.OWNER
    except Exception:
        return False


async def bot_can_restrict(app, chat_id):
    try:
        me = await app.get_chat_member(chat_id, "me")
        return bool(getattr(me.privileges, "can_restrict_members", False))
    except Exception:
        return False
