import os
import asyncio
import logging
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

import certifi
from hydrogram import Client, filters
from hydrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pymongo import MongoClient

logging.basicConfig(level=logging.INFO)

# ---------- DUMMY WEB SERVER (FOR RENDER) ----------
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is Running Perfectly!")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

Thread(target=run_web_server, daemon=True).start()
# ----------------------------------------------------

# ---------- CREDENTIALS ----------
API_ID = 28300966
API_HASH = "c0a1fe56b13f260c62bc4838feb416d9"
BOT_TOKEN = "8686380719:AAGXFrU7MymK59RXU8iioBAAqn4O_fLuYtk"

# SSL പ്രശ്നം വരാതിരിക്കാൻ സ്ട്രിംഗിൽ നേരിട്ട് tlsAllowInvalidCertificates നൽകിയിരിക്കുന്നു
MONGO_URI = "mongodb+srv://footballusere_db_user:Hnm6rRWbUHvhmbWd@cluster0.k2t3crf.mongodb.net/?retryWrites=true&w=majority&tls=true&tlsAllowInvalidCertificates=true"
# ---------------------------------

# MongoDB Client Setup
try:
    mongo_client = MongoClient(MONGO_URI, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=5000)
    db = mongo_client["AutoFilterDB"]
    files_col = db["files"]
    print("MongoDB Connected Successfully!")
except Exception as e:
    print(f"MongoDB Connection Error: {e}")

# Telegram Bot Client
app = Client("FilterBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# 1. Start Command
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message: Message):
    await message.reply_text(
        f"ഹലോ **{message.from_user.first_name}**,\n\n"
        "ഞാൻ ഒരു **Auto-Filter Search Bot** ആണ്. ചാനലുകളിൽ ഇടുന്ന ഫയലുകൾ ഇൻഡക്സ് ചെയ്ത് സെർച്ച് ചെയ്യുന്ന ഫയലുകൾ ഇവിടെ നൽകാം."
    )

# 2. Save Files (Private Chat & Channels)
@app.on_message(filters.document | filters.video | filters.audio)
async def media_indexer(client, message: Message):
    media = message.document or message.video or message.audio
    if not media:
        return

    file_name = media.file_name or "Unknown_File"
    file_id = media.file_id
    file_size = media.file_size

    try:
        # Check if already exists
        if not files_col.find_one({"file_id": file_id}):
            files_col.insert_one({
                "file_name": file_name,
                "file_id": file_id,
                "file_size": file_size
            })
            
            if message.chat.type.value == "private":
                await message.reply_text(f"✅ **സേവ് ചെയ്തു:** `{file_name}`", quote=True)
            else:
                logging.info(f"Channel File Saved: {file_name}")
        else:
            if message.chat.type.value == "private":
                await message.reply_text("ℹ️ ഈ ഫയൽ മുൻപേ ഡാറ്റാബേസിൽ ഉള്ളതാണ്.", quote=True)
    except Exception as err:
        logging.error(f"Save Error: {err}")

# 3. Search Files
@app.on_message(filters.text & filters.private & ~filters.command("start"))
async def search_handler(client, message: Message):
    query = message.text.strip()
    
    try:
        # Case-insensitive Regex Search
        matches = list(files_col.find({"file_name": {"$regex": query, "$options": "i"}}).limit(10))

        if not matches:
            await message.reply_text("❌ **ക്ഷമിക്കണം, നിങ്ങൾ തിരഞ്ഞ ഫയൽ കണ്ടെത്താനായില്ല.**")
            return

        btn_list = []
        for file in matches:
            btn_title = f"📁 {file['file_name']}"
            btn_list.append([InlineKeyboardButton(btn_title, callback_data=f"file_{file['_id']}")])

        markup = InlineKeyboardMarkup(btn_list)
        await message.reply_text(f"🔍 **'{query}'** സെർച്ച് റിസൾട്ടുകൾ:", reply_markup=markup)

    except Exception as err:
        logging.error(f"Search Error: {err}")
        await message.reply_text("❌ ഡാറ്റാബേസ് കണക്ഷൻ പ്രോബ്ലം ആണ്. ദയവായി അല്പം കഴിഞ്ഞ് ശ്രമിക്കൂ.")

# 4. Callback Query Handler (Button Click)
@app.on_callback_query(filters.regex(r"^file_"))
async def file_callback(client, callback):
    from bson.objectid import ObjectId
    doc_id = callback.data.split("_")[1]

    try:
        file_info = files_col.find_one({"_id": ObjectId(doc_id)})
        if file_info:
            await callback.message.reply_cached_media(file_info["file_id"])
            await callback.answer("ഫയൽ അയച്ചിട്ടുണ്ട്!")
        else:
            await callback.answer("ഫയൽ ഡാറ്റാബേസിൽ ലഭ്യമല്ല!", show_alert=True)
    except Exception as err:
        logging.error(f"Callback Error: {err}")

if __name__ == "__main__":
    print("Bot is starting...")
    app.run()
