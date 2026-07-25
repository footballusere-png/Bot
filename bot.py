import os
import asyncio
import logging
import requests
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
from hydrogram import Client, filters
from hydrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ChatJoinRequest, BotCommand
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

# ---------- FIREBASE REALTIME DATABASE CONFIG ----------
RTDB_URL = "https://a-one-chat-e3642-default-rtdb.firebaseio.com"

# ---------- BOT CONFIGURATION ----------
API_ID = 28300966
API_HASH = "c0a1fe56b13f260c62bc4838feb416d9"
BOT_TOKEN = "8174552245:AAGzK5x7A55r-JVk-DVdteCz8nLBpu0jndU"

ADMIN_ID = 7312906293  # Telegram User ID

GROUP_ID = -1002702148703
CHANNEL_ID = -1003938671650

app = Client("KeralaSyllabusBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ---------------- FORCE SUBSCRIBE CHECK ----------------
async def check_force_sub(client, user_id):
    try:
        member1 = await client.get_chat_member(GROUP_ID, user_id)
        if member1.status in ["kicked", "left"]:
            return False
        
        member2 = await client.get_chat_member(CHANNEL_ID, user_id)
        if member2.status in ["kicked", "left"]:
            return False

        return True
    except UserNotParticipant:
        return False
    except Exception as e:
        logging.error(f"Force Sub Error: {e}")
        return True

# ---------------- AUTO APPROVE JOIN REQUEST (NO DM MESSAGE) ----------------
@app.on_chat_join_request()
async def handle_join_request(client, request: ChatJoinRequest):
    user_id = request.from_user.id
    chat_id = request.chat.id

    try:
        # Join Request ഓട്ടോമാറ്റിക്കായി Approve ചെയ്യുന്നു
        await client.approve_chat_join_request(chat_id, user_id)
        
        # യൂസറെ മെസ്സേജ് അയക്കാതെ ഫയർബേസിൽ മാത്രം സേവ് ചെയ്യുന്നു
        user_data = {
            "user_id": user_id, 
            "name": request.from_user.first_name,
            "join_requested": True
        }
        requests.put(f"{RTDB_URL}/users/{user_id}.json", json=user_data)
    except Exception as e:
        logging.error(f"Join Request Error: {e}")

# ---------------- ADMIN COMMAND: ADD TEXTBOOK ----------------
@app.on_message(filters.command("add") & filters.private)
async def add_textbook_cmd(client, message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    if not message.reply_to_message or not message.reply_to_message.document:
        await message.reply_text(
            "⚠️ **ഉപയോഗിക്കേണ്ട രീതി:**\n"
            "ചാനലിൽ നിന്നുള്ള PDF ഫയലിന് Reply ആയി താഴെ കാണുന്ന രീതിയിൽ ടൈപ്പ് ചെയ്യുക:\n\n"
            "`/add [Class] [Subject] [Part]`\n\n"
            "📌 **Example:** `/add 1 Malayalam Part-1`"
        )
        return

    args = message.text.split(maxsplit=3)
    if len(args) < 4:
        await message.reply_text("❌ **Format തെറ്റാണ്!**\nExample: `/add 1 Malayalam Part-1` എന്ന് നൽകുക.")
        return

    class_num = args[1]
    subject = args[2]
    part = args[3]

    doc = message.reply_to_message.document
    file_id = doc.file_id
    file_name = doc.file_name or f"Class_{class_num}_{subject}_{part}.pdf"

    data = {
        "class": class_num,
        "subject": subject,
        "part": part,
        "file_id": file_id,
        "file_name": file_name
    }

    node_key = f"std_{class_num}_{subject}_{part}".replace(" ", "_").replace("-", "_")

    # Realtime Database-ലേക്ക് ഡാറ്റ സേവ് ചെയ്യുന്നു
    rtdb_endpoint = f"{RTDB_URL}/textbooks/{node_key}.json"
    res = requests.put(rtdb_endpoint, json=data)

    if res.status_code == 200:
        await message.reply_text(
            f"✅ **പാഠപുസ്തകം റിയൽ ടൈം ഡാറ്റാബേസിലേക്ക് ചേർത്തു!**\n\n"
            f"🏫 **Class:** {class_num}\n"
            f"📖 **Subject:** {subject}\n"
            f"📑 **Part:** {part}\n"
            f"📁 **File Name:** {file_name}"
        )
    else:
        await message.reply_text("❌ **Realtime Database-ലേക്ക് ആഡ് ചെയ്യാൻ സാധിച്ചില്ല.**")

# ---------------- START COMMAND ----------------
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message: Message):
    user_id = message.from_user.id

    # Save user to Realtime Database
    user_data = {"user_id": user_id, "name": message.from_user.first_name}
    requests.put(f"{RTDB_URL}/users/{user_id}.json", json=user_data)

    welcome_text = (
        f"👋 **നമസ്കാരം {message.from_user.first_name}!**\n\n"
        "📚 **കേരള സിലബസ് പാഠപുസ്തകങ്ങളിലേക്ക് സ്വാഗതം!**\n\n"
        "താഴെ നൽകിയിരിക്കുന്ന ബട്ടണുകളിൽ ക്ലിക്ക് ചെയ്ത് പാഠപുസ്തകങ്ങൾ ഡൗൺലോഡ് ചെയ്യാം."
    )

    main_buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📚 Textbooks (ക്ലാസ്സ് 1 - 10)", callback_data="btn_textbooks")],
        [InlineKeyboardButton("📰 School News & Updates", callback_data="btn_news")]
    ])

    await message.reply_text(welcome_text, reply_markup=main_buttons)

# ---------------- CALLBACK HANDLER ----------------
@app.on_callback_query()
async def callback_handler(client, query: CallbackQuery):
    user_id = query.from_user.id
    data = query.data

    if data == "check_sub":
        is_joined = await check_force_sub(client, user_id)
        if is_joined:
            await query.answer("✅ Verified Successfully!", show_alert=True)
            main_buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton("📚 Textbooks (ക്ലാസ്സ് 1 - 10)", callback_data="btn_textbooks")],
                [InlineKeyboardButton("📰 School News & Updates", callback_data="btn_news")]
            ])
            await query.message.edit_text("✅ **പരിശോധന പൂർത്തിയായി!**", reply_markup=main_buttons)
        else:
            await query.answer("❌ നിങ്ങൾ ചാനലിലും ഗ്രൂപ്പിലും ജോയിൻ ചെയ്തിട്ടില്ല!", show_alert=True)
        return

    is_joined = await check_force_sub(client, user_id)
    if not is_joined:
        await query.answer("⚠️ ആദ്യം ചാനലിലും ഗ്രൂപ്പിലും ജോയിൻ ചെയ്യുക!", show_alert=True)
        return

    # Classes Menu (1 to 10)
    if data == "btn_textbooks":
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("Class 10", callback_data="std_10"), InlineKeyboardButton("Class 9", callback_data="std_9")],
            [InlineKeyboardButton("Class 8", callback_data="std_8"), InlineKeyboardButton("Class 7", callback_data="std_7")],
            [InlineKeyboardButton("Class 6", callback_data="std_6"), InlineKeyboardButton("Class 5", callback_data="std_5")],
            [InlineKeyboardButton("Class 4", callback_data="std_4"), InlineKeyboardButton("Class 3", callback_data="std_3")],
            [InlineKeyboardButton("Class 2", callback_data="std_2"), InlineKeyboardButton("Class 1", callback_data="std_1")],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
        ])
        await query.message.edit_text("📖 **നിങ്ങളുടെ ക്ലാസ്സ് തിരഞ്ഞെടുക്കുക:**", reply_markup=buttons)

    # Fetch Books for selected Class from Realtime Database
    elif data.startswith("std_"):
        class_num = data.replace("std_", "")
        
        res = requests.get(f"{RTDB_URL}/textbooks.json")
        buttons = []

        if res.status_code == 200 and res.json():
            all_books = res.json()
            for key, item in all_books.items():
                if str(item.get("class")) == str(class_num):
                    btn_title = f"📘 {item['subject']} ({item['part']})"
                    buttons.append([InlineKeyboardButton(btn_title, callback_data=f"getpdf_{key}")])

        buttons.append([InlineKeyboardButton("🔙 Back to Classes", callback_data="btn_textbooks")])
        
        if not buttons[:-1]:
            await query.message.edit_text(f"⚠️ **Class {class_num}-ൽ ലഭ്യമായ പുസ്തകങ്ങൾ ഒന്നും ചേർത്തിട്ടില്ല.**", reply_markup=InlineKeyboardMarkup(buttons))
        else:
            await query.message.edit_text(f"🌐 **Class {class_num} - ലഭ്യമായ പുസ്തകങ്ങൾ:**", reply_markup=InlineKeyboardMarkup(buttons))

    # Send PDF File
    elif data.startswith("getpdf_"):
        node_key = data.replace("getpdf_", "")
        res = requests.get(f"{RTDB_URL}/textbooks/{node_key}.json")

        if res.status_code == 200 and res.json():
            book_data = res.json()
            file_id = book_data.get("file_id")

            await query.message.delete()
            await client.send_chat_action(chat_id=query.message.chat.id, action=ChatAction.UPLOAD_DOCUMENT)

            back_btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Classes", callback_data="btn_textbooks")]])
            
            await client.send_document(
                chat_id=query.message.chat.id,
                document=file_id,
                caption=f"📚 **Class {book_data['class']} - {book_data['subject']} ({book_data['part']})**\n\nDownloaded via Kerala Syllabus Bot",
                reply_markup=back_btn
            )
        else:
            await query.answer("❌ File not found in Realtime Database!", show_alert=True)

    elif data == "btn_news":
        news_text = (
            "📰 **സ്കൂൾ വാർത്തകളും വിവരങ്ങളും (Live Updates):**\n\n"
            "• **അധ്യയന ദിനങ്ങൾ & പരീക്ഷണ ടൈംടേബിൾ**\n"
            "• **സ്കോളർഷിപ്പ് വിവരങ്ങൾ**\n"
            "• **വിദ്യാഭ്യാസ അറിയിപ്പുകൾ**\n\n"
            "എല്ലാ വിവരങ്ങളും ലൈവ് ആയി കാണാൻ ചാനലിലേക്ക് സ്വാഗതം!"
        )
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
        ])
        await query.message.edit_text(news_text, reply_markup=buttons)

    elif data == "main_menu":
        main_buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("📚 Textbooks (ക്ലാസ്സ് 1 - 10)", callback_data="btn_textbooks")],
            [InlineKeyboardButton("📰 School News & Updates", callback_data="btn_news")]
        ])
        await query.message.edit_text("🎯 **Main Menu:**", reply_markup=main_buttons)

# ---------------- BROADCAST COMMAND ----------------
@app.on_message(filters.command("broadcast") & filters.private)
async def broadcast_cmd(client, message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    if not message.reply_to_message:
        await message.reply_text("⚠️ മെസ്സേജിന് മറുപടിയായി `/broadcast` എന്ന് നൽകുക.")
        return

    res = requests.get(f"{RTDB_URL}/users.json")
    broadcast_msg = message.reply_to_message
    success = 0

    if res.status_code == 200 and res.json():
        users = res.json()
        for u_id, u_info in users.items():
            try:
                await broadcast_msg.copy(chat_id=int(u_id))
                success += 1
                await asyncio.sleep(0.05)
            except Exception:
                pass

    await message.reply_text(f"✅ **Broadcast Completed! Sent to {success} users.**")

# ---------------- BOT START & MENU BUTTON SETTINGS ----------------
if __name__ == "__main__":
    async def main():
        await app.start()
        
        # Telegram App-ൽ താഴെ Menu Button സെറ്റ് ചെയ്യുന്നു
        await app.set_bot_commands([
            BotCommand("start", "🚀 സ്റ്റാർട്ട് ചെയ്യുക / Main Menu"),
            BotCommand("add", "➕ പാഠപുസ്തകം ആഡ് ചെയ്യുക (Admin)"),
            BotCommand("broadcast", "📢 എല്ലാവർക്കും മെസ്സേജ് അയക്കുക (Admin)")
        ])
        
        print("Bot Started with Menu Button Configured!")
        await asyncio.Event().wait()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
