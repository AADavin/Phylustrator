"""Tests for the ZOMBI2 integration (reading zombi2 output and drawing reconciliations).

The fixture writes a minimal folder in ZOMBI2's ``Genomes.write()`` layout to ``tmp_path``,
so the tests are self-contained and do not depend on zombi2 being installed.
"""

import pytest

from phylustrator import zombi2
from phylustrator.drawing import VerticalTreeDrawer

# Ultrametric species tree, tips at t=2: root(0) -> AB(1) -> {A,B}(2); root -> C(2)
SPECIES_TREE = "((A:1,B:1)AB:1,C:2)root;\n"

# family 1: originates at the root (no branch -> not drawn), duplicates on AB, transfers
# C -> B at t=1.5 (both branches alive), and is lost in A.
FAM1 = (
    "time\tevent\tbranch\tdonor\trecipient\tnodes\n"
    "0\tO\troot\t\t\torigin=g1\n"
    "0.5\tD\tAB\t\t\tparent=g2;left=g3;right=g4\n"
    "1.5\tT\tC\tC\tB\tparent=g5;donor_copy=g6;transfer_copy=g7\n"
    "1.8\tL\tA\t\t\tlost=g8\n"
)
# family 2: originates on branch C (drawable), duplicates and is lost there. No transfer.
FAM2 = (
    "time\tevent\tbranch\tdonor\trecipient\tnodes\n"
    "0.8\tO\tC\t\t\torigin=g10\n"
    "1.2\tD\tC\t\t\tparent=g10;left=g11;right=g12\n"
    "1.5\tL\tC\t\t\tlost=g11\n"
)


@pytest.fixture
def zdir(tmp_path):
    """A minimal ZOMBI2 output folder."""
    (tmp_path / "species_tree.nwk").write_text(SPECIES_TREE)
    ev = tmp_path / "gene_family_events"
    ev.mkdir()
    (ev / "1_events.tsv").write_text(FAM1)
    (ev / "2_events.tsv").write_text(FAM2)
    return tmp_path


@pytest.fixture
def data(zdir):
    return zombi2.load(zdir)


def test_load_annotates_species_tree_times(data):
    byname = {n.name: n for n in data.species_tree.traverse()}
    assert {"A", "B", "C", "AB", "root"} <= set(byname)
    assert byname["root"].time_from_origin == 0.0          # root at t=0
    assert abs(byname["AB"].time_from_origin - 1.0) < 1e-9  # cumulative branch length
    assert abs(byname["A"].time_from_origin - 2.0) < 1e-9


def test_families_in_natural_order(data):
    assert data.families() == ["1", "2"]


def test_events_and_transfers_parsed(data):
    assert set(data.events["family"]) == {"1", "2"}
    assert len(data.transfers) == 1
    row = data.transfers.iloc[0]
    assert row["from"] == "C" and row["to"] == "B" and abs(row["time"] - 1.5) < 1e-9


def test_event_markers_placed_at_true_time(data):
    # family 1: O@root has no branch (skipped); D@AB at t=0.5 -> where 0.5; L@A at t=1.8 -> 0.8
    m = {s["event_type"]: s for s in zombi2.event_markers(data, "1")}
    assert set(m) == {"D", "L"}
    assert abs(m["D"]["where"] - 0.5) < 1e-9
    assert abs(m["L"]["where"] - 0.8) < 1e-9
    for s in m.values():
        assert 0.0 <= s["where"] <= 1.0 and s["branch"].up is not None


def test_event_markers_include_origination_on_a_branch(data):
    # family 2 originates on branch C, so O is drawable here
    assert {s["event_type"] for s in zombi2.event_markers(data, "2")} == {"O", "D", "L"}


def test_transfer_records_per_family(data):
    assert len(zombi2.transfer_records(data, "1")) == 1
    assert zombi2.transfer_records(data, "2") == []


def test_family_accepts_int_or_str(data):
    assert len(zombi2.event_markers(data, 1)) == len(zombi2.event_markers(data, "1"))


def test_draw_reconciliation_returns_drawer_and_svg(data, tmp_path):
    v = zombi2.draw_reconciliation(data, "1")
    assert isinstance(v, VerticalTreeDrawer)
    out = tmp_path / "fam1.svg"
    v.save_svg(out)
    assert "svg" in out.read_text() and out.stat().st_size > 500


def test_draw_accepts_a_folder_path(zdir, tmp_path):
    v = zombi2.draw_reconciliation(str(zdir), "2")
    v.save_svg(tmp_path / "fam2.svg")
    assert (tmp_path / "fam2.svg").exists()


def test_load_missing_species_tree_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        zombi2.load(tmp_path / "does_not_exist")
