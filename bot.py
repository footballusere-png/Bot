import os
import asyncio
import logging
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
from hydrogram import Client, filters
from hydrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from hydrogram.enums import ChatAction
from hydrogram.errors import UserNotParticipant

# Asyncio Event Loop Fix
try:
    asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

logging.basicConfig(level=logging.INFO)

# ---------- DUMMY WEB SERVER FOR RENDER ----------
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Kerala Syllabus Textbooks Bot Active")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

Thread(target=run_web_server, daemon=True).start()
# ------------------------------------------------

# ---------- CONFIGURATION ----------
API_ID = 28300966
API_HASH = "c0a1fe56b13f260c62bc4838feb416d9"
BOT_TOKEN = "8174552245:AAGzK5x7A55r-JVk-DVdteCz8nLBpu0jndU"

# നിങ്ങളുടെ അഡ്മിൻ ടെലിഗ്രാം ID (ബ്രോഡ്കാസ്റ്റിനായി മാത്രം)
ADMIN_ID = 1234567890  # ⚠️ ഇവിടെ നിങ്ങളുടെ യഥാർത്ഥ Telegram User ID നൽകുക

# ചാനൽ & ഗ്രൂപ്പ് ID-കൾ
GROUP_ID = -1002702148703
CHANNEL_ID = -1003938671650

app = Client("KeralaSyllabusBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# യൂസേഴ്സ് ലിസ്റ്റ് സൂക്ഷിക്കാൻ Set
USERS_DB = set()

# ------------------------------------------------
# PDF FILE IDs Database
# ⚠️ താഴെ കാണുന്ന File ID-കൾ നിങ്ങളുടെ ചാനലിലെ PDF ഫയലുകളുടെ File ID നൽകുക.
# ------------------------------------------------
TEXTBOOKS = {
    # Class 10
    "std10_mal": "https://t.me/c/2702148703/101", # അല്ലെങ്കിൽ Telegram File ID
    "std10_eng": "https://t.me/c/2702148703/102",
    
    # Class 9
    "std9_mal": "https://t.me/c/2702148703/91",
    "std9_eng": "https://t.me/c/2702148703/92",

    # Class 8
    "std8_mal": "https://t.me/c/2702148703/81",
    "std8_eng": "https://t.me/c/2702148703/82",
}

# ---------------- FORCE SUBSCRIBE CHECK ----------------
async def check_force_sub(client, user_id):
    try:
        # Check Group
        member1 = await client.get_chat_member(GROUP_ID, user_id)
        if member1.status in ["kicked", "left"]:
            return False
        
        # Check Channel
        member2 = await client.get_chat_member(CHANNEL_ID, user_id)
        if member2.status in ["kicked", "left"]:
            return False

        return True
    except UserNotParticipant:
        return False
    except Exception as e:
        logging.error(f"Force Sub Error: {e}")
        return True

# ---------------- START COMMAND ----------------
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message: Message):
    user_id = message.from_user.id
    USERS_DB.add(user_id)

    welcome_text = (
        f"👋 **നമസ്കാരം {message.from_user.first_name}!**\n\n"
        "📚 **കേരള സിലബസ് പാഠപുസ്തകങ്ങളിലേക്ക് സ്വാഗതം!**\n\n"
        "താഴെ നൽകിയിരിക്കുന്ന ബട്ടണുകളിൽ ക്ലിക്ക് ചെയ്ത് നിങ്ങൾക്ക് ആവശ്യമുള്ള ക്ലാസ്സും മാധ്യമവും തിരഞ്ഞെടുക്കാം."
    )

    main_buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📚 Textbooks (പാഠപുസ്തകങ്ങൾ)", callback_data="btn_textbooks")],
        [InlineKeyboardButton("📰 School News & Updates (സ്കൂൾ വാർത്തകൾ)", callback_data="btn_news")]
    ])

    await message.reply_text(welcome_text, reply_markup=main_buttons)

# ---------------- FORCE SUB UI BUILDER ----------------
async def show_force_sub_msg(client, message, is_callback=False):
    try:
        chat_group = await client.get_chat(GROUP_ID)
        group_link = chat_group.invite_link or f"https://t.me/c/{str(GROUP_ID)[4:]}"
    except Exception:
        group_link = "https://t.me"

    try:
        chat_channel = await client.get_chat(CHANNEL_ID)
        channel_link = chat_channel.invite_link or f"https://t.me/c/{str(CHANNEL_ID)[4:]}"
    except Exception:
        channel_link = "https://t.me"

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Join Discussion Group", url=group_link)],
        [InlineKeyboardButton("📢 Join Main Channel", url=channel_link)],
        [InlineKeyboardButton("🔄 Verify & Continue (സ്ഥിരീകരിക്കുക)", callback_data="check_sub")]
    ])

    sub_text = (
        "⚠️ **ഫയൽ ലഭിക്കുന്നതിനായി താഴെ കാണുന്ന ഗ്രൂപ്പിലും ചാനലിലും ജോയിൻ ചെയ്യേണ്ടതുണ്ട്!**\n\n"
        "1. **Discussion Group**\n"
        "2. **Main Channel**\n\n"
        "രണ്ടിലും ജോയിൻ ചെയ്ത ശേഷം **'Verify & Continue'** ബട്ടൺ അമർത്തുക."
    )

    if is_callback:
        await message.edit_text(sub_text, reply_markup=buttons)
    else:
        await message.reply_text(sub_text, reply_markup=buttons)

# ---------------- CALLBACK HANDLER ----------------
@app.on_callback_query()
async def callback_handler(client, query: CallbackQuery):
    user_id = query.from_user.id
    USERS_DB.add(user_id)
    data = query.data

    # Verify Subscription Button
    if data == "check_sub":
        is_joined = await check_force_sub(client, user_id)
        if is_joined:
            await query.answer("✅ Verified Successfully!", show_alert=True)
            # Main Menu Show
            main_buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton("📚 Textbooks (പാഠപുസ്തകങ്ങൾ)", callback_data="btn_textbooks")],
                [InlineKeyboardButton("📰 School News & Updates", callback_data="btn_news")]
            ])
            await query.message.edit_text("✅ **പരിശോധന പൂർത്തിയായി! നിങ്ങൾക്ക് ആവശ്യമുള്ള വിവരങ്ങൾ തിരഞ്ഞെടുക്കാം:**", reply_markup=main_buttons)
        else:
            await query.answer("❌ നിങ്ങൾ ചാനലിലും ഗ്രൂപ്പിലും ജോയിൻ ചെയ്തിട്ടില്ല!", show_alert=True)
        return

    # Check Force Sub before proceeding to downloads
    is_joined = await check_force_sub(client, user_id)
    if not is_joined:
        await show_force_sub_msg(client, query.message, is_callback=True)
        return

    # Main Textbooks Menu
    if data == "btn_textbooks":
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("Class 10", callback_data="std_10"), InlineKeyboardButton("Class 9", callback_data="std_9")],
            [InlineKeyboardButton("Class 8", callback_data="std_8"), InlineKeyboardButton("Class 7", callback_data="std_7")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]
        ])
        await query.message.edit_text("📖 **നിങ്ങളുടെ ക്ലാസ്സ് തിരഞ്ഞെടുക്കുക:**", reply_markup=buttons)

    # Class Medium Selection (Class 10)
    elif data == "std_10":
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🟢 Malayalam Medium", callback_data="dl_std10_mal")],
            [InlineKeyboardButton("🔵 English Medium", callback_data="dl_std10_eng")],
            [InlineKeyboardButton("🔙 Back", callback_data="btn_textbooks")]
        ])
        await query.message.edit_text("🌐 **Class 10 - മാധ്യമം (Medium) തിരഞ്ഞെടുക്കുക:**", reply_markup=buttons)

    # Download Handler
    elif data.startswith("dl_"):
        book_key = data.replace("dl_", "")
        pdf_url = TEXTBOOKS.get(book_key)

        if pdf_url:
            await query.message.edit_text(f"📥 **നിങ്ങളുടെ പാഠപുസ്തക ഫയൽ താഴെ നൽകിയിരിക്കുന്നു:**\n\n🔗 {pdf_url}")
        else:
            await query.message.edit_text("⚠️ **ഈ ക്ലാസ്സിലെ PDF ഫയൽ ഉടൻ അപ്‌ലോഡ് ചെയ്യുന്നതാണ്.**")

    # School News Section
    elif data == "btn_news":
        news_text = (
            "📢 **ലൈവ് സ്കൂൾ വിവരങ്ങളും വാർത്തകളും:**\n\n"
            "• **സ്കൂൾ തുറക്കുന്ന തീയതികൾ**\n"
            "• **പരീക്ഷാ ടൈംടേബിളുകൾ**\n"
            "• **സ്കോളർഷിപ്പ് വിവരങ്ങൾ**\n\n"
            "എല്ലാ വിവരങ്ങളും പ്രധാന ചാനലിൽ ദിവസവും ലൈവ് ആയി അപ്ഡേറ്റ് ചെയ്യുന്നതാണ്."
        )
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]
        ])
        await query.message.edit_text(news_text, reply_markup=buttons)

    # Back to Main Menu
    elif data == "main_menu":
        main_buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("📚 Textbooks (പാഠപുസ്തകങ്ങൾ)", callback_data="btn_textbooks")],
            [InlineKeyboardButton("📰 School News & Updates", callback_data="btn_news")]
        ])
        await query.message.edit_text("🎯 **Main Menu:**", reply_markup=main_buttons)

# ---------------- BROADCAST COMMAND (FOR ADMIN) ----------------
@app.on_message(filters.command("broadcast") & filters.private)
async def broadcast_cmd(client, message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    if not message.reply_to_message:
        await message.reply_text("⚠️ **എല്ലാവർക്കും അയക്കേണ്ട മെസ്സേജിന് മറുപടിയായി (Reply) `/broadcast` എന്ന് ടൈപ്പ് ചെയ്യുക.**")
        return

    broadcast_msg = message.reply_to_message
    total = len(USERS_DB)
    success = 0

    status_msg = await message.reply_text(f"🚀 Broadcasting to {total} users...")

    for user_id in USERS_DB:
        try:
            await broadcast_msg.copy(chat_id=user_id)
            success += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass

    await status_msg.edit_text(f"✅ **Broadcast Completed!**\n\nTotal Sent: {success}/{total}")

# ---------------- BOT START ----------------
if __name__ == "__main__":
    async def main():
        await app.start()
        print("Kerala Syllabus Bot is Live and Running!")
        await asyncio.Event().wait()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
