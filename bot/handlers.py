from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters
)
from bot.api_client import BaghbanAPI
from bot.db import save_user, get_user, update_user
from bot.utils import jalali_to_gregorian
import os

# states for registration
(NAME, FAMILY, PHONE) = range(3)
# states for adding plant
(SEARCH_PLANT, SELECT_PLANT, POT_DIAMETER, POT_HEIGHT, POT_MATERIAL,
 WATERING_DATE, FERTILIZING_DATE, FERTILIZER_INFO) = range(8)
# state for setting wp auth
WP_USER, WP_PASS = range(10, 12)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    existing = get_user(user.id)
    if not existing:
        await update.message.reply_text("به باغبون خوش آمدید! لطفاً ابتدا ثبت‌نام کنید.\nنام خود را وارد کنید:")
        return NAME
    else:
        await show_main_menu(update, context)
        return ConversationHandler.END

async def register_name(update, context):
    context.user_data["reg_name"] = update.message.text
    await update.message.reply_text("نام خانوادگی:")
    return FAMILY

async def register_family(update, context):
    context.user_data["reg_family"] = update.message.text
    await update.message.reply_text("شماره تماس (مثلاً 09121234567):")
    return PHONE

async def register_phone(update, context):
    phone = update.message.text
    user_id = update.effective_user.id
    save_user(user_id, {
        "name": context.user_data["reg_name"],
        "family": context.user_data["reg_family"],
        "phone": phone,
        "wp_user": None,
        "wp_pass": None
    })
    await update.message.reply_text("ثبت‌نام کامل شد. حالا برای اتصال به سایت باغبان من، نام کاربری و رمز برنامه (Application Password) خود را با دستور /set_auth وارد کنید.")
    await show_main_menu(update, context)
    return ConversationHandler.END

async def set_auth_start(update, context):
    await update.message.reply_text("لطفاً نام کاربری وردپرس خود را بفرستید:")
    return WP_USER

async def set_auth_user(update, context):
    context.user_data["wp_user"] = update.message.text
    await update.message.reply_text("Application Password وردپرس را وارد کنید (با فاصله نباشد):")
    return WP_PASS

async def set_auth_pass(update, context):
    user_id = update.effective_user.id
    user = get_user(user_id)
    if not user:
        await update.message.reply_text("ابتدا ثبت‌نام کنید: /start")
        return ConversationHandler.END
    update_user(user_id, "wp_user", context.user_data["wp_user"])
    update_user(user_id, "wp_pass", update.message.text)
    await update.message.reply_text("اطلاعات احراز هویت ذخیره شد. حالا می‌توانید از منوی اصلی استفاده کنید.")
    await show_main_menu(update, context)
    return ConversationHandler.END

async def show_main_menu(update, context):
    keyboard = [
        [InlineKeyboardButton("🌱 باغ من", callback_data="my_garden")],
        [InlineKeyboardButton("➕ افزودن گیاه", callback_data="add_plant")],
        [InlineKeyboardButton("📅 رویدادهای این هفته", callback_data="events")],
        [InlineKeyboardButton("💰 وضعیت اشتراک", callback_data="subscription")],
        [InlineKeyboardButton("🔔 اعلان‌ها", callback_data="notifications")],
        [InlineKeyboardButton("🛒 فروشگاه", callback_data="products")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text("منوی اصلی:", reply_markup=reply_markup)
    else:
        await update.callback_query.message.edit_text("منوی اصلی:", reply_markup=reply_markup)

async def button_handler(update, context):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user = get_user(user_id)
    if not user or not user.get("wp_user"):
        await query.edit_message_text("لطفاً ابتدا با /start ثبت‌نام و سپس با /set_auth وارد شوید.")
        return
    api = BaghbanAPI(user["wp_user"], user["wp_pass"])
    data = query.data

    if data == "my_garden":
        plants = api.get_my_plants()
        if not plants:
            await query.edit_message_text("شما هنوز گیاهی اضافه نکرده‌اید.")
        else:
            text = "🌱 گیاهان شما:\n" + "\n".join(
                f"{p['plant_name']} - گلدان {p.get('pot_material','')} - حجم خاک {p.get('soil_volume','')} لیتر"
                for p in plants
            )
            await query.edit_message_text(text)
    elif data == "events":
        events = api.get_events()
        if not events:
            await query.edit_message_text("رویدادی در این هفته ندارید.")
        else:
            msg = "📅 رویدادهای پیش رو:\n" + "\n".join(
                f"{e['jalali_date']} : {e['type']} برای {e['plant_name']}" for e in events
            )
            await query.edit_message_text(msg)
    elif data == "subscription":
        sub = api.get_subscription_status()
        msg = (
            f"💰 اشتراک شما:\n"
            f"نام پلن: {sub['subscription']['plan_name']}\n"
            f"وضعیت: {'فعال' if sub['subscription']['active'] else 'غیرفعال'}\n"
            f"تعداد گیاهان: {sub['plant_count']} / {sub['subscription']['plant_limit']}\n"
            f"روزهای باقی‌مانده: {sub['subscription']['days_left']}\n"
            f"انقضاء: {sub['subscription']['expiry_jalali']}"
        )
        await query.edit_message_text(msg)
    elif data == "notifications":
        notifs = api.get_notifications()
        if not notifs:
            await query.edit_message_text("اعلانی ندارید.")
        else:
            text = "\n".join(f"🔔 {n['message']}" for n in notifs)
            await query.edit_message_text(text)
    elif data == "products":
        # نمایش محصولات (از ووکامرس یا لیست ثابت)
        products = get_products()  # تابع سفارشی
        if not products:
            await query.edit_message_text("محصولی موجود نیست.")
        else:
            text = "🛒 محصولات:\n" + "\n".join(
                f"{p['name']} - {p['price']} تومان\n[خرید]({p['link']})"
                for p in products
            )
            await query.edit_message_text(text, parse_mode="Markdown")
    elif data == "add_plant":
        await query.edit_message_text("لطفاً نام گیاه مورد نظر را بنویسید:")
        return SEARCH_PLANT

def get_products():
    # اینجا می‌توان از WooCommerce REST API استفاده کرد
    # فعلاً یک لیست نمونه
    return [
        {"name": "کود NPK 20-20-20", "price": "150,000", "link": "https://baghbanman.ir/product/npk"},
        {"name": "گلدان سرامیکی سایز 20", "price": "350,000", "link": "https://baghbanman.ir/product/pot-20"}
    ]

async def search_plant(update, context):
    user_id = update.effective_user.id
    user = get_user(user_id)
    api = BaghbanAPI(user["wp_user"], user["wp_pass"])
    term = update.message.text
    result = api.search_plants(term)
    if not result.get("plants"):
        await update.message.reply_text("نتیجه‌ای یافت نشد. دوباره تلاش کنید:")
        return SEARCH_PLANT
    context.user_data["search_results"] = result["plants"]
    keyboard = []
    for plant in result["plants"]:
        keyboard.append([InlineKeyboardButton(plant["title"], callback_data=f"plant_{plant['remote_id']}")])
    await update.message.reply_text("نتایج جستجو:", reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECT_PLANT

async def select_plant(update, context):
    query = update.callback_query
    await query.answer()
    plant_id = int(query.data.split("_")[1])
    context.user_data["selected_plant_id"] = plant_id
    await query.edit_message_text("قطر گلدان (سانتی‌متر) را وارد کنید:")
    return POT_DIAMETER

async def pot_diameter(update, context):
    context.user_data["pot_diameter"] = float(update.message.text)
    await update.message.reply_text("ارتفاع گلدان (سانتی‌متر):")
    return POT_HEIGHT

async def pot_height(update, context):
    context.user_data["pot_height"] = float(update.message.text)
    await update.message.reply_text("جنس گلدان (اختیاری، مثلاً سرامیکی):")
    return POT_MATERIAL

async def pot_material(update, context):
    context.user_data["pot_material"] = update.message.text
    await update.message.reply_text("تاریخ آخرین آبیاری (شمسی، مثل 1402/12/15) یا /skip:")
    return WATERING_DATE

async def watering_date(update, context):
    if update.message.text != "/skip":
        g_date = jalali_to_gregorian(update.message.text.replace("/", "-"))
        context.user_data["last_watering_date"] = g_date
    else:
        context.user_data["last_watering_date"] = None
    await update.message.reply_text("تاریخ آخرین کوددهی (شمسی) یا /skip:")
    return FERTILIZING_DATE

async def fertilizing_date(update, context):
    if update.message.text != "/skip":
        g_date = jalali_to_gregorian(update.message.text.replace("/", "-"))
        context.user_data["last_fertilizing_date"] = g_date
    else:
        context.user_data["last_fertilizing_date"] = None
    await update.message.reply_text("اطلاعات کود (اختیاری، مثلاً NPK 20-20-20) یا /skip:")
    return FERTILIZER_INFO

async def fertilizer_info(update, context):
    if update.message.text != "/skip":
        context.user_data["fertilizer_info"] = update.message.text
    else:
        context.user_data["fertilizer_info"] = None
    # نهایی کردن افزودن گیاه
    user_id = update.effective_user.id
    user = get_user(user_id)
    api = BaghbanAPI(user["wp_user"], user["wp_pass"])
    plant_data = {
        "plant_id": context.user_data["selected_plant_id"],
        "pot_diameter": context.user_data["pot_diameter"],
        "pot_height": context.user_data["pot_height"],
        "pot_material": context.user_data.get("pot_material"),
        "last_watering_date": context.user_data.get("last_watering_date"),
        "last_fertilizing_date": context.user_data.get("last_fertilizing_date"),
        "fertilizer_info": context.user_data.get("fertilizer_info")
    }
    resp = api.add_plant(plant_data)
    if resp.get("success"):
        await update.message.reply_text(f"✅ گیاه با موفقیت اضافه شد!\nحجم خاک: {resp['soil_volume']} لیتر")
    else:
        await update.message.reply_text("❌ خطا در افزودن گیاه.")
    return ConversationHandler.END

async def cancel(update, context):
    await update.message.reply_text("عملیات لغو شد.")
    return ConversationHandler.END