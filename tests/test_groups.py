from duplicate_finder.models import DuplicateGroup, FileInfo

def f(path, priority): return FileInfo(path, 10, 1, priority, "x")
def test_keep_protects_all_keep_files():
    group = DuplicateGroup([f("keep/a", -1), f("keep/b", -1), f("else/a", 999)])
    assert [x.path for x in group.suggested_removals] == ["else/a"]
def test_priority_keeper_without_keep():
    group = DuplicateGroup([f("p2/a", 1), f("p1/a", 0), f("other/a", 999)])
    assert group.keeper.path == "p1/a"
    assert {x.path for x in group.suggested_removals} == {"p2/a", "other/a"}
