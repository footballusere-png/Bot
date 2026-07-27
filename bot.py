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

TARGET_BOT = "@DPCBackup_Files_01_Bot"  # ബാക്കപ്പ് ബോട്ട്
MY_CHANNEL = -1004296254082             # ഫയലുകൾ സേവ് ആകുന്ന നിങ്ങളുടെ ചാനൽ

# Force Join Configuration
FORCE_SUB_CHANNEL = -1002644197954
UPDATE_CHANNEL_LINK = "https://t.me/c/2644197954"

# Admin Configuration
ADMIN_ID = 7312906293
USER_DB_FILE = "users.txt"
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
            f"👋 **ഹലോ {message.from_user.mention},**\n\n"
            "🎬 **Movie Finder Bot**-ലേക്ക് സ്വാഗതം!\n\n"
            "നിങ്ങൾക്ക് ആവശ്യമായ ഏത് സിനിമയുടെയും പേര് കൃത്യമായി താഴെ ടൈപ്പ് ചെയ്ത് അയക്കുക."
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 അപ്‌ഡേറ്റ് ചാനൽ", url=UPDATE_CHANNEL_LINK)]
        ])
        await message.reply_text(text=welcome_text, reply_markup=keyboard, disable_web_page_preview=True)

    # 2. Admin Command: /add [Movie Name]
    @main_bot.on_message(filters.command("add") & filters.private & filters.user(ADMIN_ID))
    async def add_movie_cmd(client: Client, message: Message):
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
            await message.reply_text("⚠️ **ഉപയോഗിക്കേണ്ട രീതി:** `/add athiradi` അല്ലെങ്കിൽ ഒന്നിധികം പേരുകൾ വരിയായി നൽകുക.")
            return

        status_msg = await message.reply_text("⏳ **ഫയൽ തിരയുന്ന പ്രക്രിയ ആരംഭിച്ചു...**")
        
        success_count = 0
        failed_count = 0

        for movie in movies_to_process:
            try:
                await status_msg.edit_text(f"🔍 സെർച്ച് ചെയ്യുന്നു: `{movie}`")
                
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
                            # ഫയലിന്റെ യഥാർത്ഥ കാപ്ഷൻ അല്ലെങ്കിൽ ഫയൽ നെയിം എടുക്കുന്നു
                            file_name = file_msg.caption or (file_msg.document.file_name if file_msg.document else movie)
                            await file_msg.copy(chat_id=MY_CHANNEL, caption=f"🎬 **{file_name}**")
                            success_count += 1
                            file_added = True
                            break
                    
                    if not file_added:
                        failed_count += 1
                else:
                    failed_count += 1

                await asyncio.sleep(2)
            except Exception:
                failed_count += 1

        await status_msg.edit_text(
            f"✨ **പ്രക്രിയ വിജയകരമായി പൂർത്തിയായി!**\n\n"
            f"📥 ചാനലിലേക്ക് സേവ് ചെയ്തവ: `{success_count}`\n"
            f"❌ കണ്ടെത്താനാവാത്തവ: `{failed_count}`"
        )

    # 3. User Search Handler (ചാനലിൽ നിന്ന് മാച്ച് ആവുന്നവ ലിസ്റ്റ് ബട്ടണുകളായി കാണിക്കുന്നു)
    @main_bot.on_message(filters.text & filters.private & ~filters.regex(r"^/") & ~filters.via_bot)
    async def handle_user_search(client: Client, message: Message):
        if message.outgoing or message.from_user.is_bot:
            return

        save_user(message.from_user.id)
        movie_name = message.text.strip()
        
        if "t.me/" in movie_name or len(movie_name) < 2:
            return

        status_msg = await message.reply_text(f"🔎 `{movie_name}` സെർച്ച് ചെയ്യുന്നു...")

        try:
            buttons = []
            async for ch_message in userbot.search_messages(MY_CHANNEL, query=movie_name):
                if ch_message.document or ch_message.video or ch_message.audio:
                    # ഫയലിന്റെ പേര് അല്ലെങ്കിൽ കാപ്ഷൻ എടുക്കുന്നു
                    title = ch_message.caption or (ch_message.document.file_name if ch_message.document else "Movie File")
                    # ബട്ടൺ വലുപ്പം കുറക്കാൻ പേര് ചെറുതാക്കാം
                    if len(title) > 40:
                        title = title[:37] + "..."
                    
                    # കോൾബാക്ക് ഡാറ്റയിൽ മെസ്സേജ് ഐഡിയും സ്റ്റോർ ചെയ്യുന്നു (Format: file_MessageID)
                    buttons.append([InlineKeyboardButton(title, callback_data=f"get_{ch_message.id}")])
                    
                    if len(buttons) >= 10:  # പരമാവധി 10 ഫീലുകൾ മാത്രം ബട്ടണായി കാണിക്കാൻ
                        break

            await status_msg.delete()

            if not buttons:
                await message.reply_text(f"❌ **'{movie_name}'** സംബന്ധമായ ഫയലുകൾ ഒന്നും കണ്ടെത്താനായില്ല.")
            else:
                keyboard = InlineKeyboardMarkup(buttons)
                await message.reply_text(
                    f"🎬 **'{movie_name}'** എന്ന പേരിൽ താഴെ കാണുന്ന ഫയലുകൾ ലഭ്യമBാണ്:\n\n👇 ആവശ്യമായ ഫയലിൽ ക്ലിക്ക് ചെയ്യുക:",
                    reply_markup=keyboard
                )

        except Exception as e:
            try:
                await status_msg.delete()
            except:
                pass
            print(f"Search Error: {e}")

    # 4. Callback Query Handler (ബട്ടൺ ക്ലിക്ക് ചെയ്യുമ്പോൾ വർക്ക് ചെയ്യുന്നത്)
    @main_bot.on_callback_query()
    async def callback_handler(client: Client, callback_query: CallbackQuery):
        data = callback_query.data
        user_id = callback_query.from_user.id

        if data.startswith("get_"):
            file_msg_id = int(data.split("_")[1])

            # Force Join Check
            is_joined = await check_force_sub(client, user_id)
            if not is_joined:
                join_keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("📢 ചാനലിൽ ജോയിൻ ചെയ്യുക", url=UPDATE_CHANNEL_LINK)],
                    [InlineKeyboardButton("🔄 ഞാൻ ജോയിൻ ചെയ്തു", callback_data=data)]
                ])
                await callback_query.answer("⚠️ ആദ്യം ചാനലിൽ ജോയിൻ ചെയ്യുക!", show_alert=True)
                await callback_query.message.edit_text(
                    "⚠️ **ഫയലുകൾ ലഭിക്കുന്നതിനായി ആദ്യം ഞങ്ങളുടെ ചാനലിൽ ജോയിൻ ചെയ്യുക!**\n\n"
                    "👇 താഴെയുള്ള ബട്ടണിൽ ക്ലിക്ക് ചെയ്ത് ജോയിൻ ചെയ്ത ശേഷം **'ഞാൻ ജോയിൻ ചെയ്തു'** ബട്ടൺ അമർത്തുക.",
                    reply_markup=join_keyboard
                )
                return

            # ജോയിൻ ചെയ്തിട്ടുണ്ടെങ്കിൽ ഫയൽ സെന്റ് ചെയ്യുക
            await callback_query.answer("📥 ഫയൽ അയച്ചുകൊണ്ടിരിക്കുന്നു...", show_alert=False)
            try:
                await main_bot.copy_message(
                    chat_id=callback_query.message.chat.id,
                    from_chat_id=MY_CHANNEL,
                    message_id=file_msg_id
                )
                await callback_query.message.delete()
            except Exception as e:
                await callback_query.message.reply_text("❌ ഫയൽ സെന്റ് ചെയ്യുന്നതിൽ തടസ്സം നേരിട്ടു. ദയവായി വീണ്ടും ശ്രമിക്കുക.")
                print(f"Copy Error: {e}")

    # Start Flask in a separate thread so it binds to Render's port
    Thread(target=run_flask, daemon=True).start()

    await userbot.start()
    await main_bot.start()
    print("🚀 Movie Bot & Web Server വിജയകരമായി റൺ ആയി!")

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
