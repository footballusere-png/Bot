import os
import asyncio
import logging
import requests
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
from hydrogram import Client, filters
from hydrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from hydrogram.errors import UserNotParticipant

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
        self.wfile.write(b"JioSaavn Music Bot Active")

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

app = Client("JioSaavnMusicBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

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

# JioSaavn API Search Function (Updated Stable Endpoint)
def search_jiosaavn(query):
    url = f"https://jiosaavn-api-v3.vercel.app/search/songs?query={query}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if isinstance(data, list):
            return data[:5]
        elif isinstance(data, dict) and data.get("results"):
            return data["results"][:5]
        elif isinstance(data, dict) and data.get("data"):
            return data["data"][:5]
            
    except Exception as e:
        logging.error(f"JioSaavn API Error: {e}")
    return []

# Download File Function
def download_file(url, destination):
    res = requests.get(url, stream=True)
    with open(destination, 'wb') as f:
        for chunk in res.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)

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
    
    # Status: serching song
    status_msg = await message.reply_text("🔍 **serching song...**")

    loop = asyncio.get_running_loop()
    results = await loop.run_in_executor(None, search_jiosaavn, query)

    if not results:
        await status_msg.edit_text("❌ **No exact songs found. Please check the spelling.**")
        return

    buttons = []
    for idx, song in enumerate(results):
        # Handle different API field names for ID and Title
        song_id = song.get("id") or song.get("_id") or str(idx)
        SONG_CACHE[str(song_id)] = song  

        title = song.get("name") or song.get("title") or "Unknown Title"
        album = ""
        if isinstance(song.get("album"), dict):
            album = song["album"].get("name", "")
        elif isinstance(song.get("album"), str):
            album = song["album"]
        
        # Display Song Name on Button
        btn_text = f"🎵 {title} ({album})" if album else f"🎵 {title}"
        
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
        
        # Status: downloading mp3 file
        await query.message.edit_text("📥 **downloading mp3 file...**")

        try:
            title = song_data.get("name") or song_data.get("title") or "Audio Track"
            
            # Extract Artists
            artists = "Unknown Artist"
            if song_data.get("artists"):
                if isinstance(song_data["artists"], dict) and "primary" in song_data["artists"]:
                    artists = ", ".join([a.get("name", "") for a in song_data["artists"]["primary"]])
                elif isinstance(song_data["artists"], list):
                    artists = ", ".join([str(a) for a in song_data["artists"]])

            # Extract Audio Download URL
            audio_url = None
            if "downloadUrl" in song_data:
                urls = song_data["downloadUrl"]
                if isinstance(urls, list) and len(urls) > 0:
                    audio_url = urls[-1].get("url") or urls[-1].get("link")
                elif isinstance(urls, str):
                    audio_url = urls
            elif "media_url" in song_data:
                audio_url = song_data["media_url"]
            elif "url" in song_data:
                audio_url = song_data["url"]

            # Extract Thumbnail URL
            thumb_url = None
            if "image" in song_data:
                images = song_data["image"]
                if isinstance(images, list) and len(images) > 0:
                    if isinstance(images[-1], dict):
                        thumb_url = images[-1].get("url") or images[-1].get("link")
                    elif isinstance(images[-1], str):
                        thumb_url = images[-1]
                elif isinstance(images, str):
                    thumb_url = images

            if not audio_url:
                await query.message.edit_text("❌ **Download link not available for this song.**")
                return

            file_path = f"downloads/{song_id}.mp3"
            thumb_path = f"downloads/{song_id}.jpg" if thumb_url else None

            loop = asyncio.get_running_loop()
            
            # Download MP3 and Thumbnail Files
            await loop.run_in_executor(None, download_file, audio_url, file_path)
            if thumb_url:
                try:
                    await loop.run_in_executor(None, download_file, thumb_url, thumb_path)
                except Exception:
                    pass

            # Status: file senting mp3 file
            await query.message.edit_text("📤 **file senting mp3 file...**")

            duration = int(song_data.get("duration", 0))

            # Send Audio File
            await query.message.reply_audio(
                audio=file_path,
                caption=f"🎵 **{title}**\n🎤 **Artist:** {artists}\n\nDownloaded via Music Bot",
                title=title,
                performer=artists,
                duration=duration,
                thumb=thumb_path if thumb_path and os.path.exists(thumb_path) else None
            )

            # Cleanup local files
            if os.path.exists(file_path):
                os.remove(file_path)
            if thumb_path and os.path.exists(thumb_path):
                os.remove(thumb_path)

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
        print("JioSaavn Music Bot is Running!")
        await asyncio.Event().wait()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
