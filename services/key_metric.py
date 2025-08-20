from datetime import timedelta, datetime
from typing import Any, Optional, List, Dict

from .sys_sta import _p95
from .log_label import get_label_log


AUTH_FAIL_LABELS = {
    'AUTHZ_FAILED',
    'AUTH_SCHEME_CHALLENGED',
    'CHALLENGE_RESULT',
}

def _as_int(x: Any) -> Optional[int]:
    if isinstance(x, (int, float)):
        return int(x)
    if isinstance(x, str) and x.isdigit():
        return int(x)
    return None

def _delta_pct(curr: Optional[float], prev: Optional[float]) -> Optional[float]:
    if curr is None or prev is None or prev == 0:
        return None
    return ((curr - prev) / prev) * 100.0

def total_logs_from_docs(docs: List[Dict[str, Any]]) -> int:
    total = 0

    for doc in docs:
        total += 1

    return total

async def compute_key_metrics(docs_now, docs_prev):
    cln_docs_now = []
    cln_docs_prev = []
    i = 0

    for doc in docs_now:
        datas = doc['docs']

        for data in datas: 
            i+=1
            print(i)
            label, data_extracted = get_label_log(data.get('message', ''))
            labeled_value = {
                **data,
                "label": label,
                "data_extracted": data_extracted
            }
        cln_docs_now.append(labeled_value)
    
    print(cln_docs_now)
    i=0

    for doc in docs_prev:
        datas = doc['docs']

        for data in datas: 
            i+=1
            print(i)
            label, data_extracted = get_label_log(data.get('message', ''))
            labeled_value = {
                **data,
                "label": label,
                "data_extracted": data_extracted
            }
        cln_docs_prev.append(labeled_value) 

    print(cln_docs_prev)   

    # total_now = total_logs_from_docs(docs_now)
    # total_prev = total_logs_from_docs(docs_prev)

    # p95_now = _avg_response_time_ms_from_docs(docs_now)
    # p95_prev = _avg_response_time_ms_from_docs(docs_prev)

    # db_avg_now = db_query_avg_ms_from_docs(docs_now)
    # db_avg_prev = db_query_avg_ms_from_docs(docs_prev)

    # auth_now = auth_failures_count_from_docs(docs_now)
    # auth_prev = auth_failures_count_from_docs(docs_prev)


    # return {
    #     "window": window,
    #     "logVolume": {
    #         "total": int(total_now),
    #         "changePct": _delta_pct(float(total_now), float(total_prev)) if total_prev else None,
    #     },
    #     "dbQuery": {
    #         "avgMs": float(db_avg_now) if db_avg_now is not None else None,
    #         "changePct": _delta_pct(float(db_avg_now), float(db_avg_prev)) if (db_avg_now and db_avg_prev) else None,
    #     },
    #     "responseTime": {
    #         "p95Ms": int(p95_now) if p95_now is not None else None,
    #         "changePct": _delta_pct(float(p95_now), float(p95_prev)) if (p95_now and p95_prev) else None,
    #     },
    #     "authFailures": {
    #         "count": int(auth_now),
    #         "changePct": _delta_pct(float(auth_now), float(auth_prev)) if auth_prev else None,
    #     },
    # }
    pass