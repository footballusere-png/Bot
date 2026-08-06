# bot.py
import re
import asyncio
import sys
import traceback
from bson import ObjectId
from hydrogram import Client, filters
from hydrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from config import API_ID, API_HASH, BOT_TOKEN, DB_CHANNEL, FORCE_CHANNEL, ADMINS
import database as db

# എറർ ഡെബഗ്ഗിംഗിനായി
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    print("Uncaught exception:", file=sys.stderr)
    traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)

sys.excepthook = handle_exception

bot = Client(
    "FileSearchBot", 
    api_id=API_ID, 
    api_hash=API_HASH, 
    bot_token=BOT_TOKEN
)

async def is_subscribed(client, user_id):
    if not FORCE_CHANNEL:
        return True
    try:
        user = await client.get_chat_member(FORCE_CHANNEL, user_id)
        if user.status in ["banned", "left"]:
            return False
        return True
    except:
        return False

@bot.on_message(filters.command("start") & filters.private)
async def start_handler(client, message: Message):
    user_id = message.from_user.id
    await db.add_user(user_id)
    
    welcome_text = (
        f"ഹലോ **{message.from_user.first_name}**! 👋\n\n"
        "ഞാനൊരു **File Searching Bot** ആണ്. നിങ്ങൾക്ക് ആവശ്യമുള്ള ഫയലുകളുടെ പേര് "
        "ചോദിച്ചാൽ ഞാൻ അത് സെർച്ച് ചെയ്ത് തരുന്നതാണ്.\n\n"
        "നിങ്ങൾക്ക് വേണ്ട ഫയലിന്റെ പേര് ഇപ്പോൾ അയക്കൂ!"
    )
    await message.reply_text(welcome_text)

@bot.on_message(filters.chat(DB_CHANNEL))
async def auto_save_files(client, message: Message):
    media = message.document or message.video or message.audio
    if media:
        file_id = media.file_id
        file_name = media.file_name or "Unknown File"
        file_size = round(media.file_size / (1024 * 1024), 2)
        caption = message.caption or ""
        await db.save_file(file_id, file_name, f"{file_size} MB", caption)

@bot.on_message(filters.text & filters.private & ~filters.command(["broadcast", "botStates", "total_files", "total_users", "daily_status", "daily_searches"]))
async def search_handler(client, message: Message):
    user_id = message.from_user.id
    query = message.text.strip()
    
    await db.add_user(user_id)
    searching_msg = await message.reply_text("🔎 **Searching files...**")
    
    buttons = []
    async for file in db.files_collection.find({"file_name": {"$regex": query, "$options": "i"}}).limit(10):
        btn_text = f"📂 {file['file_name']} ({file['file_size']})"
        buttons.append([InlineKeyboardButton(btn_text, callback_data=f"file_{file['_id']}")])

    await searching_msg.delete()

    if not buttons:
        await message.reply_text("❌ ക്ഷമിക്കണം, നിങ്ങൾ ചോദിച്ച ഫയൽ ഡാറ്റാബേസിൽ കണ്ടെത്താനായില്ല.")
        return

    keyboard = InlineKeyboardMarkup(buttons)
    await message.reply_text(f"✨ **'{query}'** എന്നതിനായി താഴെ കാണുന്ന ഫയലുകൾ ലഭിച്ചു:", reply_markup=keyboard)

@bot.on_callback_query(filters.regex(r"^file_"))
async def send_file_callback(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    
    if not await is_subscribed(client, user_id):
        join_button = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/c/{str(FORCE_CHANNEL)[4:]}/1")],
            [InlineKeyboardButton("🔄 Try Again", callback_data=callback_query.data)]
        ])
        await callback_query.answer("⚠️ ബോട്ട് ഉപയോഗിക്കാൻ ആദ്യം ഞങ്ങളുടെ ചാനൽ ജോയിൻ ചെയ്യൂ!", show_alert=True)
        await callback_query.message.edit_text(
            "⚠️ **നിങ്ങൾ നിർബന്ധമായും ഞങ്ങളുടെ ചാനൽ ജോയിൻ ചെയ്യേണ്ടതുണ്ട്!**\n\nചാനൽ ജോയിൻ ചെയ്ത ശേഷം താഴെയുള്ള 'Try Again' ബട്ടൺ ക്ലിക്ക് ചെയ്യുക.",
            reply_markup=join_button
        )
        return

    file_db_id = callback_query.data.split("_")[1]
    
    try:
        file_data = await db.files_collection.find_one({"_id": ObjectId(file_db_id)})
    except:
        await callback_query.answer("❌ ഫയൽ കണ്ടെത്താനായില്ല.", show_alert=True)
        return

    if not file_data:
        await callback_query.answer("❌ ഫയൽ ഡാറ്റാബേസിൽ ലഭ്യമായില്ല.", show_alert=True)
        return

    await callback_query.answer("Sending file...")
    
    warning_text = (
        f"📂 **{file_data['file_name']}**\n\n"
        f"{file_data.get('caption', '')}\n\n"
        "⚠️ **കോപ്പിറൈറ്റ് പ്രശ്നങ്ങൾ ഉള്ളതിനാൽ ഈ ഫയൽ 5 മിനിറ്റിനുള്ളിൽ ഓട്ടോ ഡിലീറ്റ് ആകുന്നതാണ്!**\n"
        "📥 ഇത് പെട്ടെന്ന് തന്നെ നിങ്ങളുടെ **Saved Messages**-ലേക്ക് ഫോർവേഡ് ചെയ്ത് സേവ് ചെയ്തു വെക്കുക."
    )
    
    sent_msg = await client.send_cached_media(
        chat_id=user_id,
        file_id=file_data['file_id'],
        caption=warning_text
    )
    
    async def delete_later():
        await asyncio.sleep(300)
        try:
            await sent_msg.delete()
        except:
            pass
            
    asyncio.create_task(delete_later())

# Admin Commands
@bot.on_message(filters.command("broadcast") & filters.user(ADMINS))
async def broadcast_handler(client, message: Message):
    if not message.reply_to_message:
        await message.reply_text("⚠️ ഏതെങ്കിലും മെസ്സേജിന് റിപ്ലൈ ആയി വേണം `/broadcast` എന്ന് കൊടുക്കാൻ!")
        return
        
    sent, failed = 0, 0
    async for user in db.users_collection.find({}):
        try:
            await message.reply_to_message.copy(chat_id=user["user_id"])
            sent += 1
            await asyncio.sleep(0.1)
        except:
            failed += 1
    await message.reply_text(f"✅ **Broadcast Completed!**\n\nSent: {sent}\nFailed: {failed}")

@bot.on_message(filters.command("botStates") & filters.user(ADMINS))
async def bot_states_handler(client, message: Message):
    users = await db.total_users_count()
    files = await db.total_files_count()
    await message.reply_text(f"📊 **Bot Status:**\n\n👥 Total Users: {users}\n📁 Total Files: {files}")

# Public Commands
@bot.on_message(filters.command("total_files"))
async def total_files_cmd(client, message: Message):
    count = await db.total_files_count()
    await message.reply_text(f"📁 ഡാറ്റാബേസിൽ ആകെ ഉള്ള ഫയലുകൾ: **{count}**")

@bot.on_message(filters.command("total_users"))
async def total_users_cmd(client, message: Message):
    count = await db.total_users_count()
    await message.reply_text(f"👥 ബോട്ടിൽ ആകെ ഉള്ള യൂസേഴ്സ്: **{count}**")

@bot.on_message(filters.command("daily_status"))
async def daily_status_cmd(client, message: Message):
    users = await db.total_users_count()
    await message.reply_text(f"📈 **Daily Status:**\nആകെ യൂസേഴ്സ്: {users}")

@bot.on_message(filters.command("daily_searches"))
async def daily_searches_cmd(client, message: Message):
    await message.reply_text("🔍 ഇന്നത്തെ സേർച്ച് വിവരങ്ങൾ ഇവിടെ ലഭ്യമാണ്.")

if __name__ == "__main__":
    print("Main Search Bot started...")
    bot.run()
