"""Tree model: traversal, leaves, lookup, and the stem-excluding depth."""

import pytest

from phylustrator.trees import dumps, loads


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


def test_prune_preserves_branch_distances_and_the_original_tree():
    newick = "(((A:1,B:1):1,C:2):1,(D:1.5,E:1.5):1.5);"
    tree = loads(newick)
    original = dumps(tree)
    small = tree.prune(keep={"A", "C", "D"})
    assert dumps(small).strip() == "((A:2,C:2):1,D:3);"
    assert dumps(tree) == original
    assert all(small.depth(leaf) == 3 for leaf in small.leaves)
    assert {id(node) for node in small.walk()}.isdisjoint(id(node) for node in tree.walk())
    for node in small.walk():
        for child in node.children:
            assert child.parent is node
    assert small.root.parent is None


def test_prune_keeps_names_and_leaf_order():
    tree = loads("((A:1,B:1)ab:2,(C:1,D:1)cd:2)root:0.5;")
    small = tree.prune(keep=["C", "B", "A"])
    assert dumps(small).strip() == "((A:1,B:1)ab:2,C:3)root:0.5;"
    assert [leaf.name for leaf in small.leaves] == ["A", "B", "C"]


def test_prune_one_leaf_collapses_the_root_and_keeps_the_total_stem():
    small = loads("((A:1,B:1)ab:2,C:3)root:0.5;").prune(keep={"A"})
    assert small.root.is_leaf and small.root.name == "A"
    assert small.root.length == 3.5
    assert small.root.parent is None


def test_prune_all_leaves_returns_an_independent_copy():
    tree = loads("(A:1,B:2)root:0.5;")
    small = tree.prune(keep=(leaf.name for leaf in tree.leaves))
    assert dumps(small) == dumps(tree)
    small.find("A").length = 10
    assert tree.find("A").length == 1


@pytest.mark.parametrize("keep", [set(), {"missing"}, {"A", "root"}])
def test_prune_requires_a_nonempty_set_of_existing_leaf_names(keep):
    with pytest.raises(ValueError, match="keep|leaf"):
        loads("(A:1,B:1)root;").prune(keep=keep)


def test_prune_duplicate_leaf_names_keeps_all_occurrences():
    small = loads("((A:1,B:1):1,A:2);").prune(keep={"A"})
    assert dumps(small).strip() == "(A:2,A:2);"
