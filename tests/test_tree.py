"""Tree model: traversal, leaves, lookup, and the stem-excluding depth."""

from phylustrator import loads


def test_walk_orders():
    tree = loads("((A:1,B:1)C:1,D:1)R;")
    pre = [n.name for n in tree.walk("preorder")]
    post = [n.name for n in tree.walk("postorder")]
    assert pre[0] == "R"          # a node precedes its children
    assert post[-1] == "R"        # ...and follows them in postorder
    assert set(pre) == set(post) == {"R", "C", "A", "B", "D"}


def test_leaves_left_to_right():
    tree = loads("((A,B)C,D)R;")
    assert [leaf.name for leaf in tree.leaves] == ["A", "B", "D"]


def test_find():
    tree = loads("((A,B)C,D)R;")
    assert tree.find("C").name == "C"
    assert tree.find("absent") is None


def test_depth_excludes_root_stem():
    # Root R carries a stem of 5; leaf A sits at C(1) + A(2) below the crown.
    tree = loads("((A:2,B:2)C:1,D:3)R:5;")
    assert tree.depth(tree.root) == 0.0    # the stem does not shift the tree
    assert tree.depth(tree.find("A")) == 3.0
    assert tree.root.length == 5.0         # ...but the stem is still stored
