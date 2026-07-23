from flask import Flask, request, Response
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
from bot.handlers import (
    start, register_name, register_family, register_phone,
    set_auth_start, set_auth_user, set_auth_pass,
    button_handler, search_plant, select_plant,
    pot_diameter, pot_height, pot_material,
    watering_date, fertilizing_date, fertilizer_info,
    cancel, show_main_menu
)
from bot.handlers import (NAME, FAMILY, PHONE, SEARCH_PLANT, SELECT_PLANT,
                          POT_DIAMETER, POT_HEIGHT, POT_MATERIAL,
                          WATERING_DATE, FERTILIZING_DATE, FERTILIZER_INFO,
                          WP_USER, WP_PASS)
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
app = Flask(__name__)

application = Application.builder().token(TOKEN).build()

# Registration conversation
reg_conv = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_name)],
        FAMILY: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_family)],
        PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_phone)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

# Set auth conversation
auth_conv = ConversationHandler(
    entry_points=[CommandHandler("set_auth", set_auth_start)],
    states={
        WP_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_auth_user)],
        WP_PASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_auth_pass)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

# Add plant conversation
add_plant_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(button_handler, pattern="^add_plant$")],
    states={
        SEARCH_PLANT: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_plant)],
        SELECT_PLANT: [CallbackQueryHandler(select_plant, pattern=r"^plant_\d+$")],
        POT_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, pot_diameter)],
        POT_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, pot_height)],
        POT_MATERIAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, pot_material)],
        WATERING_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, watering_date)],
        FERTILIZING_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, fertilizing_date)],
        FERTILIZER_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, fertilizer_info)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

application.add_handler(reg_conv)
application.add_handler(auth_conv)
application.add_handler(add_plant_conv)
application.add_handler(CallbackQueryHandler(button_handler, pattern="^(my_garden|events|subscription|notifications|products)$"))

@app.route("/api/bot", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.process_update(update)
    return Response("ok", status=200)

@app.route("/api/set_webhook", methods=["GET"])
def set_webhook():
    url = request.args.get("url")
    if not url:
        return "Need url param"
    application.bot.set_webhook(url + "/api/bot")
    return "Webhook set"