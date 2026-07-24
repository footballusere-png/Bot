import asyncio
# Python 3.14 compatibility fix
asyncio.set_event_loop(asyncio.new_event_loop())

import dns.resolver
# DNS resolution fix for MongoDB
dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers = ['8.8.8.8']

import os
import logging
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
from hydrogram import Client, filters
from hydrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pymongo import MongoClient

# ---------- DUMMY WEB SERVER FOR RENDER PORT BINDING ----------
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is Running Alive!")

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

# Web Server ബാക്ക്ഗ്രൗണ്ടിൽ സ്റ്റാർട്ട് ചെയ്യുന്നു
Thread(target=run_web_server, daemon=True).start()
# -------------------------------------------------------------

# ---------- CONFIGURATION ----------
API_ID = 28300966
API_HASH = "c0a1fe56b13f260c62bc4838feb416d9"
BOT_TOKEN = "8686380719:AAGoYkxNrtrZ034sGSPbMxEG39lMZuHIm9Y"

# MongoDB Connection URI
MONGO_URI = "mongodb+srv://footballusere_db_user:Hnm6rRWbUHvhmbWd@cluster0.k2t3crf.mongodb.net/?appName=Cluster0"
DB_NAME = "AutoFilterBot"
# -----------------------------------

# MongoDB Connection Setup
mongo_client = MongoClient(MONGO_URI)
db = mongo_client[DB_NAME]
files_collection = db["files"]

# Hydrogram Client Setup
app = Client("AutoFilterBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

logging.basicConfig(level=logging.INFO)

# 1. /start Command Handling
@app.on_message(filters.command("start") & filters.private)
async def start_handler(client, message: Message):
    await message.reply_text(
        f"ഹലോ {message.from_user.first_name}!\n\n"
        "ഞാൻ ഒരു **Auto-Filter Search Bot** ആണ്. ഫയലുകൾ സെർച്ച് ചെയ്യാൻ അതിൻ്റെ പേര് മാത്രം ടൈപ്പ് ചെയ്തു അയക്കൂ!"
    )

# 2. ഫയലുകൾ Index ചെയ്യാനുള്ള System (Documents, Videos, Audio)
@app.on_message(filters.document | filters.video | filters.audio)
async def save_file(client, message: Message):
    media = message.document or message.video or message.audio
    if not media:
        return

    file_name = media.file_name or "Unknown File"
    file_id = media.file_id
    file_size = media.file_size

    # ഡാറ്റാബേസിൽ ഫയൽ ഉണ്ടോ എന്ന് പരിശോധിച്ച് ഇല്ലെങ്കിൽ മാത്രം ചേർക്കുന്നു
    if not files_collection.find_one({"file_id": file_id}):
        files_collection.insert_one({
            "file_name": file_name,
            "file_id": file_id,
            "file_size": file_size
        })
        await message.reply_text(f"✅ ഫയൽ ഡാറ്റാബേസിൽ സേവ് ചെയ്തു: `{file_name}`", quote=True)
    else:
        await message.reply_text("ℹ️ ഈ ഫയൽ മുൻപേ സേവ് ചെയ്തതാണ്.", quote=True)

# 3. Auto-Filter Search System
@app.on_message(filters.text & filters.private & ~filters.command(["start"]))
async def filter_search(client, message: Message):
    query = message.text.strip()
    
    # MongoDB-യിൽ സെർച്ച് ചെയ്യുന്നു (Case-insensitive)
    results = list(files_collection.find({"file_name": {"$regex": query, "$options": "i"}}).limit(10))

    if not results:
        await message.reply_text("❌ ക്ഷമിക്കണം, നിങ്ങൾ തിരഞ്ഞ ഫയൽ കണ്ടെത്താനായില്ല.")
        return

    # Results Inline Buttons ആയി നൽകുന്നു
    buttons = []
    for file in results:
        btn_text = f"📁 {file['file_name']}"
        buttons.append([InlineKeyboardButton(btn_text, callback_data=f"getfile_{file['_id']}")])

    reply_markup = InlineKeyboardMarkup(buttons)
    await message.reply_text(f"🔍 **'{query}'** എന്ന തിരച്ചിലിന്റെ റിസൾട്ടുകൾ:", reply_markup=reply_markup)

# 4. Button ക്ലിക്ക് ചെയ്യുമ്പോൾ ഫയൽ സെൻഡ് ചെയ്യുന്നത്
@app.on_callback_query(filters.regex(r"^getfile_"))
async def send_file_handler(client, callback_query):
    from bson.objectid import ObjectId
    file_id_db = callback_query.data.split("_")[1]
    
    file_data = files_collection.find_one({"_id": ObjectId(file_id_db)})
    if file_data:
        await callback_query.message.reply_cached_media(file_data["file_id"])
        await callback_query.answer("ഫയൽ അയച്ചിട്ടുണ്ട്!")
    else:
        await callback_query.answer("ഫയൽ കണ്ടെത്താനായില്ല!", show_alert=True)

# Bot റൺ ചെയ്യുന്നു
if __name__ == "__main__":
    print("Bot Started Successfully!")
    app.run()
