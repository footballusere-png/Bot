import os
import logging
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

import firebase_admin
from firebase_admin import credentials, db
from hydrogram import Client, filters
from hydrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

logging.basicConfig(level=logging.INFO)

# ---------- DUMMY WEB SERVER (FOR RENDER) ----------
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is Running Perfectly with Realtime Database!")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

Thread(target=run_web_server, daemon=True).start()
# ----------------------------------------------------

# ---------- FIREBASE REALTIME DATABASE SETUP ----------
FIREBASE_DB_URL = "https://a-one-chat-e3642-default-rtdb.firebaseio.com"

try:
    # Initialize without service account key for public/rules-allowed RTDB
    if not firebase_admin._apps:
        firebase_admin.initialize_app(options={
            'databaseURL': FIREBASE_DB_URL
        })
    files_ref = db.reference('files')
    print("✅ Firebase Realtime Database Connected Successfully!")
except Exception as e:
    print(f"❌ Firebase Connection Error: {e}")
# ------------------------------------------------------

# ---------- CREDENTIALS ----------
API_ID = 28300966
API_HASH = "c0a1fe56b13f260c62bc4838feb416d9"
BOT_TOKEN = "8686380719:AAGXFrU7MymK59RXU8iioBAAqn4O_fLuYtk"
# ---------------------------------

app = Client("RTDBFilterBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# 1. Start Command
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message: Message):
    await message.reply_text(
        f"ഹലോ **{message.from_user.first_name}**,\n\n"
        "ഞാൻ ഒരു **Auto-Filter Search Bot (Realtime DB)** ആണ്. ഫയലുകൾ സെർച്ച് ചെയ്യാൻ അതിൻ്റെ പേര് മാത്രം ടൈപ്പ് ചെയ്തു അയക്കൂ!"
    )

# 2. Save Files (Private Chat & Channels)
@app.on_message((filters.document | filters.video | filters.audio) & (filters.private | filters.channel))
async def media_indexer(client, message: Message):
    media = message.document or message.video or message.audio
    if not media:
        return

    file_name = media.file_name or "Unknown_File"
    file_id = media.file_id
    file_size = media.file_size

    # Base64 unsafe characters clean up for Firebase key
    safe_key = file_id.replace("/", "_").replace(".", "_").replace("$", "_").replace("[", "_").replace("]", "_").replace("#", "_")

    try:
        # Check if file exists
        existing_file = files_ref.child(safe_key).get()
        if not existing_file:
            files_ref.child(safe_key).set({
                "file_name": file_name,
                "file_name_lower": file_name.lower(),
                "file_id": file_id,
                "file_size": file_size
            })
            
            if message.chat.type.value == "private":
                await message.reply_text(f"✅ **ഫയൽ Realtime DB-യിൽ സേവ് ചെയ്തു:** `{file_name}`", quote=True)
            else:
                logging.info(f"Channel File Saved: {file_name}")
        else:
            if message.chat.type.value == "private":
                await message.reply_text("ℹ️ ഈ ഫയൽ മുൻപേ ഡാറ്റാബേസിൽ ഉള്ളതാണ്.", quote=True)
    except Exception as err:
        logging.error(f"Realtime DB Save Error: {err}")

# 3. Auto-Filter Search System
@app.on_message(filters.text & filters.private & ~filters.command("start"))
async def search_handler(client, message: Message):
    query = message.text.strip().lower()
    
    try:
        all_files = files_ref.get()
        if not all_files:
            await message.reply_text("❌ **ഡാറ്റാബേസിൽ ഫയലുകളൊന്നും ലഭ്യമല്ല.**")
            return

        matches = []
        for key, data in all_files.items():
            if isinstance(data, dict) and query in data.get("file_name_lower", ""):
                matches.append(data)
                if len(matches) >= 10:  # Limit 10 results
                    break

        if not matches:
            await message.reply_text("❌ **ക്ഷമിക്കണം, നിങ്ങൾ തിരഞ്ഞ ഫയൽ കണ്ടെത്താനായില്ല.**")
            return

        btn_list = []
        for file in matches:
            btn_title = f"📁 {file['file_name']}"
            btn_list.append([InlineKeyboardButton(btn_title, callback_data=f"getfile_{file['file_id']}")])

        markup = InlineKeyboardMarkup(btn_list)
        await message.reply_text(f"🔍 **'{message.text.strip()}'** സെർച്ച് റിസൾട്ടുകൾ:", reply_markup=markup)

    except Exception as err:
        logging.error(f"Search Error: {err}")
        await message.reply_text("❌ സെർച്ച് ചെയ്യുമ്പോൾ പ്രശ്നം ഉണ്ടായി. പിന്നീട് ശ്രമിക്കൂ.")

# 4. Button Action Handling
@app.on_callback_query(filters.regex(r"^getfile_"))
async def send_file_handler(client, callback_query):
    file_id = callback_query.data.replace("getfile_", "")
    
    try:
        await callback_query.message.reply_cached_media(file_id)
        await callback_query.answer("ഫയൽ അയച്ചിട്ടുണ്ട്!")
    except Exception as e:
        logging.error(f"Callback Error: {e}")
        await callback_query.answer("ഫയൽ അയക്കാൻ കഴിഞ്ഞില്ല!", show_alert=True)

if __name__ == "__main__":
    print("Bot is starting...")
    app.run()
