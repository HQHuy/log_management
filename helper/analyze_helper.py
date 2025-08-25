import pandas as pd
import numpy as np
from typing import Optional
from pathlib import Path

from core.config import settings

def _pct95(series: pd.Series) -> float:
    """
    VN: Tính p95 an toàn (rỗng -> 0).
    EN: Safe p95 (empty -> 0).
    """
    vals = pd.to_numeric(series.dropna(), errors="coerce").dropna()
    if vals.empty:
        return 0.0
    return float(np.percentile(vals, 95))

def _safe_ratio(part: int, whole: int) -> float:
    return round(100.0 * part / whole, 2) if whole > 0 else 0.0

def find_file_for_date(date_str: str) -> Optional[Path]:
    output_fol = Path(settings.OUTPUT_BASE_DIR)
    cands = sorted(output_fol.glob(f"*{date_str}*"))
    return cands[0] if cands else None