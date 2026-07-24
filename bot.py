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
        self.wfile.write(b"Free MP3 Music Downloader Active")

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

app = Client("FreeMP3Bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Start Command
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message: Message):
    welcome = (
        f"👋 **Hello {message.from_user.first_name}!**\n\n"
        "🎵 **Free MP3 Music Downloader**\n\n"
        "Send me any **Song Name** or **SoundCloud Link**, and I will download & send the high-quality MP3 audio to you!"
    )
    await message.reply_text(welcome)

# SoundCloud / Free Engine Audio Downloader
def download_free_audio(query):
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
        # YouTube-ന് പകരം SoundCloud-ൽ ഫ്രീയായി സെർച്ച് ചെയ്യുന്നു
        'default_search': 'scsearch1', 
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=True)
        if 'entries' in info:
            info = info['entries'][0]
        
        file_path = ydl.prepare_filename(info).rsplit('.', 1)[0] + ".mp3"
        title = info.get('title', 'Audio Track')
        performer = info.get('uploader', 'Artist')
        duration = int(info.get('duration', 0))
        
        return file_path, title, performer, duration

# Search and Download Handler
@app.on_message(filters.text & filters.private & ~filters.command("start"))
async def handle_music_download(client, message: Message):
    query = message.text.strip()
    
    status_msg = await message.reply_text("📥 **Searching & Downloading Audio... Please wait.**")

    try:
        loop = asyncio.get_running_loop()
        file_path, title, performer, duration = await loop.run_in_executor(
            None, download_free_audio, query
        )

        await status_msg.edit_text("📤 **Uploading MP3 to Telegram...**")

        await message.reply_audio(
            audio=file_path,
            caption=f"🎵 **{title}**\n\nDownloaded via Music Downloader Bot",
            title=title,
            performer=performer,
            duration=duration
        )

        # Download ചെയ്ത ശേഷം ഫയൽ സർവറിൽ നിന്ന് മായ്ക്കുന്നു
        if os.path.exists(file_path):
            os.remove(file_path)

        await status_msg.delete()

    except Exception as e:
        logging.error(f"Download Error: {e}")
        await status_msg.edit_text("❌ **Error:** Could not find or download this track. Please check the song name.")

# ---------- BOT START ----------
if __name__ == "__main__":
    if not os.path.exists("downloads"):
        os.makedirs("downloads")

    async def main():
        await app.start()
        print("Free Music Bot is Running!")
        await asyncio.Event().wait()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
