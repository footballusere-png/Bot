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
            f"⏳ *ഫയലുകൾ കണ്ടെത്തുന്നു, ദയവായി അല്പം കാത്തിരിക്കൂ...*"
        )

        try:
            # Target ബോട്ടിലേക്ക് സിനിമയുടെ പേര് അയക്കുന്നു
            sent_msg = await userbot.send_message(TARGET_BOT, movie_name)
            await asyncio.sleep(4)

            clicked_buttons = 0

            # Target ബോട്ടിൽ വന്ന റിസൾട്ട് മെസ്സേജ് പരിശോധിക്കുന്നു
            async for reply in userbot.get_chat_history(TARGET_BOT, limit=3):
                if reply.id > sent_msg.id and reply.reply_markup:
                    # മെസ്സേജിലെ ബട്ടണുകളിൽ ഓട്ടോമാറ്റിക് ആയി ക്ലിക്ക് ചെയ്യുന്നു (Max 5 Files)
                    for row in reply.reply_markup.inline_keyboard:
                        for btn in row:
                            if btn.callback_data and clicked_buttons < 5:
                                try:
                                    await userbot.request_callback_answer(
                                        chat_id=TARGET_BOT,
                                        message_id=reply.id,
                                        callback_data=btn.callback_data
                                    )
                                    clicked_buttons += 1
                                    await asyncio.sleep(2) # ഫയൽ ലോഡ് ആകാൻ ചെറിയ സമയം
                                except Exception as btn_err:
                                    print(f"Button Click Error: {btn_err}")
                                    continue

            # ബട്ടൺ ക്ലിക്ക് ചെയ്തതിന് ശേഷം വന്ന വിഡിയോ/ഫയൽ മെസ്സേജുകൾ തപ്പിയെടുക്കുന്നു
            await asyncio.sleep(3)
            sent_files_count = 0

            async for file_msg in userbot.get_chat_history(TARGET_BOT, limit=10):
                if file_msg.id > sent_msg.id and (file_msg.document or file_msg.video or file_msg.audio):
                    # 1. ചാനലിലേക്ക് ഫോർവേഡ് ചെയ്യുന്നു
                    await file_msg.forward(MY_CHANNEL)
                    
                    # 2. യൂസറുടെ ചാറ്റിലേക്ക് ഡയറക്ട് ഫയൽ കോപ്പി ചെയ്തു നൽകുന്നു
                    await file_msg.copy(chat_id=message.chat.id)
                    sent_files_count += 1
                    await asyncio.sleep(1)

            if sent_files_count > 0:
                await status_msg.delete() # ഫയലുകൾ അയച്ച ശേഷം Status Message ഡിലീറ്റ് ചെയ്യും
            else:
                await status_msg.edit_text(
                    f"❌ **ക്ഷമിക്കണം!**\n\n**'{movie_name}'** എന്ന സിനിമയുടെ ഫയലുകൾ ഡയറക്ട് ആയി ലഭിച്ചില്ല.\n"
                    "Spelling കൃത്യമായി ടൈപ്പ് ചെയ്തു വീണ്ടും ശ്രമിക്കുക."
                )

        except Exception as e:
            await status_msg.edit_text(f"⚠️ **ഒരു സാങ്കേതിക തടസ്സം നേരിട്ടു!**\n\n`{e}`")

    # Start Both Clients
    await userbot.start()
    await main_bot.start()
    print("🚀 Movie Bot & Userbot വിജയകരമായി റൺ ആയി!")

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
