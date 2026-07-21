import os
import re
import logging
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Your Bot API Token directly added
BOT_TOKEN = os.getenv("BOT_TOKEN", "8766799282:AAHsc62jeHjvrikkatWyqnDCSUlFkv4Qr6U")

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
}

# Expand short links (pin.it) to full Pinterest URL
def get_full_url(url):
    try:
        response = requests.get(url, headers=HEADERS, allow_redirects=True, timeout=10)
        return response.url
    except Exception as e:
        logger.error(f"Error expanding URL: {e}")
        return url

# Extract Direct Media URL from Pinterest
def get_pinterest_media(url):
    full_url = get_full_url(url)
    
    try:
        res = requests.get(full_url, headers=HEADERS, timeout=10)
        if res.status_code != 200:
            return None, None

        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Check for Video Tag
        video_tag = soup.find('video')
        if video_tag and video_tag.get('src'):
            video_url = video_tag['src']
            video_url = video_url.replace('/hls/', '/736x/').replace('.m3u8', '.mp4')
            return video_url, 'video'
            
        # Meta Video Tag
        meta_video = soup.find('meta', property='og:video:secure_url') or soup.find('meta', property='og:video')
        if meta_video and meta_video.get('content'):
            return meta_video['content'], 'video'

        # Meta Image Tag (High Quality)
        meta_image = soup.find('meta', property='og:image')
        if meta_image and meta_image.get('content'):
            img_url = meta_image['content']
            img_url = re.sub(r'/(originals|\d+x)/', '/originals/', img_url)
            return img_url, 'image'

    except Exception as e:
        logger.error(f"Scraping error: {e}")

    return None, None


# Professional /start Command with Tutorial & FAQ
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = (
        "📌 **Welcome to Pinterest Downloader Bot!**\n\n"
        "I can help you download high-quality **Videos & Images** directly from Pinterest instantly!\n\n"
        "━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎\n"
        "📖 **How to Use (Tutorial):**\n"
        "1️⃣ Open the **Pinterest** app or website.\n"
        "2️⃣ Choose any Video, Image, or GIF you want to download.\n"
        "3️⃣ Tap on **Share** ➡️ **Copy Link**.\n"
        "4️⃣ Paste and send the link in this chat!\n"
        "5️⃣ Wait a few seconds, and your media will be delivered here in HD! 🚀\n\n"
        "━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎\n"
        "❓ **Frequently Asked Questions (FAQ):**\n\n"
        "🔹 *Does it support short links?*\n"
        "👉 Yes! Both `pin.it` and `pinterest.com` links work perfectly.\n\n"
        "🔹 *Is it free?*\n"
        "👉 Yes, completely free with unlimited downloads.\n\n"
        "🔹 *Why did my download fail?*\n"
        "👉 Make sure the pin is from a **public account**. Private or age-restricted content cannot be fetched.\n\n"
        "━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎━︎\n"
        "⚡ Send your Pinterest link now to try it out!"
    )
    await update.message.reply_text(welcome_message, parse_mode="Markdown", disable_web_page_preview=True)


# Handle user sent links
async def process_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    # Link Validation
    if "pinterest.com" not in url and "pin.it" not in url:
        await update.message.reply_text(
            "⚠️ **Invalid Link!**\n"
            "Please send a valid Pinterest URL (e.g., `https://pin.it/xxxxx` or `https://pinterest.com/pin/xxxxx`).",
            parse_mode="Markdown"
        )
        return

    status_msg = await update.message.reply_text("⏳ **Processing your link... Please wait.**", parse_mode="Markdown")

    try:
        media_url, media_type = get_pinterest_media(url)

        if not media_url:
            await status_msg.edit_text(
                "❌ **Download Failed!**\n"
                "Unable to fetch media. Please make sure the link is public and try again.",
                parse_mode="Markdown"
            )
            return

        caption = "✨ **Downloaded via Pinterest Downloader Bot**"

        if media_type == 'video':
            await update.message.reply_video(video=media_url, caption=caption, parse_mode="Markdown")
        elif media_type == 'image':
            await update.message.reply_photo(photo=media_url, caption=caption, parse_mode="Markdown")

        await status_msg.delete()

    except Exception as e:
        logger.error(f"Error in processing: {e}")
        await status_msg.edit_text(
            "❌ **Error!** Something went wrong while downloading. Please try again later.",
            parse_mode="Markdown"
        )


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_link))

    print("Bot is running successfully...")
    app.run_polling()


if __name__ == "__main__":
    main()
