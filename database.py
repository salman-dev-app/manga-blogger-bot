# database.py
from pymongo import MongoClient
from config import MONGO_URI

client = MongoClient(MONGO_URI)
db = client.get_database("MangaBotDB")
state_collection = db.get_collection("bot_state")

def get_state():
    state = state_collection.find_one({"_id": "global_state"})
    if not state:
        return {"main_posts_created": [], "chapters_posted": {}}
    return state

def save_state(data):
    state_collection.update_one(
        {"_id": "global_state"},
        {"$set": data},
        upsert=True
    )
