from motor.motor_asyncio import AsyncIOMotorClient
from config import Config

client = AsyncIOMotorClient(Config.MONGO_URI)
db = client["getobot"]

users = db.users
chats = db.chats
warns = db.warns
mutes = db.mutes
bans = db.bans
filters_c = db.filters
notes_c = db.notes
locks = db.locks
blocklist = db.blocklist
allowlist = db.allowlist
emojis = db.emojis
approvals = db.approvals
join_requests = db.join_requests
sudo_users = db.sudo_users
disabled_c = db.disabled
logs_c = db.logs
feds = db.feds
fed_bans = db.fed_bans
floods = db.floods
captcha_c = db.captcha


# ---------- USERS ----------
async def add_user(user_id, name=""):
    await users.update_one({"user_id": user_id},
        {"$set": {"name": name}, "$setOnInsert": {"user_id": user_id}}, upsert=True)

async def get_user(user_id):
    return await users.find_one({"user_id": user_id})

def all_users():                          # ← def (not async def)
    return users.find({})

async def count_users():
    return await users.count_documents({})


# ---------- CHATS ----------
async def add_chat(chat_id, title=""):
    await chats.update_one({"chat_id": chat_id},
        {"$set": {"title": title}, "$setOnInsert": {"chat_id": chat_id}}, upsert=True)

async def get_chat(chat_id):
    c = await chats.find_one({"chat_id": chat_id})
    if not c:
        await add_chat(chat_id)
        c = await chats.find_one({"chat_id": chat_id})
    return c

async def set_chat_field(chat_id, field, value):
    await chats.update_one({"chat_id": chat_id},
        {"$set": {field: value}}, upsert=True)

def all_chats():                          # ← def (not async def)
    return chats.find({})

async def count_chats():
    return await chats.count_documents({})


# ---------- WARNS ----------
async def add_warn(chat_id, user_id, reason=""):
    await warns.update_one(
        {"chat_id": chat_id, "user_id": user_id},
        {"$inc": {"count": 1}, "$push": {"reasons": reason}}, upsert=True)
    doc = await warns.find_one({"chat_id": chat_id, "user_id": user_id})
    return doc.get("count", 1) if doc else 1

async def get_warns(chat_id, user_id):
    doc = await warns.find_one({"chat_id": chat_id, "user_id": user_id})
    return doc.get("count", 0) if doc else 0

async def get_warn_reasons(chat_id, user_id):
    doc = await warns.find_one({"chat_id": chat_id, "user_id": user_id})
    return doc.get("reasons", []) if doc else []

async def remove_last_warn(chat_id, user_id):
    doc = await warns.find_one({"chat_id": chat_id, "user_id": user_id})
    if not doc or doc.get("count", 0) <= 0:
        return 0
    new_count = doc["count"] - 1
    if new_count <= 0:
        await warns.delete_one({"chat_id": chat_id, "user_id": user_id})
        return 0
    reasons = doc.get("reasons", [])
    if reasons: reasons.pop()
    await warns.update_one({"chat_id": chat_id, "user_id": user_id},
        {"$set": {"count": new_count, "reasons": reasons}})
    return new_count

async def reset_warns(chat_id, user_id):
    await warns.delete_one({"chat_id": chat_id, "user_id": user_id})


# ---------- MUTES ----------
async def mute_user(chat_id, user_id, until=0, reason=""):
    await mutes.update_one(
        {"chat_id": chat_id, "user_id": user_id},
        {"$set": {"until": until, "reason": reason}}, upsert=True)

async def unmute_user(chat_id, user_id):
    await mutes.delete_one({"chat_id": chat_id, "user_id": user_id})

async def is_muted(chat_id, user_id):
    return await mutes.find_one({"chat_id": chat_id, "user_id": user_id})

def get_mutelist(chat_id):                # ← def (not async def)
    return mutes.find({"chat_id": chat_id})


# ---------- FILTERS ----------
async def save_filter(chat_id, keyword, reply, msg_type="text", file_id="", buttons=None):
    await filters_c.update_one(
        {"chat_id": chat_id, "keyword": keyword.lower()},
        {"$set": {"reply": reply, "msg_type": msg_type,
                  "file_id": file_id, "buttons": buttons or []}}, upsert=True)

async def get_filter(chat_id, keyword):
    return await filters_c.find_one({"chat_id": chat_id, "keyword": keyword.lower()})

def get_all_filters(chat_id):             # ← def (not async def)
    return filters_c.find({"chat_id": chat_id})

async def delete_filter(chat_id, keyword):
    await filters_c.delete_one({"chat_id": chat_id, "keyword": keyword.lower()})

async def delete_all_filters(chat_id):
    await filters_c.delete_many({"chat_id": chat_id})


# ---------- NOTES ----------
async def save_note(chat_id, name, reply, msg_type="text", file_id="", buttons=None):
    await notes_c.update_one(
        {"chat_id": chat_id, "name": name.lower()},
        {"$set": {"reply": reply, "msg_type": msg_type,
                  "file_id": file_id, "buttons": buttons or []}}, upsert=True)

async def get_note(chat_id, name):
    return await notes_c.find_one({"chat_id": chat_id, "name": name.lower()})

def get_all_notes(chat_id):               # ← def (not async def)
    return notes_c.find({"chat_id": chat_id})

async def delete_note(chat_id, name):
    await notes_c.delete_one({"chat_id": chat_id, "name": name.lower()})

async def delete_all_notes(chat_id):
    await notes_c.delete_many({"chat_id": chat_id})


# ---------- LOCKS ----------
async def set_lock(chat_id, lock_type, value=True):
    await locks.update_one({"chat_id": chat_id},
        {"$set": {lock_type: value}}, upsert=True)

async def get_locks(chat_id):
    return await locks.find_one({"chat_id": chat_id}) or {}


# ---------- BLOCKLIST ----------
async def add_block(chat_id, word):
    await blocklist.update_one(
        {"chat_id": chat_id, "word": word.lower()},
        {"$set": {"word": word.lower()}}, upsert=True)

async def remove_block(chat_id, word):
    await blocklist.delete_one({"chat_id": chat_id, "word": word.lower()})

def get_blocks(chat_id):                  # ← def (not async def)
    return blocklist.find({"chat_id": chat_id})

async def clear_blocks(chat_id):
    await blocklist.delete_many({"chat_id": chat_id})


# ---------- ALLOWLIST ----------
async def add_allow(chat_id, value):
    await allowlist.update_one(
        {"chat_id": chat_id, "value": value.lower()},
        {"$set": {"value": value.lower()}}, upsert=True)

async def remove_allow(chat_id, value):
    await allowlist.delete_one({"chat_id": chat_id, "value": value.lower()})

def get_allows(chat_id):                  # ← def (not async def)
    return allowlist.find({"chat_id": chat_id})

async def clear_allows(chat_id):
    await allowlist.delete_many({"chat_id": chat_id})


# ---------- EMOJIS ----------
async def save_emoji(name, emoji_id, fallback, owner_id):
    await emojis.update_one(
        {"name": name.upper()},
        {"$set": {"name": name.upper(), "emoji_id": emoji_id,
                  "fallback": fallback, "owner_id": owner_id}}, upsert=True)

async def get_emoji(name):
    return await emojis.find_one({"name": name.upper()})

def get_all_emojis():                     # ← def (not async def)
    return emojis.find({})

async def delete_emoji(name):
    await emojis.delete_one({"name": name.upper()})


# ---------- APPROVALS ----------
async def approve_user(chat_id, user_id, reason=""):
    await approvals.update_one(
        {"chat_id": chat_id, "user_id": user_id},
        {"$set": {"reason": reason}}, upsert=True)

async def is_approved(chat_id, user_id):
    return await approvals.find_one({"chat_id": chat_id, "user_id": user_id})

async def unapprove_user(chat_id, user_id):
    await approvals.delete_one({"chat_id": chat_id, "user_id": user_id})

def get_approved_list(chat_id):           # ← def (not async def)
    return approvals.find({"chat_id": chat_id})

async def unapprove_all(chat_id):
    await approvals.delete_many({"chat_id": chat_id})


# ---------- SUDO ----------
async def add_sudo(user_id):
    await sudo_users.update_one({"user_id": user_id},
        {"$set": {"user_id": user_id}}, upsert=True)

async def remove_sudo(user_id):
    await sudo_users.delete_one({"user_id": user_id})

def get_sudo_list():                      # ← def (not async def)
    return sudo_users.find({})

async def is_sudo(user_id):
    if user_id == Config.OWNER_ID: return True
    return await sudo_users.find_one({"user_id": user_id}) is not None


# ---------- DISABLED COMMANDS ----------
async def disable_cmd(chat_id, cmd):
    await disabled_c.update_one(
        {"chat_id": chat_id, "cmd": cmd.lower()},
        {"$set": {"cmd": cmd.lower()}}, upsert=True)

async def enable_cmd(chat_id, cmd):
    await disabled_c.delete_one({"chat_id": chat_id, "cmd": cmd.lower()})

def get_disabled(chat_id):                # ← def (not async def)
    return disabled_c.find({"chat_id": chat_id})

async def is_disabled(chat_id, cmd):
    return await disabled_c.find_one({"chat_id": chat_id, "cmd": cmd.lower()}) is not None


# ---------- LOGS ----------
async def save_log(chat_id, category, text):
    await logs_c.insert_one({"chat_id": chat_id, "category": category, "text": text})

async def get_log_chat(chat_id):
    c = await get_chat(chat_id)
    return c.get("log_channel", 0)


# ---------- FEDERATION ----------
async def create_fed(fed_id, name, owner):
    await feds.update_one({"fed_id": fed_id},
        {"$set": {"fed_id": fed_id, "name": name, "owner": owner,
                  "chats": [], "admins": [owner]}}, upsert=True)

async def get_fed(fed_id):
    return await feds.find_one({"fed_id": fed_id})

async def delete_fed(fed_id):
    await feds.delete_one({"fed_id": fed_id})

async def join_fed(fed_id, chat_id):
    await feds.update_one({"fed_id": fed_id}, {"$addToSet": {"chats": chat_id}})

async def leave_fed(fed_id, chat_id):
    await feds.update_one({"fed_id": fed_id}, {"$pull": {"chats": chat_id}})

async def add_fed_ban(fed_id, user_id, reason=""):
    await fed_bans.update_one({"fed_id": fed_id, "user_id": user_id},
        {"$set": {"reason": reason}}, upsert=True)

async def remove_fed_ban(fed_id, user_id):
    await fed_bans.delete_one({"fed_id": fed_id, "user_id": user_id})

def get_fed_bans(fed_id):                 # ← def (not async def)
    return fed_bans.find({"fed_id": fed_id})

async def is_fed_banned(fed_id, user_id):
    return await fed_bans.find_one({"fed_id": fed_id, "user_id": user_id})


# ---------- FLOOD ----------
async def add_flood(chat_id, user_id):
    result = await floods.find_one_and_update(     # ← Return count
        {"chat_id": chat_id, "user_id": user_id},
        {"$inc": {"count": 1}},
        upsert=True,
        return_document=True
    )
    return result.get("count", 1) if result else 1

async def get_flood(chat_id, user_id):
    doc = await floods.find_one({"chat_id": chat_id, "user_id": user_id})
    return doc.get("count", 0) if doc else 0

async def reset_flood(chat_id, user_id):
    await floods.delete_one({"chat_id": chat_id, "user_id": user_id})


# ---------- CAPTCHA ----------
async def save_captcha(chat_id, user_id, answer):
    await captcha_c.update_one(
        {"chat_id": chat_id, "user_id": user_id},
        {"$set": {"answer": answer}}, upsert=True)

async def get_captcha(chat_id, user_id):
    return await captcha_c.find_one({"chat_id": chat_id, "user_id": user_id})

async def delete_captcha(chat_id, user_id):
    await captcha_c.delete_one({"chat_id": chat_id, "user_id": user_id})
