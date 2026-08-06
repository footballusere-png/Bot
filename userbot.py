# userbot.py
import re
from pyrogram import Client, filters
from config import API_ID, API_HASH, DB_CHANNEL, SOURCE_CHANNELS, STRING_SESSION

app = Client(
    "my_userbot",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=STRING_SESSION
)

@app.on_message(filters.chat(SOURCE_CHANNELS) & (filters.document | filters.video | filters.audio))
async def forward_files(client, message):
    try:
        caption = message.caption or ""
        
        # യൂസറ്‍നെയിമുകളും ലിങ്കുകളും നീക്കം ചെയ്യുന്നു
        cleaned_caption = re.sub(r'@\w+', '', caption)
        cleaned_caption = re.sub(r'https?://\S+', '', cleaned_caption)
        cleaned_caption = cleaned_caption.strip()
        
        media = message.document or message.video or message.audio
        file_name = media.file_name if hasattr(media, "file_name") else "Media File"
        
        await message.copy(
            chat_id=DB_CHANNEL,
            caption=f"📁 {file_name}\n\n{cleaned_caption}"
        )
    except Exception as e:
        print(f"Error forwarding file: {e}")

if __name__ == "__main__":
    print("Userbot started...")
    app.run()
