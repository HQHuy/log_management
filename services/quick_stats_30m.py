from .log_label import get_label_log
from helper.calculate_func import _as_int
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger

HTTP_EVENTS_WITH_STATUS = {
    "HTTP_REQUEST_END",
    "HTTP_RESPONSE_RECEIVED",
    "HTTP_REQUEST_END_PROCESSING",
    "HTTP_REQUEST_DETAIL",
}

ERROR_REQUEST = {
    "REQUEST_ERROR",
    "EXTERNAL_API_ERROR"
}

DB_QUERY_LABELS = {'DATABASE_QUERY'}

def _group_requests_errors(docs: List[Dict]):
    buckets: Dict[tuple, Dict[str, Any]] = {}
    total = 0
    for it in docs:
        label = it.get('label')
        data = it.get('data', {})

        is_req_err = False
        if label in ERROR_REQUEST:
            is_req_err = True
        else:
            if label in HTTP_EVENTS_WITH_STATUS:
                status_code = _as_int(data.get('status_code'))
                if status_code is not None and status_code >= 400:
                    is_req_err = True

        if not is_req_err:
            continue

        url = data.get("url") or data.get("request_info") or data.get("path") 
        # print(url)
        # if isinstance(url, str) and ((url.startswith('"') and url.endswith('"')) or (url.startswith("'") and url.endswith("'"))):
        #     url = url[1:-1]

        status = _as_int(data.get("status_code"))
        # logger.info(f'API Loi: {url}:{status}')
        key = (url, status) # Ví dụ: ("http://abc.com", 404) khác với ("http://abc.com", "505").

        bucket = buckets.get(key)

        if not bucket:
            bucket = {"url": url, "status": status, "count": 0, "last_at": None}
            buckets[key] = bucket

        bucket["count"] += 1
        ts: Optional[datetime] = it.get("timestamp")
        if ts is not None:
            iso = ts.isoformat()
            if (bucket["last_at"] is None) or (iso > bucket["last_at"]):
                bucket["last_at"] = iso
        total += 1
        # print(buckets)
    # print(total, list(buckets.values()))
    return total, list(buckets.values())

def _sys_error(docs: List[Dict]):
    buckets = {}
    total = 0
    for it in docs:
        if it.get("severity") != "error":
            continue
        msg = it.get("message") or ""
        label = it.get('label')
        key = msg
        if key not in buckets:
            buckets[key] = {"message": msg, "label": label,"count": 0, "last_at": None}
        buckets[key]["count"] += 1
        ts = it.get("timestamp")
        if isinstance(ts, datetime):
            iso = ts.isoformat()
            if not buckets[key]["last_at"] or iso > buckets[key]["last_at"]:
                buckets[key]["last_at"] = iso
        total += 1
    # print(total, list(buckets.values()))
    return total, list(buckets.values())

def _slow_query(docs: List[Dict]):
    key_list: List[int] = []
    buckets = {}
    for it in docs:
        label = it.get('label') 
        if label not in DB_QUERY_LABELS:
            continue

        data = it.get('data', {})
        dur = data.get("duration_ms")
        # print(dur)
        dur_i = _as_int(dur)
        # print(dur_i)
        key = data.get("sql_command")

        if key not in buckets:
            buckets[key] = {'run_time': dur_i}
        else: 
            if buckets[key]['run_time'] < dur_i:
                buckets[key]['run_time'] = dur_i 
    # print(f'bucket: {buckets}')
    if not buckets:
        return "", 0
    elif len(buckets) == 1:
        key, value = next(iter(buckets.items()))
        return key, value
    else:
        max_item = max(buckets.items(), key=lambda kv: kv[1]['run_time'])

        return max_item[0], max_item[1].get('run_time')

def _perform_warn(docs: List[Dict]):
    total = 0
    buckets: Dict[str, Dict[str, Any]] = {}
    for it in docs:
        if "PERFORMANCE_WARNING" not in (it.get("label") or "").upper():
            continue
        data = it.get("data", {})
        req_info = data.get("request_info") or "(unknown)"
        if req_info not in buckets:
            buckets[req_info] = {
                "label": "PERFORMANCE_WARNING",
                "request_info": req_info,
                "count": 0,
                "last_at": None,
            }
        buckets[req_info]["count"] += 1
        ts = it.get("timestamp")
        if isinstance(ts, datetime):
            iso = ts.isoformat()
            if not buckets[req_info]["last_at"] or iso > buckets[req_info]["last_at"]:
                buckets[req_info]["last_at"] = iso
        total += 1
    return total, list(buckets.values())

async def compute_quick_stats(docs):
    for doc in docs:
        if 'message' in doc:
            label, data = get_label_log(doc['message'])
            doc['label'] = label
            doc['data'] = data
    
    req_total, req_items = _group_requests_errors(docs)
    sys_total, sys_items = _sys_error(docs)
    queries, run_time = _slow_query(docs)
    perf_total, perf_items = _perform_warn(docs)

    return {
        "requests_error_count": req_total,
        "system_error_count": sys_total,
        "slow_query_count": run_time,
        "perf_warning_count": perf_total,
        "details": {
            "requests_errors": req_items,
            "system_errors": sys_items,
            "slow_queries": queries,
            "perf_warnings": perf_items,
        },
    }