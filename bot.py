import asyncio
from hydrogram import Client

# ------------ CONFIGURATION ------------
API_ID = 28300966
API_HASH = "c0a1fe56b13f260c62bc4838feb416d9"
STRING_SESSION = "BQGv1qYAIeWJGD5qT23izLbMJPiWJ-AAmld2QM4rXcoRMwJw5iZfJBPcG3BTaX31W5OhlCfHr_cc_GVIB5Qiquf8503yugDygjD4IWb5UArRRtZ3guBKlZzjNln8E2oDyKCapD0YmsqN8UVZ3CCyDke3uKRZfqLNc6p5EkfAhaAgiUhcMyiqJIdb2c4a3CAIxizLxXopfs7e890zZfJjyQk7MMyMvsBlrlmSafudbcgb8BbFrX-XUTX1QknieWjnjtWeHFODjZ2K64BDC2Fo2fmQk4_6iVSXZJ9zK1bR-dTGJ30xHxznt8_j_DMNIkDePOa8KxW1uSD9vBGZv0CH1q5qQRoyCAAAAAGz4hg1AA"

TARGET_BOT = "@DPCBackup_Files_01_Bot"
MY_CHANNEL = -1004296254082  # നിങ്ങളുടെ ചാനൽ ID
# ----------------------------------------

# മുഴുവൻ സിനിമകളുടെയും പുതിയ ലിസ്റ്റ്
MOVIE_LIST = [
    # ആദ്യത്തെ ലിസ്റ്റ്
    "Pushpa: The Rise", "Pushpa 2: The Rule", "RRR", "KGF Chapter 1", "KGF Chapter 2",
    "Kantara", "Salaar", "Kalki 2898 AD", "Devara", "Leo", "Vikram", "Master", "Beast",
    "Jailer", "Thunivu", "Varisu", "Valimai", "Doctor", "Don", "Love Today", "Good Night",
    "Maamannan", "Garudan", "Captain Miller", "Raayan", "Maharaja", "Indian 2", "Ayalaan",
    "Mark Antony", "Jigarthanda DoubleX", "Ponniyin Selvan: I", "Ponniyin Selvan: II",
    "Pathaan", "Jawan", "Dunki", "Animal", "Fighter", "Chandu Champion", "Munjya", "Stree",
    "Stree 2", "Bhool Bhulaiyaa 2", "Bhool Bhulaiyaa 3", "Drishyam 2", "Bhediya", "Brahmāstra",
    "Shaitaan", "Article 370", "Merry Christmas", "Laapataa Ladies", "12th Fail", "OMG 2",
    "Sam Bahadur", "Mission Raniganj", "Crew", "Bad Newz", "Yodha", "Kill", "Vedaa",
    "Singham Again", "Chhaava", "Sita Ramam", "Hi Nanna", "Lucky Baskhar", "Hanu-Man",
    "Tillu Square", "Baby", "Dasara", "Virupaksha", "Guntur Kaaram", "Saripodhaa Sanivaaram",
    "Mathu Vadalara 2", "2018", "RDX", "Aavesham", "Manjummel Boys", "Premalu", "Aadujeevitham",
    "ARM", "Kishkindha Kaandam", "Romancham", "Neru", "Kannur Squad", "Garudan Malayalam",
    "Thalavan", "Marco", "Bougainvillea", "Bramayugam", "Iratta", "Saudi Vellakka",
    "Malikappuram", "Ela Veezha Poonchira", "Falimy", "Mukundan Unni Associates", "Jan.E.Man",
    "Jana Gana Mana", "Joji", "Nayattu", "Malik", "Home",
    
    # രണ്ടാമത് നൽകിയ സിനിമകളുടെ ലിസ്റ്റ്
    "Minnal Murali", "Kurup", "Bheeshma Parvam", "Rorschach", "Christopher", "Kaapa",
    "King of Kotha", "Ozler", "Abraham Ozler", "Phoenix", "Kooman", "Night Drive", "Heaven",
    "Pathonpatham Noottandu", "Palthu Janwar", "Dear Friend", "Solamante Theneechakal",
    "Hridayam", "Super Sharanya", "Pranaya Vilasam", "Madhura Manohara Moham", "Neram",
    "Bangalore Days", "Charlie", "Ustad Hotel", "Kumbalangi Nights",
    "Android Kunjappan Version 5.25", "Thinkalazhcha Nishchayam", "Operation Java", "Vellam",
    "Rekhachithram", "Thudarum", "Identity", "Rifle Club", "Sookshmadarshini", "Golam",
    "Level Cross", "Gaganachari", "Nunakkuzhi", "Adios Amigo", "Vaazha: Biopic of a Billion Boys",
    "Guruvayoor Ambalanadayil", "Turbo", "Ullozhukku", "Ozler Returns", "Jaya Jaya Jaya Jaya Hey",
    "Nna Thaan Case Kodu", "Rani", "Thattassery Koottam", "Kotthu", "Bro Daddy", "Aaraattu",
    "CBI 5: The Brain", "Puzhu", "Kaduva", "Gold", "Monster", "Kaathal – The Core",
    "Voice of Sathyanathan", "Corona Papers", "Christy", "Maheshum Marutiyum", "Romancham 2",
    "Vivekanandan Viralanu", "Tholvi F.C.", "Neymar", "Corona Dhavan", "Chaaver",
    "Journey of Love 18+", "Jackson Bazaar Youth", "Pookkaalam", "Live", "Queen Elizabeth",
    "Pendulum", "Appan", "Keedam", "Priyan Ottathilanu", "Four", "Meppadiyan", "Pada",
    "Bheemante Vazhi", "Archana 31 Not Out", "Freedom Fight", "Jack N Jill",
    "Member Rameshan 9A Ward", "Sunny", "One", "The Priest", "Cold Case", "Star", "Cobra",
    "Etharkkum Thunindhavan", "Sardar", "Prince", "Love", "Don 2022 Tamil", "Ayothi",
    "Parking", "Dada"
]

async def start_indexing():
    async with Client("indexer_userbot", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION) as userbot:
        print("🚀 ഓട്ടോമാറ്റിക് ഫയൽ ഇൻഡക്സിംഗ് ആരംഭിച്ചു...\n")

        for index, movie in enumerate(MOVIE_LIST, start=1):
            print("----------------------------------------")
            print(f"[{index}/{len(MOVIE_LIST)}] സെർച്ച് ചെയ്യുന്നു: {movie}")

            try:
                # Step 1: സിനിമയുടെ പേര് ടാർഗെറ്റ് ബോട്ടിന് അയക്കുന്നു
                sent_msg = await userbot.send_message(TARGET_BOT, movie)
                await asyncio.sleep(8)

                first_link = None

                # Step 2: റിസൾട്ടിൽ ഫയൽ ലിങ്ക് ഉണ്ടോ എന്ന് നോക്കുന്നു
                async for reply in userbot.get_chat_history(TARGET_BOT, limit=5):
                    if reply.id > sent_msg.id and reply.text and reply.entities:
                        for entity in reply.entities:
                            if entity.type.name == "TEXT_LINK" and entity.url:
                                first_link = entity.url
                                break
                    if first_link:
                        break

                # Step 3: ഡീപ് ലിങ്ക് ക്ലിക്ക് ചെയ്ത് ഫയൽ നേടുന്നു
                if first_link and "start=" in first_link:
                    param = first_link.split("start=")[1].split("?")[0]
                    start_msg = await userbot.send_message(TARGET_BOT, f"/start {param}")
                    await asyncio.sleep(8)

                    # Step 4: ലഭിച്ച ഫയൽ ചാനലിലേക്ക് ആഡ് ചെയ്യുന്നു
                    file_added = False
                    async for file_msg in userbot.get_chat_history(TARGET_BOT, limit=5):
                        if file_msg.id > start_msg.id and (file_msg.document or file_msg.video):
                            await file_msg.copy(chat_id=MY_CHANNEL, caption=f"🎬 **{movie}**")
                            print(f"✅ ചാനലിൽ ആഡ് ചെയ്തു: {movie}")
                            file_added = True
                            break

                    if not file_added:
                        print(f"⚠️ ഫയൽ ലഭ്യമായില്ല/കിട്ടിയില്ല: {movie}")

                else:
                    print(f"⚠️ ലിങ്ക് ലഭിച്ചില്ല: {movie}")

            except Exception as e:
                print(f"❌ എറർ സംഭവിച്ചു ({movie}): {e}")

            # 🛑 അക്കൗണ്ട് സെയിഫ് ആയിരിക്കാൻ 20 സെക്കൻഡ് ഗ്യാപ്പ് നൽകുന്നു
            print("⏳ അടുത്ത സിനിമ സെർച്ച് ചെയ്യുന്നതിന് മുൻപ് 20 സെക്കൻഡ് കാത്തിരിക്കുന്നു...")
            await asyncio.sleep(20)

if __name__ == "__main__":
    asyncio.run(start_indexing())
