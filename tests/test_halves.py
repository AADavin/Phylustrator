"""node_halves: a disc at a node, split in two, each half a colour or open."""
from phylustrator.trees import loads, node_halves, plot


def test_halves_draw_two_sectors_per_node():
    tree = loads("((A:1,B:1)n1:1,(C:1.5,D:1.5)n2:0.5)r:0.2;")
    svg = (plot(tree) + node_halves({"n1": ("#c9a227", "#4682b4"), "n2": ("#c9a227", None),
                                     "nope": (None, None)})).as_svg()
    assert svg.count('fill="#c9a227"') == 2 and svg.count('fill="#4682b4"') == 1
    assert svg.count('fill="#ffffff"') >= 1                # the open half of n2; the missing node is skipped
