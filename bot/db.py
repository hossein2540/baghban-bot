import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL", "")
key = os.getenv("SUPABASE_KEY", "")
supabase: Client = create_client(url, key) if url and key else None

def save_user(telegram_id: int, data: dict):
    """ذخیره یا به‌روزرسانی کاربر"""
    if not supabase:
        return
    try:
        existing = supabase.table("users").select("*").eq("telegram_id", telegram_id).execute()
        if existing.data:
            supabase.table("users").update(data).eq("telegram_id", telegram_id).execute()
        else:
            data["telegram_id"] = telegram_id
            supabase.table("users").insert(data).execute()
    except Exception as e:
        print(f"Error saving user: {e}")

def get_user(telegram_id: int):
    """دریافت اطلاعات کاربر"""
    if not supabase:
        return None
    try:
        result = supabase.table("users").select("*").eq("telegram_id", telegram_id).execute()
        if result.data:
            return result.data[0]
        return None
    except Exception as e:
        print(f"Error getting user: {e}")
        return None

def update_user(telegram_id: int, key: str, value):
    """آپدیت یک فیلد خاص از کاربر"""
    if not supabase:
        return
    try:
        supabase.table("users").update({key: value}).eq("telegram_id", telegram_id).execute()
    except Exception as e:
        print(f"Error updating user: {e}")