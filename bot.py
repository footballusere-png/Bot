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

TARGET_BOT = "@DPCBackup_Files_01_Bot"
MY_CHANNEL = -1004296254082

# Force Join Configuration
FORCE_SUB_CHANNEL = -1002644197954
UPDATE_CHANNEL_LINK = "https://t.me/c/2644197954"

# Admin Configuration
ADMIN_ID = 7312906293
USER_DB_FILE = "users.txt"
MOVIE_DB_FILE = "movies.txt"
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

    # 2. Admin Command: Add Movie via Bot (/add Movie Name)
    @main_bot.on_message(filters.command("add") & filters.private & filters.user(ADMIN_ID))
    async def add_movie_cmd(client: Client, message: Message):
        if len(message.command) < 2:
            await message.reply_text("⚠️ **ഉപയോഗിക്കേണ്ട രീതി:** `/add Pushpa 2`")
            return

        movie_name = message.text.split(None, 1)[1].strip()
        
        if not os.path.exists(MOVIE_DB_FILE):
            open(MOVIE_DB_FILE, "w", encoding="utf-8").close()

        with open(MOVIE_DB_FILE, "r+", encoding="utf-8") as f:
            existing_movies = [line.strip().lower() for line in f.readlines()]
            
            if movie_name.lower() in existing_movies:
                await message.reply_text(f"⚠️ **'{movie_name}'** ഇതിനകം ലിസ്റ്റിൽ ഉണ്ട്!")
                return
                
            f.write(f"{movie_name}\n")

        await message.reply_text(f"✅ **'{movie_name}'** വിജയകരമായി ലിസ്റ്റിലേക്ക് ആഡ് ചെയ്തു!")

    # 3. Admin Command: List Movies (/list)
    @main_bot.on_message(filters.command("list") & filters.private & filters.user(ADMIN_ID))
    async def list_movies_cmd(client: Client, message: Message):
        if not os.path.exists(MOVIE_DB_FILE):
            await message.reply_text("❌ ലിസ്റ്റിൽ സിനിമകളൊന്നും ആഡ് ചെയ്തിട്ടില്ല.")
            return

        with open(MOVIE_DB_FILE, "r", encoding="utf-8") as f:
            movies = f.read().splitlines()

        if not movies:
            await message.reply_text("❌ ലിസ്റ്റിൽ സിനിമകളൊന്നും ആഡ് ചെയ്തിട്ടില്ല.")
            return

        text = f"🎬 **ആകെ സിനിമകൾ: {len(movies)}**\n\n"
        text += "\n".join([f"{i+1}. {m}" for i, m in enumerate(movies[:50])])
        
        if len(movies) > 50:
            text += f"\n\n...ബാക്കി {len(movies)-50} സിനിമകൾ കൂടി ഉണ്ട്."

        await message.reply_text(text)

    # 4. Admin Broadcast Command (/broadcast)
    @main_bot.on_message(filters.command("broadcast") & filters.private & filters.user(ADMIN_ID))
    async def broadcast_cmd(client: Client, message: Message):
        if not message.reply_to_message and len(message.command) < 2:
            await message.reply_text("⚠️ **ബ്രോഡ്കാസ്റ്റ് ചെയ്യാൻ ഒരു മെസ്സേജിന് റിപ്ലൈ ചെയ്യുക അല്ലെങ്കിൽ ടെക്സ്റ്റ് അയക്കുക.**")
            return

        if not os.path.exists(USER_DB_FILE):
            await message.reply_text("❌ യൂസേഴ്സ് ആരും ഡാറ്റാബേസിൽ ലഭ്യമല്ല.")
            return

        with open(USER_DB_FILE, "r") as f:
            users = f.read().splitlines()

        status_msg = await message.reply_text(f"⏳ **ബ്രോഡ്കാസ്റ്റ് ആരംഭിച്ചു...**\n👥 ആകെ യൂസേഴ്സ്: `{len(users)}`")
        
        success = 0
        failed = 0

        for user_id in users:
            try:
                if message.reply_to_message:
                    await message.reply_to_message.copy(chat_id=int(user_id))
                else:
                    broadcast_text = message.text.split(None, 1)[1]
                    await client.send_message(chat_id=int(user_id), text=broadcast_text)
                success += 1
                await asyncio.sleep(0.1)
            except FloodWait as e:
                await asyncio.sleep(e.value)
            except Exception:
                failed += 1

        await status_msg.edit_text(
            f"✅ **ബ്രോഡ്കാസ്റ്റ് പൂർത്തിയായി!**\n\n"
            f"🎯 വിജയിച്ചത്: `{success}`\n"
            f"❌ പരാജയപ്പെട്ടത്: `{failed}`"
        )

    # 5. Movie Search Request (~filters.regex(r"^/") ഉപയോഗിച്ച് ഫിക്സ് ചെയ്തു)
    @main_bot.on_message(filters.text & filters.private & ~filters.regex(r"^/"))
    async def handle_user_search(client: Client, message: Message):
        save_user(message.from_user.id)

        movie_name = message.text.strip()
        if "t.me/" in movie_name:
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

        status_msg = await message.reply_text(
            f"🔍 **സെർച്ച് ചെയ്യുന്നു...**\n"
            f"🎬 **സിനിമ:** `{movie_name}`\n\n"
            f"⏳ *ഫയലുകൾ തിരയുന്നു, കാത്തിരിക്കൂ...*"
        )

        try:
            sent_msg = await userbot.send_message(TARGET_BOT, movie_name)
            await asyncio.sleep(4)

            first_link = None

            async for reply in userbot.get_chat_history(TARGET_BOT, limit=5):
                if reply.id > sent_msg.id and reply.text:
                    if reply.entities:
                        for entity in reply.entities:
                            if entity.type.name == "TEXT_LINK" and entity.url:
                                first_link = entity.url
                                break
                if first_link:
                    break

            if first_link and "t.me/" in first_link:
                await status_msg.edit_text("⏳ *ഫയൽ ലഭിക്കുന്നു, ദയവായി കാത്തിരിക്കൂ...*")

                if "start=" in first_link:
                    param = first_link.split("start=")[1]
                    if "?" in param:
                        param = param.split("?")[0]
                    
                    start_msg = await userbot.send_message(TARGET_BOT, f"/start {param}")
                else:
                    start_msg = sent_msg

                await asyncio.sleep(5)

                file_sent = False
                async for file_msg in userbot.get_chat_history(TARGET_BOT, limit=6):
                    if file_msg.id > start_msg.id and (file_msg.document or file_msg.video or file_msg.audio):
                        ch_msg = await file_msg.copy(chat_id=MY_CHANNEL)
                        
                        await main_bot.copy_message(
                            chat_id=message.chat.id,
                            from_chat_id=MY_CHANNEL,
                            message_id=ch_msg.id
                        )
                        file_sent = True
                        break

                if file_sent:
                    await status_msg.delete()
                else:
                    await status_msg.edit_text("⚠️ ഫയൽ ലഭ്യമായില്ല. ഫയൽ ലിങ്ക് വാലിഡ് ആണോ എന്ന് പരിശോധിക്കുക.")
            else:
                await status_msg.edit_text(
                    f"❌ **ക്ഷമിക്കണം!**\n\n**'{movie_name}'**യുടെ ഫയലുകൾ ലഭ്യമല്ല."
                )

        except Exception as e:
            await status_msg.edit_text(f"⚠️ **ഒരു സാങ്കേതിക തടസ്സം നേരിട്ടു!**\n\n`{e}`")

    await userbot.start()
    await main_bot.start()
    print("🚀 Movie Bot & Userbot വിജയകരമായി റൺ ആയി!")

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
