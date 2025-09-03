import pandas as pd
from pathlib import Path
from typing import Any, Optional
import ast

def _get_data(path_to_file):
    file_source = Path(path_to_file)
    return pd.read_excel(file_source)

def _to_iso8601(val: Any) -> Optional[str]:
    if val is None:
        return None
    ts = pd.to_datetime(val, utc=False, errors="coerce")
    if pd.isna(ts):
        return None
    iso = ts.isoformat()
    if iso.endswith("+00:00"):
        iso = iso[:-6] + "Z"
    return iso

def return_data_from_file(path_to_file):
    return _get_data(path_to_file)

def normalize_data_extracted(df) -> pd.DataFrame | None:
    try:
        # df = _get_data(path_to_file)
        df['timestamp'] = df['timestamp'].apply(_to_iso8601)
        df["data_extracted"] = df["data_extracted"].apply(ast.literal_eval)
        df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
        return df
    except Exception:
        pass


