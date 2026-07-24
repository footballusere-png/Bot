import os
import asyncio
import logging
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

# Python 3.14+ Asyncio Event Loop Fix
try:
    asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

from hydrogram import Client, filters
from hydrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

logging.basicConfig(level=logging.INFO)

# ---------- DUMMY WEB SERVER (FOR RENDER) ----------
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is Active and Running!")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

Thread(target=run_web_server, daemon=True).start()
# ----------------------------------------------------

# ---------- CONFIGURATION ----------
API_ID = 28300966
API_HASH = "c0a1fe56b13f260c62bc4838feb416d9"
BOT_TOKEN = "8686380719:AAGXFrU7MymK59RXU8iioBAAqn4O_fLuYtk"

# നിങ്ങളുടെ ചാനൽ ID
CHANNEL_ID = -1004320858359
# -----------------------------------

app = Client("TelegramLocalFilterBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ഫയലുകൾ താത്കാലികമായി സൂക്ഷിക്കാനുള്ള Memory Cache
FILES_CACHE = {}

# 1. ബോട്ട് സ്റ്റാർട്ട് ചെയ്യുമ്പോൾ ചാനലിലെ പഴയ ഫയലുകൾ ഇൻഡക്സ് ചെയ്യുക
async def index_channel_files():
    logging.info("Indexing channel files into memory...")
    try:
        async for msg in app.get_chat_history(CHANNEL_ID, limit=300):
            if msg.document or msg.video or msg.audio:
                media = msg.document or msg.video or msg.audio
                file_name = getattr(media, "file_name", None) or msg.caption or "Unknown File"
                FILES_CACHE[msg.id] = file_name
        logging.info(f"Successfully indexed {len(FILES_CACHE)} files!")
    except Exception as e:
        logging.error(f"Indexing Error: {e}")

# 2. ചാനലിൽ പുതിയ ഫയൽ വരുമ്പോൾ തനിയെ Cache-ലേക്ക് ആഡ് ചെയ്യുക
@app.on_message(filters.chat(CHANNEL_ID) & (filters.document | filters.video | filters.audio))
async def auto_index_new_file(client, message: Message):
    media = message.document or message.video or message.audio
    file_name = getattr(media, "file_name", None) or message.caption or "Unknown File"
    FILES_CACHE[message.id] = file_name
    logging.info(f"New file added to memory: {file_name}")

# 3. Start Command
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message: Message):
    await message.reply_text(
        f"ഹലോ **{message.from_user.first_name}**!\n\n"
        "ഞാൻ ഒരു **Auto-Filter Search Bot** ആണ്. ചാനലിലുള്ള ഫയലുകൾ സെർച്ച് ചെയ്യാൻ അതിൻ്റെ പേര് മാത്രം അയക്കൂ!"
    )

# 4. Search Files From Memory
@app.on_message(filters.text & filters.private & ~filters.command("start"))
async def search_handler(client, message: Message):
    query = message.text.strip().lower()
    
    # കുറഞ്ഞത് 2 അക്ഷരമെങ്കിലും ഉണ്ടെന്ന് ഉറപ്പ് വരുത്തുക
    if len(query) < 2:
        await message.reply_text("❌ തിരയാൻ കുറഞ്ഞത് 2 അക്ഷരങ്ങളെങ്കിലും നൽകുക.")
        return

    results = []
    for msg_id, file_name in FILES_CACHE.items():
        if query in file_name.lower():
            results.append([
                InlineKeyboardButton(
                    f"📁 {file_name}", 
                    callback_data=f"getmsg_{msg_id}"
                )
            ])
            if len(results) >= 10:  # 10 എണ്ണം വരെ കാണിക്കുക
                break

    if not results:
        await message.reply_text("❌ **ക്ഷമിക്കണം, നിങ്ങൾ തിരഞ്ഞ ഫയൽ കണ്ടെത്താനായില്ല.**")
        return

    markup = InlineKeyboardMarkup(results)
    await message.reply_text(f"🔍 **'{message.text.strip()}'** സെർച്ച് റിസൾട്ടുകൾ:", reply_markup=markup)

# 5. Send File Handling
@app.on_callback_query(filters.regex(r"^getmsg_"))
async def send_file_handler(client, callback_query):
    msg_id = int(callback_query.data.split("_")[1])
    
    try:
        await app.copy_message(
            chat_id=callback_query.from_user.id,
            from_chat_id=CHANNEL_ID,
            message_id=msg_id
        )
        await callback_query.answer("ഫയൽ അയച്ചിട്ടുണ്ട്!")
    except Exception as e:
        logging.error(f"Copy Error: {e}")
        await callback_query.answer("ഫയൽ ലഭ്യമല്ല അല്ലെങ്കിൽ ഡിലീറ്റ് ചെയ്യപ്പെട്ടു!", show_alert=True)

if __name__ == "__main__":
    print("Bot starting and loading files...")
    # Background Indexing Run
    async def main():
        await app.start()
        await index_channel_files()
        print("Bot is ready for searching!")
        await asyncio.Event().wait()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
