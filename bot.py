import os
import logging
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

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

# നിങ്ങളുടെ ചാനൽ ID ചേർത്തു
CHANNEL_ID = -1004320858359  
# -----------------------------------

app = Client("TelegramNativeSearchBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# 1. Start Command
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message: Message):
    await message.reply_text(
        f"ഹലോ **{message.from_user.first_name}**!\n\n"
        "ഞാൻ ഒരു **Auto-Filter Search Bot** ആണ്. ചാനലിലുള്ള ഫയലുകൾ സെർച്ച് ചെയ്യാൻ അതിൻ്റെ പേര് മാത്രം അയക്കൂ!"
    )

# 2. Search Files Directly From Telegram Channel
@app.on_message(filters.text & filters.private & ~filters.command("start"))
async def search_handler(client, message: Message):
    query = message.text.strip()
    
    try:
        results = []
        async for msg in app.search_messages(CHANNEL_ID, query=query, limit=10):
            if msg.document or msg.video or msg.audio:
                media = msg.document or msg.video or msg.audio
                file_name = getattr(media, "file_name", None) or msg.caption or "Unknown File"
                
                results.append([
                    InlineKeyboardButton(
                        f"📁 {file_name}", 
                        callback_data=f"getmsg_{msg.id}"
                    )
                ])

        if not results:
            await message.reply_text("❌ **ക്ഷമിക്കണം, നിങ്ങൾ തിരഞ്ഞ ഫയൽ ചാനലിൽ കണ്ടെത്താനായില്ല.**")
            return

        markup = InlineKeyboardMarkup(results)
        await message.reply_text(f"🔍 **'{query}'** സെർച്ച് റിസൾട്ടുകൾ:", reply_markup=markup)

    except Exception as err:
        logging.error(f"Telegram Search Error: {err}")
        await message.reply_text("❌ സെർച്ച് ചെയ്യുമ്പോൾ പ്രശ്നം ഉണ്ടായി. Channel ID ശരിയാണോ എന്നും ബോട്ട് Admin ആണോ എന്നും ഉറപ്പാക്കുക.")

# 3. Button Action Handling
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
    print("Bot started with Channel ID: -1004320858359")
    app.run()
