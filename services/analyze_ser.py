from pathlib import Path
import pandas as pd
from typing import List, Any, Dict
import json
import ast
import re
import numpy as np

def load_data(file_path: Path):
    path = Path(file_path)
    suf = path.suffix.lower()
    if suf not in [".xlsx", ".xls"]:
        raise ValueError(f"Unsupported file format: {suf}")
    return pd.read_excel(path)

def build_top_log_types(df: pd.DataFrame) -> List[Dict[str, Any]]:
    counts = df["severity"].value_counts(dropna=False)
    rows = [{"type": k.upper() if k else "UNKNOWN", "count": int(v)} for k, v in counts.items()] # type: ignore
    return rows

def build_top_frequent(df: pd.DataFrame, top_n: int = 50) -> List[Dict[str, Any]]:
    gp = df["label"].fillna("").astype(str).str.strip()
    counts = gp.value_counts().head(top_n)
    return [{"label": str(k), "count": int(v)} for k, v in counts.items() if k]

def build_pie(df: pd.DataFrame) -> Dict[str, Any]:
    by_sev = [{"label": k.upper() if k else "UNKNOWN", "count": int(v)} # type: ignore
              for k, v in df["severity"].value_counts().items()]
    by_lbl = [{"label": str(k), "count": int(v)}
              for k, v in df["label"].fillna("").astype(str).value_counts().items() if k]
    return {"by_severity": by_sev, "by_label": by_lbl}

def p95(values: List[float]) -> int:
    if not values: return 0
    vs = sorted([v for v in values if pd.notna(v)])
    if not vs: return 0
    idx = int(round(0.95 * (len(vs) - 1)))
    return int(vs[idx])

def build_mini(df: pd.DataFrame) -> Dict[str, Any]:
    def _safe_parse_extracted(val):
        if isinstance(val, dict):
            return val
        if isinstance(val, str):
            s = val.strip()
            try: return json.loads(s)
            except Exception: pass
            try: return ast.literal_eval(s)
            except Exception: return None
        return None

    def _parse_duration_ms(x):
        if x is None or (isinstance(x, float) and np.isnan(x)): return None
        try:
            if isinstance(x, str):
                s = x.strip().lower()
                m = re.match(r'^([0-9][0-9,\.]*)\s*ms$', s)
                if m: return float(m.group(1).replace(',', ''))
                m = re.match(r'^([0-9][0-9,\.]*)\s*s(?:ec|econd|)?$', s)
                if m: return float(m.group(1).replace(',', '')) * 1000.0
                m = re.match(r'^(?:(\d{1,2}):)?(\d{1,2}):(\d{1,2})(?:\.(\d{1,3}))?$', s)
                if m:
                    h = int(m.group(1) or 0); mi = int(m.group(2)); se = int(m.group(3)); ms = int(m.group(4) or 0)
                    return (h*3600 + mi*60 + se) * 1000 + ms
                return float(s.replace(',', ''))
            return float(x)
        except Exception:
            return None

    def _as_int(x):
        try:
            if x is None: return None
            if isinstance(x, str) and x.strip() == '': return None
            return int(float(str(x).replace(',', '').strip()))
        except Exception:
            return None

    total = int(len(df)) or 1
    sev = df.get("severity")
    sev_lower = sev.fillna("").astype(str).str.lower() if sev is not None else pd.Series([""]*len(df))

    label = df.get("label")
    label_lower = label.fillna("").astype(str).str.upper() if label is not None else pd.Series([""]*len(df))

    msg = df.get("message")
    msg_lower = msg.fillna("").astype(str).str.lower() if msg is not None else pd.Series([""]*len(df))

    if "duration_ms" not in df.columns:
        df["duration_ms"] = np.nan

    status_code = []
    is_http = []
    is_db = []
    is_auth_fail = []
    is_perf_warn = []

    HTTP_LABELS = ("HTTP_REQUEST_DETAIL","HTTP_REQUEST_END","HTTP_RESPONSE_RECEIVED",
                   "HTTP_REQUEST_SENDING","HTTP_REQUEST_END_PROCESSING")
    DB_LABELS = ("DATABASE_QUERY","MONGO_QUERY","SQL_QUERY","DB_QUERY","BULK_WRITE_UNIVERSAL")
    AUTH_LABELS = ("AUTHZ_FAILED","AUTH_FAILURE","LOGIN_FAILED","AUTH_FAILED","UNAUTHORIZED")
    PERF_LABELS = ("PERFORMANCE_WARNING","PERF_WARNING","PERFORMANCE_WARN")

    for i, row in df.iterrows():
        ext = _safe_parse_extracted(row.get("data_extracted")) if "data_extracted" in df.columns else None

        if pd.isna(row.get("duration_ms")) and isinstance(ext, dict):
            dur = ext.get("duration_ms") or ext.get("elapsed_ms") or ext.get("latency_ms") or ext.get("duration")
            dms = _parse_duration_ms(dur)
            if dms is not None:
                df.at[i, "duration_ms"] = dms

        sc = None
        if isinstance(ext, dict):
            sc = ext.get("status_code") or ext.get("status") or ext.get("http_status") or ext.get("code")
        status_code.append(_as_int(sc))

        L = str(label_lower.iat[i] if len(label_lower) > i else "").upper() # type: ignore
        is_http.append(L.startswith("HTTP_") or L in HTTP_LABELS or "request" in (msg_lower.iat[i] if len(msg_lower)>i else "")) # type: ignore
        is_db.append(any(k in L for k in DB_LABELS) or (isinstance(ext, dict) and any(k in ext for k in ("sql_command","db","pipeline"))))
        is_auth_fail.append(L in AUTH_LABELS or ("unauthor" in (msg_lower.iat[i] if len(msg_lower)>i else "") or "invalid credential" in (msg_lower.iat[i] if len(msg_lower)>i else ""))) # type: ignore
        is_perf_warn.append(L in PERF_LABELS or (isinstance(ext, dict) and (ext.get("perf_warning") is True)))

    status_code = pd.Series(status_code)

    http_err = ((sev_lower == "error") & pd.Series(is_http)) | (status_code.fillna(0) >= 400)
    requests_err = int(http_err.sum())

    system_err = int(((sev_lower == "error") & (~http_err)).sum())

    perf_warn = int(pd.Series(is_perf_warn).sum())

    auth_fail = int(pd.Series(is_auth_fail).sum())

    db_mask = pd.Series(is_db)
    slow_q_count = 0
    avg_db_ms = None
    if db_mask.any():
        db_df = df[db_mask]
        if not db_df.empty:
            ds = db_df["duration_ms"].dropna().astype(float)
            if not ds.empty:
                avg_db_ms = int(round(ds.mean()))
                slow_q_count = int((ds > 1000).sum())  

    return {
        "api_error_rate_pct": round((requests_err / total) * 100, 1),
        "system_error_rate_pct": round((system_err / total) * 100, 1),
        "slow_queries": int(slow_q_count),
        "auth_failures": int(auth_fail),
        "perf_warnings": int(perf_warn),
        "avg_db_query_ms": int(avg_db_ms) if avg_db_ms is not None else None,
    }


def build_response_time(df: pd.DataFrame) -> Dict[str, Any]:
    def _safe_parse_extracted(val):
        if isinstance(val, dict):
            return val
        if isinstance(val, str):
            s = val.strip()
            try: return json.loads(s)
            except Exception: pass
            try: return ast.literal_eval(s)
            except Exception: return None
        return None

    def _parse_duration_ms(x):
        if x is None or (isinstance(x, float) and np.isnan(x)):
            return None
        try:
            if isinstance(x, str):
                s = x.strip().lower()
                m = re.match(r'^([0-9][0-9,\.]*)\s*ms$', s)
                if m: return float(m.group(1).replace(',', ''))
                m = re.match(r'^([0-9][0-9,\.]*)\s*s(?:ec|econd|)?$', s)
                if m: return float(m.group(1).replace(',', '')) * 1000.0
                m = re.match(r'^(?:(\d{1,2}):)?(\d{1,2}):(\d{1,2})(?:\.(\d{1,3}))?$', s)
                if m:
                    h = int(m.group(1) or 0); mi = int(m.group(2)); se = int(m.group(3)); ms = int(m.group(4) or 0)
                    return (h*3600 + mi*60 + se) * 1000 + ms
                return float(s.replace(',', ''))
            return float(x)
        except Exception:
            return None

    def _norm_url(u):
        if not u: return None
        s = str(u).strip().strip('"').strip("'")
        if " " in s and "/" not in s:
            return None
        # cắt query
        s = s.split("?")[0]
        try:
            if "://" in s:
                s = re.sub(r'^[a-z]+://[^/]+', '', s, flags=re.I)
        except Exception:
            pass
        return s or None

    dur_col = next((c for c in ["duration_ms","latency_ms","elapsed_ms","duration"] if c in df.columns), None)
    url_col = next((c for c in ["url","raw_url","request_info","path","endpoint","api","route"] if c in df.columns), None)

    durations, urls = [], []

    for _, row in df.iterrows():
        d = _parse_duration_ms(row.get(dur_col)) if dur_col else None
        u = row.get(url_col) if url_col else None

        if (d is None or not u) and "data_extracted" in df.columns:
            ext = _safe_parse_extracted(row.get("data_extracted"))
            if isinstance(ext, dict):
                if d is None:
                    d = _parse_duration_ms(
                        ext.get("duration_ms") or ext.get("elapsed_ms") or
                        ext.get("latency_ms")  or ext.get("duration")
                    )
                if not u:
                    u = (ext.get("raw_url") or ext.get("url") or ext.get("request_info") or
                         ext.get("path") or ext.get("endpoint") or ext.get("api") or ext.get("route"))

        u = _norm_url(u)

        if d is None:
            continue
        durations.append(d)
        urls.append(u if u else "(unknown)")

    if not durations:
        return {"p95": 0, "top_apis": []}

    p95_all = p95(durations)

    by_url: Dict[str, list] = {}
    for u, d in zip(urls, durations):
        by_url.setdefault(u, []).append(d)

    top_rows = []
    for u, vals in by_url.items():
        p = p95([v for v in vals if v is not None])
        if p and p > 0:
            top_rows.append({"url": u, "p95_ms": int(p)})

    top_rows.sort(key=lambda r: r["p95_ms"], reverse=True)
    top_rows = top_rows[:50]

    return {"p95": int(p95_all), "top_apis": top_rows}

def build_logs(df: pd.DataFrame, limit: int = 2000) -> List[Dict[str, Any]]:
    out = []
    for _, row in df.head(limit).iterrows():
        ts = row.get("timestamp")
        if isinstance(ts, pd.Timestamp):
            ts = ts.isoformat()
        data_val = row.get("data_extracted")

        if isinstance(data_val, str):
            try:
                data_val = json.loads(data_val)
            except Exception:
                pass
        out.append({
            "timestamp": ts,
            "label": str(row.get("label") or ""),
            "severity": str(row.get("severity") or ""),
            "message": str(row.get("message") or ""),
            "data_extracted": data_val if data_val is not None else None
        })
    return out

def analyze_df(df: pd.DataFrame) -> Dict[str, Any]:
    # df = normalize_df(df)
    analysis = {
        "summary": { "total_logs_today": int(len(df)) },
        "top_log_types": build_top_log_types(df),
        "top_frequent_logs": build_top_frequent(df, top_n=50),
        "pie": build_pie(df),
        "response_time": build_response_time(df),
        "mini": build_mini(df),
        "logs": build_logs(df, limit=3000),
    }
    return analysis