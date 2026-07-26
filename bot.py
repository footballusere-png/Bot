import asyncio
from hydrogram import Client, filters
from hydrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

# ------------ CONFIGURATION ------------
API_ID = 28300966
API_HASH = "c0a1fe56b13f260c62bc4838feb416d9"
STRING_SESSION = "BQGv1qYAIeWJGD5qT23izLbMJPiWJ-AAmld2QM4rXcoRMwJw5iZfJBPcG3BTaX31W5OhlCfHr_cc_GVIB5Qiquf8503yugDygjD4IWb5UArRRtZ3guBKlZzjNln8E2oDyKCapD0YmsqN8UVZ3CCyDke3uKRZfqLNc6p5EkfAhaAgiUhcMyiqJIdb2c4a3CAIxizLxXopfs7e890zZfJjyQk7MMyMvsBlrlmSafudbcgb8BbFrX-XUTX1QknieWjnjtWeHFODjZ2K64BDC2Fo2fmQk4_6iVSXZJ9zK1bR-dTGJ30xHxznt8_j_DMNIkDePOa8KxW1uSD9vBGZv0CH1q5qQRoyCAAAAAGz4hg1AA"

BOT_TOKEN = "8014212534:AAEtlOlMPuXbkPHOxQdj0mJ8yXTPDG0x25M"

# ഡയറക്ട് ബട്ടൺ തരുന്ന ബോട്ട്
TARGET_BOT = "@ProSearchM5Bot"

# ഫയലുകൾ ബാക്ക്ഗ്രൗണ്ടിൽ സൂക്ഷിക്കുന്ന ചാനൽ ID
MY_CHANNEL = -1004296254082

# അപ്ഡേറ്റ് ചാനൽ ലിങ്ക്
UPDATE_CHANNEL_LINK = "https://t.me/c/2644197954"
# ----------------------------------------

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
            "✨ *ഉദാഹരണത്തിന്:* `Manjummel Boys`"
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
            f"⏳ *ദയവായി കുറച്ചു സമയം കാത്തിരിക്കൂ...*"
        )

        try:
            # Target ബോട്ടിലേക്ക് സിനിമയുടെ പേര് അയക്കുന്നു
            sent_msg = await userbot.send_message(TARGET_BOT, movie_name)
            await asyncio.sleep(4)

            file_buttons = []

            # Target ബോട്ടിൽ വന്ന മറുപടി പരിശോധിക്കുന്നു
            async for reply in userbot.get_chat_history(TARGET_BOT, limit=1):
                if reply.id != sent_msg.id and reply.reply_markup:
                    
                    # ബോട്ടിൽ നിന്ന് കിട്ടിയ ബട്ടണുകളിലൂടെ ലൂപ്പ് ചെയ്യുന്നു
                    for row in reply.reply_markup.inline_keyboard:
                        for btn in row:
                            if btn.callback_data:
                                try:
                                    # ഓട്ടോമാറ്റിക്കായി ബട്ടണിൽ ക്ലിക്ക് ചെയ്യുന്നു (Click Event)
                                    res = await userbot.request_callback_answer(
                                        chat_id=TARGET_BOT,
                                        message_id=reply.id,
                                        callback_data=btn.callback_data
                                    )
                                    await asyncio.sleep(2)

                                    # പുതിയതായി വന്ന ഫയൽ ചാനലിലേക്ക് ഫോർവേഡ് ചെയ്യുന്നു
                                    async for file_msg in userbot.get_chat_history(TARGET_BOT, limit=1):
                                        if file_msg.id != reply.id:
                                            fwd = await file_msg.forward(MY_CHANNEL)
                                            
                                            # ചാനലിലെ ഫയലിന്റെ ഡയറക്ട് ലിങ്ക് നിർമ്മിക്കുന്നു
                                            clean_channel_id = str(MY_CHANNEL).replace("-100", "")
                                            file_link = f"https://t.me/c/{clean_channel_id}/{fwd.id}"
                                            
                                            # ബട്ടൺ തയ്യാറാക്കുന്നു
                                            btn_text = btn.text if btn.text else "📥 Download File"
                                            file_buttons.append([InlineKeyboardButton(btn_text, url=file_link)])

                                except Exception as e:
                                    print(f"Button Click Error: {e}")
                                    continue

            # ഫയലുകൾ ലഭിച്ചെങ്കിൽ യൂസർക്ക് പ്രൊഫഷണൽ രീതിയിൽ ബട്ടണുകൾ അയക്കുന്നു
            if file_buttons:
                # അപ്ഡേറ്റ് ചാനൽ ലിങ്കും താഴെ ബട്ടണായി ചേർക്കുന്നു
                file_buttons.append([InlineKeyboardButton("📢 അപ്‌ഡേറ്റ് ചാനൽ", url=UPDATE_CHANNEL_LINK)])
                
                success_text = (
                    f"🎉 **സിനിമ കണ്ടെത്തിയിരിക്കുന്നു!**\n\n"
                    f"🎬 **മൂവി Name:** `{movie_name}`\n\n"
                    f"👇 താഴെ നൽകിയിരിക്കുന്ന ബട്ടണുകളിൽ അമർത്തി ഫയലുകൾ കാണാം/ഡൗൺലോഡ് ചെയ്യാം:"
                )
                
                await status_msg.edit_text(
                    text=success_text,
                    reply_markup=InlineKeyboardMarkup(file_buttons)
                )
            else:
                not_found_text = (
                    f"❌ **ക്ഷമിക്കണം!**\n\n"
                    f"**'{movie_name}'** എന്ന സിനിമയുടെ ഫയലുകൾ ലഭ്യമല്ല.\n"
                    "Spelling തെറ്റുകൂടാതെ വീണ്ടും ടൈപ്പ് ചെയ്തു നോക്കൂ."
                )
                await status_msg.edit_text(text=not_found_text)

        except Exception as e:
            await status_msg.edit_text(f"⚠️ **ഒരു സാങ്കേതിക തടസ്സം നേരിട്ടു!**\n\n`{e}`")

    await userbot.start()
    await main_bot.start()
    print("🚀 Movie Bot & Userbot വിജയകരമായി റൺ ആയി!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
