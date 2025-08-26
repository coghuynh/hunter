

from typing import Optional

def _strip_or_none(s: Optional[str]) -> Optional[str]:
    return s.strip() if isinstance(s, str) else None
