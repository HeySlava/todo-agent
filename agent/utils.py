import datetime as dt
from zoneinfo import ZoneInfo


MOSCOW_TZ = ZoneInfo('Europe/Moscow')
TIME_FORMAT = '%d.%m.%Y %H:%M'


def now_moscow() -> dt.datetime:
    now_utc = dt.datetime.now(dt.timezone.utc)
    return now_utc.astimezone(MOSCOW_TZ)
