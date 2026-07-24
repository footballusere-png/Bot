import os
import asyncio
import logging
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

# Python 3.14+ Asyncio Event Loop Fix for Hydrogram
try:
    asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

from hydrogram import Client, filters
from hydrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

logging.basicConfig(level=logging.INFO)

# ---------- DUMMY WEB SERVER (FOR RENDER KEEP-ALIVE) ----------
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot Status: Active and Healthy")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

Thread(target=run_web_server, daemon=True).start()
# ---------------------------------------------------------------

# ---------- CONFIGURATION ----------
API_ID = 28300966
API_HASH = "c0a1fe56b13f260c62bc4838feb416d9"

# ⚠️ Replace with your NEW Bot Token generated from @BotFather
BOT_TOKEN = "YOUR_NEW_BOT_TOKEN_HERE" 

# Target Channel ID
CHANNEL_ID = -1004320858359
# -----------------------------------

app = Client("MovieSearchBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Memory Cache for Files
FILES_CACHE = {}

# 1. Index channel files into memory on startup
async def index_channel_files():
    logging.info("Indexing channel files into memory...")
    try:
        async for msg in app.get_chat_history(CHANNEL_ID, limit=500):
            if msg.document or msg.video or msg.audio:
                media = msg.document or msg.video or msg.audio
                file_name = getattr(media, "file_name", None) or msg.caption or "Media File"
                FILES_CACHE[msg.id] = file_name
        logging.info(f"Successfully indexed {len(FILES_CACHE)} media files!")
    except Exception as e:
        logging.error(f"Indexing Error: {e}")

# 2. Auto-Index new incoming files from the channel
@app.on_message(filters.chat(CHANNEL_ID) & (filters.document | filters.video | filters.audio))
async def auto_index_new_file(client, message: Message):
    media = message.document or message.video or message.audio
    file_name = getattr(media, "file_name", None) or message.caption or "Media File"
    FILES_CACHE[message.id] = file_name
    logging.info(f"New file indexed: {file_name}")

# 3. Professional Start Command
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message: Message):
    welcome_text = (
        f"👋 **Welcome, {message.from_user.first_name}!**\n\n"
        "🎬 **Movie & Media Search Engine**\n\n"
        "I can help you search and retrieve movies, series, and media files directly from our repository.\n\n"
        "💡 **How to use:**\n"
        "Simply type and send the **name of the movie or file** you are looking for!"
    )
    await message.reply_text(welcome_text)

# 4. Professional Movie Search System
@app.on_message(filters.text & filters.private & ~filters.command("start"))
async def search_handler(client, message: Message):
    query = message.text.strip()

    if len(query) < 2:
        await message.reply_text("⚠️ **Notice:** Please enter at least 2 characters to initiate a search.")
        return

    # Show "Searching Movie..." status
    status_msg = await message.reply_text(f"🔍 **Searching repository for:** `{query}`...")

    results = []
    for msg_id, file_name in FILES_CACHE.items():
        if query.lower() in file_name.lower():
            results.append([
                InlineKeyboardButton(
                    f"🎬 {file_name}", 
                    callback_data=f"getmsg_{msg_id}"
                )
            ])
            if len(results) >= 10:  # Limit up to 10 results
                break

    if not results:
        await status_msg.edit_text(
            f"❌ **No Results Found**\n\n"
            f"Could not find any files matching: `{query}`\n"
            "Please check the spelling and try again."
        )
        return

    markup = InlineKeyboardMarkup(results)
    await status_msg.edit_text(
        f"🎯 **Search Results for:** `{query}`\n\n"
        f"Select a file below to receive it instantly:",
        reply_markup=markup
    )

# 5. Professional File Delivery System
@app.on_callback_query(filters.regex(r"^getmsg_"))
async def send_file_handler(client, callback_query):
    msg_id = int(callback_query.data.split("_")[1])
    
    # Notify user that the file is being transferred
    await callback_query.answer("🚀 Processing request: Sending file now...", show_alert=False)
    
    sending_status = await callback_query.message.reply_text("📤 **Sending requested file... Please wait.**")

    try:
        await app.copy_message(
            chat_id=callback_query.from_user.id,
            from_chat_id=CHANNEL_ID,
            message_id=msg_id
        )
        await sending_status.edit_text("✅ **File delivered successfully! Enjoy watching.**")
    except Exception as e:
        logging.error(f"File Transfer Error: {e}")
        await sending_status.edit_text("❌ **Error:** Failed to deliver the file. It may have been deleted or moved.")

# ---------- BOT INITIALIZATION ----------
if __name__ == "__main__":
    print("Initializing Movie Search Engine...")

    async def main():
        await app.start()
        await index_channel_files()
        print("Bot is fully operational and ready to serve requests!")
        await asyncio.Event().wait()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
