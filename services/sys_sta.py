from typing import List, Dict, Any, Optional
from datetime import datetime
from .log_label import get_label_log

HTTP_EVENTS_WITH_STATUS = {
    'HTTP_REQUEST_END',
    'HTTP_RESPONSE_RECEIVED',
    'HTTP_REQUEST_END_PROCESSING',
    'HTTP_REQUEST_DETAIL',
}

REQUEST_COUNT_LABEL = 'HTTP_REQUEST_END'

STARTUP_LABEL = 'APP_STARTUP'
SHUTDOWN_LABEL = 'APP_SHUTDOWN'

def _p95(values: List[int]) -> int:
    """Return the 95th percentile (integer). If empty -> 0."""
    if not values:
        return 0
    vs = sorted(values)
    k = (len(vs) - 1) * 0.95
    f = int(k)
    c = min(f + 1, len(vs) - 1)
    if f == c:
        return int(vs[f])
    d0 = vs[f] * (c - k)
    d1 = vs[c] * (k - f)
    return int(round(d0 + d1))

def _avg_response_time_ms_from_docs(docs: List[Dict[str, Any]]):
    """Compute P95 of duration_ms from HTTP events. Kept name for backward-compat with callers/UI."""
    values: List[int] = []
    lbl_lst: List[Any] = []
    for doc in docs:
        if doc['data_extracted'].get('duration_ms'):
            dur = doc['data_extracted'].get('duration_ms')
            if isinstance(dur, (int, float)) and dur > 0:
                values.append(int(dur))

    return _p95(values)

def _api_error_rate_from_docs(docs: List[Dict[str, Any]]):
    total = 0
    errors = 0

    lbl_lst: List[Any] = []
    for doc in docs:
        # lbl_lst.append(f"{doc['label']}")
        if doc['label'] not in HTTP_EVENTS_WITH_STATUS:
            continue
        
        total += 1
        for i in doc['data_extracted'].keys():
            if i == 'status_code':
                status_code = doc['data_extracted'].get(i) 
                if isinstance(status_code, int):
                    if status_code >= 400:
                        errors += 1

    if total == 0:
        return 0.0, 0, 0

    return (errors * 100.0 / total), errors, total
            

    # print(lbl_lst)
    # if len(lbl_lst) == 0:
    #     return 0.0, 0, 0
    
    # for i in lbl_lst:
    #     print(i)
    #     label, code = i.split(": ", 1) 

    #     if label not in HTTP_EVENTS_WITH_STATUS:
    #         continue
        
    #     if isinstance(code, int):
    #         total += 1
    #         if code >= 400:
    #             errors += 1

        
    #     return (errors * 100.0 / total), errors, total

def _system_error_rate_from_docs(docs: List[Dict[str, Any]]) -> tuple[float, int, int]:
    total = 0
    errors = 0

    lbl_lst: List[Any] = []
    for doc in docs:
        lbl_lst.append(f"{doc['severity']}")
    
    for i in lbl_lst:
        total += 1
        if i == 'error':
            errors += 1
    
    if total == 0:
        return 0.0, 0, 0

    return (errors * 100.0 / total), errors, total

def _total_requests_today_from_docs(docs: List[Dict[str, Any]]) -> int:
    count = 0
    lbl_lst: List[Any] = []
    for doc in docs:
        lbl_lst.append(f"{doc['label']}")
        
    for i in lbl_lst:
        # label, _ = i.split(": ", 1)
        if i == REQUEST_COUNT_LABEL:
            count += 1

    return count

def _latest_startup_shutdown_from_docs(docs: List[Dict[str, Any]]) -> str:
    last_label: Optional[str] = None
    last_ts: Optional[datetime] = None
    lbl_lst: List[Any] = []

    for doc in docs:
        lbl_lst.append(f"{doc['label']}: {doc['timestamp']}")
        
    for i in lbl_lst:
        label, ts_str = i.split(": ", 1)
        if label not in (STARTUP_LABEL, SHUTDOWN_LABEL):
            continue

        ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S.%f%z")
        if isinstance(ts, datetime):
            if last_ts is None or ts > last_ts:
                last_ts = ts
                last_label = label

    if last_label is None:
        return 'unknown'
    if last_label == SHUTDOWN_LABEL:
        return 'offline'
    return 'online'


async def compute_system_status(docs):
    cln_docs = []

    for doc in docs:
        datas = doc['docs']

        for data in datas: 
            label, data_extracted = get_label_log(data.get('message', ''))
            labeled_value = {
                **data,
                "label": label,
                "data_extracted": data_extracted
            }
            cln_docs.append(labeled_value)
    
    # print(cln_docs) 
    now = datetime.now()

    status = _latest_startup_shutdown_from_docs(cln_docs)
    total_today = _total_requests_today_from_docs(cln_docs)
    avg_rt = _avg_response_time_ms_from_docs(cln_docs)
    api_err_pct, _, _ = _api_error_rate_from_docs(cln_docs)
    # _api_error_rate_from_docs(cln_docs)
    sys_err_pct, _, _ = _system_error_rate_from_docs(cln_docs)

    return {
        'status': status,  # 'healthy' | 'offline' | 'online' | 'unknown'
        'total_requests_today': int(total_today),
        'avg_response_time': int(avg_rt),  # p95 ms
        'error_rate_api_percent': round(api_err_pct, 2),
        'error_system_rate_percent': round(sys_err_pct, 2),
        'last_update': now.isoformat(),
    }