"""Colormaps you bring yourself (issue #70).

Six built-in ramps is a fixed set, and a figure whose quantity none of them suits had nowhere to go:
the one in the issue wanted a single-hue warm scale for a temperature, and `coolwarm` reads as
"below or above a midpoint", which a temperature in these data does not have.

So `cmap=` takes the colours themselves, and `register` gives a ramp of your own a name — including
to the colour bar that has to explain it.
"""

from __future__ import annotations

import pytest

from phylustrator import color
from phylustrator.trees import colorbar, loads, plot, ring, tip_track

_WARM = ["#fff7bc", "#fec44f", "#d95f0e", "#993404"]
_NWK = "((A:1,B:1)x:1,(C:1,D:1)y:1)r;"
_VALUES = {"A": 10.0, "B": 25.0, "C": 40.0, "D": 70.0}


@pytest.fixture(autouse=True)
def _registry_is_put_back():
    """`register` writes into the module, so a test that adds a name must not leave it there for
    the next one to find."""
    kept = dict(color._COLORMAPS)
    yield
    color._COLORMAPS.clear()
    color._COLORMAPS.update(kept)


# --- the colours themselves -----------------------------------------------------------------------


def test_a_list_of_hex_colours_is_a_colormap():
    assert color.colormap_hex(_WARM) == _WARM


def test_the_ends_are_the_ends_and_the_middle_is_between_them():
    sample = color.colormap(["#000000", "#ffffff"])
    assert sample(0.0) == (0, 0, 0)
    assert sample(1.0) == (255, 255, 255)
    assert sample(0.5) == pytest.approx((127.5, 127.5, 127.5))


def test_rgb_triples_work_as_well_as_hex():
    assert color.colormap_hex([(255, 247, 188), (153, 52, 4)]) == ["#fff7bc", "#993404"]


def test_three_digit_hex_is_read_the_way_css_reads_it():
    assert color.colormap_hex(["#fc0", "#000"]) == ["#ffcc00", "#000000"]


def test_two_colours_are_enough():
    assert len(color.colormap_hex(["#fff7bc", "#993404"])) == 2


def test_one_colour_is_not_a_ramp():
    with pytest.raises(ValueError, match="at least two colours"):
        color.colormap(["#993404"])


def test_something_that_is_not_a_colour_says_so():
    with pytest.raises(ValueError, match="not a colour"):
        color.colormap(["#993404", "burnt sienna"])


def test_a_triple_written_in_zero_to_one_is_refused_rather_than_drawn_black():
    """`(0.9, 0.4, 0.1)` is a colour in matplotlib and very nearly black here. Silently drawing it
    is worse than saying which convention this is."""
    with pytest.raises(ValueError, match="matplotlib's 0-1"):
        color.colormap([(0.9, 0.4, 0.1), (0.2, 0.1, 0.0)])


# --- a name for it --------------------------------------------------------------------------------


def test_a_registered_ramp_can_be_asked_for_by_name():
    color.register("warm", _WARM)
    assert color.colormap_hex("warm") == _WARM
    assert "warm" in color.colormaps()


def test_a_registered_ramp_runs_backwards_too():
    color.register("warm", _WARM)
    assert color.colormap_hex("warm_r") == list(reversed(_WARM))


def test_the_name_is_read_without_its_case_or_its_spaces():
    color.register("  Warm  ", _WARM)
    assert color.colormap_hex("warm") == _WARM


def test_a_name_already_taken_is_refused():
    """Redefining viridis halfway through a script leaves two figures that disagree about what a
    colour means."""
    with pytest.raises(ValueError, match="already registered"):
        color.register("viridis", _WARM)


def test_a_name_can_be_redefined_on_purpose():
    color.register("viridis", _WARM, overwrite=True)
    assert color.colormap_hex("viridis") == _WARM


def test_a_name_ending_in_the_reverse_suffix_is_refused():
    """It could never be reached: `_r` is stripped before the lookup."""
    with pytest.raises(ValueError, match="asked for backwards"):
        color.register("warm_r", _WARM)


def test_a_ramp_of_pure_black_says_black_and_means_it():
    """The 0-1 check must not catch a ramp that is honestly dark."""
    assert color.colormap_hex([(0, 0, 0), (0, 0, 0)]) == ["#000000", "#000000"]


def test_a_ramp_needs_a_name():
    with pytest.raises(ValueError, match="needs a name"):
        color.register("   ", _WARM)


def test_a_registered_ramp_is_checked_when_it_is_registered():
    """Not later, in the middle of drawing a figure."""
    with pytest.raises(ValueError, match=r"register\('warm'\)"):
        color.register("warm", ["#993404"])


# --- the error that sends you here ----------------------------------------------------------------


def test_an_unknown_name_says_what_to_do_instead():
    with pytest.raises(ValueError) as caught:
        color.colormap("YlOrRd")
    said = str(caught.value)
    assert "unknown colormap 'YlOrRd'" in said
    assert "cmap=" in said and "register()" in said, "the two ways out"


# --- through the layers, and into the key that explains it ----------------------------------------


def _drawn(cmap):
    return (plot(loads(_NWK), layout="radial") + ring(_VALUES, cmap=cmap)
            + colorbar("temperature", loc="bottom-left")).as_svg()


def test_a_layer_takes_a_ramp_of_its_own_and_the_colorbar_follows():
    """The issue's figure. The bar has to draw the same ramp, or it explains a colouring that is
    not on the tree."""
    svg = _drawn(_WARM)
    assert ">temperature</text>" in svg
    assert ">10.00</text>" in svg and ">70.00</text>" in svg
    assert "#fff7bc" in svg and "#993404" in svg, "the ramp's ends are in the gradient"
    assert "#440154" not in svg, "and viridis is not"


def test_a_registered_name_draws_exactly_what_the_list_draws():
    color.register("warm", _WARM)
    assert _drawn("warm") == _drawn(_WARM)


def test_every_layer_that_takes_a_cmap_takes_one_of_these():
    """They all pass it to `map_values`, so this is one check that the signatures agree."""
    svg = (plot(loads(_NWK)) + tip_track(_VALUES, cmap=_WARM)).as_svg()
    assert "#993404" in svg
