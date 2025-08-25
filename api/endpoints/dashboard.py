from fastapi import APIRouter, Depends, Query
from typing import List, Literal
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from loguru import logger
# from icecream import ic

from core.dependencies import ( get_log_repo )
from repository.log import LogRepository
import helper.check_exist_file as file_helper
import helper.pipeline_create as date_pipeline_helper
import helper.save_log_file as save_log
import helper.timeline_helper as tl_help
TIME_DEMO = datetime(2025, 5, 17,  3, 59, 59, tzinfo=timezone.utc)

from services import sys_sta
from services import key_metric as metrics_key
from services import quick_stats_30m

router = APIRouter()
dates_lst: List[str] = []

@router.get('/data-collection/date')
async def collect_date(log_repo: LogRepository = Depends(get_log_repo)):
    
    result = await log_repo.get_date_from_db()
    # dates_lst = result
    return result

@router.get('/download/data-by-date')
async def download_data(log_repo: LogRepository = Depends(get_log_repo)):
    dates_exist = await log_repo.get_date_from_db()
    missing_dates = file_helper.missing_dates(dates_exist)
    # data_lst: List[Any] = []
    format_date = '%Y-%m-%d'

    # print(missing_dates)

    if missing_dates is None or len(missing_dates) == 0:
        return None
    
    # if (datetime.strptime(day, format_date) == datetime.today().date() for day in missing_dates):
    #     missing_dates.remove(str(datetime.today().date()))

    if (str(datetime.today().date()) in missing_dates):
        missing_dates.remove(str(datetime.today().date()))
    
    if len(missing_dates) == 1:
        date = datetime.strptime(missing_dates[0], format_date)
        start, end = date_pipeline_helper.one_day_time(date)

        pipeline = date_pipeline_helper.data_pipeline_from_to(start, end)

        data = await log_repo.get_data(pipeline_custom=pipeline)
        

        
    else:
        start_date = datetime.strptime(missing_dates[-1], format_date)
        end_date = datetime.strptime(missing_dates[0], format_date)

        pipeline = date_pipeline_helper.data_pipeline_from_to(start_date, end_date)

        data = await log_repo.get_data(pipeline_custom=pipeline)

    print(data[0])
    print(len(data))
    save_log.export_log(data)
    return True

@router.get('/system-status')
async def system_status(log_repo: LogRepository = Depends(get_log_repo)):
    # last_time = datetime.now()
    last_time_local = TIME_DEMO.astimezone(timezone(timedelta(hours=7))) 
    start_date = date_pipeline_helper.start_of_day(last_time_local)

    query = date_pipeline_helper.data_query_find_from_to(start_date, last_time_local)

    data = await log_repo.get_data_find(query)

    # print(data[0]) 

    result = await sys_sta.compute_system_status(data)
    return result

@router.get('/key-metrics')
async def key_metrics(log_repo: LogRepository = Depends(get_log_repo)):
    end_now = TIME_DEMO.astimezone(timezone(timedelta(hours=7)))
    start_now = date_pipeline_helper.time_ago(end_now, unit='hours', num=1)

    end_prev = start_now
    start_prev = date_pipeline_helper.time_ago(end_prev, unit='hours', num=1)

    query_now = date_pipeline_helper.data_query_find_from_to(start_now, end_now)
    query_prev = date_pipeline_helper.data_query_find_from_to(start_prev, end_prev)

    data_now = await log_repo.get_data_find(query_now)
    data_prev = await log_repo.get_data_find(query_prev)

    result = await metrics_key.compute_key_metrics(data_now, data_prev)
    return result

@router.get('/quick-stats')
async def quick_stats_30min(log_repo: LogRepository = Depends(get_log_repo)):
    end = TIME_DEMO.astimezone(timezone(timedelta(hours=7)))
    start = date_pipeline_helper.time_ago(end, unit='minutes', num=30)

    query = date_pipeline_helper.data_query_find_from_to(start, end)

    data = await log_repo.get_data_find(query)

    result = await quick_stats_30m.compute_quick_stats(data)

    return result

@router.get('/log-type')
async def top_log_type(log_repo: LogRepository = Depends(get_log_repo)):
    end = TIME_DEMO.astimezone(timezone(timedelta(hours=7)))
    start, end = date_pipeline_helper.one_day_time(end)
    
    pipeline = [
        { '$match': { 'timestamp': { '$gte': start, '$lt': end } } },
        { '$group': 
            {
            '_id': '$severity',
            'count': { '$sum': 1 }
            } 
        },
    ]

    # pipeline = date_pipeline_helper.data_pipeline_from_to(start, end, unit='day', binsize=1)
    data = await log_repo.get_data(pipeline_custom=pipeline)

    # print(data)
    return data

@router.get('/timeline')
async def time_line(log_repo: LogRepository = Depends(get_log_repo),
                    window: Literal['1h', '6h', 'now', '7d'] = Query(default='now')):
    unit = 'hour'
    binsize = 1
    start = end = None
    bucket_for_fe = None  

    if window == '1h':
        unit = 'minute'; binsize = 5; bucket_for_fe = 5
        end_aligned = tl_help.align_min_floor(TIME_DEMO, binsize)
        start = end_aligned - timedelta(hours=1)
        end = end_aligned + timedelta(minutes=binsize)  
    elif window == '6h':
        unit = 'minute'; binsize = 30; bucket_for_fe = 30
        end_aligned = tl_help.align_min_floor(TIME_DEMO, binsize)
        start = end_aligned - timedelta(hours=6)
        end = end_aligned + timedelta(minutes=binsize)  
    elif window == 'now':
        unit = 'hour'; binsize = 1; bucket_for_fe = 1
        start = tl_help.start_of_day(TIME_DEMO)
        end = start + timedelta(days=1)  
    elif window == '7d':
        unit = 'day'; binsize = 1; bucket_for_fe = 1
        today0 = tl_help.start_of_day(TIME_DEMO)
        start = today0 - timedelta(days=6)
        end = today0 + timedelta(days=1) 

    pipeline = date_pipeline_helper.data_pipeline_for_chart(
        start, end, unit=unit, binsize=binsize
    )
    data = await log_repo.get_data(pipeline_custom=pipeline)

    return {
        "window": window,
        "bucket": bucket_for_fe,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "items": data, 
    }