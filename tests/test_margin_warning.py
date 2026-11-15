"""The margin suggested by a guide warning should make the guide fit."""

import re
import warnings

import pytest

from phylustrator import Style
from phylustrator.trees import legend, loads, note, plot, ring


def _render(margin: float, preceding_note: bool) -> tuple[str, list[str]]:
    tree = loads("((a:1,b:1)x:1,(c:1,d:1)y:1)r;")
    groups = {"a": "Group one long name", "b": "Group one long name", "c": "other", "d": "other"}
    palette = {"Group one long name": "#336699", "other": "#cccccc"}
    style = Style(width=426, height=350, margin=16, margin_right=margin, font_size=8)
    figure = plot(tree, layout="radial", style=style, skeleton=False, stem=False) + ring(groups, palette=palette)
    if preceding_note:
        figure += note("First", loc="right", size=7.5)
    figure += legend(loc="right", size=7.5, swatch=6)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        svg = figure.as_svg()
    return svg, [str(w.message) for w in caught if "margin_right=" in str(w.message)]


@pytest.mark.parametrize("preceding_note", [False, True])
def test_suggested_right_margin_fits_the_guide(preceding_note: bool) -> None:
    _, messages = _render(97, preceding_note)
    assert messages
    suggested = max(int(re.search(r"margin_right=(\d+)", message)[1]) for message in messages)

    svg, remaining = _render(suggested, preceding_note)
    assert "Group one long name" in svg
    assert not remaining

    # The suggestion rounds upwards when the text has a fractional width.
    _, too_small = _render(suggested - 1, preceding_note)
    assert too_small
