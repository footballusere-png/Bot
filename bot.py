import os
import asyncio
import logging
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
from hydrogram import Client, filters
from hydrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from hydrogram.errors import UserNotParticipant
import yt_dlp

# Asyncio Event Loop Fix for Python 3.14+
try:
    asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

logging.basicConfig(level=logging.INFO)

# ---------- DUMMY WEB SERVER FOR RENDER ----------
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Professional Music Downloader Active")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

Thread(target=run_web_server, daemon=True).start()
# ------------------------------------------------

# ---------- CONFIGURATION ----------
API_ID = 28300966
API_HASH = "c0a1fe56b13f260c62bc4838feb416d9"
BOT_TOKEN = "8174552245:AAGzK5x7A55r-JVk-DVdteCz8nLBpu0jndU"
CHANNEL_ID = -1004320858359  # നിങ്ങളുടെ ചാനൽ ID

app = Client("ProMusicBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Temporary Memory for Search Results
SEARCH_CACHE = {}

# Helper: Check Force Subscribe
async def check_force_sub(client, user_id):
    try:
        member = await client.get_chat_member(CHANNEL_ID, user_id)
        if member.status in ["kicked", "left"]:
            return False
        return True
    except UserNotParticipant:
        return False
    except Exception as e:
        logging.error(f"Force Sub Error: {e}")
        return True

# Start Command
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message: Message):
    welcome = (
        f"👋 **Hello {message.from_user.first_name}!**\n\n"
        "🎶 **Welcome to Professional Music Downloader Bot**\n\n"
        "Send me any **Song Name**, and I will give you top search results with instant MP3 download buttons!"
    )
    await message.reply_text(welcome)

# Helper Function: Search Top 5 Tracks from SoundCloud
def search_soundcloud_top5(query):
    ydl_opts = {
        'extract_flat': True,
        'quiet': True,
        'no_warnings': True,
        'allowed_extractors': ['soundcloud', 'soundcloud:search'],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"scsearch5:{query}", download=False)
        results = []
        if 'entries' in info:
            for entry in info['entries'][:5]:
                results.append({
                    'id': entry.get('id'),
                    'title': entry.get('title', 'Unknown Title'),
                    'url': entry.get('url') or entry.get('webpage_url')
                })
        return results

# Helper Function: Download Specific Track
def download_sc_track(track_url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        }],
        'quiet': True,
        'no_warnings': True,
        'allowed_extractors': ['soundcloud'],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(track_url, download=True)
        file_path = ydl.prepare_filename(info).rsplit('.', 1)[0] + ".mp3"
        title = info.get('title', 'Audio Track')
        performer = info.get('uploader', 'Artist')
        duration = int(info.get('duration', 0))
        return file_path, title, performer, duration

# Search Handler
@app.on_message(filters.text & filters.private & ~filters.command("start"))
async def handle_search(client, message: Message):
    user_id = message.from_user.id

    # Check Force Sub
    is_joined = await check_force_sub(client, user_id)
    if not is_joined:
        chat = await client.get_chat(CHANNEL_ID)
        invite_link = chat.invite_link or f"https://t.me/c/{str(CHANNEL_ID)[4:]}"
        
        btn = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Join Our Channel", url=invite_link)],
            [InlineKeyboardButton("🔄 Try Again", callback_data="check_sub")]
        ])
        await message.reply_text(
            "⚠️ **You must join our channel to use this bot!**\n\nPlease join the channel below and click **Try Again**.",
            reply_markup=btn
        )
        return

    query = message.text.strip()
    status_msg = await message.reply_text("🔍 **Searching song...**")

    try:
        loop = asyncio.get_running_loop()
        results = await loop.run_in_executor(None, search_soundcloud_top5, query)

        if not results:
            await status_msg.edit_text("❌ **No results found for this song name.**")
            return

        buttons = []
        for idx, item in enumerate(results):
            # Save URL in memory cache
            cache_key = f"{user_id}_{idx}"
            SEARCH_CACHE[cache_key] = item['url']
            
            # Add inline button for each song
            btn_text = f"🎵 {idx+1}. {item['title'][:40]}"
            buttons.append([InlineKeyboardButton(btn_text, callback_data=f"dl_{cache_key}")])

        keyboard = InlineKeyboardMarkup(buttons)
        await status_msg.edit_text(
            f"🔎 **Search Results for:** `{query}`\n👇 Click a song below to download MP3:",
            reply_markup=keyboard
        )

    except Exception as e:
        logging.error(f"Search Error: {e}")
        await status_msg.edit_text("❌ **Error occurred while searching.**")

# Callback Handler (Button Clicks)
@app.on_callback_query()
async def callback_handler(client, query: CallbackQuery):
    data = query.data

    if data == "check_sub":
        is_joined = await check_force_sub(client, query.from_user.id)
        if is_joined:
            await query.message.edit_text("✅ **Thank you for joining! Now send me a song name.**")
        else:
            await query.answer("❌ You haven't joined the channel yet!", show_alert=True)
        return

    if data.startswith("dl_"):
        cache_key = data.replace("dl_", "")
        track_url = SEARCH_CACHE.get(cache_key)

        if not track_url:
            await query.answer("❌ Search expired. Please search for the song again.", show_alert=True)
            return

        await query.answer()
        await query.message.edit_text("📤 **Sending MP3...**")

        try:
            loop = asyncio.get_running_loop()
            file_path, title, performer, duration = await loop.run_in_executor(
                None, download_sc_track, track_url
            )

            await query.message.reply_audio(
                audio=file_path,
                caption=f"🎵 **{title}**\n\nDownloaded via Music Bot",
                title=title,
                performer=performer,
                duration=duration
            )

            if os.path.exists(file_path):
                os.remove(file_path)

            await query.message.delete()

        except Exception as e:
            logging.error(f"Download Error: {e}")
            await query.message.edit_text("❌ **Failed to download the audio track.**")

# ---------- BOT START ----------
if __name__ == "__main__":
    if not os.path.exists("downloads"):
        os.makedirs("downloads")

    async def main():
        await app.start()
        print("Pro Music Bot is Running!")
        await asyncio.Event().wait()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
