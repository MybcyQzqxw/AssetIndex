"""Parse the asset number out of OCR results of an asset label photo."""
from __future__ import annotations

import re
from typing import List, Optional, Sequence

_COLON = r"[:：;；.,，。、]?"
_VALUE = r"([0-9A-Za-z][0-9A-Za-z\-_]{3,})"

# 资产编号 + value on the same text line (OCR sometimes drops/misreads single glyphs,
# so a few looser variants follow).
_LABEL_PATTERNS = [
    re.compile(r"资\s*产\s*编\s*号\s*" + _COLON + r"\s*" + _VALUE),
    re.compile(r"产\s*编\s*号\s*" + _COLON + r"\s*" + _VALUE),
    re.compile(r"资\s*产\s*编\s*" + _COLON + r"\s*" + _VALUE),
    re.compile(r"编\s*号\s*" + _COLON + r"\s*" + _VALUE),
]
_LABEL_ONLY_RE = re.compile(r"(资\s*产\s*)?编\s*号\s*[:：;；]?\s*$")
_VALUE_ONLY_RE = re.compile(r"^\s*" + _VALUE + r"\s*$")
_KEYWORD_RE = re.compile(r"资\s*产\s*(名\s*称|编\s*号)|所\s*属\s*单\s*位|资产")
_LONG_DIGITS_RE = re.compile(r"(?<!\d)\d{8,}(?!\d)")
_OCR_DIGIT_FIX = str.maketrans({"O": "0", "o": "0", "I": "1", "l": "1", "|": "1"})


def _clean_value(value: str) -> str:
    value = value.strip("-_")
    letters_digits = [c for c in value if c.isalnum()]
    digits = sum(c.isdigit() for c in letters_digits)
    # Label numbers are numeric; repair common O/0, I/1 confusions when mostly digits.
    if letters_digits and digits / len(letters_digits) >= 0.7:
        value = value.translate(_OCR_DIGIT_FIX)
    return value


def parse_asset_number(texts: Sequence[str]) -> Optional[str]:
    """Find the value after “资产编号” in OCR text lines (top-to-bottom order)."""
    lines: List[str] = [t.replace(" ", "").replace("\u3000", "") for t in texts if t and t.strip()]

    for pattern in _LABEL_PATTERNS:
        for line in lines:
            m = pattern.search(line)
            if m:
                return _clean_value(m.group(1))

    # Label and value recognised as separate text boxes.
    for i, line in enumerate(lines[:-1]):
        if _LABEL_ONLY_RE.search(line):
            m = _VALUE_ONLY_RE.match(lines[i + 1])
            if m:
                return _clean_value(m.group(1))

    # Label glyphs unreadable, but the other label fields prove this is an asset tag:
    # take the long digit run.
    if any(_KEYWORD_RE.search(line) for line in lines):
        for line in lines:
            m = _LONG_DIGITS_RE.search(line)
            if m:
                return m.group(0)
    return None
