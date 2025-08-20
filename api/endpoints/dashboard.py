from fastapi import APIRouter, Depends
from typing import List, Any
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from loguru import logger

from core.dependencies import ( get_log_repo )
from repository.log import LogRepository
import helper.check_exist_file as file_helper
import helper.pipeline_create as date_pipeline_helper
import helper.save_log_file as save_log
TIME_DEMO = datetime(2025, 5, 14,  4, 59, 59, tzinfo=timezone.utc)

from services import sys_sta
from services import key_metric

router = APIRouter()
dates_lst: List[str] = []

@router.get('/data-collection/date')
async def collect_date(log_repo: LogRepository = Depends(get_log_repo)):
    
    result = await log_repo.get_date_from_db()
    dates_lst = result
    return result

@router.get('/download/data-by-date')
async def download_data(log_repo: LogRepository = Depends(get_log_repo)):
    dates_exist = dates_lst
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
        
        # data_lst.append(data)
        
    else:
        start_date = datetime.strptime(missing_dates[-1], format_date)
        end_date = datetime.strptime(missing_dates[0], format_date)

        pipeline = date_pipeline_helper.data_pipeline_from_to(start_date, end_date)

        data = await log_repo.get_data(pipeline_custom=pipeline)

        # data_lst.append(data)
    # print(len(data))
    save_log.export_log(data)
    return True

@router.get('/system-status')
async def system_status(log_repo: LogRepository = Depends(get_log_repo)):
    # last_time = datetime.now()
    last_time_local = TIME_DEMO.astimezone(timezone(timedelta(hours=7))) 
    start_date = date_pipeline_helper.start_of_day(last_time_local)

    pipeline = date_pipeline_helper.data_pipeline_from_to(start_date, last_time_local)

    data = await log_repo.get_data(pipeline_custom=pipeline)

    # print(data)

    system_data_today = await sys_sta.compute_system_status(data)

    print(system_data_today)
    return system_data_today

@router.get('/key-metrics')
async def key_metrics_1_hour(log_repo: LogRepository = Depends(get_log_repo)):
    last_time_local = TIME_DEMO.astimezone(timezone(timedelta(hours=7))) 
    start_time1 = date_pipeline_helper.hour_ago(last_time_local)

    end_time2 = start_time1
    start_time2 = date_pipeline_helper.hour_ago(start_time1)

    print(start_time1, last_time_local)
    print(start_time2, end_time2)

    pipeline = date_pipeline_helper.data_pipeline_from_to(start_time1, last_time_local)
    pipeline2 = date_pipeline_helper.data_pipeline_from_to(start_time2, end_time2)

    data1 = await log_repo.get_data(pipeline_custom=pipeline)
    data2 = await log_repo.get_data(pipeline_custom=pipeline2)

    print(len(data1))
    print(len(data2))
    await key_metric.compute_key_metrics(docs_now=data1, docs_prev=data2)
    # key_metrics = await key_metric.compute_key_metrics(docs_now=data1, docs_prev=data2)