import os
from loguru import logger
from typing import List

def file_already():
    try:
        os.makedirs("output", exist_ok=True)

        existing_dates_files = [
            f.split("_")[1].split(".")[0]
            for f in os.listdir("output")
            if f.endswith(".xlsx")
        ]

        return existing_dates_files
    except Exception as e:
        print('Have error: {}', str(e))
        logger.error('Have error at check exist file')

def missing_dates(dates):
    miss_dates: List[str] = []
    exist_dates = file_already()
    
    if dates is None or dates == []:
        return None
    
    for i in dates:
        if i not in exist_dates:
            miss_dates.append(i)

    return miss_dates
    