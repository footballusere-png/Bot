import asyncio
from hydrogram import Client, filters
from hydrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

# ------------ CONFIGURATION ------------
API_ID = 28300966
API_HASH = "c0a1fe56b13f260c62bc4838feb416d9"
STRING_SESSION = "BQGv1qYAIeWJGD5qT23izLbMJPiWJ-AAmld2QM4rXcoRMwJw5iZfJBPcG3BTaX31W5OhlCfHr_cc_GVIB5Qiquf8503yugDygjD4IWb5UArRRtZ3guBKlZzjNln8E2oDyKCapD0YmsqN8UVZ3CCyDke3uKRZfqLNc6p5EkfAhaAgiUhcMyiqJIdb2c4a3CAIxizLxXopfs7e890zZfJjyQk7MMyMvsBlrlmSafudbcgb8BbFrX-XUTX1QknieWjnjtWeHFODjZ2K64BDC2Fo2fmQk4_6iVSXZJ9zK1bR-dTGJ30xHxznt8_j_DMNIkDePOa8KxW1uSD9vBGZv0CH1q5qQRoyCAAAAAGz4hg1AA"

BOT_TOKEN = "8014212534:AAEtlOlMPuXbkPHOxQdj0mJ8yXTPDG0x25M"

TARGET_BOT = "@FilesSearchBot"
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

            first_link = None
            first_link_text = ""

            # Step 2: റിസൾട്ടിൽ നിന്നും ആദ്യത്തെ Text Hyperlink കണ്ടെത്തുന്നു
            async for reply in userbot.get_chat_history(TARGET_BOT, limit=3):
                if reply.id > sent_msg.id and reply.text and reply.entities:
                    for entity in reply.entities:
                        if entity.type.name == "TEXT_LINK" and entity.url:
                            first_link = entity.url
                            start = entity.offset
                            end = entity.offset + entity.length
                            first_link_text = reply.text[start:end]
                            break
                if first_link:
                    break

            if first_link:
                # 1-ാമത്തെ ഫയൽ ലിങ്ക് ടെലഗ്രാം ബോട്ടിലെ തന്നെയുള്ള deep link (/start=...) ആണെങ്കിൽ:
                if "t.me/" in first_link and "start=" in first_link:
                    bot_username = first_link.split("t.me/")[1].split("?")[0]
                    param = first_link.split("start=")[1]

                    await status_msg.edit_text("⏳ *ഫയൽ ലഭിക്കുന്നു, ദയവായി കാത്തിരിക്കൂ...*")

                    # Userbot വഴി ആ ലിങ്ക് സ്റ്റാർട്ട് ചെയ്യുന്നു
                    start_msg = await userbot.send_message(f"@{bot_username}", f"/start {param}")
                    await asyncio.sleep(6)

                    file_sent = False
                    async for file_msg in userbot.get_chat_history(f"@{bot_username}", limit=5):
                        if file_msg.id > start_msg.id and (file_msg.document or file_msg.video or file_msg.audio):
                            # Step 1: ആദ്യം ചാനലിലേക്ക് ഫയൽ അയക്കുന്നു
                            ch_msg = await file_msg.copy(chat_id=MY_CHANNEL)
                            
                            # Step 2: Main Bot വഴി യൂസറുടെ ചാറ്റിലേക്ക് അയക്കുന്നു
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
                        await status_msg.edit_text("⚠️ ഫയൽ ലഭ്യമാക്കാൻ കഴിഞ്ഞില്ല. വീണ്ടും ശ്രമിക്കുക.")

                # പുറത്തുള്ള വെബ് ലിങ്ക് ആണെങ്കിൽ ബട്ടൺ നൽകുന്നു:
                else:
                    button_markup = InlineKeyboardMarkup([
                        [InlineKeyboardButton(f"📥 {first_link_text[:30]}...", url=first_link)],
                        [InlineKeyboardButton("📢 അപ്‌ഡേറ്റ് ചാനൽ", url=UPDATE_CHANNEL_LINK)]
                    ])
                    await status_msg.edit_text(
                        f"🎉 **ഫയൽ കണ്ടെത്തി!**\n\n"
                        f"🎬 **{movie_name}**\n"
                        f"📁 `{first_link_text}`\n\n"
                        f"👇 ഡൗൺലോഡ് ചെയ്യാൻ ബട്ടൺ അമർത്തുക:",
                        reply_markup=button_markup
                    )
            else:
                await status_msg.edit_text(
                    f"❌ **ക്ഷമിക്കണം!**\n\n**'{movie_name}'** എന്ന സിനിമയുടെ ഫയലുകൾ ലഭ്യമല്ല."
                )

        except Exception as e:
            await status_msg.edit_text(f"⚠️ **ഒരു സാങ്കേതിക തടസ്സം നേരിട്ടു!**\n\n`{e}`")

    await userbot.start()
    await main_bot.start()
    print("🚀 Movie Bot & Userbot വിജയകരമായി റൺ ആയി!")

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
