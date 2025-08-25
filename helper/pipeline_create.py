from datetime import datetime, timedelta

# def convert_timezon_to_utc(time: datetime):
#     return time.astimezone(timezone.utc)

def time_ago(day: datetime, unit: str, num: int):
    if unit == "days":
        return day - timedelta(days=num)
    elif unit == "hours":
        return day - timedelta(hours=num)
    elif unit == "minutes":
        return day - timedelta(minutes=num)
    elif unit == "seconds":
        return day - timedelta(seconds=num)
    else:
        raise ValueError(f"Unsupported unit: {unit}")

def one_day_time(day: datetime):
    start = day.replace(hour=0, minute=0, second=0, microsecond=000000)
    end = start + timedelta(days=1)

    return start, end

def start_of_day(day: datetime):
    return day.replace(hour=0, minute=0, second=0, microsecond=0)

# def end_of_day(day: datetime):
#     return day.replace(hour=23, minute=59, second=59,microsecond=999000)

def data_pipeline_from_to(start: datetime, end: datetime, unit: str, binsize:int):
    pipeline = [
        { '$match': { 'timestamp': { '$gte': start, '$lt': end } } },
        { '$group': 
            {
            '_id': {
                    '$dateTrunc': {
                        'date': '$timestamp',
                        'unit': unit,
                        'binSize': binsize,
                        'timezone': '+07:00'
                        },
                    '_id': '$severity',
                    'count': { '$sum': 1 }
                    }
            } 
        },
        { '$sort': {'_id': -1} },
        { '$count': '$severity'}
    ]

    return pipeline

def data_query_find_from_to(start: datetime, end: datetime):
    return {
        'timestamp': {
            '$gte': start,
            '$lt': end
        }
    }