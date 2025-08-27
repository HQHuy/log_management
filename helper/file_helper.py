import re
import os
from datetime import datetime
from core.config import settings

def safe_filename(name: str) -> str:
    name = name.replace("\\", "/").split("/")[-1]
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name)

def extract_date_from_filename(folder_path):
    try:
        filenames = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
        
        pattern = r'\d{4}-\d{2}-\d{2}'
        dates = []
        
        for filename in filenames:
            if filename.endswith('.xlsx'):
                match = re.search(pattern, filename)
                if match:
                    dates.append(match.group(0))
            else: continue
        
        if dates:
            return dates  
        else:
            return "Not found dates format in file name"
    except Exception as e:
        return f"Lỗi: {str(e)}"
    
def get_data_file(date_str: str, folder: str = ""):
    try:
        # Parse input date string to datetime
        dt = datetime.fromisoformat(date_str)
    except ValueError:
        raise ValueError(f"Invalid date string: {date_str}. Expected format YYYY-MM-DD.")

    file_name = f"log_{dt.year:04d}-{dt.month:02d}-{dt.day:02d}.xlsx"
    file_path = os.path.join(settings.OUTPUT_BASE_DIR, file_name)
    print(os.path.exists(file_path))
    if os.path.exists(file_path):
        return file_path
    return None