import asyncio
from hydrogram import Client, filters
from hydrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

# ------------ CONFIGURATION ------------
API_ID = 28300966
API_HASH = "c0a1fe56b13f260c62bc4838feb416d9"
STRING_SESSION = "BQGv1qYAIeWJGD5qT23izLbMJPiWJ-AAmld2QM4rXcoRMwJw5iZfJBPcG3BTaX31W5OhlCfHr_cc_GVIB5Qiquf8503yugDygjD4IWb5UArRRtZ3guBKlZzjNln8E2oDyKCapD0YmsqN8UVZ3CCyDke3uKRZfqLNc6p5EkfAhaAgiUhcMyiqJIdb2c4a3CAIxizLxXopfs7e890zZfJjyQk7MMyMvsBlrlmSafudbcgb8BbFrX-XUTX1QknieWjnjtWeHFODjZ2K64BDC2Fo2fmQk4_6iVSXZJ9zK1bR-dTGJ30xHxznt8_j_DMNIkDePOa8KxW1uSD9vBGZv0CH1q5qQRoyCAAAAAGz4hg1AA"

BOT_TOKEN = "8014212534:AAEtlOlMPuXbkPHOxQdj0mJ8yXTPDG0x25M"

TARGET_BOT = "@Movie_Channel_06_bot"
MY_CHANNEL = -1004296254082
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
            "സിനിമയുടെ പേര് കൃത്യമായി താഴെ ടൈപ്പ് ചെയ്ത് അയക്കുക.\n\n"
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
            f"⏳ *ഫയലുകൾ തിരയുന്നു, കാത്തിരിക്കൂ...*"
        )

        try:
            # Step 1: TARGET_BOT-ലേക്ക് സിനിമ പേര് അയക്കുന്നു
            sent_msg = await userbot.send_message(TARGET_BOT, movie_name)
            await asyncio.sleep(5)

            target_button = None

            # Step 2: റിസൾട്ടിൽ നിന്നും ആദ്യത്തെ ബട്ടൺ കണ്ടുപിടിക്കുന്നു
            async for reply in userbot.get_chat_history(TARGET_BOT, limit=3):
                if reply.id > sent_msg.id and reply.reply_markup:
                    for row in reply.reply_markup.inline_keyboard:
                        for btn in row:
                            if "NEXT" not in btn.text:
                                target_button = btn
                                break
                        if target_button:
                            break
                if target_button:
                    break

            if target_button:
                # ബട്ടൺ Web Link (URL) ആണെങ്കിൽ:
                if target_button.url:
                    button_markup = InlineKeyboardMarkup([
                        [InlineKeyboardButton(f"📥 {target_button.text}", url=target_button.url)],
                        [InlineKeyboardButton("📢 അപ്‌ഡേറ്റ് ചാനൽ", url=UPDATE_CHANNEL_LINK)]
                    ])

                    await status_msg.edit_text(
                        f"🎉 **സിനിമ ഫയൽ കണ്ടെത്തി!**\n\n"
                        f"🎬 **{movie_name}**\n\n"
                        f"👇 താഴെയുള്ള ബട്ടണിൽ ക്ലിക്ക് ചെയ്ത് ലിങ്ക് വഴി ഡൗൺലോഡ് ചെയ്യുക:",
                        reply_markup=button_markup
                    )
                
                # Normal Callback Button ആണെങ്കിൽ:
                elif target_button.callback_data:
                    await status_msg.edit_text("⏳ ഫയൽ ഡൗൺലോഡ് ചെയ്യുന്നു...")
                    await userbot.request_callback_answer(
                        chat_id=TARGET_BOT,
                        message_id=reply.id,
                        callback_data=target_button.callback_data
                    )
                    await asyncio.sleep(5)
                    
                    async for file_msg in userbot.get_chat_history(TARGET_BOT, limit=5):
                        if file_msg.id > reply.id and (file_msg.document or file_msg.video):
                            await file_msg.forward(MY_CHANNEL)
                            await file_msg.copy(chat_id=message.chat.id)
                            await status_msg.delete()
                            return
            else:
                await status_msg.edit_text(
                    f"❌ **ക്ഷമിക്കണം!**\n\n**'{movie_name}'** എന്ന സിനിമയുടെ ലിങ്കുകൾ ലഭ്യമായില്ല."
                )

        except Exception as e:
            await status_msg.edit_text(f"⚠️ **ഒരു സാങ്കേതിക തടസ്സം നേരിട്ടു!**\n\n`{e}`")

    await userbot.start()
    await main_bot.start()
    print("🚀 Movie Bot & Userbot വിജയകരമായി റൺ ആയി!")

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
