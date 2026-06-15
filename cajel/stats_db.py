import os
import json

STATS_FILE = "stats.json"

def load_stats():
if os.path.exists(STATS_FILE):
with open(STATS_FILE, "r", encoding="utf-8") as f:
try:
return json.load(f)
except:
return {}
return {}

def save_stats(db):
with open(STATS_FILE, "w", encoding="utf-8") as f:
json.dump(db, f, indent=4, ensure_ascii=False)

def update_chat_data(chat_id, chat_type, name):
db = load_stats()
cid = str(chat_id)

if cid not in db:
    db[cid] = {
        "type": chat_type,
        "name": name,
        "last_seen": "active",
        "banned": False
    }
else:
    db[cid]["type"] = chat_type
    db[cid]["name"] = name
    db[cid]["last_seen"] = "active"
    db[cid].setdefault("banned", False)

save_stats(db)

def get_summary():
db = load_stats()
total = len(db)
private = sum(1 for v in db.values() if v.get("type") == "private")
groups = sum(1 for v in db.values() if v.get("type") in ["group", "supergroup"])
banned = sum(1 for v in db.values() if v.get("banned"))

return {
    "total": total,
    "private": private,
    "groups": groups,
    "banned": banned
}

def get_all_users():
return load_stats()

def ban_user(user_id):
db = load_stats()
uid = str(user_id)

if uid not in db:
    return False

db[uid]["banned"] = True
save_stats(db)
return True

def unban_user(user_id):
db = load_stats()
uid = str(user_id)

if uid not in db:
    return False

db[uid]["banned"] = False
save_stats(db)
return True

def is_banned(user_id):
db = load_stats()
uid = str(user_id)

return db.get(uid, {}).get("banned", False)

def get_banlist():
db = load_stats()

return {
    uid: data
    for uid, data in db.items()
    if data.get("banned")
}
