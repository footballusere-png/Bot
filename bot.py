import os
import asyncio
import logging
import requests
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
from hydrogram import Client, filters
from hydrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from hydrogram.enums import ChatAction
from hydrogram.errors import UserNotParticipant

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

# Fast Direct JioSaavn Search (Bypasses Render Block)
def search_jiosaavn_direct(query):
    url = f"https://jiosaavn-api-privateindexer.vercel.app/search/songs?query={query}"
    try:
        res = requests.get(url, timeout=8)
        if res.status_code == 200:
            data = res.json()
            if data.get("status") == "SUCCESS" and data.get("data"):
                return data["data"]["results"][:5]
    except Exception as e:
        logging.error(f"Search Error: {e}")
    return []

# Download File Function
def download_file(url, destination):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    }
    res = requests.get(url, headers=headers, stream=True)
    with open(destination, 'wb') as f:
        for chunk in res.iter_content(chunk_size=1024*1024):
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
    
    # Action Status: typing
    await client.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    status_msg = await message.reply_text("🔍 **serching song...**")

    loop = asyncio.get_running_loop()
    results = await loop.run_in_executor(None, search_jiosaavn_direct, query)

    if not results:
        await status_msg.edit_text("❌ **No exact songs found. Please check the spelling.**")
        return

    buttons = []
    for idx, song in enumerate(results):
        song_id = song.get("id") or str(idx)
        SONG_CACHE[song_id] = song  

        title = song.get("name", "Unknown Title")
        album = song.get("album", {}).get("name", "") if isinstance(song.get("album"), dict) else ""
        
        # Song Title First in Inline Button
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
        
        # Action Status: downloading
        await client.send_chat_action(chat_id=query.message.chat.id, action=ChatAction.RECORD_AUDIO)
        await query.message.edit_text("📥 **downloading mp3 file...**")

        try:
            title = song_data.get("name", "Audio Track")
            
            # Extract Artist
            artists = "Unknown Artist"
            if song_data.get("primaryArtists"):
                artists = song_data["primaryArtists"]

            # Extract Direct MP3 URL
            download_urls = song_data.get("downloadUrl", [])
            audio_url = download_urls[-1].get("link") or download_urls[-1].get("url") if download_urls else None

            if not audio_url:
                await query.message.edit_text("❌ **Download link not available for this song.**")
                return

            file_path = f"downloads/{song_id}.mp3"

            loop = asyncio.get_running_loop()
            
            # Fast Direct Download
            await loop.run_in_executor(None, download_file, audio_url, file_path)

            # Action Status: sending
            await client.send_chat_action(chat_id=query.message.chat.id, action=ChatAction.UPLOAD_AUDIO)
            await query.message.edit_text("📤 **file senting mp3 file...**")

            duration = int(song_data.get("duration", 0))

            # Send MP3
            await query.message.reply_audio(
                audio=file_path,
                caption=f"🎵 **{title}**\n🎤 **Artist:** {artists}\n\nDownloaded via Music Bot",
                title=title,
                performer=artists,
                duration=duration
            )

            # Cleanup
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
