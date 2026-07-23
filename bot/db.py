# ذخیره موقت اطلاعات کاربر (در حافظه، فقط برای تست)
users = {}   # user_id تلگرام : {name, family, phone, wp_user, wp_pass}

def save_user(telegram_id, data: dict):
    users[telegram_id] = data

def get_user(telegram_id):
    return users.get(telegram_id)

def update_user(telegram_id, key, value):
    if telegram_id in users:
        users[telegram_id][key] = value