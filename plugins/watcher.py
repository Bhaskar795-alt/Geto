from pyrogram import Client, filters
from database import db
from utils.permissions import is_admin


@Client.on_message(filters.group & ~filters.service, group=99)
async def watcher(client, message):
    if message.from_user and await is_admin(client, message.chat.id, message.from_user.id):
        return

    if message.from_user and await db.is_approved(message.chat.id, message.from_user.id):
        return

    if message.from_user:
        m = await db.is_muted(message.chat.id, message.from_user.id)
        if m:
            try: await message.delete()
            except: pass
            return

    locks = await db.get_locks(message.chat.id)
    def locked(key): return locks.get(key, False)

    delete = False
    if locked("links") and message.text and ("http://" in message.text or "https://" in message.text or "t.me/" in message.text):
        delete = True
    if locked("forward") and message.forward_date:
        delete = True
    if locked("photo") and message.photo: delete = True
    if locked("video") and message.video: delete = True
    if locked("audio") and message.audio: delete = True
    if locked("voice") and message.voice: delete = True
    if locked("document") and message.document: delete = True
    if locked("sticker") and message.sticker: delete = True
    if locked("animation") and message.animation: delete = True
    if locked("bot") and message.from_user and message.from_user.is_bot: delete = True
    if locked("inline") and message.via_bot: delete = True

    if delete:
        try: await message.delete()
        except: pass
        return

    if message.text or message.caption:
        text = (message.text or message.caption).lower()
        async for b in db.get_blocks(message.chat.id):
            if b["word"] in text:
                try: await message.delete()
                except: pass
                return
