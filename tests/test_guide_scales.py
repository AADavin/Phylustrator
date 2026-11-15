"""Continuous and categorical guides can follow the same set of layers."""

import xml.etree.ElementTree as ET
from collections.abc import Callable

import pytest

from phylustrator import Style
from phylustrator.trees import color_branches, colorbar, legend, loads, plot, ring, tip_track
from phylustrator.trees.figure import Figure

VALUES = {"a": 0.1, "b": 0.9, "c": 0.5, "x": 0.4, "r": 0.3}
GROUPS = {"a": "one", "b": "two", "c": "one"}
PALETTE = {"one": "#E69F00", "two": "#56B4E9"}


def _figure(layout: str = "rectangular") -> Figure:
    tree = loads("((a:1,b:1)x:1,c:2)r;")
    return plot(tree, layout=layout, style=Style(width=600, height=480, margin=80, margin_right=180))


def _texts(svg: str) -> list[str]:
    return ["".join(node.itertext()) for node in ET.fromstring(svg).iter("{http://www.w3.org/2000/svg}text")]


@pytest.mark.parametrize("track,layout", [(tip_track, "rectangular"), (ring, "radial")])
@pytest.mark.parametrize("categorical_first", [False, True])
def test_mixed_layers_keep_both_guides(track: Callable, layout: str, categorical_first: bool) -> None:
    figure = _figure(layout)
    branches = color_branches(VALUES, limits=(0, 1), gradient=False)
    categories = track(GROUPS, palette=PALETTE)
    figure = figure + categories + branches if categorical_first else figure + branches + categories
    svg = (figure + colorbar("Branch values") + legend("Groups", loc="right")).as_svg()
    texts = _texts(svg)
    assert "Branch values" in texts
    assert "0.00" in texts
    assert "1.00" in texts
    assert "Groups" in texts
    assert "one" in texts
    assert "two" in texts
    assert "linearGradient" in svg


def test_colorbar_uses_the_last_continuous_scale() -> None:
    svg = (
        _figure()
        + color_branches(VALUES, limits=(0, 1), gradient=False)
        + tip_track(VALUES, cmap="magma")
        + tip_track(GROUPS, palette=PALETTE)
        + colorbar("Latest values")
    ).as_svg()
    texts = _texts(svg)
    assert "Latest values" in texts
    assert "0.10" in texts
    assert "0.90" in texts
    assert "0.00" not in texts
    assert "1.00" not in texts


def test_legend_uses_the_last_categorical_scale() -> None:
    svg = (
        _figure()
        + tip_track(GROUPS, palette=PALETTE)
        + tip_track({"a": "new group"}, palette={"new group": "#123456"})
        + color_branches(VALUES, limits=(0, 1), gradient=False)
        + legend("Latest groups", loc="right")
    ).as_svg()
    texts = _texts(svg)
    assert "Latest groups" in texts
    assert "new group" in texts
    assert "one" not in texts
    assert "two" not in texts


def test_explicit_legend_entries_override_the_recorded_scale() -> None:
    svg = (
        _figure()
        + tip_track(GROUPS, palette=PALETTE)
        + color_branches(VALUES, limits=(0, 1), gradient=False)
        + legend(entries={"custom group": "#123456"}, loc="right")
    ).as_svg()
    texts = _texts(svg)
    assert "custom group" in texts
    assert "one" not in texts
    assert "two" not in texts


def test_guides_without_a_matching_scale_draw_nothing() -> None:
    svg = (_figure() + colorbar("No values") + legend("No groups")).as_svg()
    texts = _texts(svg)
    assert "No values" not in texts
    assert "No groups" not in texts


def test_custom_layer_can_clear_recorded_scales() -> None:
    def clear_scales(canvas, tree, layout, style) -> None:
        # Keep the existing scale attribute available to custom layers.
        assert canvas.scale["kind"] == "categorical"
        canvas.scale = None

    svg = (
        _figure()
        + color_branches(VALUES, limits=(0, 1), gradient=False)
        + tip_track(GROUPS, palette=PALETTE)
        + clear_scales
        + colorbar("Cleared values")
        + legend("Cleared groups")
    ).as_svg()
    texts = _texts(svg)
    assert "Cleared values" not in texts
    assert "Cleared groups" not in texts
