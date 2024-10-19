import time
from datetime import datetime, timezone

def shift_decimal(number, places):
    return number * (10 ** places)

def gen_timestamp():
    return int(shift_decimal(time.time(), 3))

def current_seconds():
    return int(time.time())


def current_utc_time():
    # 獲取當前 UTC 時間
    current_time_utc = datetime.now(timezone.utc)

    # 將時間格式化為 ISO 8601 格式
    formatted_time = current_time_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
    return formatted_time
