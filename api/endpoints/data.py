from fastapi import APIRouter, UploadFile, File, Query
from typing import Dict, Any
import os
from pathlib import Path
from core.config import settings
from helper.file_helper import extract_date_from_filename, safe_filename
from helper.analyze_helper import find_file_for_date
from services import analyze_ser as analyzer
from loguru import logger
from tempfile import SpooledTemporaryFile
import pandas as pd

router = APIRouter()


@router.get('/dates')
def starter():
    dir = getattr(settings, "OUTPUT_BASE_DIR")
    if not os.path.isdir(dir):
        return {"dates": []}

    dates = extract_date_from_filename(dir) or []
    try:
        dates.sort(reverse=True) # type: ignore
    except Exception:
        pass
    return {'dates': dates}

@router.post("/upload")
async def upload(file: UploadFile = File(...), analyze: int = Query(0)):
    raw = await file.read()
    filename = safe_filename(file.filename or "upload.xlsx")
    suffix = Path(filename).suffix.lower()

    try:
        result: Dict[str, Any] = {
            "ok": True,
            "filename": filename,
            "persisted": False,
        }
        if analyze:
            with SpooledTemporaryFile(max_size=10 * 1024 * 1024, mode="w+b", suffix=suffix) as tf:
                tf.write(raw)
                tf.seek(0)
                if suffix in (".xlsx", ".xls"):
                    df = pd.read_excel(tf)
                else:
                    raise ValueError(f"Unsupported upload: {filename}")
                
            result["analysis"] = analyzer.analyze_df(df)
        return result
    finally:
        await file.close()


@router.get("/analyze")
def analyze(date: str = Query(..., description="Date for analyze")):
    f = find_file_for_date(date)
    if not f:
        return { "ok": False, "error": f"Not fond file for date: {date}" }
    df = analyzer.load_data(f)
    return { "ok": True, "analysis": analyzer.analyze_df(df) }