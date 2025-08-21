from typing import List, Dict, Any, Optional


# Tính 95th percentile (p95) từ một danh sách số
def _p95(values: List[int]):
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

# Tính p95 của thời gian phản hồi (response time) từ danh sách log/documents
def _avg_response_time_ms_from_docs(docs: List[Dict[str, Any]], condition):
    values: List[int] = []
    for it in docs:
        if it['label'] in condition:
            data = it.get('data', {})
            dur = data.get('duration_ms')
            if isinstance(dur, (int, float)) and dur > 0:
                values.append(int(dur))
    return _p95(values)


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