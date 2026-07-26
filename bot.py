import asyncio
import re
from hydrogram import Client, filters
from hydrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from hydrogram.errors import FloodWait

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
            "✨ *ഉദാഹരണത്തിന്:* `Madhura Naranga`"
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
            f"⏳ *ഫയൽ കണ്ടെത്തുന്നു, ദയവായി കാത്തിരിക്കൂ...*"
        )

        try:
            # Step 1: ടാർഗെറ്റ് ബോട്ടിലേക്ക് സിനിമയുടെ പേര് അയക്കുന്നു
            sent_msg = await userbot.send_message(TARGET_BOT, movie_name)
            await asyncio.sleep(6)  # ഡിലെ 6 സെക്കൻഡ് ആക്കി

            target_message = None
            target_button = None

            # Step 2: റിസൾട്ട് കണ്ടുപിടിക്കുന്നു
            async for reply in userbot.get_chat_history(TARGET_BOT, limit=3):
                if reply.id > sent_msg.id and reply.reply_markup:
                    target_message = reply
                    for row in reply.reply_markup.inline_keyboard:
                        for btn in row:
                            if "NEXT" not in btn.text:
                                target_button = btn
                                break
                        if target_button:
                            break
                if target_button:
                    break

            if target_message and target_button:
                if target_button.url:
                    await status_msg.edit_text(
                        f"🎬 **ബട്ടൺ ലിങ്ക് കണ്ടെത്തി!**\n"
                        f"📁 `{target_button.text}`\n\n"
                        f"🔗 [ഇവിടെ ക്ലിക്ക് ചെയ്തു ഫയൽ തുറക്കുക]({target_button.url})"
                    )
                elif target_button.callback_data:
                    await status_msg.edit_text(
                        f"🎬 **ഫയൽ കണ്ടെത്തി! പ്രോസസ്സ് ചെയ്യുന്നു...**\n"
                        f"📁 `{target_button.text}`\n\n"
                        f"⏳ *വീഡിയോ ലഭിക്കാൻ കാത്തിരിക്കൂ...*"
                    )

                    # Callback Click
                    try:
                        await userbot.request_callback_answer(
                            chat_id=TARGET_BOT,
                            message_id=target_message.id,
                            callback_data=target_button.callback_data
                        )
                    except FloodWait as e:
                        await asyncio.sleep(e.value)
                        await userbot.request_callback_answer(
                            chat_id=TARGET_BOT,
                            message_id=target_message.id,
                            callback_data=target_button.callback_data
                        )
                    
                    await asyncio.sleep(7)

                    file_sent = False
                    async for file_msg in userbot.get_chat_history(TARGET_BOT, limit=5):
                        if file_msg.id > target_message.id and (file_msg.document or file_msg.video or file_msg.audio):
                            await file_msg.forward(MY_CHANNEL)
                            await file_msg.copy(chat_id=message.chat.id)
                            file_sent = True
                            break

                    if file_sent:
                        await status_msg.delete()
                    else:
                        await status_msg.edit_text("⚠️ ഫയൽ ലഭിക്കാൻ വൈകുന്നു. ദയവായി വീണ്ടും ശ്രമിക്കുക.")
            else:
                await status_msg.edit_text(
                    f"❌ **ക്ഷമിക്കണം!**\n\n**'{movie_name}'** എന്ന സിനിമയുടെ ഫയലുകൾ ലഭ്യമല്ല."
                )

        except FloodWait as e:
            await status_msg.edit_text(f"⏳ **ടെലഗ്രാം പരിധി കടന്നു.** `{e.value}` സെക്കൻഡിന് ശേഷം വീണ്ടും ശ്രമിക്കുക.")
        except Exception as e:
            await status_msg.edit_text(f"⚠️ **ഒരു സാങ്കേതിക തടസ്സം നേരിട്ടു!**\n\n`{e}`")

    await userbot.start()
    await main_bot.start()
    print("🚀 Movie Bot & Userbot വിജയകരമായി റൺ ആയി!")

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
