import os
import asyncio
import logging
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
from hydrogram import Client, filters
from hydrogram.types import Message
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
        self.wfile.write(b"YouTube Downloader Bot Active")

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

app = Client("YTMP3Bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Start Command
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message: Message):
    welcome = (
        f"👋 **Hello {message.from_user.first_name}!**\n\n"
        "🎵 **YouTube to MP3 Downloader**\n\n"
        "Send me any **YouTube Link** or type a **Song Name**, and I will convert & send the MP3 audio to you!"
    )
    await message.reply_text(welcome)

# Helper Function: Download Audio using yt-dlp
def download_yt_audio(url_or_query):
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
        'default_search': 'ytsearch1', # Search YouTube if text query is sent
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url_or_query, download=True)
        if 'entries' in info:
            info = info['entries'][0]
        
        file_path = ydl.prepare_filename(info).rsplit('.', 1)[0] + ".mp3"
        title = info.get('title', 'Audio Track')
        performer = info.get('uploader', 'YouTube')
        duration = int(info.get('duration', 0))
        
        return file_path, title, performer, duration

# YouTube Download Handler
@app.on_message(filters.text & filters.private & ~filters.command("start"))
async def handle_youtube_download(client, message: Message):
    query = message.text.strip()
    
    status_msg = await message.reply_text("📥 **Processing & Downloading Audio... Please wait.**")

    try:
        # Run blocking download function in async thread
        loop = asyncio.get_running_loop()
        file_path, title, performer, duration = await loop.run_in_executor(
            None, download_yt_audio, query
        )

        await status_msg.edit_text("📤 **Uploading MP3 to Telegram...**")

        # Send Audio File
        await message.reply_audio(
            audio=file_path,
            caption=f"🎵 **{title}**\n\nDownloaded via MP3 Downloader Bot",
            title=title,
            performer=performer,
            duration=duration
        )

        # Cleanup downloaded file from server storage
        if os.path.exists(file_path):
            os.remove(file_path)

        await status_msg.delete()

    except Exception as e:
        logging.error(f"Download Error: {e}")
        await status_msg.edit_text("❌ **Error:** Unable to download this track. YouTube might be restricting this query or IP.")

# ---------- BOT START ----------
if __name__ == "__main__":
    if not os.path.exists("downloads"):
        os.makedirs("downloads")

    async def main():
        await app.start()
        print("YouTube MP3 Bot is Running!")
        await asyncio.Event().wait()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
