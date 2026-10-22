"""Extract a timestamp from an image file name."""
from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

# 20261022_151528 / 2026-10-22 15.15.28 / 20261022151528123 ...
_DATETIME_RE = re.compile(
    r"(?<!\d)(20\d{2}|19\d{2})[-_.]?(0[1-9]|1[0-2])[-_.]?(0[1-9]|[12]\d|3[01])"
    r"[-_.T ]?([01]\d|2[0-3])[-_.:]?([0-5]\d)[-_.:]?([0-5]\d)(\d{0,3})(?!\d)"
)
# Unix epoch in milliseconds (13 digits) or seconds (10 digits), e.g. mmexport1666422928000.jpg
_EPOCH_RE = re.compile(r"(?<!\d)(1\d{12}|1\d{9})(?!\d)")


def extract_timestamp(stem: str) -> Optional[datetime]:
    """Return the timestamp encoded in ``stem`` or ``None`` if there is none."""
    for m in _DATETIME_RE.finditer(stem):
        year, month, day, hour, minute, second, frac = m.groups()
        try:
            value = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))
        except ValueError:
            continue
        if frac:
            value = value.replace(microsecond=int(frac.ljust(6, "0")))
        return value

    m = _EPOCH_RE.search(stem)
    if m:
        raw = m.group(1)
        seconds = int(raw) / 1000 if len(raw) == 13 else int(raw)
        try:
            return datetime.fromtimestamp(seconds)
        except (OverflowError, OSError, ValueError):
            return None
    return None
