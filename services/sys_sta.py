from __future__ import annotations

from datetime import datetime
from typing import Optional, Dict, Any, List

from .log_label import get_label_log
from helper.calculate_func import _avg_response_time_ms_from_docs

# Labels considered as HTTP request lifecycle events (keep in sync with key_metrics)
HTTP_EVENTS_WITH_STATUS = {
    'HTTP_REQUEST_END',
    'HTTP_RESPONSE_RECEIVED',
    'HTTP_REQUEST_END_PROCESSING',
    'HTTP_REQUEST_DETAIL',
}

REQUEST_COUNT_LABEL = 'HTTP_REQUEST_END'

STARTUP_LABEL = 'APP_STARTUP'
SHUTDOWN_LABEL = 'APP_SHUTDOWN'


def _api_error_rate_from_docs(docs: List[Dict[str, Any]]) -> tuple[float, int, int]:
    total = 0
    errors = 0
    for it in docs:
        if it.get('label') not in HTTP_EVENTS_WITH_STATUS:
            continue
        status_code = it.get('data', {}).get('status_code')
        if isinstance(status_code, int):
            total += 1
            if status_code >= 400:
                errors += 1
    if total == 0:
        return 0.0, 0, 0
    return (errors * 100.0 / total), errors, total


def _system_error_rate_from_docs(docs: List[Dict[str, Any]]) -> tuple[float, int, int]:
    total = 0
    errors = 0
    for it in docs:
        total += 1
        sev = it.get('severity')
        if isinstance(sev, str) and sev == 'error':
            errors += 1
    if total == 0:
        return 0.0, 0, 0
    return (errors * 100.0 / total), errors, total


def _total_requests_today_from_docs(docs: List[Dict[str, Any]]) -> int:
    count = 0
    for it in docs:
        if it.get('label') == REQUEST_COUNT_LABEL:
            count += 1
    return count


def _latest_startup_shutdown_from_docs(docs: List[Dict[str, Any]]) -> str:
    last_label: Optional[str] = None
    last_ts: Optional[datetime] = None
    for it in docs:
        lbl = it.get('label')
        if lbl not in (STARTUP_LABEL, SHUTDOWN_LABEL):
            continue
        ts = it.get('timestamp')
        if isinstance(ts, datetime):
            if last_ts is None or ts > last_ts:
                last_ts = ts
                last_label = lbl
    if last_label is None:
        return 'unknown'  # TODO: Ping to server to check status
    if last_label == SHUTDOWN_LABEL:
        return 'offline'
    return 'online'


async def compute_system_status(docs):
    # print(docs[0])
    count = 0
    
    for doc in docs:
        if 'message' in doc:
            label, data = get_label_log(doc['message'])
            doc['label'] = label
            doc['data'] = data

    print(docs[0])

    now_utc = datetime.now()
    status = _latest_startup_shutdown_from_docs(docs)
    # print(status)
    total_today = _total_requests_today_from_docs(docs)
    # print(total_today)
    avg_rt = _avg_response_time_ms_from_docs(docs, HTTP_EVENTS_WITH_STATUS)
    # print(total_today)
    api_err_pct, _, _ = _api_error_rate_from_docs(docs)
    # print(api_err_pct)
    sys_err_pct, _, _ = _system_error_rate_from_docs(docs)
    # print(sys_err_pct)

    return {
        'status': status,  # 'healthy' | 'offline' | 'online' | 'unknown'
        'total_requests_today': int(total_today),
        'avg_response_time': int(avg_rt),  # p95 ms
        'error_rate_api_percent': round(api_err_pct, 2),
        'error_system_rate_percent': round(sys_err_pct, 2),
        'last_update': now_utc.isoformat(),
    }