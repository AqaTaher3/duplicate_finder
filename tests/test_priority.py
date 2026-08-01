from pathlib import Path
from duplicate_finder.core.priority import PriorityResolver

def test_keep_has_absolute_priority(tmp_path: Path):
    keep = tmp_path / "keep"; p1 = tmp_path / "p1"; other = tmp_path / "other"
    keep.mkdir(); p1.mkdir(); other.mkdir()
    resolver = PriorityResolver(str(keep), [str(p1)])
    assert resolver.value(str(keep / "a.txt")) == -1
    assert resolver.value(str(p1 / "a.txt")) == 0
    assert resolver.value(str(other / "a.txt")) == 999
