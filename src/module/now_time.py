from datetime import datetime
import time


def now_time():
    Time = time.time()
    datetime_obj = datetime.fromtimestamp(Time)
    formatted_date = datetime_obj.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    return formatted_date


def proxy_time():
    current_time = time.time()
    next_minute_time = current_time + 30  # 秒
    datetime_obj = datetime.fromtimestamp(next_minute_time)
    formatted_date = datetime_obj.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    return formatted_date


def today():
    Time = time.time()
    datetime_obj = datetime.fromtimestamp(Time)
    formatted_date = datetime_obj.strftime("%Y-%m-%d")
    return formatted_date


def day():
    Time = time.time()
    datetime_obj = datetime.fromtimestamp(Time)
    formatted_date = datetime_obj.strftime("%d")
    return formatted_date


def year():
    Time = time.time()
    datetime_obj = datetime.fromtimestamp(Time)
    formatted_date = datetime_obj.strftime("%Y")
    return formatted_date


def moon():
    Time = time.time()
    datetime_obj = datetime.fromtimestamp(Time)
    formatted_date = datetime_obj.strftime("%m")
    return formatted_date
