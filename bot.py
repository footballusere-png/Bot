import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters

# Configuration & Tokens
TMDB_READ_ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI4YjY5NjhjNGFiZGM5NjllMjQ0MGQwZDRkYWY1NGIwMiIsIm5iZiI6MTc2ODgwMTUyMy40MTUsInN1YiI6IjY5NmRjNGYzZWM4NjcyM2Q2MDhmY2Y3MCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.huLmybTc_7lk7TDv8mw1iQtuZf4aek1_OGsfU9r9KuI"
TELEGRAM_BOT_TOKEN = "8684424014:AAEhpnG4oCEqDf6hQYqLRx_EVWOdQFjgf7k"
CHANNEL_ID = "-1003391211397"  # @mfottupdates
GROUP_ID = "-1004283563750"    # @mfottupdatesgroup
CHANNEL_USERNAME = "@mfottupdates"

# Database to store user IDs for broadcasting
USER_DATABASE = set()

# TMDB Movie Search Function with Image Support
def search_movie(movie_name):
    url = f"https://api.themoviedb.org/3/search/movie?query={encode_query(movie_name)}&language=en-US&page=1"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {TMDB_READ_ACCESS_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        results = data.get("results", [])
        if results:
            movie = results[0]
            title = movie.get("title")
            release_date = movie.get("release_date", "N/A")
            overview = movie.get("overview", "No overview available.")
            vote_average = movie.get("vote_average", "N/A")
            poster_path = movie.get("poster_path")
            
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
            
            caption = (
                f"🎬 **MOVIE INFORMATION** 🎬\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"📌 **Title:** `{title}`\n"
                f"📅 **Release Date:** `{release_date}`\n"
                f"⭐ **IMDb Rating:** `{vote_average} / 10`\n"
                f"━━━━━━━━━━━━━━━━━━━\n\n"
                f"📖 **Overview:**\n_{overview}_\n\n"
                f"🤖 *Powered by @mfottupdates*"
            )
            return caption, poster_url
    return None, None

def encode_query(text):
    return requests.utils.quote(text)

# Live Auto Updates for Channel and Group (No Force Join Required)
async def post_live_movie_updates(context: ContextTypes.DEFAULT_TYPE):
    url = "https://api.themoviedb.org/3/movie/upcoming?language=en-US&page=1"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {TMDB_READ_ACCESS_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        movies = response.json().get("results", [])
        if movies:
            movie = movies[0]
            title = movie.get("title")
            release_date = movie.get("release_date")
            overview = movie.get("overview")
            poster_path = movie.get("poster_path")
            
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
            
            msg = (
                f"🔥 **LIVE UPCOMING MOVIE ALERT** 🔥\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"📌 **Title:** `{title}`\n"
                f"📅 **Release Date:** `{release_date}`\n"
                f"━━━━━━━━━━━━━━━━━━━\n\n"
                f"📖 _{overview}_\n\n"
                f"🔔 *Stay tuned to {CHANNEL_USERNAME} for more OTT & Movie updates!*"
            )
            
            try:
                if poster_url:
                    await context.bot.send_photo(chat_id=CHANNEL_ID, photo=poster_url, caption=msg, parse_mode="Markdown")
                    await context.bot.send_photo(chat_id=GROUP_ID, photo=poster_url, caption=msg, parse_mode="Markdown")
                else:
                    await context.bot.send_message(chat_id=CHANNEL_ID, text=msg, parse_mode="Markdown")
                    await context.bot.send_message(chat_id=GROUP_ID, text=msg, parse_mode="Markdown")
            except Exception as e:
                print(f"Error posting live updates: {e}")

# Start Command
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    USER_DATABASE.add(user.id)
    
    welcome_msg = (
        f"👋 **Welcome, {user.first_name}!**\n\n"
        f"I am your official **MF OTT Updates** Bot. Send me any movie name to get instant premium details with posters!\n\n"
        f"📢 *Updates Channel:* {CHANNEL_USERNAME}"
    )
    await update.message.reply_text(welcome_msg, parse_mode="Markdown")

# Handle User Queries (Force Join Applied only for user search)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.effective_message
    
    if not message or not message.text:
        return

    user_id = user.id
    user_message = message.text.strip()
    USER_DATABASE.add(user_id)

    if user_message.startswith("/"):
        return

    # Check Force Join
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        if member.status not in ["creator", "administrator", "member"]:
            keyboard = [[InlineKeyboardButton("📢 Join Update Channel", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await message.reply_text(
                f"🔒 **Access Restricted!**\n\n"
                f"To search and view movie details, you must join our official update channel first.",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            return
    except Exception as e:
        print(f"Subscription check error: {e}")

    # Fetch and Send Movie Details with Image
    caption, poster_url = search_movie(user_message)
    if caption:
        if poster_url:
            await message.reply_photo(photo=poster_url, caption=caption, parse_mode="Markdown")
        else:
            await message.reply_text(caption, parse_mode="Markdown")
    else:
        await message.reply_text("❌ Sorry, no information found for this movie.", parse_mode="Markdown")

# Broadcast Command
async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Please provide a message to broadcast.\nUsage: `/broadcast Your message here`", parse_mode="Markdown")
        return

    broadcast_msg = " ".join(context.args)
    success, fail = 0, 0
    
    status_msg = await update.message.reply_text("📢 **Broadcasting in progress...**", parse_mode="Markdown")

    for uid in USER_DATABASE:
        try:
            await context.bot.send_message(chat_id=uid, text=broadcast_msg, parse_mode="Markdown")
            success += 1
        except:
            fail += 1

    await status_msg.edit_text(
        f"✅ **Broadcast Completed Successfully!**\n\n"
        f"📤 Sent: `{success}`\n"
        f"❌ Failed: `{fail}`",
        parse_mode="Markdown"
    )

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Job Queue for Live Auto Updates (Runs every 24 hours / 86400 seconds)
    if app.job_queue:
        app.job_queue.run_repeating(post_live_movie_updates, interval=86400, first=10)

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("🤖 Professional Live Movie Bot is running successfully...")
    app.run_polling()

if __name__ == "__main__":
    main()
