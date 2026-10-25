"""Style presets — a whole figure's look, in one call.

A preset is an ordinary :class:`~phylustrator.style.Style` with its fields already set, so anything
it chooses can be overridden at the call:

    import phylustrator as ph
    ph.trees.plot(tree, style=ph.styles.tikz(width=360, height=240))

It is a style, not a layout and not a backend, so it works with every layout and every layer.

**Two things the font has to survive.** The PNG/PDF path goes through cairosvg, and it takes the
family string as *one* name: a CSS stack — ``"Latin Modern Roman, serif"`` — matches nothing and
falls back to a **sans** face, silently. And the generic ``"serif"`` resolves to a face that renders
**bold** at every weight, so a title asked for in roman comes out heavy. So a preset here names one
real family, and a machine without it should be given one it has:

    ph.styles.tikz(font_family="Liberation Serif")    # or "DejaVu Serif", "Georgia", "Palatino"

Both only bite on the PNG/PDF path. An ``.svg`` saved for Inkscape or a browser resolves a stack
and a generic the way the standard says.
"""

from __future__ import annotations

from dataclasses import replace

from .style import Style

#: The family name of the Computer Modern that ships with a modern TeX distribution. Pass it as
#: ``tikz(font_family=ph.styles.LATEX_SERIF)`` on a machine that has TeX installed, for the real
#: thing rather than whatever serif the system picks. It is **not** the default: a machine without
#: it renders in a sans face and the figure then looks nothing like the document it goes into.
#: ``"CMU Serif"`` is the name the Computer Modern Unicode fonts install under, if that is what you
#: have.
LATEX_SERIF = "Latin Modern Roman"

#: Event marks for a figure printed in ink: one shape per kind, drawn in black and greys rather than
#: the default colour set. Pass it through ``branch_events(styles=…)``, which merges it over the
#: defaults, so a kind left out keeps its usual colour.
TIKZ_EVENTS = {
    "duplication": ("square", "#000000"),
    "loss": ("cross", "#000000"),
    "transfer": ("arrow", "#555555"),
    "origination": ("diamond", "#000000"),
}


def tikz(**overrides) -> Style:
    """The look of a phylogenetic diagram drawn in LaTeX/TikZ: a serif text face, fine black lines,
    squared-off branch ends and a white page.

    It is the style for a small teaching or manuscript figure meant to sit in a LaTeX document
    without looking like it came from somewhere else. Every field is an ordinary ``Style`` field, so
    the typography (``font_family``, ``font_size``), the stroke widths (``branch_width``,
    ``gene_stroke_width``) and the branch ends (``line_cap``) are all still yours to set:

        ph.styles.tikz(branch_width=1.4, font_size=13)

    It pairs with the ``diagonal`` layout for the straight slanted branches of a textbook figure,
    but it is a style and works with every layout. For the event marks, pass :data:`TIKZ_EVENTS` to
    ``branch_events(styles=…)``: a style cannot reach them, since a kind's colour is the layer's.

    The text is set in Times, which macOS and Windows both have. On a machine with TeX,
    ``tikz(font_family=ph.styles.LATEX_SERIF)`` asks for Computer Modern itself; on one with
    neither, name the serif it does have. One name, never a list, and never the generic
    ``"serif"`` — the module docstring says why."""
    base = Style(
        # a real family, not the generic "serif": that one renders bold at every weight, and a
        # LaTeX figure's text is light roman. Times is on macOS and Windows; a machine without it
        # takes the family it does have (see the module docstring).
        font_family="Times New Roman",
        font_size=11.0,
        label_color="#000000",
        # a LaTeX figure sets its taxon names in maths, which is italic; the title stays roman
        label_style="italic",
        background="white",
        # fine and black, the weight a TikZ figure draws at; round caps would bulge each branch end
        # by half its width and turn a short deep branch into a capsule
        branch_color="#000000",
        branch_width=1.0,
        line_cap="butt",
        # genomes, so a gene diagram in the same document matches: thin ink outlines, pale fill
        gene_stroke="#000000",
        gene_stroke_width=0.6,
        default_color="#e8e8e8",
    )
    return replace(base, **overrides) if overrides else base
