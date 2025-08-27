from fastapi import APIRouter, Query, UploadFile, File, Body
from fastapi.responses import JSONResponse
from helper.analyze_helper import find_file_for_date
from helper.process_pre_compare import normalize_data_extracted, return_data_from_file
from typing import Optional
from io import BytesIO
import pandas as pd
from pathlib import Path
import shutil
from core.config import settings

router = APIRouter()


def _backup_file(path: Path):
    backup = path.with_suffix(f".bakup.{path.suffix}")

    shutil.copy(path, settings.BACKUP_BASE_DIR)
    return str(backup)

@router.get('/by-date')
def get_dates(d: Optional[str] = Query(None, description="YYYY-MM-DD")):
    if not d:
        return {'rows': []}
    print(d)
    f = find_file_for_date(d)
    print(f)
    df = return_data_from_file(f)
    result = normalize_data_extracted(df)
    if result is None:
        return {'rows': []}

    return {'rows': result.to_dict(orient='records')}

@router.post('/upload-parse')
async def coverse_data(file: UploadFile = File(...)):
    content = await file.read()
    name = (file.filename or '').lower()

    try:
        if name.endswith('.xlsx') or name.endswith('.xls'):
            df = pd.read_excel(BytesIO(content))  
        else:
            try:
                df = pd.read_csv(BytesIO(content))
            except Exception:
                df = pd.read_csv(BytesIO(content), encoding='latin1')

        required = {"severity", "label"}

        if required.issubset(df.columns):
            print("ok")
        else:
            print("okn't")

        result = normalize_data_extracted(df)
        if result is None:
            return {'rows': []}

        return JSONResponse({'rows': result.to_dict(orient='records')})
    except Exception as e:
        return JSONResponse({"rows": [], "error": f"parse_failed: {e}"}, status_code=400)

@router.post('/apply')
def update_data(payload: dict = Body(...)):
    date = payload.get("date")
    items = payload.get("items") or []
    keys = payload.get("keys") or ["id"]
    
    f = find_file_for_date(date) # type: ignore
    if not f:
        return JSONResponse({"ok": False, "error": f"Not found file for {date}"}, status_code=404)

    df = return_data_from_file(f)
    if df is None:
        return JSONResponse({"ok": False, "error": "Failed to read original file"}, status_code=400)


    _backup_file(Path(f))
    
    # df.to_csv('test.csv')
    for item in items:
        k = item.get("key")
        typ = item.get("type")
        new_row = item.get("new")
        old_row = item.get("old")

        if typ == "added" and new_row:
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

        elif typ == "modified" and new_row:
            mask = df[keys].astype(str).agg("-".join, axis=1) == k
            print(keys)
            df.loc[mask, :] = pd.DataFrame([new_row]).values

        elif typ == "removed" and old_row:
            mask = df[keys].astype(str).agg("-".join, axis=1) == k
            df = df[~mask]

    df.to_excel(f, index=False)

    return JSONResponse({"ok": True, "rows": len(df), "path": str(f)})


@router.post('/override')
def override_data(payload: dict = Body(...)):
    date = payload.get('date')
    items = payload.get("items") or []

    # print(type(items))
    # print(date)


    f = find_file_for_date(date) # type: ignore
    if not f:
        return JSONResponse({"ok": False, "error": f"Not found file for {date}"}, status_code=404)

    _backup_file(Path(f))

    df = pd.DataFrame(items)
    df.to_excel(f, index=False)
    return payload