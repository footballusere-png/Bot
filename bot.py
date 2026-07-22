import os
import re
import logging
import threading
import base64
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp
import firebase_admin
from firebase_admin import db

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
ADMIN_ID = 7312906293  # 🎯 നിങ്ങളുടെ User ID ചേർത്തിട്ടുണ്ട്
FIREBASE_DB_URL = "https://a-one-chat-e3642-default-rtdb.firebaseio.com"
BOT_TOKEN = os.getenv("BOT_TOKEN", "8766799282:AAGvt3bcF594txi6en6JzfMO1gCLHUpkE-E")

# Firebase setup
def init_firebase():
    try:
        if not firebase_admin._apps:
            options = {'databaseURL': FIREBASE_DB_URL}
            firebase_admin.initialize_app(options=options)
    except Exception as e:
        logger.error(f"Firebase Init Error: {e}")

# Async Background User Saving
def async_add_user(user_id, first_name):
    def save():
        try:
            ref = db.reference(f'users/{user_id}')
            ref.set({'user_id': user_id, 'first_name': first_name})
        except Exception as e:
            logger.error(f"Firebase Save Error: {e}")
    threading.Thread(target=save, daemon=True).start()

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Pinterest Bot with Ad Broadcast System is Running!")

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def get_full_url(url):
    try:
        res = requests.get(url, headers=HEADERS, allow_redirects=True, timeout=10)
        return res.url
    except Exception as e:
        return url

def get_pinterest_media_direct(url):
    full_url = get_full_url(url)
    try:
        res = requests.get(full_url, headers=HEADERS, timeout=10)
        if res.status_code != 200:
            return None, None

        soup = BeautifulSoup(res.text, 'html.parser')
        
        video_tag = soup.find('video')
        if video_tag and video_tag.get('src'):
            video_url = video_tag['src'].replace('/hls/', '/736x/').replace('.m3u8', '.mp4')
            return video_url, 'video'
            
        meta_video = soup.find('meta', property='og:video:secure_url') or soup.find('meta', property='og:video')
        if meta_video and meta_video.get('content'):
            return meta_video['content'], 'video'

        meta_image = soup.find('meta', property='og:image')
        if meta_image and meta_image.get('content'):
            img_url = meta_image['content']
            img_url = re.sub(r'/(originals|\d+x)/', '/originals/', img_url)
            return img_url, 'image'

    except Exception as e:
        logger.error(f"Direct scraping error: {e}")

    return None, None

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    async_add_user(user.id, user.first_name)

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

# 📢 BROADCAST COMMAND (നിങ്ങൾക്ക് പരസ്യങ്ങൾ അയക്കാൻ)
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ **പരസ്യമായി അയക്കേണ്ട Message/Photo/Video-യ്ക്ക് റിപ്ലൈ ആയി `/broadcast` എന്ന് അയക്കുക!**", parse_mode="Markdown")
        return

    status_msg = await update.message.reply_text("🚀 **Broadcast ആരംഭിക്കുന്നു...**")
    
    try:
        ref = db.reference('users')
        users_data = ref.get()

        if not users_data:
            await status_msg.edit_text("❌ ഡാറ്റാബേസിൽ യൂസേഴ്സ് ആരും ഇല്ല.")
            return

        success = 0
        failed = 0

        for user_id in users_data.keys():
            try:
                await context.bot.copy_message(
                    chat_id=int(user_id),
                    from_chat_id=update.effective_chat.id,
                    message_id=update.message.reply_to_message.message_id
                )
                success += 1
                await asyncio.sleep(0.05)  # Telegram limits ഒഴിവാക്കാൻ
            except Exception:
                failed += 1

        await status_msg.edit_text(
            f"✅ **Broadcast പൂർത്തിയായി!**\n\n"
            f"🎯 വിജയിച്ചവ: `{success}`\n"
            f"❌ പരാജയപ്പെട്ടവ: `{failed}`",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Broadcast Error: {e}")
        await status_msg.edit_text("❌ Broadcast ചെയ്യുന്നതിൽ തടസ്സം നേരിട്ടു.")

async def process_media_download(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    status_msg = await update.message.reply_text("⏳ **Downloading media... Please wait!**", parse_mode="Markdown")

    file_path = None
    try:
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

        if not file_path or not os.path.exists(file_path):
            try:
                full_url = get_full_url(url)
                file_path = download_with_ytdlp(full_url)
                media_type = 'video' if file_path.endswith(('.mp4', '.mkv', '.webm')) else 'image'
            except Exception as yt_err:
                logger.error(f"yt-dlp error: {yt_err}")

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

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    chat_type = update.effective_chat.type

    if "pinterest.com" not in url and "pin.it" not in url:
        if chat_type == 'private':
            await update.message.reply_text("⚠️ **Please send a valid Pinterest URL.**", parse_mode="Markdown")
        return

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
    else:
        await process_media_download(update, context, url)

def main():
    init_firebase()
    threading.Thread(target=run_dummy_server, daemon=True).start()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot with Admin ID 7312906293 & Broadcast system is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
