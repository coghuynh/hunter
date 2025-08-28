

from typing import Optional
    
from datetime import datetime
from neo4j.time import DateTime, Date, Time

def _strip_or_none(s: Optional[str]) -> Optional[str]:
    return s.strip() if isinstance(s, str) else None

def _norm_str(x: Optional[str]) -> Optional[str]:
    if x is None:
        return None
    s = str(x).strip()
    return s if s else None

def jsonify_safe(data):
    if isinstance(data, dict):
        return {k: jsonify_safe(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [jsonify_safe(v) for v in data]
    else:
        return _serialize_datetime(data)
    

def _serialize_datetime(dt):
    if isinstance(dt, datetime):
        return dt.isoformat()
    if isinstance(dt, (DateTime, Date, Time)):
        return dt.iso_format()   # neo4j types have .iso_format()
    return dt