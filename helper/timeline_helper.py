from datetime import datetime, timedelta, timezone

TZ = TZ = timezone(timedelta(hours=7))

def start_of_day(dt: datetime) -> datetime:
    return dt.astimezone(TZ).replace(hour=0, minute=0, second=0, microsecond=0)

def align_min_floor(dt: datetime, step_min: int) -> datetime:
    dt = dt.astimezone(TZ).replace(second=0, microsecond=0)
    minute = (dt.minute // step_min) * step_min
    return dt.replace(minute=minute)

def align_hour_floor(dt: datetime) -> datetime:
    return dt.astimezone(TZ).replace(minute=0, second=0, microsecond=0)

def align_day_floor(dt: datetime) -> datetime:
    return start_of_day(dt)
