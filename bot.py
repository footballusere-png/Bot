import asyncio
import os
import re
import math
from threading import Thread
from flask import Flask
from hydrogram import Client, filters
from hydrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from hydrogram.errors import UserNotParticipant, FloodWait

# ------------ CONFIGURATION ------------
API_ID = 28300966
API_HASH = "c0a1fe56b13f260c62bc4838feb416d9"
STRING_SESSION = "BQGv1qYAIeWJGD5qT23izLbMJPiWJ-AAmld2QM4rXcoRMwJw5iZfJBPcG3BTaX31W5OhlCfHr_cc_GVIB5Qiquf8503yugDygjD4IWb5UArRRtZ3guBKlZzjNln8E2oDyKCapD0YmsqN8UVZ3CCyDke3uKRZfqLNc6p5EkfAhaAgiUhcMyiqJIdb2c4a3CAIxizLxXopfs7e890zZfJjyQk7MMyMvsBlrlmSafudbcgb8BbFrX-XUTX1QknieWjnjtWeHFODjZ2K64BDC2Fo2fmQk4_6iVSXZJ9zK1bR-dTGJ30xHxznt8_j_DMNIkDePOa8KxW1uSD9vBGZv0CH1q5qQRoyCAAAAAGz4hg1AA"

BOT_TOKEN = "8014212534:AAEtlOlMPuXbkPHOxQdj0mJ8yXTPDG0x25M"

TARGET_BOT = "@DPCBackup_Files_01_Bot"  # Backup bot
MY_CHANNEL = -1004296254082             # Your backup/storage channel ID

# Force Join Configuration
FORCE_SUB_CHANNEL = -1002644197954
UPDATE_CHANNEL_LINK = "https://t.me/c/2644197954"

# Multiple Admins Configuration
ADMIN_IDS = [7312906293, 7199304293]

USER_DB_FILE = "users.txt"
GROUP_DB_FILE = "groups.txt"

# Global variables
ADD_ENABLED = True
file_queue = asyncio.Queue()
is_processing_queue = False
user_request_state = set()  # To track users who clicked request
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

# Helper Function: Save Groups where Bot is Added
def save_group(group_id: int):
    if not os.path.exists(GROUP_DB_FILE):
        open(GROUP_DB_FILE, "w").close()
    
    with open(GROUP_DB_FILE, "r+") as f:
        groups = f.read().splitlines()
        if str(group_id) not in groups:
            f.write(f"{group_id}\n")

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

# Helper Function: Custom Caption / Watermark Cleaner
def clean_caption(original_text: str, fallback_name: str) -> str:
    if not original_text:
        return f"🎬 **{fallback_name}**\n\n✨ **Powered by Movie Bot**"
    
    text_without_links = re.sub(r'https?://\S+|www\.\S+|t\.me/\S+|telegram\.me/\S+', '', original_text)
    text_without_usernames = re.sub(r'@\w+', '', text_without_links)
    cleaned = " ".join(text_without_usernames.split()).strip()
    
    if not cleaned:
        cleaned = fallback_name
        
    return f"🎬 **{cleaned}**\n\n📥 **Shared via Movie Bot**"

# Helper Function to Generate Pagination Markup for Search Results
def get_search_markup(results, query_text, page=1, per_page=10, is_group=False):
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
        
        cb_prefix = "pmget_" if is_group else "get_"
        buttons.append([InlineKeyboardButton(title, callback_data=f"{cb_prefix}{item['id']}")])
        
    nav_prefix = "grpsearch_" if is_group else "search_"
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"{nav_prefix}{query_text}_{page-1}"))
    
    nav_buttons.append(InlineKeyboardButton(f"📄 Page {page} of {total_pages}", callback_data="noop"))
    
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"{nav_prefix}{query_text}_{page+1}"))
        
    if nav_buttons:
        buttons.append(nav_buttons)
        
    return InlineKeyboardMarkup(buttons), total_pages

async def main():
    userbot = Client("my_userbot", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION)
    main_bot = Client("my_main_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

    # Background Worker to process queued files safely & notify groups
    async def process_file_queue():
        global is_processing_queue
        is_processing_queue = True
        
        status_msg = None
        while not file_queue.empty():
            item = await file_queue.get()
            message = item["message"]
            status_msg = item["status_msg"]
            remaining = file_queue.qsize() + 1
            
            try:
                if status_msg:
                    await status_msg.edit_text(f"⏳ **Queue Processing:** `{remaining}` files remaining in queue...")

                fallback = message.document.file_name if message.document else (message.video.file_name if message.video and message.video.file_name else "Movie File")
                raw_caption = message.caption or fallback
                final_caption = clean_caption(raw_caption, fallback)
                
                added_file_msg = await message.copy(chat_id=MY_CHANNEL, caption=final_caption)
                
                # --- BROADCAST DIRECT UPLOADED FILE TO ALL GROUPS ---
                if os.path.exists(GROUP_DB_FILE):
                    with open(GROUP_DB_FILE, "r") as gf:
                        groups = gf.read().splitlines()
                        
                    kb = InlineKeyboardMarkup([
                        [InlineKeyboardButton(f"📥 Get File", callback_data=f"pmget_{added_file_msg.id}")]
                    ])
                    announcement_text = (
                        f"🔥 **New File Added to Database!**\n\n"
                        f"🎬 **Title:** `{fallback}`\n\n"
                        f"👇 Click the button below to get it in your **Personal Chat (PM)**:"
                    )
                    for g_id in groups:
                        try:
                            grp_msg = await main_bot.send_message(int(g_id), announcement_text, reply_markup=kb)
                            async def del_announcement(m):
                                await asyncio.sleep(600)
                                try:
                                    await m.delete()
                                except:
                                    pass
                            asyncio.create_task(del_announcement(grp_msg))
                        except Exception as ge:
                            print(f"Failed to send to group {g_id}: {ge}")
                # ----------------------------------------------------

                await asyncio.sleep(3)
            except Exception as e:
                print(f"Queue Processing Error: {e}")
            
            file_queue.task_done()
        
        if status_msg:
            try:
                await status_msg.edit_text("✨ **All files successfully saved & broadcasted to groups!**")
            except:
                pass
        is_processing_queue = False

    # Track when bot is added to groups
    @main_bot.on_message(filters.new_chat_members)
    async def new_chat_member(client: Client, message: Message):
        for member in message.new_chat_members:
            if member.id == (await client.get_me()).id:
                save_group(message.chat.id)
                await message.reply_text("👋 **Hello! Thanks for adding me here.**\n\nSend any movie name and I will give you the files via buttons!")

    # Start Command (/start) with Menu Buttons
    @main_bot.on_message(filters.command("start") & filters.private)
    async def start_cmd(client: Client, message: Message):
        save_user(message.from_user.id)
        
        welcome_text = (
            f"👋 **Hello {message.from_user.mention},**\n\n"
            "🎬 **Welcome to Movie Finder Bot!**\n\n"
            "Just type and send the name of the movie you are looking for."
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📂 Available Files", callback_data="available_files_btn")],
            [InlineKeyboardButton("📢 Update Channel", url=UPDATE_CHANNEL_LINK)]
        ])
        await message.reply_text(text=welcome_text, reply_markup=keyboard, disable_web_page_preview=True)

    # Available Files Command (/available_files)
    @main_bot.on_message(filters.command("available_files") & filters.private)
    async def available_files_cmd(client: Client, message: Message):
        status_msg = await message.reply_text("📊 **Fetching total files from database channel...**")
        try:
            count = 0
            async for _ in userbot.search_messages(MY_CHANNEL, query=""):
                count += 1
            
            await status_msg.edit_text(
                f"📁 **Database Status:**\n\n"
                f"✅ Total Available Files: `{count}`\n\n"
                f"💡 *Type any movie name to search and download!*"
            )
        except Exception as e:
            await status_msg.edit_text("❌ Failed to fetch file count. Please try again later.")
            print(f"Available Files Error: {e}")

    # Admin Settings Panel Command
    @main_bot.on_message(filters.command(["panel", "admin"]) & filters.private & filters.user(ADMIN_IDS))
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

    # Broadcast Command (/broadcast)
    @main_bot.on_message(filters.command("broadcast") & filters.private & filters.user(ADMIN_IDS))
    async def broadcast_cmd(client: Client, message: Message):
        if not message.reply_to_message:
            await message.reply_text("⚠️ **Please reply to any message/photo/video to broadcast it to all users and groups!**")
            return

        status_msg = await message.reply_text("📢 **Broadcasting started...**")
        
        broadcast_msg = message.reply_to_message
        success_users = 0
        failed_users = 0
        success_groups = 0
        failed_groups = 0

        if os.path.exists(USER_DB_FILE):
            with open(USER_DB_FILE, "r") as f:
                users = f.read().splitlines()
            for u_id in users:
                try:
                    await broadcast_msg.copy(chat_id=int(u_id))
                    success_users += 1
                    await asyncio.sleep(0.1)
                except Exception:
                    failed_users += 1

        if os.path.exists(GROUP_DB_FILE):
            with open(GROUP_DB_FILE, "r") as gf:
                groups = gf.read().splitlines()
            for g_id in groups:
                try:
                    await broadcast_msg.copy(chat_id=int(g_id))
                    success_groups += 1
                    await asyncio.sleep(0.1)
                except Exception:
                    failed_groups += 1

        await status_msg.edit_text(
            f"✨ **Broadcast Completed Successfully!**\n\n"
            f"👤 **Users:** Success: `{success_users}` | Failed: `{failed_users}`\n"
            f"👥 **Groups:** Success: `{success_groups}` | Failed: `{failed_groups}`"
        )

    # Direct File Receiver Handler for Admins
    @main_bot.on_message((filters.document | filters.video | filters.audio) & filters.private & filters.user(ADMIN_IDS))
    async def handle_direct_file(client: Client, message: Message):
        global is_processing_queue
        try:
            if file_queue.empty() and not is_processing_queue:
                status_msg = await message.reply_text("📥 **Initializing file queue...**")
            else:
                status_msg = await message.reply_text("📥 **File added to queue...**")

            await file_queue.put({"message": message, "status_msg": status_msg})
            
            if not is_processing_queue:
                asyncio.create_task(process_file_queue())
        except Exception as e:
            await message.reply_text(f"❌ Failed to queue file: `{str(e)}`")
            print(f"Direct File Queue Error: {e}")

    # Admin Command: /add [Movie Name] (With 2 Minutes Delay between each movie)
    @main_bot.on_message(filters.command("add") & filters.private & filters.user(ADMIN_IDS))
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
                            
                            added_file_msg = await file_msg.copy(chat_id=MY_CHANNEL, caption=final_caption)
                            success_count += 1
                            file_added = True

                            # --- BROADCAST NEW MOVIE TO ALL GROUPS ---
                            if os.path.exists(GROUP_DB_FILE):
                                with open(GROUP_DB_FILE, "r") as gf:
                                    groups = gf.read().splitlines()
                                    
                                kb = InlineKeyboardMarkup([
                                    [InlineKeyboardButton(f"📥 Get {movie}", callback_data=f"pmget_{added_file_msg.id}")]
                                ])
                                announcement_text = (
                                    f"🔥 **New Movie Added to Database!**\n\n"
                                    f"🎬 **Title:** `{movie}`\n\n"
                                    f"👇 Click the button below to get it in your **Personal Chat (PM)**:"
                                )
                                for g_id in groups:
                                    try:
                                        grp_msg = await main_bot.send_message(int(g_id), announcement_text, reply_markup=kb)
                                        async def del_announcement(m):
                                            await asyncio.sleep(600)
                                            try:
                                                await m.delete()
                                            except:
                                                pass
                                        asyncio.create_task(del_announcement(grp_msg))
                                    except Exception as ge:
                                        print(f"Failed to send to group {g_id}: {ge}")
                            # -----------------------------------------

                            break
                    
                    if not file_added:
                        failed_count += 1
                else:
                    failed_count += 1

                if index < total_movies:
                    await status_msg.edit_text(
                        f"✅ Completed: `{movie}`\n"
                        f"⏳ **Waiting 2 minutes (120 seconds) before searching the next movie...** [{index}/{total_movies}]"
                    )
                    await asyncio.sleep(120)
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

    # User Search Handler (Handles requests and searches)
    @main_bot.on_message(filters.text & ~filters.regex(r"^/") & ~filters.via_bot & filters.private)
    async def handle_user_search(client: Client, message: Message):
        user_id = message.from_user.id
        user_mention = message.from_user.mention
        text = message.text.strip()

        if "t.me/" in text:
            return

        save_user(user_id)

        # Check if user is currently in request state
        if user_id in user_request_state:
            user_request_state.remove(user_id)
            
            # Send "Wait the file" response to user
            await message.reply_text("⏳ Thank you! Movie name received. **Wait the file.**")
            
            # Notify admins about the request with user details
            req_text = (
                f"🚨 **New Movie Request!**\n\n"
                f"👤 **User:** {user_mention} (`{user_id}`)\n"
                f"🎬 **Requested Movie:** `{text}`"
            )
            for admin_id in ADMIN_IDS:
                try:
                    await client.send_message(admin_id, req_text)
                except Exception as ex:
                    print(f"Failed to notify admin {admin_id}: {ex}")
            return

        # Normal Search Logic
        status_msg = await message.reply_text(f"🔎 Searching for `{text}`...")

        try:
            results = []
            async for ch_message in userbot.search_messages(MY_CHANNEL, query=text):
                if ch_message.document or ch_message.video or ch_message.audio:
                    title = ch_message.caption or (ch_message.document.file_name if ch_message.document else "Movie File")
                    results.append({"id": ch_message.id, "title": title})

            await status_msg.delete()

            if not results:
                req_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton("📝 Request Admin", callback_data="request_admin_click")]
                ])
                await message.reply_text(
                    f"❌ **No files found related to '{text}'.**\n\n👇 Click below to request this movie:",
                    reply_markup=req_markup
                )
            else:
                keyboard, total_pages = get_search_markup(results, text, page=1, is_group=False)
                await message.reply_text(
                    f"🎬 **Found {len(results)} files for '{text}':**\n\n👇 Click on your preferred file below:",
                    reply_markup=keyboard
                )

        except Exception as e:
            try:
                await status_msg.delete()
            except:
                pass
            print(f"Search Error: {e}")

    # Group Search Handler
    @main_bot.on_message(filters.text & ~filters.regex(r"^/") & ~filters.via_bot & (filters.group | filters.supergroup))
    async def handle_group_search(client: Client, message: Message):
        save_group(message.chat.id)
        movie_name = message.text.strip()
        if "t.me/" in movie_name:
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
                sent_msg = await message.reply_text(f"❌ **No files found related to '{movie_name}'.**")
                async def del_err(m):
                    await asyncio.sleep(600)
                    try:
                        await m.delete()
                    except:
                        pass
                asyncio.create_task(del_err(sent_msg))
            else:
                keyboard, total_pages = get_search_markup(results, movie_name, page=1, is_group=True)
                text_msg = (
                    f"🎬 **Found {len(results)} files for '{movie_name}':**\n\n"
                    f"👇 Click on any file below to get it in your **Personal Chat (PM)**!\n\n"
                    f"⚠️ *This message will be automatically deleted after 10 minutes.*"
                )
                sent_msg = await message.reply_text(text=text_msg, reply_markup=keyboard)

                async def delete_after_delay(msg):
                    await asyncio.sleep(600)
                    try:
                        await msg.delete()
                    except:
                        pass
                asyncio.create_task(delete_after_delay(sent_msg))

        except Exception as e:
            try:
                await status_msg.delete()
            except:
                pass
            print(f"Group Search Error: {e}")

    # Callback Query Handler
    @main_bot.on_callback_query()
    async def callback_handler(client: Client, callback_query: CallbackQuery):
        global ADD_ENABLED
        data = callback_query.data
        user_id = callback_query.from_user.id
        user_mention = callback_query.from_user.mention

        if data == "request_admin_click":
            user_request_state.add(user_id)
            await callback_query.answer("Please send the movie name now!", show_alert=True)
            await callback_query.message.edit_text(
                "📝 **Please send the name of the movie you want to request in the chat below:**"
            )
            return

        if data == "toggle_add":
            if user_id not in ADMIN_IDS:
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

        if data == "available_files_btn":
            await callback_query.answer("📊 Fetching file count...", show_alert=False)
            try:
                count = 0
                async for _ in userbot.search_messages(MY_CHANNEL, query=""):
                    count += 1
                
                await callback_query.message.reply_text(
                    f"📁 **Database Status:**\n\n"
                    f"✅ Total Available Files: `{count}`\n\n"
                    f"💡 *Type any movie name to search and download!*"
                )
            except Exception as e:
                await callback_query.message.reply_text("❌ Failed to fetch file count. Please try again later.")
                print(f"Available Files Callback Error: {e}")
            return

        if data.startswith("search_") or data.startswith("grpsearch_"):
            parts = data.split("_")
            is_grp = data.startswith("grpsearch_")
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

                keyboard, total_pages = get_search_markup(results, query_text, page=page, is_group=is_grp)
                await callback_query.message.edit_text(
                    f"🎬 **Found {len(results)} files for '{query_text}':**\n\n👇 Click on your preferred file below:",
                    reply_markup=keyboard
                )
                await callback_query.answer()
            except Exception as e:
                print(f"Pagination Error: {e}")
                await callback_query.answer("❌ Error loading page!", show_alert=True)
            return

        if data.startswith("pmget_") or data.startswith("get_"):
            is_pm = data.startswith("pmget_")
            file_msg_id = int(data.split("_")[1])

            if is_pm:
                bot_username = (await client.get_me()).username
                try:
                    await client.send_message(user_id, "👋 Hello! Here is your requested file:")
                except Exception:
                    start_link = f"https://t.me/{bot_username}?start=start"
                    pm_keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("🚀 Start Bot in PM", url=start_link)]
                    ])
                    await callback_query.answer("⚠️ Please start the bot in Personal Chat (PM) first!", show_alert=True)
                    await callback_query.message.reply_text(
                        f"👋 {user_mention}, please start the bot in your **Personal Chat (PM)** to receive files!",
                        reply_markup=pm_keyboard
                    )
                    return

            is_joined = await check_force_sub(client, user_id)
            if not is_joined:
                join_keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("📢 Join Channel", url=UPDATE_CHANNEL_LINK)],
                    [InlineKeyboardButton("🔄 I Have Joined", callback_data=data)]
                ])
                await callback_query.answer("⚠️ Please join our update channel first!", show_alert=True)
                if is_pm:
                    await client.send_message(
                        user_id,
                        "⚠️ **You must join our update channel to get files!**\n\n"
                        "👇 Click the button below to join, then click the movie button again.",
                        reply_markup=join_keyboard
                    )
                else:
                    await callback_query.message.edit_text(
                        "⚠️ **You must join our update channel to get files!**\n\n"
                        "👇 Click the button below to join, then click **'I Have Joined'**.",
                        reply_markup=join_keyboard
                    )
                return

            await callback_query.answer("📥 Sending file...", show_alert=False)
            target_chat = user_id if is_pm else callback_query.message.chat.id
            try:
                await main_bot.copy_message(
                    chat_id=target_chat,
                    from_chat_id=MY_CHANNEL,
                    message_id=file_msg_id
                )
            except Exception as e:
                await client.send_message(target_chat, "❌ Failed to send file. Please try again later.")
                print(f"Copy Error: {e}")

    Thread(target=run_flask, daemon=True).start()

    await userbot.start()
    await main_bot.start()
    print("🚀 Movie Bot & Web Server successfully running!")

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
