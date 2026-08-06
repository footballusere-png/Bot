# database.py
import motor.motor_asyncio
from config import DATABASE_URL

# SSL എറർ വരാതിരിക്കാൻ tlsAllowInvalidCertificates=True നൽകിയിരിക്കുന്നു
client = motor.motor_asyncio.AsyncIOMotorClient(
    DATABASE_URL, 
    tlsAllowInvalidCertificates=True
)
db = client["FileSearchBot"]

users_collection = db["users"]
files_collection = db["files"]

async def add_user(user_id):
    if not await users_collection.find_one({"user_id": user_id}):
        await users_collection.insert_one({"user_id": user_id})

async def save_file(file_id, file_name, file_size, caption):
    # ഡ്യൂപ്ലിക്കേറ്റ് വരാതിരിക്കാൻ പരിശോധിക്കുന്നു
    if not await files_collection.find_one({"file_id": file_id}):
        await files_collection.insert_one({
            "file_id": file_id,
            "file_name": file_name,
            "file_size": file_size,
            "caption": caption
        })

async def total_users_count():
    return await users_collection.count_documents({})

async def total_files_count():
    return await files_collection.count_documents({})
