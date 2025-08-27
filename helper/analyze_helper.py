from typing import Optional
from pathlib import Path

from core.config import settings

def find_file_for_date(date_str: str) -> Optional[Path]:
    output_fol = Path(settings.OUTPUT_BASE_DIR)
    cands = sorted(output_fol.glob(f"*{date_str}*"))
    return cands[0] if cands else None