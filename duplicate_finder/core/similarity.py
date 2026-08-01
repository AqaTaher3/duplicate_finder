from __future__ import annotations
import re
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from duplicate_finder.models import DuplicateGroup, FileInfo

def normalize_name(path: str) -> str:
    value = Path(path).stem.casefold()
    value = re.sub(r"\b(copy|duplicate|final|new|نسخه|کپی)\b", "", value)
    value = re.sub(r"\s*\(\d+\)$", "", value)
    value = re.sub(r"[\W_]+", " ", value, flags=re.UNICODE)
    return re.sub(r"\s+", " ", value).strip()

def find_similar(files: list[FileInfo], threshold: float) -> list[DuplicateGroup]:
    buckets: dict[tuple[str, str], list[FileInfo]] = defaultdict(list)
    for item in files:
        name = normalize_name(item.path)
        buckets[(Path(item.path).suffix.casefold(), name[:1])].append(item)
    groups: list[DuplicateGroup] = []
    for bucket in buckets.values():
        if len(bucket) > 500:
            continue
        used: set[str] = set()
        for index, left in enumerate(bucket):
            if left.path in used:
                continue
            left_name = normalize_name(left.path)
            matches = [left]
            for right in bucket[index + 1:]:
                if right.path in used:
                    continue
                if SequenceMatcher(None, left_name, normalize_name(right.path)).ratio() >= threshold:
                    matches.append(right)
                    used.add(right.path)
            if len(matches) > 1:
                used.add(left.path)
                matches.sort(key=lambda x: (x.priority, len(x.path), x.path.casefold()))
                groups.append(DuplicateGroup(matches, exact=False))
    return groups
