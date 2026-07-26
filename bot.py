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

MY_CHANNEL = -1004296254082 # ഫയലുകൾ ഉള്ള നിങ്ങളുടെ ചാനൽ ID

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

    # 2. Multiple Movie Add Command (/add)
    @main_bot.on_message(filters.command("add") & filters.private & filters.user(ADMIN_ID))
    async def add_movie_cmd(client: Client, message: Message):
        lines = message.text.split("\n")
        
        movies_to_add = []
        if len(lines) == 1:
            parts = lines[0].split(None, 1)
            if len(parts) > 1:
                movies_to_add.append(parts[1].strip())
        else:
            for line in lines:
                cleaned_line = line.replace("/add", "").strip()
                if cleaned_line:
                    movies_to_add.append(cleaned_line)

        if not movies_to_add:
            await message.reply_text(
                "⚠️ **ഉപയോഗിക്കേണ്ട രീതി:**\n\n"
                "`/add`\n"
                "`Movie 1`\n"
                "`Movie 2`"
            )
            return

        if not os.path.exists(MOVIE_DB_FILE):
            open(MOVIE_DB_FILE, "w", encoding="utf-8").close()

        added_count = 0
        already_exists = 0

        with open(MOVIE_DB_FILE, "r+", encoding="utf-8") as f:
            existing_movies = [l.strip().lower() for l in f.readlines()]
            
            for m in movies_to_add:
                if m.lower() not in existing_movies:
                    f.write(f"{m}\n")
                    existing_movies.append(m.lower())
                    added_count += 1
                else:
                    already_exists += 1

        await message.reply_text(
            f"✅ **ഫലങ്ങൾ:**\n\n"
            f"➕ ഇൻഡെക്സിംഗ് ലിസ്റ്റിലേക്ക് ആഡ് ചെയ്തവ: `{added_count}`\n"
            f"⚠️ ലിസ്റ്റിൽ മുൻപേ ഉള്ളവ: `{already_exists}`"
        )

    # 3. List Movies Command (/list)
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

        text = f"🎬 **ആകെ ഇൻഡെക്സ് ചെയ്യാനുള്ള സിനിമകൾ: {len(movies)}**\n\n"
        text += "\n".join([f"{i+1}. {m}" for i, m in enumerate(movies[:50])])
        
        if len(movies) > 50:
            text += f"\n\n...ബാക്കി {len(movies)-50} സിനിമകൾ കൂടി ഉണ്ട്."

        await message.reply_text(text)

    # 4. Single Search Handler (സ്വന്തം ചാനലിൽ നിന്ന് യൂസർക്ക് സിനിമ അയച്ചു നൽകുന്നു)
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
            f"🔍 **ചാനലിൽ സെർച്ച് ചെയ്യുന്നു...**\n"
            f"🎬 **സിനിമ:** `{movie_name}`"
        )

        try:
            file_found = False
            # സ്വന്തം ചാനലിൽ (`MY_CHANNEL`) സിനിമയുടെ ഫയൽ ഉണ്ടോ എന്ന് തിരയുന്നു
            async for ch_message in userbot.search_messages(MY_CHANNEL, query=movie_name):
                if ch_message.document or ch_message.video or ch_message.audio:
                    await main_bot.copy_message(
                        chat_id=message.chat.id,
                        from_chat_id=MY_CHANNEL,
                        message_id=ch_message.id
                    )
                    file_found = True
                    break

            if file_found:
                await status_msg.delete()
            else:
                await status_msg.edit_text(f"❌ **ക്ഷമിക്കണം!**\n\n**'{movie_name}'** ഡാറ്റാബേസിൽ ലഭ്യമല്ല.")

        except Exception as e:
            await status_msg.edit_text(f"⚠️ **ഒരു സാങ്കേതിക തടസ്സം നേരിട്ടു!**\n\n`{e}`")

    await userbot.start()
    await main_bot.start()
    print("🚀 Movie Bot & Userbot വിജയകരമായി റൺ ആയി!")

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
