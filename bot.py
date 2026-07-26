import asyncio
import os
from hydrogram import Client, filters
from hydrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from hydrogram.errors import UserNotParticipant, FloodWait

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
        
        is_joined = await check_force_sub(client, message.from_user.id)
        if not is_joined:
            join_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 ചാനലിൽ ജോയിൻ ചെയ്യുക", url=UPDATE_CHANNEL_LINK)],
                [InlineKeyboardButton("🔄 Try Again", url=f"https://t.me/{(await client.get_me()).username}?start=start")]
            ])
            await message.reply_text(
                f"👋 **ഹലോ {message.from_user.mention},**\n\n"
                "⚠️ **സിനിമകൾ ഡൗൺലോഡ് ചെയ്യുന്നതിനായി ആദ്യം ഞങ്ങളുടെ അപ്‌ഡേറ്റ് ചാനലിൽ സബ്‌സ്‌ക്രൈബ് ചെയ്യേണ്ടതുണ്ട്!**\n\n"
                "👇 താഴെയുള്ള ബട്ടണിൽ ക്ലിക്ക് ചെയ്ത് ചാനലിൽ ജോയിൻ ചെയ്ത ശേഷം **Try Again** അമർത്തുക.",
                reply_markup=join_keyboard
            )
            return

        welcome_text = (
            f"👋 **ഹലോ {message.from_user.mention},**\n\n"
            "🎬 **Movie Finder Bot**-ലേക്ക് സ്വാഗതം!\n\n"
            "നിങ്ങൾക്ക് ആവശ്യമായ ഏത് സിനിമയുടെയും പേര് കൃത്യമായി താഴെ ടൈപ്പ് ചെയ്ത് അയക്കുക.\n\n"
            "✨ *ഉദാഹരണത്തിന്:* `Naran`"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 അപ്‌ഡേറ്റ് ചാനൽ", url=UPDATE_CHANNEL_LINK)]
        ])
        await message.reply_text(text=welcome_text, reply_markup=keyboard, disable_web_page_preview=True)

    # 2. Admin Command: /add [Movie Name] (നേരിട്ട് ബോട്ടിൽ പോയി സെർച്ച് ചെയ്ത് ചാനലിൽ ആഡ് ചെയ്യുന്നു)
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
            await status_msg.edit_text(f"🔍 സെർച്ച് ചെയ്യുന്നു: `{movie}`")
            try:
                # Step 1: TARGET_BOT-ലേക്ക് സിനിമയുടെ പേര് അയക്കുന്നു
                sent_msg = await userbot.send_message(TARGET_BOT, movie)
                await asyncio.sleep(6)

                first_link = None
                # Step 2: റിസൾട്ടിൽ നിന്ന് ലിങ്ക് എടുക്കുന്നു
                async for reply in userbot.get_chat_history(TARGET_BOT, limit=5):
                    if reply.id > sent_msg.id and reply.text and reply.entities:
                        for entity in reply.entities:
                            if entity.type.name == "TEXT_LINK" and entity.url:
                                first_link = entity.url
                                break
                    if first_link:
                        break

                # Step 3: ഡീപ് ലിങ്ക് വഴി ഫയൽ വരുത്തുന്നു
                if first_link and "start=" in first_link:
                    param = first_link.split("start=")[1].split("?")[0]
                    start_msg = await userbot.send_message(TARGET_BOT, f"/start {param}")
                    await asyncio.sleep(6)

                    # Step 4: ഫയൽ എടുത്ത് ചാനലിലേക്ക് സേവ് ചെയ്യുന്നു
                    file_added = False
                    async for file_msg in userbot.get_chat_history(TARGET_BOT, limit=5):
                        if file_msg.id > start_msg.id and (file_msg.document or file_msg.video):
                            await file_msg.copy(chat_id=MY_CHANNEL, caption=f"🎬 **{movie}**")
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
            f"✅ **പ്രക്രിയ പൂർത്തിയായി!**\n\n"
            f"🎯 വിജയകരമായി ചാനലിൽ ആഡ് ചെയ്തവ: `{success_count}`\n"
            f"❌ കിട്ടാത്തവ / പരാജയപ്പെട്ടവ: `{failed_count}`"
        )

    # 3. User Search Handler (യൂസർ ചോദിക്കുമ്പോൾ സ്വന്തം ചാനലിൽ നിന്ന് മാത്രം ഫയൽ നൽകുന്നു - ലൂപ്പ് തടയാൻ ഫിൽട്ടറുകൾ ശക്തമാക്കിയിരിക്കുന്നു)
    @main_bot.on_message(filters.text & filters.private & ~filters.regex(r"^/") & ~filters.via_bot)
    async def handle_user_search(client: Client, message: Message):
        # ബോട്ട് അയക്കുന്ന സ്വന്തം മെസ്സേജുകളെ ഒഴിവാക്കാൻ (ലൂപ്പ് തടയാൻ)
        if message.from_user.is_bot:
            return

        save_user(message.from_user.id)
        movie_name = message.text.strip()
        
        if "t.me/" in movie_name or len(movie_name) < 2:
            return

        is_joined = await check_force_sub(client, message.from_user.id)
        if not is_joined:
            join_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 ചാനലിൽ ജോയിൻ ചെയ്യുക", url=UPDATE_CHANNEL_LINK)],
                [InlineKeyboardButton("🔄 Try Again", url=f"https://t.me/{(await client.get_me()).username}?start=start")]
            ])
            await message.reply_text(
                "⚠️ **ഫയലുകൾ ലഭിക്കുന്നതിനായി ആദ്യം ഞങ്ങളുടെ ചാനലിൽ ജോയിൻ ചെയ്യുക!**\n\n"
                "👇 താഴെയുള്ള ബട്ടണിൽ ക്ലിക്ക് ചെയ്ത് ജോയിൻ ചെയ്ത ശേഷം വീണ്ടും സിനിമ പേര് സെർച്ച് ചെയ്യുക.",
                reply_markup=join_keyboard
            )
            return

        status_msg = await message.reply_text(f"🔍 **സെർച്ച് ചെയ്യുന്നു:** `{movie_name}`...")

        try:
            file_found = False
            async for ch_message in userbot.search_messages(MY_CHANNEL, query=movie_name):
                if ch_message.document or ch_message.video or ch_message.audio:
                    # ഫയൽ കണ്ടെത്തിയാൽ യൂസർക്ക് അയച്ചു കൊടുക്കുന്നു
                    await main_bot.copy_message(
                        chat_id=message.chat.id,
                        from_chat_id=MY_CHANNEL,
                        message_id=ch_message.id
                    )
                    file_found = True
                    break

            if file_found:
                await status_msg.delete()  # സെർച്ച് ചെയ്തപ്പോൾ വന്ന വെറും ടെക്സ്റ്റ് മെസ്സേജ് ഡിലീറ്റ് ചെയ്യുന്നു
            else:
                await status_msg.edit_text(f"❌ **'{movie_name}'** ഡാറ്റാബേസിൽ ലഭ്യമല്ല.")

        except Exception as e:
            await status_msg.edit_text(f"⚠️ ഒരു ചെറിയ തടസ്സം നേരിട്ടു: `{e}`")

    await userbot.start()
    await main_bot.start()
    print("🚀 Movie Bot വിജയകരമായി റൺ ആയി!")

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
