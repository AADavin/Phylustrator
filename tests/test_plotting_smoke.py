import pytest


def test_radial_plot_transfers_smoke():
    """RadialTreeDrawer.plot_transfers should not crash (regression: radius vs rad)."""
    from ete3 import Tree
    from phylustrator.drawing import RadialTreeDrawer, TreeStyle

    t = Tree("((A:1,B:1):1,C:2);", format=1)
    drawer = RadialTreeDrawer(t, style=TreeStyle(width=400, height=400, radius=120))

    transfers = [{"from": "A", "to": "C", "freq": 0.5}]
    drawer.plot_transfers(transfers)

    # Legend should not crash (direction swatches are the default now)
    drawer.add_transfer_legend(low=0.1, high=1.0)


def test_vertical_plot_transfers_smoke():
    """VerticalTreeDrawer.plot_transfers should not crash."""
    from ete3 import Tree
    from phylustrator.drawing import VerticalTreeDrawer, TreeStyle

    t = Tree("((A:1,B:1):1,C:2);", format=1)
    drawer = VerticalTreeDrawer(t, style=TreeStyle(width=400, height=400))
    transfers = [{"from": "A", "to": "C", "freq": 0.5}]
    drawer.plot_transfers(transfers)

    # Legend should not crash
    drawer.add_transfer_legend(low=0.1, high=1.0)


def test_add_legend_smoke():
    """BaseDrawer.add_legend should exist and place a box without crashing."""
    from ete3 import Tree
    from phylustrator.drawing import VerticalTreeDrawer, TreeStyle

    t = Tree("(A:1,B:1);", format=1)
    drawer = VerticalTreeDrawer(t, style=TreeStyle(width=400, height=400))
    drawer.add_legend(
        title="Metabolism",
        mapping={"aerobic": "#ff0000", "anaerobic": "#0000ff"},
        position="top-left",
        symbol="square",
    )
