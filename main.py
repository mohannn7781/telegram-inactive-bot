import json
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

TOKEN = "8760694566:AAEbsYD4LYZKoaQmaJHpRDRKqzsWLVJ-yQE"

DATA_FILE = "activity.json"

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

activity = load_data()

def today():
    return datetime.utcnow().date().isoformat()

async def track_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or not update.effective_user:
        return
    chat_id = str(update.effective_chat.id)
    user_id = str(update.effective_user.id)

    if chat_id not in activity:
        activity[chat_id] = {}

    activity[chat_id][user_id] = today()
    save_data(activity)

async def daily_check(context: ContextTypes.DEFAULT_TYPE):
    for chat_id, users in list(activity.items()):
        chat_id_int = int(chat_id)
        for user_id, last_date in list(users.items()):
            last = datetime.fromisoformat(last_date).date()
            diff = (datetime.utcnow().date() - last).days

            try:
                if diff == 3:
                    await context.bot.send_message(
                        chat_id=chat_id_int,
                        text=f"⚠️ Warning: <a href='tg://user?id={user_id}'>You</a> have been inactive for 3 days!",
                        parse_mode="HTML"
                    )
                elif diff >= 5:
                    await context.bot.ban_chat_member(chat_id=chat_id_int, user_id=int(user_id))
                    await context.bot.send_message(
                        chat_id=chat_id_int,
                        text=f"⛔ A member was removed due to 5 days inactivity.",
                        parse_mode="HTML"
                    )
                    del activity[chat_id][user_id]
                    save_data(activity)
            except:
                pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is running! I will track activity and auto-kick inactive members.")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.ALL, track_message))

job_queue = app.job_queue
job_queue.run_repeating(daily_check, interval=86400, first=10)

print("Bot started...")
app.run_polling()
