from typing import Any, List, Dict

from .log_label import get_label_log
from helper.calculate_func import _avg_response_time_ms_from_docs, _delta_pct


AUTH_FAIL_LABELS = {
    'AUTHZ_FAILED',
    'AUTH_SCHEME_CHALLENGED',
    'CHALLENGE_RESULT',
}

HTTP_EVENTS = {
    'HTTP_REQUEST_END',
    'HTTP_RESPONSE_RECEIVED',
    'HTTP_REQUEST_END_PROCESSING',
    'HTTP_REQUEST_DETAIL',
}

DATABASES_QUERY = {'DATABASE_QUERY'}

def total_logs_from_docs(docs: List[Dict[str, Any]]) -> int:
    return len(docs)

def auth_failures_count_from_docs(docs: List[Dict[str, Any]]) -> int:
    count = 0
    for it in docs:
        if it.get("label") in AUTH_FAIL_LABELS:
            count += 1
    return count

async def compute_key_metrics(docs_now, docs_prev):
    for doc in docs_now:
        if 'message' in doc:
            label, data = get_label_log(doc['message'])
            doc['label'] = label
            doc['data'] = data

    for doc in docs_prev:
        if 'message' in doc:
            label, data = get_label_log(doc['message'])
            doc['label'] = label
            doc['data'] = data

    total_now = total_logs_from_docs(docs_now)
    total_prev = total_logs_from_docs(docs_prev)

    p95_now = _avg_response_time_ms_from_docs(docs_now, HTTP_EVENTS)
    p95_prev = _avg_response_time_ms_from_docs(docs_prev, HTTP_EVENTS)

    db_avg_now = _avg_response_time_ms_from_docs(docs_now, DATABASES_QUERY)
    db_avg_prev = _avg_response_time_ms_from_docs(docs_prev, DATABASES_QUERY)

    auth_now = auth_failures_count_from_docs(docs_now)
    auth_prev = auth_failures_count_from_docs(docs_prev)


    return {
        "logVolume": {
            "total": int(total_now),
            "changePct": _delta_pct(float(total_now), float(total_prev)) if total_prev else None,
        },
        "dbQuery": {
            "avgMs": float(db_avg_now) if db_avg_now is not None else None,
            "changePct": _delta_pct(float(db_avg_now), float(db_avg_prev)) if (db_avg_now and db_avg_prev) else None,
        },
        "responseTime": {
            "p95Ms": int(p95_now) if p95_now is not None else None,
            "changePct": _delta_pct(float(p95_now), float(p95_prev)) if (p95_now and p95_prev) else None,
        },
        "authFailures": {
            "count": int(auth_now),
            "changePct": _delta_pct(float(auth_now), float(auth_prev)) if auth_prev else None,
        },
    }
