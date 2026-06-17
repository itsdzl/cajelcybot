import json
import os

MEMORY_FILE = "memory_ai.json"

def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_memory(db):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(
            db,
            f,
            indent=4,
            ensure_ascii=False
        )

def get_user_memory(user_id):

    db = load_memory()

    uid = str(user_id)

    if uid not in db:

        db[uid] = {
            "profile": {},
            "facts": {},
            "summary": []
        }

        save_memory(db)

    return db[uid]

def save_user_memory(user_id, memory_data):

    db = load_memory()

    db[str(user_id)] = memory_data

    save_memory(db)

def update_profile(
    user_id,
    telegram_name=None,
    username=None
):

    db = load_memory()

    uid = str(user_id)

    if uid not in db:
        db[uid] = {
            "profile": {},
            "facts": {},
            "summary": []
        }

    if telegram_name:
        db[uid]["profile"]["telegram_name"] = telegram_name

    if username:
        db[uid]["profile"]["username"] = username

    save_memory(db)

def add_fact(user_id, key, value):

    db = load_memory()

    uid = str(user_id)

    if uid not in db:
        db[uid] = {
            "profile": {},
            "facts": {},
            "summary": []
        }

    db[uid]["facts"][key] = value

    save_memory(db)

def add_summary(user_id, text):

    db = load_memory()

    uid = str(user_id)

    if uid not in db:
        db[uid] = {
            "profile": {},
            "facts": {},
            "summary": []
        }

    if text not in db[uid]["summary"]:
        db[uid]["summary"].append(text)

    db[uid]["summary"] = db[uid]["summary"][-20:]

    save_memory(db)

def clear_memory(user_id):

    db = load_memory()

    uid = str(user_id)

    if uid in db:
        del db[uid]

    save_memory(db)
  
