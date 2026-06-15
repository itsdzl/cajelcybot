import os
import json

STATS_FILE = "stats.json"

def load_stats():
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            try: return json.load(f)
            except: return {}
    return {}

def save_stats(db):
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=4, ensure_ascii=False)

def update_chat_data(chat_id, chat_type, name):
    db = load_stats()
    cid = str(chat_id)
    db[cid] = {
        "type": chat_type,
        "name": name,
        "last_seen": "active"
    }
    save_stats(db)

def get_stats_summary():
    db = load_stats()
    total = len(db)
    private = sum(1 for v in db.values() if v.get("type") == "private")
    groups = sum(1 for v in db.values() if v.get("type") in ["group", "supergroup"])
    return {"total": total, "private": private, "groups": groups}
    
