import asyncio
import os
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

# Global variable to control Add feature status
ADD_ENABLED = True
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

async def main():
    userbot = Client("my_userbot", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION)
    main_bot = Client("my_main_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

    # 1. Start Command (/start)
    @main_bot.on_message(filters.command("start") & filters.private)
    async def start_cmd(client: Client, message: Message):
        save_user(message.from_user.id)
        
        welcome_text = (
            f"👋 **Hello {message.from_user.mention},**\n\n"
            "🎬 **Welcome to Movie Finder Bot!**\n\n"
            "Just type and send the name of the movie you are looking for."
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Update Channel", url=UPDATE_CHANNEL_LINK)]
        ])
        await message.reply_text(text=welcome_text, reply_markup=keyboard, disable_web_page_preview=True)

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

    # 2. Admin Command: /add [Movie Name] (With 30s delay and ON/OFF check)
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
                            file_name = file_msg.caption or (file_msg.document.file_name if file_msg.document else movie)
                            await file_msg.copy(chat_id=MY_CHANNEL, caption=f"🎬 **{file_name}**")
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
                        f"⏳ **Waiting 30 seconds before searching the next movie...** [{index}/{total_movies}]"
                    )
                    await asyncio.sleep(30)
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

    # 3. User Search Handler
    @main_bot.on_message(filters.text & filters.private & ~filters.regex(r"^/") & ~filters.via_bot)
    async def handle_user_search(client: Client, message: Message):
        if message.outgoing or message.from_user.is_bot:
            return

        save_user(message.from_user.id)
        movie_name = message.text.strip()
        
        if "t.me/" in movie_name or len(movie_name) < 2:
            return

        status_msg = await message.reply_text(f"🔎 Searching for `{movie_name}`...")

        try:
            buttons = []
            async for ch_message in userbot.search_messages(MY_CHANNEL, query=movie_name):
                if ch_message.document or ch_message.video or ch_message.audio:
                    title = ch_message.caption or (ch_message.document.file_name if ch_message.document else "Movie File")
                    if len(title) > 40:
                        title = title[:37] + "..."
                    
                    buttons.append([InlineKeyboardButton(title, callback_data=f"get_{ch_message.id}")])
                    
                    if len(buttons) >= 10:
                        break

            await status_msg.delete()

            if not buttons:
                await message.reply_text(f"❌ **No files found related to '{movie_name}'.**")
            else:
                keyboard = InlineKeyboardMarkup(buttons)
                await message.reply_text(
                    f"🎬 **Found files for '{movie_name}':**\n\n👇 Click on your preferred file below:",
                    reply_markup=keyboard
                )

        except Exception as e:
            try:
                await status_msg.delete()
            except:
                pass
            print(f"Search Error: {e}")

    # 4. Callback Query Handler (Handles toggle and file delivery)
    @main_bot.on_callback_query()
    async def callback_handler(client: Client, callback_query: CallbackQuery):
        global ADD_ENABLED
        data = callback_query.data
        user_id = callback_query.from_user.id

        # Admin Toggle Handler
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
                await callback_query.message.delete()
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
