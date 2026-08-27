import os

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

mongo_host = os.environ.get("MONGO_URI", "localhost")

client = MongoClient(mongo_host, 27017)
db = client["jungle_errand"]
users_collection = db["users"]
errands_collection = db["errands"]
