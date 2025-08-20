from datetime import datetime, timedelta, timezone

# def convert_timezon_to_utc(time: datetime):
#     return time.astimezone(timezone.utc)

def hour_ago(day: datetime):
    return day - timedelta(hours=1)

def one_day_time(day: datetime):
    start = day.replace(hour=0, minute=0, second=0, microsecond=000000)
    end = start + timedelta(days=1)

    return start, end

def start_of_day(day: datetime):
    return day.replace(hour=0, minute=0, second=0, microsecond=0)

# def end_of_day(day: datetime):
#     return day.replace(hour=23, minute=59, second=59,microsecond=999000)

def data_pipeline_from_to(start, end):
    pipeline = [
        { '$match': { 'timestamp': { '$gte': start, '$lt': end } } },
        { '$group': {
            '_id': {'$dateToString': {'format': '%Y-%m-%d', 'date': '$timestamp', 'timezone': '+07:00' }},
            'docs': {'$push': { '_id': { '$toString': '$_id'}, 'message': '$message', 'severity': '$severity', 'timestamp': '$timestamp' }}
        } },
        { '$sort': {'_id': -1} }
    ]

    return pipeline

def data_