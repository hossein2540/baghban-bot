from jdatetime import date as jdate, datetime as jdatetime
from datetime import datetime, timedelta

def jalali_to_gregorian(jalali_date_str: str) -> str:
    """تبدیل تاریخ شمسی به میلادی (فرمت Y-m-d)"""
    try:
        year, month, day = map(int, jalali_date_str.split("-"))
        g = jdate(year, month, day).togregorian()
        return g.strftime("%Y-%m-%d")
    except:
        return None

def gregorian_to_jalali(greg_date_str: str) -> str:
    """تبدیل میلادی به شمسی"""
    g = datetime.strptime(greg_date_str, "%Y-%m-%d")
    j = jdatetime.fromgregorian(datetime=g)
    return j.strftime("%Y/%m/%d")