from datetime import datetime
import firebase_admin
from firebase_admin import credentials, db
import telebot

# 1. ഫയർബേസ് കോൺഫിഗറേഷൻ (serviceAccountKey.json ഫയൽ വഴി)
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(
    cred,
    {
        "databaseURL": (
            "https://a-one-chat-e3642-default-rtdb.firebaseio.com"
        )
    },
)

# 2. ടെലഗ്രാം ബോട്ട് ടോക്കൺ
TOKEN = "8872037190:AAHchhDIzV7aEZNqNwR6uO99emTk9MUi0-c"
bot = telebot.TeleBot(TOKEN)


# സ്റ്റാർട്ട് കമാൻഡ്
@bot.message_handler(commands=["start"])
def send_welcome(message):
    welcome_text = (
        "👋 ഹലോ! നിങ്ങളുടെ സേവിങ്സ് കണക്കാക്കാൻ ഞാൻ തയ്യാറാണ്.\n\n"
        "💰 **ഉപയോഗിക്കുന്ന വിധം:**\n"
        "• ക്യാഷ് ആഡ് ചെയ്യാൻ: സംഖ്യ മാത്രം അയക്കുക (ഉദാഹരണത്തിന്: `500`)\n"
        "• മൊത്തം ബാലൻസ് അറിയാൻ: `/total`"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")


# തുക അയച്ചാൽ ഫയർബേസിൽ സേവ് ചെയ്യാൻ (ഉദാഹരണത്തിന്: 200 അല്ലെങ്കിൽ 500)
@bot.message_handler(
    func=lambda msg: msg.text and msg.text.replace(".", "", 1).isdigit()
)
def add_cash_direct(message):
    try:
        amount = float(message.text)
        save_to_firebase(message.chat.id, amount)
        bot.reply_to(
            message,
            f"✅ വിജയകരമായി ₹{amount} നിങ്ങളുടെ സേവിങ്സിൽ ആഡ് ചെയ്തിരിക്കുന്നു! 🪙",
        )
    except ValueError:
        bot.reply_to(message, "❌ എന്തോ കുഴപ്പമുണ്ട്, വീണ്ടും ശ്രമിക്കുക.")


# /add കമാൻഡ് ഉപയോഗിച്ചും തുക ചേർക്കാം
@bot.message_handler(commands=["add"])
def add_cash_command(message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(
                message,
                "⚠️ ദയവായി തുക കൂടി ചേർക്കുക. (ഉദാഹരണത്തിന്: `/add 500`)",
                parse_mode="Markdown",
            )
            return

        amount = float(parts[1])
        save_to_firebase(message.chat.id, amount)
        bot.reply_to(
            message,
            f"✅ വിജയകരമായി ₹{amount} നിങ്ങളുടെ സേവിങ്സിൽ ആഡ് ചെയ്തിരിക്കുന്നു! 🪙",
        )
    except ValueError:
        bot.reply_to(message, "❌ തെറ്റായ തുക. ദയവായി ശരിയായ സംഖ്യ നൽകുക.")


# മൊത്തം തുക പരിശോധിക്കാൻ
@bot.message_handler(commands=["total"])
def check_total(message):
    user_id = str(message.chat.id)
    ref = db.reference(f"savings/{user_id}/transactions")
    data = ref.get()

    if not data:
        bot.reply_to(
            message, "📭 ഇതുവരെ സേവിങ്സ് ഒന്നും ആഡ് ചെയ്തിട്ടില്ല."
        )
        return

    total_amount = sum(item["amount"] for item in data.values())
    bot.reply_to(
        message,
        f"📊 **ഇതുവരെയുള്ള മൊത്തം സേവിങ്സ്:**\n\n💵 **₹{total_amount}**",
        parse_mode="Markdown",
    )


# ഫയർബേസിലേക്ക് ഡാറ്റ സേവ് ചെയ്യുന്ന ഫങ്ഷൻ
def save_to_firebase(user_id, amount):
    user_id = str(user_id)
    ref = db.reference(f"savings/{user_id}/transactions")
    new_transaction = {
        "amount": amount,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    ref.push(new_transaction)


# ബോട്ട് റൺ ചെയ്യാൻ
print("🤖 ബോട്ട് വർക്ക്‌ ചെയ്യാൻ തുടങ്ങിയിരിക്കുന്നു...")
bot.infinity_polling()
