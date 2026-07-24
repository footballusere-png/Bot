import os
import asyncio
import logging
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
from hydrogram import Client, filters
from hydrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from hydrogram.enums import ChatAction
from hydrogram.errors import UserNotParticipant
import yt_dlp

# Asyncio Event Loop Fix
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
        self.wfile.write(b"Music Downloader Bot Active")

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

app = Client("MusicDownloaderBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Temporary Memory Store for Songs
SONG_CACHE = {}

# Check Force Subscribe Status
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
        "🎵 **Professional Music Downloader Bot**\n\n"
        "Send me any **Song Name**, and I'll find the exact track for you in high quality!"
    )
    await message.reply_text(welcome)

# Youtube Search Function (100% Reliable & No API Ban)
def search_yt(query):
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'extract_flat': 'in_playlist',
        'default_search': 'ytsearch5'
    }
    results = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch5:{query}", download=False)
            if 'entries' in info:
                for entry in info['entries']:
                    results.append({
                        'id': entry.get('id'),
                        'title': entry.get('title'),
                        'url': f"https://www.youtube.com/watch?v={entry.get('id')}",
                        'duration': entry.get('duration', 0),
                        'uploader': entry.get('uploader', 'Unknown Artist')
                    })
        except Exception as e:
            logging.error(f"YouTube Search Error: {e}")
    return results

# Download Audio Function
def download_yt_audio(video_url, output_path):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        }],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])

# Search Handler
@app.on_message(filters.text & filters.private & ~filters.command("start"))
async def handle_search(client, message: Message):
    user_id = message.from_user.id

    # Force Subscribe Check
    is_joined = await check_force_sub(client, user_id)
    if not is_joined:
        try:
            chat = await client.get_chat(CHANNEL_ID)
            invite_link = chat.invite_link or f"https://t.me/c/{str(CHANNEL_ID)[4:]}"
        except Exception:
            invite_link = "https://t.me"

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
    
    # Action Status
    await client.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    status_msg = await message.reply_text("🔍 **serching song...**")

    loop = asyncio.get_running_loop()
    results = await loop.run_in_executor(None, search_yt, query)

    if not results:
        await status_msg.edit_text("❌ **No exact songs found. Please check the spelling.**")
        return

    buttons = []
    for song in results:
        song_id = song['id']
        SONG_CACHE[song_id] = song  

        title = song['title']
        
        # Song Title First in Button
        btn_text = f"🎵 {title}"
        buttons.append([InlineKeyboardButton(btn_text[:45], callback_data=f"dl_{song_id}")])

    keyboard = InlineKeyboardMarkup(buttons)
    await status_msg.edit_text(
        f"🎯 **Select your song below:**",
        reply_markup=keyboard
    )

# Callback Query Handler (Button Click)
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
        song_id = data.replace("dl_", "")
        song_data = SONG_CACHE.get(song_id)

        if not song_data:
            await query.answer("❌ Search expired. Please search for the song again.", show_alert=True)
            return

        await query.answer()
        
        # Action indicator: Downloading
        await client.send_chat_action(chat_id=query.message.chat.id, action=ChatAction.RECORD_AUDIO)
        await query.message.edit_text("📥 **downloading mp3 file...**")

        try:
            title = song_data['title']
            artist = song_data['uploader']
            video_url = song_data['url']
            duration = song_data['duration']

            file_base = f"downloads/{song_id}"
            file_path = f"downloads/{song_id}.mp3"

            loop = asyncio.get_running_loop()
            
            # Download Audio
            await loop.run_in_executor(None, download_yt_audio, video_url, file_base)

            # Action indicator: Sending Audio
            await client.send_chat_action(chat_id=query.message.chat.id, action=ChatAction.UPLOAD_AUDIO)
            await query.message.edit_text("📤 **file senting mp3 file...**")

            # Send Audio File
            await query.message.reply_audio(
                audio=file_path,
                caption=f"🎵 **{title}**\n🎤 **Artist:** {artist}\n\nDownloaded via Music Bot",
                title=title,
                performer=artist,
                duration=duration
            )

            # Cleanup local files
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
        print("Music Downloader Bot is Running!")
        await asyncio.Event().wait()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
