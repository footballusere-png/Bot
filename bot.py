import os
import re
import logging
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Replace with your Telegram Bot Token or set BOT_TOKEN env variable
BOT_TOKEN = os.getenv("8766799282:AAF-THrk7-YtBVQnJ7y1KL0m_CKoySuJumg")

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
}

# Expand short links (like pin.it) to full URL
def get_full_url(url):
    try:
        response = requests.get(url, headers=HEADERS, allow_redirects=True, timeout=10)
        return response.url
    except Exception as e:
        logger.error(f"Error expanding URL: {e}")
        return url

# Extract Video or Image direct URL from Pinterest
def get_pinterest_media(url):
    full_url = get_full_url(url)
    
    try:
        res = requests.get(full_url, headers=HEADERS, timeout=10)
        if res.status_code != 200:
            return None, None

        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Check for Video URL
        video_tag = soup.find('video')
        if video_tag and video_tag.get('src'):
            video_url = video_tag['src']
            # Convert m3u8 or thumbnail video links to mp4 if needed
            video_url = video_url.replace('/hls/', '/736x/').replace('.m3u8', '.mp4')
            return video_url, 'video'
            
        # Alternative Video extraction from meta tags
        meta_video = soup.find('meta', property='og:video:secure_url') or soup.find('meta', property='og:video')
        if meta_video and meta_video.get('content'):
            return meta_video['content'], 'video'

        # Check for High-Quality Image URL
        meta_image = soup.find('meta', property='og:image')
        if meta_image and meta_image.get('content'):
            img_url = meta_image['content']
            # Convert to original high quality image link
            img_url = re.sub(r'/(originals|\d+x)/', '/originals/', img_url)
            return img_url, 'image'

    except Exception as e:
        logger.error(f"Scraping error: {e}")

    return None, None


# Command: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 **Welcome to Pinterest Downloader Bot!**\n\n"
        "Send me any Pinterest link (Video or Image), "
        "and I will download and send it to you instantly!"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")


# Main Link Processor
async def process_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    # Validate Pinterest URL
    if "pinterest.com" not in url and "pin.it" not in url:
        await update.message.reply_text("❌ Please send a valid Pinterest link.")
        return

    status_msg = await update.message.reply_text("⏳ Processing your link, please wait...")

    try:
        media_url, media_type = get_pinterest_media(url)

        if not media_url:
            await status_msg.edit_text("❌ Failed to fetch media from this link. Make sure the pin is public.")
            return

        caption = "✨ Downloaded via Pinterest Downloader Bot"

        if media_type == 'video':
            await update.message.reply_video(video=media_url, caption=caption)
        elif media_type == 'image':
            await update.message.reply_photo(photo=media_url, caption=caption)

        await status_msg.delete()

    except Exception as e:
        logger.error(f"Error in sending message: {e}")
        await status_msg.edit_text("❌ Failed to download media from this link. Please try another one.")


def main():
    if BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print("Please set your BOT_TOKEN!")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_link))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
