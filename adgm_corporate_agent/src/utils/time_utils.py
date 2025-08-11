from datetime import datetime
import pytz


def now_timestamp_ist() -> str:
    tz = pytz.timezone("Asia/Kolkata")
    return datetime.now(tz).strftime("%Y-%m-%d_%H-%M-%S")


