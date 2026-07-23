from flask import Flask
import os
from dotenv import load_dotenv
from bot.db import users
from bot.api_client import BaghbanAPI
from bot.utils import gregorian_to_jalali
from telegram.ext import Application
from datetime import date

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
app = Flask(__name__)

# ساخت Application فقط برای ارسال پیام (بدون نیاز به webhook)
application = Application.builder().token(TOKEN).build()

@app.route("/api/cron/reminders")
def reminders():
    today = date.today()
    for uid, user in users.items():
        if not user.get("wp_user"):
            continue
        api = BaghbanAPI(user["wp_user"], user["wp_pass"])
        events = api.get_events()
        for ev in events:
            if ev.get("jalali_date") == gregorian_to_jalali(today.strftime("%Y-%m-%d")):
                try:
                    application.bot.send_message(uid, f"یادآوری: امروز باید {ev['type']} گیاه {ev['plant_name']} را انجام دهید.")
                except:
                    pass
    return "Reminders sent"