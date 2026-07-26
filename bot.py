import asyncio
from hydrogram import Client, filters
from hydrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

# ------------ CONFIGURATION ------------
API_ID = 28300966
API_HASH = "c0a1fe56b13f260c62bc4838feb416d9"
STRING_SESSION = "BQGv1qYAIeWJGD5qT23izLbMJPiWJ-AAmld2QM4rXcoRMwJw5iZfJBPcG3BTaX31W5OhlCfHr_cc_GVIB5Qiquf8503yugDygjD4IWb5UArRRtZ3guBKlZzjNln8E2oDyKCapD0YmsqN8UVZ3CCyDke3uKRZfqLNc6p5EkfAhaAgiUhcMyiqJIdb2c4a3CAIxizLxXopfs7e890zZfJjyQk7MMyMvsBlrlmSafudbcgb8BbFrX-XUTX1QknieWjnjtWeHFODjZ2K64BDC2Fo2fmQk4_6iVSXZJ9zK1bR-dTGJ30xHxznt8_j_DMNIkDePOa8KxW1uSD9vBGZv0CH1q5qQRoyCAAAAAGz4hg1AA"

BOT_TOKEN = "8014212534:AAEtlOlMPuXbkPHOxQdj0mJ8yXTPDG0x25M"

TARGET_BOT = "@ProSearchM5Bot"
MY_CHANNEL = -1004296254082
UPDATE_CHANNEL_LINK = "https://t.me/c/2644197954"
# ----------------------------------------

async def main():
    userbot = Client("my_userbot", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION)
    main_bot = Client("my_main_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

    @main_bot.on_message(filters.command("start") & filters.private)
    async def start_cmd(client: Client, message: Message):
        welcome_text = (
            f"👋 **ഹലോ {message.from_user.mention},**\n\n"
            "🎬 **Movie Finder Bot**-ലേക്ക് സ്വാഗതം!\n\n"
            "നിങ്ങൾക്ക് ആവശ്യമായ ഏത് സിനിമയുടെയും പേര് കൃത്യമായി താഴെ ടൈപ്പ് ചെയ്ത് അയക്കുക.\n\n"
            "✨ *ഉദാഹരണത്തിന്:* `Manjummel Boys`"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 അപ്‌ഡേറ്റ് ചാനൽ", url=UPDATE_CHANNEL_LINK)]
        ])
        await message.reply_text(text=welcome_text, reply_markup=keyboard, disable_web_page_preview=True)

    @main_bot.on_message(filters.text & filters.private)
    async def handle_user_search(client: Client, message: Message):
        movie_name = message.text.strip()
        if movie_name.startswith("/"):
            return

        status_msg = await message.reply_text(
            f"🔍 **സെർച്ച് ചെയ്യുന്നു...**\n"
            f"🎬 **സിനിമ:** `{movie_name}`\n\n"
            f"⏳ *ദയവായി കുറച്ചു സമയം കാത്തിരിക്കൂ...*"
        )

        try:
            # 1. Target ബോട്ടിലേക്ക് സിനിമയുടെ പേര് അയക്കുന്നു
            sent_msg = await userbot.send_message(TARGET_BOT, movie_name)
            await asyncio.sleep(5)  # ബോട്ട് റിപ്ലൈ നൽകാൻ സമയം നൽകുന്നു

            file_buttons = []
            count = 0

            # 2. Target ബോട്ടിൽ നിന്ന് വരുന്ന അവസാന മെസ്സേജുകൾ പരിശോധിക്കുന്നു
            async for reply in userbot.search_messages(TARGET_BOT, limit=5):
                # നമ്മൾ അയച്ച മെസ്സേജിന് ശേഷമുള്ളവ മാത്രം എടുക്കുന്നു
                if reply.id > sent_msg.id:
                    # ഫയലോ മെസ്സേജോ ആണെങ്കിൽ ചാനലിലേക്ക് ഫോർവേഡ് ചെയ്യുന്നു
                    fwd = await reply.forward(MY_CHANNEL)
                    
                    clean_channel_id = str(MY_CHANNEL).replace("-100", "")
                    file_link = f"https://t.me/c/{clean_channel_id}/{fwd.id}"
                    
                    # മെസ്സേജിൽ ഉള്ള ക്യാപ്ഷൻ അല്ലെങ്കിൽ ഒരു പേര് ബട്ടണിനായി എടുക്കുന്നു
                    btn_text = reply.text[:30] if reply.text else f"📥 Movie File {count+1}"
                    file_buttons.append([InlineKeyboardButton(btn_text, url=file_link)])
                    count += 1

            if file_buttons:
                file_buttons.append([InlineKeyboardButton("📢 അപ്‌ഡേറ്റ് ചാനൽ", url=UPDATE_CHANNEL_LINK)])
                success_text = (
                    f"🎉 **സിനിമ കണ്ടെത്തിയിരിക്കുന്നു!**\n\n"
                    f"🎬 **മൂവി Name:** `{movie_name}`\n\n"
                    f"👇 താഴെ നൽകിയിരിക്കുന്ന ബട്ടണുകളിൽ അമർത്തി ഫയലുകൾ ഡൗൺലോഡ് ചെയ്യാം:"
                )
                await status_msg.edit_text(text=success_text, reply_markup=InlineKeyboardMarkup(file_buttons))
            else:
                await status_msg.edit_text(
                    f"❌ **ക്ഷമിക്കണം!**\n\n**'{movie_name}'** എന്ന സിനിമയുടെ ഫയലുകൾ ലഭ്യമല്ല."
                )

        except Exception as e:
            await status_msg.edit_text(f"⚠️ **ഒരു സാങ്കേതിക തടസ്സം നേരിട്ടു!**\n\n`{e}`")

    await userbot.start()
    await main_bot.start()
    print("🚀 Movie Bot & Userbot വിജയകരമായി റൺ ആയി!")
    asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
