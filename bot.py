import asyncio
from hydrogram import Client, filters
from hydrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# ------------ CONFIGURATION ------------
API_ID = 28300966
API_HASH = "c0a1fe56b13f260c62bc4838feb416d9"
STRING_SESSION = "BQGv1qYAIeWJGD5qT23izLbMJPiWJ-AAmld2QM4rXcoRMwJw5iZfJBPcG3BTaX31W5OhlCfHr_cc_GVIB5Qiquf8503yugDygjD4IWb5UArRRtZ3guBKlZzjNln8E2oDyKCapD0YmsqN8UVZ3CCyDke3uKRZfqLNc6p5EkfAhaAgiUhcMyiqJIdb2c4a3CAIxizLxXopfs7e890zZfJjyQk7MMyMvsBlrlmSafudbcgb8BbFrX-XUTX1QknieWjnjtWeHFODjZ2K64BDC2Fo2fmQk4_6iVSXZJ9zK1bR-dTGJ30xHxznt8_j_DMNIkDePOa8KxW1uSD9vBGZv0CH1q5qQRoyCAAAAAGz4hg1AA"

BOT_TOKEN = "8014212534:AAEtlOlMPuXbkPHOxQdj0mJ8yXTPDG0x25M"

TARGET_BOT = "@ProSearchM5Bot"
MY_CHANNEL = -1004296254082
UPDATE_CHANNEL_LINK = "https://t.me/c/2644197954"
# ----------------------------------------

# Temporarily store exact button queries
SEARCH_CACHE = {}

async def main():
    userbot = Client("my_userbot", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION)
    main_bot = Client("my_main_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

    # 1. Start Command (/start)
    @main_bot.on_message(filters.command("start") & filters.private)
    async def start_cmd(client: Client, message: Message):
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

    # 2. Movie Search Request
    @main_bot.on_message(filters.text & filters.private)
    async def handle_user_search(client: Client, message: Message):
        movie_name = message.text.strip()
        if movie_name.startswith("/"):
            return

        status_msg = await message.reply_text(
            f"🔍 **സെർച്ച് ചെയ്യുന്നു...**\n"
            f"🎬 **സിനിമ:** `{movie_name}`\n\n"
            f"⏳ *ഫയലുകൾ കണ്ടെത്തുന്നു, ദയവായി കാത്തിരിക്കൂ...*"
        )

        try:
            sent_msg = await userbot.send_message(TARGET_BOT, movie_name)
            await asyncio.sleep(5)

            buttons = []
            btn_count = 0
            
            # Target ബോട്ട് നൽകിയ ബട്ടണുകളിലെ ഫയൽ നെയിമുകൾ ടെക്സ്റ്റ് ആയി എടുക്കുന്നു
            async for reply in userbot.get_chat_history(TARGET_BOT, limit=3):
                if reply.id > sent_msg.id and reply.reply_markup:
                    for row in reply.reply_markup.inline_keyboard:
                        for btn in row:
                            if "NEXT" not in btn.text and btn_count < 8:
                                # ബട്ടണിന്റെ ടെക്സ്റ്റ് മാത്രം സൂക്ഷിക്കുന്നു
                                cb_key = f"mov_{btn_count}"
                                SEARCH_CACHE[cb_key] = btn.text
                                buttons.append([InlineKeyboardButton(btn.text, callback_data=cb_key)])
                                btn_count += 1

            if buttons:
                buttons.append([InlineKeyboardButton("📢 അപ്‌ഡേറ്റ് ചാനൽ", url=UPDATE_CHANNEL_LINK)])
                await status_msg.edit_text(
                    f"🎉 **സിനിമ കണ്ടെത്തിയിരിക്കുന്നു!**\n\n🎬 **{movie_name}**\n\n👇 ആവശ്യമായ ഫയൽ ക്ലിക്ക് ചെയ്ത് ഡൗൺലോഡ് ചെയ്യുക:",
                    reply_markup=InlineKeyboardMarkup(buttons)
                )
            else:
                await status_msg.edit_text(
                    f"❌ **ക്ഷമിക്കണം!**\n\n**'{movie_name}'** എന്ന സിനിമയുടെ ഫയലുകൾ ലഭ്യമല്ല."
                )

        except Exception as e:
            await status_msg.edit_text(f"⚠️ **ഒരു സാങ്കേതിക തടസ്സം നേരിട്ടു!**\n\n`{e}`")

    # 3. Handle User Button Clicks
    @main_bot.on_callback_query()
    async def handle_callback(client: Client, callback_query: CallbackQuery):
        data = callback_query.data
        
        if data in SEARCH_CACHE:
            file_query = SEARCH_CACHE[data]
            await callback_query.answer("⏳ ഫയൽ പ്രോസസ്സ് ചെയ്യുന്നു, ദയവായി കാത്തിരിക്കൂ...", show_alert=False)
            
            try:
                # Userbot ആ നിർദ്ദിഷ്ട ഫയൽ പേര് ടാർഗെറ്റ് ബോട്ടിലേക്ക് അയക്കുന്നു
                sent_req = await userbot.send_message(TARGET_BOT, file_query)
                await asyncio.sleep(6)
                
                found = False
                # വന്ന വീഡിയോ ഫയൽ യൂസർക്കും ചാനലിലേക്കും ഫോർവേഡ് ചെയ്യുന്നു
                async for file_msg in userbot.get_chat_history(TARGET_BOT, limit=5):
                    if file_msg.id > sent_req.id and (file_msg.document or file_msg.video or file_msg.audio):
                        await file_msg.forward(MY_CHANNEL) # ചാനലിലേക്ക്
                        await file_msg.copy(chat_id=callback_query.message.chat.id) # യൂസർക്ക്
                        found = True
                        break

                if not found:
                    await callback_query.message.reply_text("⚠️ ഫയൽ ലഭിക്കാൻ അല്പം വൈകുന്നു. ദയവായി വീണ്ടും ബട്ടൺ അമർത്തുക.")

            except Exception as e:
                await callback_query.message.reply_text(f"⚠️ സാങ്കേതിക പ്രശ്നം: `{e}`")
        else:
            await callback_query.answer("ഈ സെർച്ച് ലേറ്റ് ആയിപ്പോയി. വീണ്ടും സിനിമയുടെ പേര് അയക്കുക.", show_alert=True)

    await userbot.start()
    await main_bot.start()
    print("🚀 Movie Bot & Userbot വിജയകരമായി റൺ ആയി!")

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
