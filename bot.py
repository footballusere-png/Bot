import asyncio
import os
import re
import math
from threading import Thread
from flask import Flask
from hydrogram import Client, filters
from hydrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from hydrogram.errors import UserNotParticipant

# ------------ CONFIGURATION ------------
API_ID = 28300966
API_HASH = "c0a1fe56b13f260c62bc4838feb416d9"
STRING_SESSION = "BQGv1qYAIeWJGD5qT23izLbMJPiWJ-AAmld2QM4rXcoRMwJw5iZfJBPcG3BTaX31W5OhlCfHr_cc_GVIB5Qiquf8503yugDygjD4IWb5UArRRtZ3guBKlZzjNln8E2oDyKCapD0YmsqN8UVZ3CCyDke3uKRZfqLNc6p5EkfAhaAgiUhcMyiqJIdb2c4a3CAIxizLxXopfs7e890zZfJjyQk7MMyMvsBlrlmSafudbcgb8BbFrX-XUTX1QknieWjnjtWeHFODjZ2K64BDC2Fo2fmQk4_6iVSXZJ9zK1bR-dTGJ30xHxznt8_j_DMNIkDePOa8KxW1uSD9vBGZv0CH1q5qQRoyCAAAAAGz4hg1AA"

BOT_TOKEN = "8014212534:AAEtlOlMPuXbkPHOxQdj0mJ8yXTPDG0x25M"

TARGET_BOT = "@DPCBackup_Files_01_Bot"  # Backup bot
MY_CHANNEL = -1004296254082             # Your backup/storage channel ID

# Force Join Configuration
FORCE_SUB_CHANNEL = -1002644197954
UPDATE_CHANNEL_LINK = "https://t.me/moviestore_imdb_updates"

# Admin Configuration
ADMIN_ID = 7312906293
USER_DB_FILE = "users.txt"

# Global variables
ADD_ENABLED = True
file_queue = asyncio.Queue()
is_processing_queue = False
# ----------------------------------------

# Dummy Flask App to satisfy Render Port Binding requirement
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive and running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# Helper Function: Save New Users
def save_user(user_id: int):
    if not os.path.exists(USER_DB_FILE):
        open(USER_DB_FILE, "w").close()
    
    with open(USER_DB_FILE, "r+") as f:
        users = f.read().splitlines()
        if str(user_id) not in users:
            f.write(f"{user_id}\n")

# Helper Function: Force Sub Check
async def check_force_sub(client: Client, user_id: int) -> bool:
    try:
        member = await client.get_chat_member(FORCE_SUB_CHANNEL, user_id)
        if member.status in ["kicked", "banned"]:
            return False
        return True
    except UserNotParticipant:
        return False
    except Exception:
        return True

# Helper Function: Remove Links, Usernames (@), and Clean Caption
def clean_caption(original_text: str, fallback_name: str) -> str:
    if not original_text:
        return f"🎬 **{fallback_name}**"
    
    # 1. Remove URLs (http, https, t.me, www, etc.)
    text_without_links = re.sub(r'https?://\S+|www\.\S+|t\.me/\S+', '', original_text)
    
    # 2. Remove Telegram Usernames (e.g., @username, @MoviesChannel)
    text_without_usernames = re.sub(r'@\w+', '', text_without_links)
    
    # 3. Remove extra spaces and newlines, keep clean text
    cleaned = " ".join(text_without_usernames.split()).strip()
    
    if not cleaned:
        cleaned = fallback_name
        
    return f"🎬 **{cleaned}**"

# Helper Function to Generate Pagination Markup for Search Results (10 files per page)
def get_search_markup(results, query_text, page=1, per_page=10):
    total_results = len(results)
    total_pages = math.ceil(total_results / per_page)
    
    if page < 1:
        page = 1
    elif page > total_pages and total_pages > 0:
        page = total_pages
        
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    current_page_items = results[start_idx:end_idx]
    
    buttons = []
    for item in current_page_items:
        title = item["title"]
        if len(title) > 40:
            title = title[:37] + "..."
        buttons.append([InlineKeyboardButton(title, callback_data=f"get_{item['id']}")])
        
    # Navigation Buttons Row
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"search_{query_text}_{page-1}"))
    
    nav_buttons.append(InlineKeyboardButton(f"📄 Page {page} of {total_pages}", callback_data="noop"))
    
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"search_{query_text}_{page+1}"))
        
    if nav_buttons:
        buttons.append(nav_buttons)
        
    return InlineKeyboardMarkup(buttons), total_pages

async def main():
    userbot = Client("my_userbot", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION)
    main_bot = Client("my_main_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

    # Background Worker to process queued files safely with a 3s gap to avoid FloodWait
    async def process_file_queue():
        global is_processing_queue
        is_processing_queue = True
        while not file_queue.empty():
            item = await file_queue.get()
            message = item["message"]
            status_msg = item["status_msg"]
            
            try:
                fallback = message.document.file_name if message.document else (message.video.file_name if message.video and message.video.file_name else "Movie File")
                raw_caption = message.caption or fallback
                final_caption = clean_caption(raw_caption, fallback)
                
                await message.copy(chat_id=MY_CHANNEL, caption=final_caption)
                
                remaining = file_queue.qsize()
                if remaining > 0:
                    await status_msg.edit_text(f"⚡ Saving safely... ({remaining} files left in queue)")
                    await asyncio.sleep(3)  # Safe 3 seconds delay between files to prevent FloodWait
                else:
                    await status_msg.edit_text("✨ **All files successfully saved to channel with clean names!**")
            except Exception as e:
                await status_msg.edit_text(f"❌ Failed to save a file: `{str(e)}`")
                print(f"Queue Processing Error: {e}")
            
            file_queue.task_done()
        is_processing_queue = False

    # 1. Start Command (/start) with Menu Buttons
    @main_bot.on_message(filters.command("start") & filters.private)
    async def start_cmd(client: Client, message: Message):
        save_user(message.from_user.id)
        
        welcome_text = (
            f"👋 **Hello {message.from_user.mention},**\n\n"
            "🎬 **Welcome to Movie Finder Bot!**\n\n"
            "Just type and send the name of the movie you are looking for (Minimum 4 letters)."
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📂 Available Files", callback_data="available_files_btn")],
            [InlineKeyboardButton("📢 Update Channel", url=UPDATE_CHANNEL_LINK)]
        ])
        await message.reply_text(text=welcome_text, reply_markup=keyboard, disable_web_page_preview=True)

    # Available Files Command (/available_files) for all users
    @main_bot.on_message(filters.command("available_files") & filters.private)
    async def available_files_cmd(client: Client, message: Message):
        status_msg = await message.reply_text("📊 **Calculating available files in database...**")
        try:
            count = 0
            async for _ in userbot.search_messages(MY_CHANNEL, query=""):
                count += 1
            
            await status_msg.edit_text(
                f"📁 **Database Status:**\n\n"
                f"✅ Total Available Files: `~{count}`\n\n"
                f"💡 *Type any movie name (minimum 4 letters) to search and download!*"
            )
        except Exception as e:
            await status_msg.edit_text("❌ Failed to fetch file count. Please try again later.")
            print(f"Available Files Error: {e}")

    # Admin Settings Panel Command (/panel or /admin)
    @main_bot.on_message(filters.command(["panel", "admin"]) & filters.private & filters.user(ADMIN_ID))
    async def admin_panel(client: Client, message: Message):
        global ADD_ENABLED
        status_text = "🟢 Enabled" if ADD_ENABLED else "🔴 Disabled"
        toggle_btn_text = "Turn Off Add 🔴" if ADD_ENABLED else "Turn On Add 🟢"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"Add Feature: {status_text}", callback_data="noop")],
            [InlineKeyboardButton(toggle_btn_text, callback_data="toggle_add")]
        ])
        await message.reply_text(
            "⚙️ **Admin Control Panel**\n\nManage your bot settings below:",
            reply_markup=keyboard
        )

    # 2. Direct File Receiver Handler for Admin (Fast Queue Method)
    @main_bot.on_message((filters.document | filters.video | filters.audio) & filters.private & filters.user(ADMIN_ID))
    async def handle_direct_file(client: Client, message: Message):
        global is_processing_queue
        try:
            status_msg = await message.reply_text("📥 **File added to queue...**")
            await file_queue.put({"message": message, "status_msg": status_msg})
            
            if not is_processing_queue:
                asyncio.create_task(process_file_queue())
        except Exception as e:
            await message.reply_text(f"❌ Failed to queue file: `{str(e)}`")
            print(f"Direct File Queue Error: {e}")

    # 3. Admin Command: /add [Movie Name]
    @main_bot.on_message(filters.command("add") & filters.private & filters.user(ADMIN_ID))
    async def add_movie_cmd(client: Client, message: Message):
        global ADD_ENABLED
        if not ADD_ENABLED:
            await message.reply_text("❌ **The Add feature is currently turned OFF by the admin.**")
            return

        lines = message.text.split("\n")
        movies_to_process = []
        
        if len(lines) == 1:
            parts = lines[0].split(None, 1)
            if len(parts) > 1:
                movies_to_process.append(parts[1].strip())
        else:
            for line in lines:
                cleaned = line.replace("/add", "").strip()
                if cleaned:
                    movies_to_process.append(cleaned)

        if not movies_to_process:
            await message.reply_text("⚠️ **Usage:** `/add athiradi` or send multiple names line by line.")
            return

        status_msg = await message.reply_text("⏳ **Indexing process started...**")
        
        success_count = 0
        failed_count = 0
        total_movies = len(movies_to_process)

        for index, movie in enumerate(movies_to_process, start=1):
            if not ADD_ENABLED:
                await status_msg.edit_text("⚠️ **Process aborted! The Add feature was turned off.**")
                return

            try:
                await status_msg.edit_text(
                    f"🔍 **Processing [{index}/{total_movies}]:** `{movie}`\n"
                    "⏳ *Please wait, searching and adding to channel...*"
                )
                
                sent_msg = await userbot.send_message(TARGET_BOT, movie)
                await asyncio.sleep(6)

                first_link = None
                async for reply in userbot.get_chat_history(TARGET_BOT, limit=5):
                    if reply.id > sent_msg.id and reply.text and reply.entities:
                        for entity in reply.entities:
                            if entity.type.name == "TEXT_LINK" and entity.url:
                                first_link = entity.url
                                break
                    if first_link:
                        break

                if first_link and "start=" in first_link:
                    param = first_link.split("start=")[1].split("?")[0]
                    start_msg = await userbot.send_message(TARGET_BOT, f"/start {param}")
                    await asyncio.sleep(6)

                    file_added = False
                    async for file_msg in userbot.get_chat_history(TARGET_BOT, limit=5):
                        if file_msg.id > start_msg.id and (file_msg.document or file_msg.video):
                            fallback = file_msg.document.file_name if file_msg.document else movie
                            raw_caption = file_msg.caption or fallback
                            
                            final_caption = clean_caption(raw_caption, movie)
                            
                            await file_msg.copy(chat_id=MY_CHANNEL, caption=final_caption)
                            success_count += 1
                            file_added = True
                            break
                    
                    if not file_added:
                        failed_count += 1
                else:
                    failed_count += 1

                if index < total_movies:
                    await status_msg.edit_text(
                        f"✅ Completed: `{movie}`\n"
                        f"⏳ **Waiting 60 seconds before searching the next movie...** [{index}/{total_movies}]"
                    )
                    await asyncio.sleep(60)
                else:
                    await asyncio.sleep(2)

            except Exception as e:
                failed_count += 1
                print(f"Error adding {movie}: {e}")

        await status_msg.edit_text(
            f"✨ **Process Completed Successfully!**\n\n"
            f"📥 Successfully Added: `{success_count}`\n"
            f"❌ Failed / Not Found: `{failed_count}`"
        )

    # 4. User Search Handler (Requires minimum 4 letters and lists all matching files)
    @main_bot.on_message(filters.text & filters.private & ~filters.regex(r"^/") & ~filters.via_bot)
    async def handle_user_search(client: Client, message: Message):
        if message.outgoing or message.from_user.is_bot:
            return

        save_user(message.from_user.id)
        movie_name = message.text.strip()
        
        if "t.me/" in movie_name:
            return

        # Check if movie name has at least 4 characters
        if len(movie_name) < 4:
            await message.reply_text("⚠️ **Please type at least 4 characters to search for a movie!**")
            return

        status_msg = await message.reply_text(f"🔎 Searching for `{movie_name}`...")

        try:
            results = []
            async for ch_message in userbot.search_messages(MY_CHANNEL, query=movie_name):
                if ch_message.document or ch_message.video or ch_message.audio:
                    title = ch_message.caption or (ch_message.document.file_name if ch_message.document else "Movie File")
                    results.append({"id": ch_message.id, "title": title})

            await status_msg.delete()

            if not results:
                await message.reply_text(f"❌ **No files found related to '{movie_name}'.**")
            else:
                keyboard, total_pages = get_search_markup(results, movie_name, page=1)
                await message.reply_text(
                    f"🎬 **Found {len(results)} files for '{movie_name}':**\n\n👇 Click on your preferred file below:",
                    reply_markup=keyboard
                )

        except Exception as e:
            try:
                await status_msg.delete()
            except:
                pass
            print(f"Search Error: {e}")

    # 5. Callback Query Handler
    @main_bot.on_callback_query()
    async def callback_handler(client: Client, callback_query: CallbackQuery):
        global ADD_ENABLED
        data = callback_query.data
        user_id = callback_query.from_user.id

        if data == "toggle_add":
            if user_id != ADMIN_ID:
                await callback_query.answer("⚠️ You are not authorized!", show_alert=True)
                return
            
            ADD_ENABLED = not ADD_ENABLED
            status_text = "🟢 Enabled" if ADD_ENABLED else "🔴 Disabled"
            toggle_btn_text = "Turn Off Add 🔴" if ADD_ENABLED else "Turn On Add 🟢"
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"Add Feature: {status_text}", callback_data="noop")],
                [InlineKeyboardButton(toggle_btn_text, callback_data="toggle_add")]
            ])
            await callback_query.message.edit_text(
                "⚙️ **Admin Control Panel**\n\nManage your bot settings below:",
                reply_markup=keyboard
            )
            await callback_query.answer(f"Add feature is now {'Enabled' if ADD_ENABLED else 'Disabled'}!", show_alert=False)
            return

        if data == "noop":
            await callback_query.answer()
            return

        # Callback for Available Files Button in Start Menu
        if data == "available_files_btn":
            await callback_query.answer("📊 Fetching file count...", show_alert=False)
            try:
                count = 0
                async for _ in userbot.search_messages(MY_CHANNEL, query=""):
                    count += 1
                
                await callback_query.message.reply_text(
                    f"📁 **Database Status:**\n\n"
                    f"✅ Total Available Files: `~{count}`\n\n"
                    f"💡 *Type any movie name (minimum 4 letters) to search and download!*"
                )
            except Exception as e:
                await callback_query.message.reply_text("❌ Failed to fetch file count. Please try again later.")
                print(f"Available Files Callback Error: {e}")
            return

        # Pagination Handler for Search Results
        if data.startswith("search_"):
            parts = data.split("_")
            page_str = parts[-1]
            page = int(page_str)
            query_text = "_".join(parts[1:-1])

            try:
                results = []
                async for ch_message in userbot.search_messages(MY_CHANNEL, query=query_text):
                    if ch_message.document or ch_message.video or ch_message.audio:
                        title = ch_message.caption or (ch_message.document.file_name if ch_message.document else "Movie File")
                        results.append({"id": ch_message.id, "title": title})

                if not results:
                    await callback_query.answer("❌ No files found!", show_alert=True)
                    return

                keyboard, total_pages = get_search_markup(results, query_text, page=page)
                await callback_query.message.edit_text(
                    f"🎬 **Found {len(results)} files for '{query_text}':**\n\n👇 Click on your preferred file below:",
                    reply_markup=keyboard
                )
                await callback_query.answer()
            except Exception as e:
                print(f"Pagination Error: {e}")
                await callback_query.answer("❌ Error loading page!", show_alert=True)
            return

        if data.startswith("get_"):
            file_msg_id = int(data.split("_")[1])

            is_joined = await check_force_sub(client, user_id)
            if not is_joined:
                join_keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("📢 Join Channel", url=UPDATE_CHANNEL_LINK)],
                    [InlineKeyboardButton("🔄 I Have Joined", callback_data=data)]
                ])
                await callback_query.answer("⚠️ Please join our update channel first!", show_alert=True)
                await callback_query.message.edit_text(
                    "⚠️ **You must join our update channel to get files!**\n\n"
                    "👇 Click the button below to join, then click **'I Have Joined'**.",
                    reply_markup=join_keyboard
                )
                return

            await callback_query.answer("📥 Sending file...", show_alert=False)
            try:
                await main_bot.copy_message(
                    chat_id=callback_query.message.chat.id,
                    from_chat_id=MY_CHANNEL,
                    message_id=file_msg_id
                )
            except Exception as e:
                await callback_query.message.reply_text("❌ Failed to send file. Please try again later.")
                print(f"Copy Error: {e}")

    # Start Flask in a separate thread so it binds to Render's port
    Thread(target=run_flask, daemon=True).start()

    await userbot.start()
    await main_bot.start()
    print("🚀 Movie Bot & Web Server successfully running!")

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
