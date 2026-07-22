import os
import re
import logging
import threading
import base64
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp
import firebase_admin
from firebase_admin import credentials, db

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ----------------- ADMIN & FIREBASE SETUP ----------------- #
ADMIN_ID = 7312906293  # നിങ്ങളുടെ Telegram User ID
FIREBASE_DB_URL = "https://a-one-chat-e3642-default-rtdb.firebaseio.com"

# Firebase Initialize ചെയ്യാനുള്ള ഫംഗ്ഷൻ
def init_firebase():
    try:
        if not firebase_admin._apps:
            options = {'databaseURL': FIREBASE_DB_URL}
            firebase_admin.initialize_app(options=options)
            logger.info("Firebase connected successfully!")
    except Exception as e:
        logger.error(f"Firebase Init Error: {e}")

# പുതിയ യൂസറെ Firebase ഡാറ്റാബേസിലേക്ക് ചേർക്കുന്നു
def add_user_firebase(user_id, first_name):
    try:
        ref = db.reference(f'users/{user_id}')
        ref.set({
            'user_id': user_id,
            'first_name': first_name
        })
    except Exception as e:
        logger.error(f"Firebase Add User Error: {e}")

# ആകെ യൂസർമാരുടെ എണ്ണം എണ്ണുന്നു
def get_total_users_firebase():
    try:
        ref = db.reference('users')
        users = ref.get()
        if users:
            return len(users)
        return 0
    except Exception as e:
        logger.error(f"Firebase Get Users Error: {e}")
        return 0
# ----------------------------------------------------------- #

# Render 24/7 റൺ ചെയ്യാനായുള്ള Dummy Web Server
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Pinterest Bot with Firebase is Running!")

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

BOT_TOKEN = os.getenv("BOT_TOKEN", "8766799282:AAGvt3bcF594txi6en6JzfMO1gCLHUpkE-E")

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def get_full_url(url):
    try:
        res = requests.get(url, headers=HEADERS, allow_redirects=True, timeout=10)
        return res.url
    except Exception as e:
        logger.error(f"URL expand error: {e}")
        return url

# Direct Web Scraping വഴി ഡൗൺലോഡ് ചെയ്യൽ
def get_pinterest_media_direct(url):
    full_url = get_full_url(url)
    try:
        res = requests.get(full_url, headers=HEADERS, timeout=10)
        if res.status_code != 200:
            return None, None

        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Video Extract
        video_tag = soup.find('video')
        if video_tag and video_tag.get('src'):
            video_url = video_tag['src'].replace('/hls/', '/736x/').replace('.m3u8', '.mp4')
            return video_url, 'video'
            
        meta_video = soup.find('meta', property='og:video:secure_url') or soup.find('meta', property='og:video')
        if meta_video and meta_video.get('content'):
            return meta_video['content'], 'video'

        # Image Extract
        meta_image = soup.find('meta', property='og:image')
        if meta_image and meta_image.get('content'):
            img_url = meta_image['content']
            img_url = re.sub(r'/(originals|\d+x)/', '/originals/', img_url)
            return img_url, 'image'

    except Exception as e:
        logger.error(f"Direct scraping error: {e}")

    return None, None

# yt-dlp ഉപയോഗിച്ചുള്ള ബാക്കപ്പ് ഡൗൺലോഡ്
def download_with_ytdlp(url):
    os.makedirs("downloads", exist_ok=True)
    ydl_opts = {
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'format': 'bestvideo+bestaudio/best',
        'check_formats': False,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        return filename

# ചാനൽ & സപ്പോർട്ട് ഇൻലൈൻ ബട്ടണുകൾ
def get_reply_markup():
    keyboard = [
        [
            InlineKeyboardButton("📢 Updates Channel", url="https://t.me/moviestore_imdb_updates"),
            InlineKeyboardButton("💬 Support Group", url="https://t.me/moviestoreimdb")
        ],
        [
            InlineKeyboardButton("➕ Share Bot", url="https://t.me/share/url?url=Try%20this%20awesome%20Pinterest%20Downloader%20Bot!")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# /start Command Handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user_firebase(user.id, user.first_name)

    # ഗ്രൂപ്പിൽ നിന്ന് ലിങ്ക് ക്ലിക്ക് ചെയ്തു വരുമ്പോൾ (Deep Linking)
    if context.args and len(context.args) > 0:
        encoded_url = context.args[0]
        try:
            url = base64.b64decode(encoded_url.encode('utf-8')).decode('utf-8')
            await process_media_download(update, context, url)
            return
        except Exception as e:
            logger.error(f"Base64 decode error: {e}")

    welcome_text = (
        "✨ **Welcome to Pinterest Downloader Pro!** ✨\n\n"
        "Send me any Pinterest link, and I will download high-quality **Videos & Photos** instantly!\n\n"
        "📖 **How to Use:**\n"
        "1️⃣ Copy a video or photo link from **Pinterest**.\n"
        "2️⃣ Paste and send it here.\n"
        "3️⃣ Receive HD content in seconds! 🚀"
    )
    await update.message.reply_text(
        welcome_text, 
        parse_mode="Markdown", 
        reply_markup=get_reply_markup(),
        disable_web_page_preview=True
    )

# 📊 Admin /stats Command
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        total_users = get_total_users_firebase()
        await update.message.reply_text(
            f"📊 **Bot Statistics (Firebase):**\n\n👤 **Total Users:** `{total_users}`",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("❌ You are not authorized to use this command.")

# Media Download Process
async def process_media_download(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    status_msg = await update.message.reply_text("⏳ **Downloading media... Please wait!**", parse_mode="Markdown")

    file_path = None
    try:
        # Method 1: Scraping
        media_url, media_type = get_pinterest_media_direct(url)

        if media_url:
            extension = "mp4" if media_type == 'video' else "jpg"
            os.makedirs("downloads", exist_ok=True)
            file_path = f"downloads/temp_{update.message.message_id}.{extension}"

            res = requests.get(media_url, headers=HEADERS, stream=True)
            if res.status_code == 200:
                with open(file_path, 'wb') as f:
                    for chunk in res.iter_content(chunk_size=1024):
                        f.write(chunk)

        # Method 2: yt-dlp Backup
        if not file_path or not os.path.exists(file_path):
            try:
                full_url = get_full_url(url)
                file_path = download_with_ytdlp(full_url)
                media_type = 'video' if file_path.endswith(('.mp4', '.mkv', '.webm')) else 'image'
            except Exception as yt_err:
                logger.error(f"yt-dlp error: {yt_err}")

        # Sending File
        if file_path and os.path.exists(file_path):
            caption = "🚀 **Downloaded via Pinterest Downloader Bot**\n\nJoin @moviestore_imdb_updates for more!"
            with open(file_path, 'rb') as file:
                if media_type == 'video':
                    await update.message.reply_video(video=file, caption=caption, parse_mode="Markdown", reply_markup=get_reply_markup())
                else:
                    await update.message.reply_photo(photo=file, caption=caption, parse_mode="Markdown", reply_markup=get_reply_markup())

            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ **Download Failed!** Make sure the Pinterest post is public.", parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error processing link: {e}")
        await status_msg.edit_text("❌ Something went wrong while downloading.", parse_mode="Markdown")
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

# Normal Message Handler (Group/Private Redirection)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user_firebase(user.id, user.first_name)

    url = update.message.text.strip()
    chat_type = update.effective_chat.type

    if "pinterest.com" not in url and "pin.it" not in url:
        if chat_type == 'private':
            await update.message.reply_text("⚠️ **Please send a valid Pinterest URL.**", parse_mode="Markdown")
        return

    # 1. ഗ്രൂപ്പിൽ സന്ദേശം വന്നാൽ
    if chat_type in ['group', 'supergroup']:
        encoded_url = base64.b64encode(url.encode('utf-8')).decode('utf-8')
        bot_username = (await context.bot.get_me()).username
        pm_link = f"https://t.me/{bot_username}?start={encoded_url}"

        group_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📥 Get Your Media (Private Chat)", url=pm_link)]
        ])

        await update.message.reply_text(
            f"👋 Hello {update.effective_user.first_name}!\n\n"
            "Click the button below to get your downloaded photo/video in private chat! 👇",
            reply_markup=group_keyboard,
            reply_to_message_id=update.message.message_id
        )
    # 2. ബോട്ടിന്റെ Private Chat-ൽ വന്നാൽ
    else:
        await process_media_download(update, context, url)

def main():
    init_firebase()
    threading.Thread(target=run_dummy_server, daemon=True).start()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running seamlessly...")
    app.run_polling()

if __name__ == "__main__":
    main()
