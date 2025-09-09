# database.py
from pymongo import MongoClient
from config import MONGO_URI

client = MongoClient(MONGO_URI)
db = client.get_database("MangaBotDB")
state_collection = db.get_collection("bot_state")

def get_state():
    """ডেটাবেস থেকে বটের বর্তমান অবস্থা লোড করে"""
    state = state_collection.find_one({"_id": "global_state"})
    if not state:
        # যদি ডেটাবেসে কোনো ডেটা না থাকে, তাহলে একটি খালি কাঠামো তৈরি করে
        return {"main_posts_created": [], "chapters_posted": {}}
    return state

def save_state(data):
    """বটের বর্তমান অবস্থাকে ডেটাবেসে সেভ করে"""
    state_collection.update_one(
        {"_id": "global_state"},
        {"$set": data},
        upsert=True # যদি কোনো ডেটা না থাকে, তাহলে নতুন করে তৈরি করবে
    )
