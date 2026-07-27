"""Newick I/O — validated *differentially against ete3* so the hand-rolled parser provably matches a
battle-tested one, plus round-trip stability. ete3 is a test-only dependency (``pip install -e .[dev]``);
the differential tests skip if it is absent."""

import pytest

from phylustrator.trees import dumps, loads

# Trees with an explicit length on every non-root branch (topology *and* lengths comparable).
# NB: quoted labels are tested separately (test_quoted_label_preserved) — ete3 format=1 keeps the
# literal quote characters in the name, whereas we correctly unquote, so they are not comparable here.
LENGTH_NEWICKS = [
    "(A:1,B:2)R;",
    "((A:1,B:1)C:2,D:3)R:0.5;",
    "((A:0.1,B:0.2)X:0.3,(C:0.4,D:0.5)Y:0.6)R;",
    "(A:1.5e-2,B:2E1)R;",
]

# Plus length-less trees (topology only — ete3 fabricates missing lengths as 1.0; we keep 0.0).
TOPOLOGY_NEWICKS = LENGTH_NEWICKS + [
    "(A,B,C)R;",
    "((A,B),(C,(D,E)));",
    "((A,B)C,D)R[a comment];",
]


def _clades(tree):
    """{frozenset(descendant leaf names): node} for every node in a phylustrator tree."""
    under: dict[int, set] = {}
    for node in tree.walk(order="postorder"):
        under[id(node)] = ({node.name} if node.is_leaf
                           else set().union(*(under[id(c)] for c in node.children)))
    return {frozenset(under[id(n)]): n for n in tree.walk()}


def _ete_clades(t):
    return {frozenset(n.get_leaf_names()): n for n in t.traverse()}


@pytest.mark.parametrize("nwk", TOPOLOGY_NEWICKS)
def test_topology_matches_ete3(nwk):
    ete3 = pytest.importorskip("ete3")
    assert set(_clades(loads(nwk))) == set(_ete_clades(ete3.Tree(nwk, format=1)))


@pytest.mark.parametrize("nwk", LENGTH_NEWICKS)
def test_lengths_match_ete3(nwk):
    ete3 = pytest.importorskip("ete3")
    mine = {c: round(n.length, 9) for c, n in _clades(loads(nwk)).items()}
    theirs = {c: round(n.dist, 9) for c, n in _ete_clades(ete3.Tree(nwk, format=1)).items()}
    # Compare non-root branches (ete3 and we differ on the root-stem convention by design).
    root = frozenset().union(*mine) if mine else frozenset()
    assert {c: v for c, v in mine.items() if c != root} == {c: v for c, v in theirs.items() if c != root}


@pytest.mark.parametrize("nwk", TOPOLOGY_NEWICKS)
def test_roundtrip_stable(nwk):
    once = dumps(loads(nwk))
    twice = dumps(loads(once))
    assert once == twice


def test_quoted_label_preserved():
    tree = loads("('Homo sapiens':1,B:2)R;")
    assert tree.find("Homo sapiens") is not None
    assert "'Homo sapiens'" in dumps(tree)
