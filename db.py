from pymongo import MongoClient

client = MongoClient("localhost", 27017)
db = client["jungle_errand"]
users_collection = db["users"]
errands_collection = db["errands"]
