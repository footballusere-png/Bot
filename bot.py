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

MY_CHANNEL = -1002696679922             # Your backup/storage channel ID

# Force Join Configuration
FORCE_SUB_CHANNEL = -1003391211397
UPDATE_CHANNEL_LINK = "https://t.me/mfbotupdates"

# Multiple Admins Configuration (അഡ്മിൻമാർ മാത്രം)
ADMIN_IDS = [7312906293, 7199304293]

USER_DB_FILE = "users.txt"
GROUP_DB_FILE = "groups.txt"

# Global variables
ADD_ENABLED = True
file_queue = asyncio.Queue()
is_processing_queue = False
user_request_state = set()
broadcast_state = {} 
admin_chat_state = {} 
# ----------------------------------------

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive and running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# Helper Function: Save New Users (Duplicate ഒഴിവാക്കാൻ check ചെയ്തിരിക്കുന്നു)
def save_user(user_id: int):
    if not os.path.exists(USER_DB_FILE):
        open(USER_DB_FILE, "w").close()
    
    try:
        with open(USER_DB_FILE, "r") as f:
            users = f.read().splitlines()
        if str(user_id) not in users:
            with open(USER_DB_FILE, "a") as f:
                f.write(f"{user_id}\n")
    except Exception:
        pass

# Helper Function: Save Groups
def save_group(group_id: int):
    if not os.path.exists(GROUP_DB_FILE):
        open(GROUP_DB_FILE, "w").close()
    
    try:
        with open(GROUP_DB_FILE, "r") as f:
            groups = f.read().splitlines()
        if str(group_id) not in groups:
            with open(GROUP_DB_FILE, "a") as f:
                f.write(f"{group_id}\n")
    except Exception:
        pass

# Helper Function: Format File Size
def get_readable_size(size_in_bytes):
    if not size_in_bytes:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_in_bytes >= 1024 and i < len(units) - 1:
        size_in_bytes /= 1024.0
        i += 1
    return f"{size_in_bytes:.2f} {units[i]}"

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

# Helper Function: Clean Caption
def clean_caption(original_text: str, fallback_name: str) -> str:
    if not original_text:
        cleaned = fallback_name
    else:
        text_without_links = re.sub(r'https?://\S+|www\.\S+|t\.me/\S+|telegram\.me/\S+', '', original_text)
        text_without_usernames = re.sub(r'@\w+', '', text_without_links)
        cleaned = " ".join(text_without_usernames.split()).strip()
        if not cleaned:
            cleaned = fallback_name
        
    return (
        f"🎬 **{cleaned}**\n\n"
        f"👑 **Developer:** `Risham004`\n"
        f"📸 **Instagram:** https://instagram.com/trollpanda.in\n\n"
        f"✨ **Shared via Official Movie Bot** ⚡"
    )

# Helper Function for Pagination with Size & Name
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
        size_str = item["size"]
        display_text = f"📦 [{size_str}] {title}"
        if len(display_text) > 42:
            display_text = display_text[:39] + "..."
        
        cb_prefix = "pmget_" if is_group else "get_"
        buttons.append([InlineKeyboardButton(display_text, callback_data=f"{cb_prefix}{item['id']}")])
        
    nav_prefix = "grpsearch_" if is_group else "search_"
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("◀️ Previous", callback_data=f"{nav_prefix}{query_text}_{page-1}"))
    
    nav_buttons.append(InlineKeyboardButton(f"📄 {page} / {total_pages}", callback_data="noop"))
    
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("Next ▶️", callback_data=f"{nav_prefix}{query_text}_{page+1}"))
        
    if nav_buttons:
        buttons.append(nav_buttons)
        
    return InlineKeyboardMarkup(buttons), total_pages

async def main():
    userbot = Client("my_userbot", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION)
    main_bot = Client("my_main_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

    async def process_file_queue():
        global is_processing_queue
        is_processing_queue = True
        
        total_in_batch = file_queue.qsize()
        current_index = 0
        status_msg = None
        
        while not file_queue.empty():
            item = await file_queue.get()
            message = item["message"]
            raw_status_msg = item["status_msg"]
            current_index += 1
            
            if not status_msg:
                status_msg = raw_status_msg
            
            try:
                if status_msg:
                    await status_msg.edit_text(f"⚡ **Uploading files... [{current_index}/{total_in_batch}]**")

                fallback = message.document.file_name if message.document else (message.video.file_name if message.video and message.video.file_name else "Movie File")
                file_size_bytes = message.document.file_size if message.document else (message.video.file_size if message.video else 0)
                size_str = get_readable_size(file_size_bytes)
                
                raw_caption = message.caption or fallback
                final_caption = clean_caption(raw_caption, fallback)
                
                added_file_msg = await message.copy(chat_id=MY_CHANNEL, caption=final_caption)
                
                if os.path.exists(GROUP_DB_FILE):
                    with open(GROUP_DB_FILE, "r") as gf:
                        groups = gf.read().splitlines()
                        
                    kb = InlineKeyboardMarkup([
                        [InlineKeyboardButton(f"📥 ɢᴇᴛ ғɪʟᴇ ɪɴ ᴘᴍ [{size_str}]", callback_data=f"pmget_{added_file_msg.id}")]
                    ])
                    announcement_text = (
                        f"🔥 **New File Added to Database!**\n\n"
                        f"📂 **File Name:** `{fallback}`\n"
                        f"📊 **File Size:** `{size_str}`\n\n"
                        f"👑 **Developer:** `Risham004`\n"
                        f"📸 **Instagram:** https://instagram.com/trollpanda.in\n\n"
                        f"👇 **Click the button below to get it instantly in your PM:**"
                    )
                    for g_id in groups:
                        try:
                            await main_bot.send_message(int(g_id), announcement_text, reply_markup=kb)
                        except Exception:
                            pass

                await asyncio.sleep(1.5)
            except Exception as e:
                print(f"Queue Error: {e}")
            
            file_queue.task_done()
        
        if status_msg:
            try:
                await status_msg.edit_text(f"✨ **Successfully uploaded all files! [{total_in_batch}/{total_in_batch}]** ✅")
            except:
                pass
        is_processing_queue = False

    @main_bot.on_message(filters.new_chat_members)
    async def new_chat_member(client: Client, message: Message):
        for member in message.new_chat_members:
            if member.id == (await client.get_me()).id:
                save_group(message.chat.id)
                await message.reply_text("👋 **Hello! Thanks for adding me here.**\n\n✨ Send any movie name and I will give you the files instantly!")

    @main_bot.on_message(filters.command("start") & filters.private)
    async def start_cmd(client: Client, message: Message):
        save_user(message.from_user.id)
        
        welcome_text = (
            f"👋 **Hello {message.from_user.mention},**\n\n"
            "🎬 **Welcome to Premium Movie Finder Bot!**\n"
            "👑 **Developer:** `Risham004`\n\n"
            "✨ Just type and send the name of the movie or series you are looking for."
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📂 Available Files", callback_data="available_files_btn")],
            [InlineKeyboardButton("📢 Update Channel", url=UPDATE_CHANNEL_LINK)]
        ])
        await message.reply_text(text=welcome_text, reply_markup=keyboard, disable_web_page_preview=True)

    @main_bot.on_message(filters.command("available_files") & filters.private)
    async def available_files_cmd(client: Client, message: Message):
        status_msg = await message.reply_text("📊 **Fetching total files from database...**")
        try:
            count = 0
            async for _ in userbot.search_messages(MY_CHANNEL, query=""):
                count += 1
            
            await status_msg.edit_text(
                f"📁 **Database Status:**\n\n"
                f"✅ Total Available Files: `{count}`\n"
                f"👑 **Developer:** `Risham004`\n\n"
                f"💡 *Type any movie name to search and download!*"
            )
        except Exception:
            await status_msg.edit_text("❌ Failed to fetch file count.")

    @main_bot.on_message(filters.command(["panel", "admin"]) & filters.private & filters.user(ADMIN_IDS))
    async def admin_panel(client: Client, message: Message):
        global ADD_ENABLED
        status_text = "🟢 Enabled" if ADD_ENABLED else "🔴 Disabled"
        toggle_btn_text = "Turn Off Add 🔴" if ADD_ENABLED else "Turn On Add 🟢"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"Add Feature: {status_text}", callback_data="noop")],
            [InlineKeyboardButton(toggle_btn_text, callback_data="toggle_add")],
            [InlineKeyboardButton("👤 User Chat", callback_data="admin_user_chat_btn")],
            [InlineKeyboardButton("📢 Broadcast (/broadcast)", callback_data="admin_broadcast_btn")]
        ])
        await message.reply_text(
            "⚙️ **Admin Control Panel**\n\n✨ Manage your bot settings below:",
            reply_markup=keyboard
        )

    @main_bot.on_message(filters.command("broadcast") & filters.private & filters.user(ADMIN_IDS))
    async def broadcast_command(client: Client, message: Message):
        user_id = message.from_user.id
        broadcast_state[user_id] = False
        
        await message.reply_text(
            "📢 **Broadcast Mode Activated**\n\n"
            "💬 Now send the promotional message, photo, video, or media you want to broadcast to all users.\n\n"
            "*(Type /cancel to abort)*"
        )

    @main_bot.on_message((filters.document | filters.video | filters.audio | filters.text) & filters.private & filters.user(ADMIN_IDS))
    async def handle_admin_messages(client: Client, message: Message):
        global is_processing_queue
        user_id = message.from_user.id
        text_content = message.text.strip() if message.text else ""

        if text_content == "/cancel":
            if user_id in admin_chat_state:
                del admin_chat_state[user_id]
            if user_id in broadcast_state:
                del broadcast_state[user_id]
            await message.reply_text("❌ **Operation cancelled successfully.**")
            return

        if user_id in broadcast_state and broadcast_state[user_id] is False:
            del broadcast_state[user_id]
            
            if not os.path.exists(USER_DB_FILE):
                await message.reply_text("❌ No users found in database (`users.txt`)!")
                return
            
            with open(USER_DB_FILE, "r") as f:
                target_users = [int(uid.strip()) for uid in f.read().splitlines() if uid.strip().isdigit()]

            status_msg = await message.reply_text(f"🚀 **Broadcasting to {len(target_users)} users... Please wait.**")
            success_count = 0
            fail_count = 0
            
            for uid in target_users:
                try:
                    await message.copy(chat_id=uid)
                    success_count += 1
                    await asyncio.sleep(0.3)
                except Exception:
                    fail_count += 1

            await status_msg.edit_text(
                f"✨ **Broadcast Completed Successfully!** ✅\n\n"
                f"👥 Total Target Users: `{len(target_users)}`\n"
                f"🟢 Successful: `{success_count}`\n"
                f"🔴 Failed / Blocked: `{fail_count}`"
            )
            return

        if user_id in admin_chat_state:
            state_data = admin_chat_state[user_id]
            
            if state_data["step"] == "waiting_user_id":
                if not text_content.isdigit():
                    await message.reply_text("❌ **Invalid User ID!** Send a numeric ID.")
                    return
                
                target_user_id = int(text_content)
                admin_chat_state[user_id] = {"step": "waiting_message", "target_user": target_user_id}
                await message.reply_text(f"✅ Target User ID set to: `{target_user_id}`\n\n💬 Send your message now:")
                return

            elif state_data["step"] == "waiting_message":
                target_user_id = state_data["target_user"]
                try:
                    await message.copy(chat_id=target_user_id)
                    await message.reply_text(f"✨ **Successfully sent to user (`{target_user_id}`)!**")
                except Exception as e:
                    await message.reply_text(f"❌ Failed: `{str(e)}`")
                return

        if message.document or message.video or message.audio:
            try:
                status_msg = None
                if file_queue.empty() and not is_processing_queue:
                    status_msg = await message.reply_text("📥 **Initializing upload queue...**")

                await file_queue.put({"message": message, "status_msg": status_msg})
                
                if not is_processing_queue:
                    asyncio.create_task(process_file_queue())
            except Exception as e:
                await message.reply_text(f"❌ Failed to queue file: `{str(e)}`")

    @main_bot.on_message(filters.text & ~filters.regex(r"^/") & ~filters.via_bot & filters.private)
    async def handle_user_search(client: Client, message: Message):
        user_id = message.from_user.id
        text = message.text.strip()

        if "t.me/" in text:
            return

        save_user(user_id)

        if user_id in user_request_state:
            user_request_state.remove(user_id)
            await message.reply_text("⏳ Thank you! Movie name received. **Wait for the file.**")
            return

        status_msg = await message.reply_text(f"🔎 **Searching for** `{text}`...")

        try:
            results = []
            async for ch_message in userbot.search_messages(MY_CHANNEL, query=text):
                if ch_message and (ch_message.document or ch_message.video or ch_message.audio):
                    title = ch_message.caption or (ch_message.document.file_name if ch_message.document else (ch_message.video.file_name if ch_message.video else "Movie File"))
                    size_bytes = ch_message.document.file_size if ch_message.document else (ch_message.video.file_size if ch_message.video else 0)
                    size_str = get_readable_size(size_bytes)
                    results.append({"id": ch_message.id, "title": title, "size": size_str})

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
                keyboard, _ = get_search_markup(results, text, page=1, is_group=False)
                await message.reply_text(
                    f"🎬 **Found {len(results)} files for '{text}':**\n\n👇 **Click on your preferred file below:**",
                    reply_markup=keyboard
                )

        except Exception as e:
            print(f"Search Error (PM): {e}")
            try:
                await status_msg.delete()
            except:
                pass
            await message.reply_text("❌ An error occurred while searching. Please try again.")

    @main_bot.on_message(filters.text & ~filters.regex(r"^/") & ~filters.via_bot & filters.group)
    async def handle_group_search(client: Client, message: Message):
        save_group(message.chat.id)
        movie_name = message.text.strip()
        if "t.me/" in movie_name:
            return

        status_msg = await message.reply_text(f"🔎 **Searching for** `{movie_name}`...")

        try:
            results = []
            async for ch_message in userbot.search_messages(MY_CHANNEL, query=movie_name):
                if ch_message and (ch_message.document or ch_message.video or ch_message.audio):
                    title = ch_message.caption or (ch_message.document.file_name if ch_message.document else (ch_message.video.file_name if ch_message.video else "Movie File"))
                    size_bytes = ch_message.document.file_size if ch_message.document else (ch_message.video.file_size if ch_message.video else 0)
                    size_str = get_readable_size(size_bytes)
                    results.append({"id": ch_message.id, "title": title, "size": size_str})

            await status_msg.delete()

            if not results:
                sent_msg = await message.reply_text(f"❌ **No files found related to '{movie_name}'.**")
                async def del_err(m):
                    await asyncio.sleep(600)
                    try: await m.delete()
                    except: pass
                asyncio.create_task(del_err(sent_msg))
            else:
                keyboard, _ = get_search_markup(results, movie_name, page=1, is_group=True)
                text_msg = (
                    f"🎬 **Found {len(results)} files for '{movie_name}':**\n\n"
                    f"👇 **Click on any file below to get it in your PM!**\n\n"
                    f"⚠️ *This message will be automatically deleted after 10 minutes.*"
                )
                sent_msg = await message.reply_text(text=text_msg, reply_markup=keyboard)

                async def delete_after_delay(msg):
                    await asyncio.sleep(600)
                    try: await msg.delete()
                    except: pass
                asyncio.create_task(delete_after_delay(sent_msg))

        except Exception as e:
            print(f"Search Error (Group): {e}")
            try: await status_msg.delete()
            except: pass

    @main_bot.on_callback_query()
    async def callback_handler(client: Client, callback_query: CallbackQuery):
        global ADD_ENABLED
        data = callback_query.data
        user_id = callback_query.from_user.id
        user_mention = callback_query.from_user.mention

        if data == "admin_user_chat_btn":
            if user_id not in ADMIN_IDS:
                await callback_query.answer("⚠️ Not authorized!", show_alert=True)
                return
            admin_chat_state[user_id] = {"step": "waiting_user_id"}
            await callback_query.answer()
            await callback_query.message.edit_text("👤 **User Chat Mode**\n\nSend target User ID:")
            return

        if data == "admin_broadcast_btn":
            if user_id not in ADMIN_IDS:
                await callback_query.answer("⚠️ Not authorized!", show_alert=True)
                return
            broadcast_state[user_id] = False
            await callback_query.answer()
            await callback_query.message.edit_text(
                "📢 **Broadcast Mode Activated**\n\n"
                "💬 Now send the promotional message, photo, video, or media you want to broadcast to all users.\n\n"
                "*(Type /cancel to abort)*"
            )
            return

        if data == "request_admin_click":
            user_request_state.add(user_id)
            await callback_query.answer("Please send the movie name now!", show_alert=True)
            await callback_query.message.edit_text("📝 **Please send the name of the movie you want to request:**")
            return

        if data == "toggle_add":
            if user_id not in ADMIN_IDS:
                await callback_query.answer("⚠️ Not authorized!", show_alert=True)
                return
            ADD_ENABLED = not ADD_ENABLED
            status_text = "🟢 Enabled" if ADD_ENABLED else "🔴 Disabled"
            toggle_btn_text = "Turn Off Add 🔴" if ADD_ENABLED else "Turn On Add 🟢"
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"Add Feature: {status_text}", callback_data="noop")],
                [InlineKeyboardButton(toggle_btn_text, callback_data="toggle_add")],
                [InlineKeyboardButton("👤 User Chat", callback_data="admin_user_chat_btn")],
                [InlineKeyboardButton("📢 Broadcast (/broadcast)", callback_data="admin_broadcast_btn")]
            ])
            await callback_query.message.edit_text("⚙️ **Admin Control Panel**", reply_markup=keyboard)
            await callback_query.answer()
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
                await callback_query.message.reply_text(f"📁 **Database Status:**\n\n✅ Total Available Files: `{count}`\n👑 **Developer:** `Risham004`")
            except:
                await callback_query.message.reply_text("❌ Failed to fetch count.")
            return

        if data.startswith("search_") or data.startswith("grpsearch_"):
            parts = data.split("_")
            is_grp = data.startswith("grpsearch_")
            page = int(parts[-1])
            query_text = "_".join(parts[1:-1])

            try:
                results = []
                async for ch_message in userbot.search_messages(MY_CHANNEL, query=query_text):
                    if ch_message and (ch_message.document or ch_message.video or ch_message.audio):
                        title = ch_message.caption or (ch_message.document.file_name if ch_message.document else (ch_message.video.file_name if ch_message.video else "Movie File"))
                        size_bytes = ch_message.document.file_size if ch_message.document else (ch_message.video.file_size if ch_message.video else 0)
                        size_str = get_readable_size(size_bytes)
                        results.append({"id": ch_message.id, "title": title, "size": size_str})

                if not results:
                    await callback_query.answer("❌ No files found!", show_alert=True)
                    return

                keyboard, _ = get_search_markup(results, query_text, page=page, is_group=is_grp)
                await callback_query.message.edit_text(f"🎬 **Found {len(results)} files:**", reply_markup=keyboard)
                await callback_query.answer()
            except:
                await callback_query.answer("❌ Error loading page!", show_alert=True)
            return

        if data.startswith("pmget_") or data.startswith("get_"):
            is_pm = data.startswith("pmget_")
            file_msg_id = int(data.split("_")[1])
            bot_username = (await client.get_me()).username

            if is_pm:
                try:
                    await client.send_chat_action(user_id, "typing")
                except Exception:
                    start_link = f"https://t.me/{bot_username}?start=start"
                    pm_keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("🚀 Start Bot in PM", url=start_link)]
                    ])
                    await callback_query.answer("⚠️ Please start the bot in PM first!", show_alert=True)
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
                    try:
                        await client.send_message(
                            user_id,
                            "⚠️ **You must join our update channel to get files!**\n\n👇 Click below to join, then click the button again.",
                            reply_markup=join_keyboard
                        )
                    except: pass
                else:
                    await callback_query.message.edit_text(
                        "⚠️ **You must join our update channel first!**",
                        reply_markup=join_keyboard
                    )
                return

            await callback_query.answer("📥 Sending file to PM...", show_alert=False)
            target_chat = user_id if is_pm else callback_query.message.chat.id
            try:
                sent_file = await main_bot.copy_message(
                    chat_id=target_chat,
                    from_chat_id=MY_CHANNEL,
                    message_id=file_msg_id
                )
                
                # ഫയൽ ഓട്ടോ-ഡിലീറ്റ് സമയം 10 മിനിറ്റായി (600 സെക്കൻഡ്) മാറ്റിയിരിക്കുന്നു
                warning_text = (
                    "⚠️ **Important Notice:**\n"
                    "Due to copyright issues, this file will be **automatically deleted after 10 minutes (600 seconds)**.\n"
                    "📥 Please **forward this file** to your Saved Messages or personal channel immediately!\n\n"
                    "👑 **Developer:** `Risham004`\n"
                    "📸 **Instagram:** https://instagram.com/trollpanda.in"
                )
                warning_msg = await main_bot.send_message(target_chat, warning_text)

                async def auto_delete_files(file_msg, warn_msg):
                    await asyncio.sleep(600)
                    try: await file_msg.delete()
                    except: pass
                    try: await warn_msg.delete()
                    except: pass

                asyncio.create_task(auto_delete_files(sent_file, warning_msg))

            except Exception as e:
                print(f"Send Error: {e}")
                try:
                    await client.send_message(target_chat, "❌ Failed to send file. Make sure you started the bot in PM.")
                except: pass

    Thread(target=run_flask, daemon=True).start()

    await userbot.start()
    await main_bot.start()
    print("🚀 Premium Movie Bot & Web Server successfully running!")

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
