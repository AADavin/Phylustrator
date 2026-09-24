"""branch_spindles: a lens on the branch, on a coloured stretch that fades into the branch."""
from phylustrator.trees import branch_spindles, loads, plot


def test_spindle_draws_lens_and_gradients():
    tree = loads("((A:1,B:1)n1:1,(C:1.5,D:1.5)n2:0.5)r:0.2;")
    svg = (plot(tree) + branch_spindles([{"node": "n1", "x": 0.7, "color": "#e07b00"},
                                         ("D", None, "#2e8b57")])).as_svg()
    assert svg.count("fill=\"#e07b00\"") >= 1 and svg.count("fill=\"#2e8b57\"") >= 1   # one lens per mark
    assert svg.count("<linearGradient") >= 4              # two fades per mark
    assert "#e07b00" in svg and "#2e8b57" in svg


def test_spindle_radial_and_missing_node():
    tree = loads("((A:1,B:1)n1:1,(C:1.5,D:1.5)n2:0.5)r:0.2;")
    svg = (plot(tree, layout="radial") + branch_spindles([("n2", 1.0, None), ("nope", 1.0, None)])).as_svg()
    assert svg.count("<linearGradient") == 2           # one mark drawn, the missing node skipped
