from datetime import datetime, timedelta

def one_day_time(day_utc: datetime):
    start = day_utc.replace(hour=0, minute=0, second=0, microsecond=000000)
    end = start + timedelta(days=1)

    return start, end

def start_of_day(day_utc: datetime):
    return day_utc.replace(hour=0, minute=0, second=0, microsecond=0)

def end_of_day(day_utc: datetime):
    return day_utc.replace(hour=23, minute=59, second=59,microsecond=999000)

def data_pipeline_from_to(start_utc, end_utc):
    pipeline = [
        { '$match': { 'timestamp': { '$gte': start_utc, '$lt': end_utc } } },
        { '$group': {
            '_id': {'$dateToString': {'format': '%Y-%m-%d', 'date': '$timestamp'}},
            'docs': {'$push': { '_id': { '$toString': '$_id'}, 'message': '$message', 'severity': '$severity', 'timestamp': '$timestamp' }}
        } },
        { '$sort': {'_id': -1} }
    ]

    return pipeline