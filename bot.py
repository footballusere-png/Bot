import asyncio
from hydrogram import Client, filters
from hydrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

# ------------ CONFIGURATION ------------
API_ID = 28300966
API_HASH = "c0a1fe56b13f260c62bc4838feb416d9"
STRING_SESSION = "BQGv1qYAIeWJGD5qT23izLbMJPiWJ-AAmld2QM4rXcoRMwJw5iZfJBPcG3BTaX31W5OhlCfHr_cc_GVIB5Qiquf8503yugDygjD4IWb5UArRRtZ3guBKlZzjNln8E2oDyKCapD0YmsqN8UVZ3CCyDke3uKRZfqLNc6p5EkfAhaAgiUhcMyiqJIdb2c4a3CAIxizLxXopfs7e890zZfJjyQk7MMyMvsBlrlmSafudbcgb8BbFrX-XUTX1QknieWjnjtWeHFODjZ2K64BDC2Fo2fmQk4_6iVSXZJ9zK1bR-dTGJ30xHxznt8_j_DMNIkDePOa8KxW1uSD9vBGZv0CH1q5qQRoyCAAAAAGz4hg1AA"

# Bot Token
BOT_TOKEN = "8014212534:AAEtlOlMPuXbkPHOxQdj0mJ8yXTPDG0x25M"

TARGET_BOT = "@Indianimxbot"
MY_CHANNEL = -1002644197954

# ചാനലിന്റെ ലിങ്ക്
CHANNEL_LINK = "https://t.me/c/2644197954"
# ----------------------------------------

userbot = Client("my_userbot", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION)
main_bot = Client("my_main_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


@main_bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client: Client, message: Message):
    welcome_text = (
        f"👋 **ഹലോ {message.from_user.mention},**\n\n"
        "🎬 **Movie Finder Bot**-ലേക്ക് സ്വാഗതം!\n\n"
        "നിങ്ങൾക്ക് ആവശ്യമായ ഏത് സിനിമയുടെയും സീരീസിന്റെയും പേര് കൃത്യമായി താഴെ ടൈപ്പ് ചെയ്ത് അയക്കുക.\n\n"
        "✨ *ഉദാഹരണത്തിന്:* `Manjummel Boys`"
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 ഞങ്ങളുടെ ചാനൽ", url=CHANNEL_LINK)]
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
        sent_msg = await userbot.send_message(TARGET_BOT, movie_name)
        await asyncio.sleep(4)

        found = False
        async for reply in userbot.get_chat_history(TARGET_BOT, limit=1):
            if reply.id != sent_msg.id:
                await reply.forward(MY_CHANNEL)
                found = True
                break

        if found:
            success_text = (
                "🎉 **സിനിമ കണ്ടെത്തിയിരിക്കുന്നു!**\n\n"
                f"🎬 **മൂവി Name:** `{movie_name}`\n"
                "✅ **Status:** Upload Completed!\n\n"
                "👇 താഴെ കാണുന്ന ബട്ടണിൽ ക്ലിക്ക് ചെയ്ത് ഫയലുകൾ ഡൗൺലോഡ് ചെയ്യാം."
            )
            
            download_btn = InlineKeyboardMarkup([
                [InlineKeyboardButton("📥 Get Movie Files / Download", url=CHANNEL_LINK)]
            ])
            
            await status_msg.edit_text(text=success_text, reply_markup=download_btn)
        else:
            not_found_text = (
                f"❌ **ക്ഷമിക്കണം!**\n\n"
                f"**'{movie_name}'** എന്ന സിനിമയുടെ ഫയലുകൾ ലഭ്യമല്ല.\n"
                "Spelling തെറ്റുകൂടാതെ വീണ്ടും ടൈപ്പ് ചെയ്തു നോക്കൂ."
            )
            await status_msg.edit_text(text=not_found_text)

    except Exception as e:
        await status_msg.edit_text(f"⚠️ **ഒരു സാങ്കേതിക തടസ്സം നേരിട്ടു!**\n\n`{e}`")


async def main():
    await userbot.start()
    await main_bot.start()
    print("🚀 Movie Bot & Userbot വിജയകരമായി റൺ ആയി!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
