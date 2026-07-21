import os
import re
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

# Logging configuration
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Render-ൽ പണം കൊടുക്കാതെ Free Web Service ആയി 24/7 പ്രവർത്തിക്കാനുള്ള Dummy Server
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Pinterest Bot is Alive and Running!")

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

# Your Telegram Bot API Token
BOT_TOKEN = os.getenv("BOT_TOKEN", "8766799282:AAHsc62jeHjvrikkatWyqnDCSUlFkv4Qr6U")

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# Short links (`pin.it`) expand ചെയ്യാനുള്ള ഫംഗ്ഷൻ
def get_full_url(url):
    try:
        res = requests.get(url, headers=HEADERS, allow_redirects=True, timeout=10)
        return res.url
    except Exception as e:
        logger.error(f"URL expand error: {e}")
        return url

# Direct Scrape വഴി HD Media കണ്ടുപിടിക്കുന്നു
def get_pinterest_media_direct(url):
    full_url = get_full_url(url)
    try:
        res = requests.get(full_url, headers=HEADERS, timeout=10)
        if res.status_code != 200:
            return None, None

        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 1. Video Tag Check
        video_tag = soup.find('video')
        if video_tag and video_tag.get('src'):
            video_url = video_tag['src'].replace('/hls/', '/736x/').replace('.m3u8', '.mp4')
            return video_url, 'video'
            
        # 2. Meta Video Tag Check
        meta_video = soup.find('meta', property='og:video:secure_url') or soup.find('meta', property='og:video')
        if meta_video and meta_video.get('content'):
            return meta_video['content'], 'video'

        # 3. High Quality Image Check
        meta_image = soup.find('meta', property='og:image')
        if meta_image and meta_image.get('content'):
            img_url = meta_image['content']
            img_url = re.sub(r'/(originals|\d+x)/', '/originals/', img_url)
            return img_url, 'image'

    except Exception as e:
        logger.error(f"Direct scraping error: {e}")

    return None, None

# Secondary Fallback: yt-dlp ഉപയോഗിച്ചുള്ള ഡൗൺലോഡ്
def download_with_ytdlp(url):
    os.makedirs("downloads", exist_ok=True)
    ydl_opts = {
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'format': 'best',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        return filename

# ചാനൽ, സപ്പോർട്ട്, ഷെയർ ബട്ടണുകൾ (Inline Keyboard)
def get_reply_markup():
    keyboard = [
        [
            InlineKeyboardButton("📢 Updates Channel", url="https://t.me/telegram"),
            InlineKeyboardButton("💬 Support", url="https://t.me/telegram")
        ],
        [
            InlineKeyboardButton("➕ Share / Add Bot", url="https://t.me/share/url?url=Try%20this%20awesome%20Pinterest%20Downloader%20Bot!")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# /start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "✨ **Welcome to Pinterest Downloader Pro!** ✨\n\n"
        "Send me any Pinterest link, and I will download high-quality **Videos, Photos, & GIFs** instantly!\n\n"
        "━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎\n"
        "📖 **How to Use (Tutorial):**\n"
        "1️⃣ Copy any Video or Image link from **Pinterest**.\n"
        "2️⃣ Paste and send the link in this chat.\n"
        "3️⃣ Receive your HD media in seconds! 🚀\n\n"
        "⚡ **Supported Links:** Both `pin.it` & `pinterest.com` work perfectly!"
    )
    await update.message.reply_text(
        welcome_text, 
        parse_mode="Markdown", 
        reply_markup=get_reply_markup(),
        disable_web_page_preview=True
    )

# Pinterest Link Processing
async def process_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if "pinterest.com" not in url and "pin.it" not in url:
        await update.message.reply_text(
            "⚠️ **Invalid Link!** Please send a valid Pinterest URL (e.g., `https://pin.it/xxxxx`).",
            parse_mode="Markdown"
        )
        return

    status_msg = await update.message.reply_text("⏳ **Processing & Downloading media... Please wait!**", parse_mode="Markdown")

    file_path = None
    try:
        # Method 1: Direct Scraping
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

        # Method 2: yt-dlp Fallback (Method 1 പരാജയപ്പെട്ടാൽ സ്വയം പ്രവർത്തിക്കും)
        if not file_path or not os.path.exists(file_path):
            try:
                full_url = get_full_url(url)
                file_path = download_with_ytdlp(full_url)
                media_type = 'video' if file_path.endswith(('.mp4', '.mkv', '.webm')) else 'image'
            except Exception as yt_err:
                logger.error(f"yt-dlp error: {yt_err}")

        # Send media to user
        if file_path and os.path.exists(file_path):
            caption = "🚀 **Downloaded via Pinterest Downloader Bot**\n\n✨ High Quality Media Delivered!"
            
            with open(file_path, 'rb') as file:
                if media_type == 'video':
                    await update.message.reply_video(
                        video=file, 
                        caption=caption, 
                        parse_mode="Markdown", 
                        reply_markup=get_reply_markup()
                    )
                else:
                    await update.message.reply_photo(
                        photo=file, 
                        caption=caption, 
                        parse_mode="Markdown", 
                        reply_markup=get_reply_markup()
                    )

            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ **Download Failed!** Make sure the Pinterest pin is public.", parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Processing error: {e}")
        await status_msg.edit_text("❌ **Error!** Unable to process this link right now.", parse_mode="Markdown")

    finally:
        # Clean up downloaded file after sending
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

def main():
    # Start Dummy Web Server for Render Web Service Port Binding
    threading.Thread(target=run_dummy_server, daemon=True).start()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_link))

    print("Professional Pinterest Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
