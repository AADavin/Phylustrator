"""``phyl`` — a one-shot tree viewer.

    phyl tree.nwk                 # render to a temporary PDF and open it
    phyl tree.nwk -o fig.svg      # save instead (format from the extension)
    phyl tree.nwk --radial --no-labels
    phyl tree.nwk --layout diagonal --orientation down --tikz

Deliberately tiny: it reads a Newick file, draws it, and shows or saves it. Anything richer
(colouring, tracks, custom styles) lives in the Python API.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from . import __version__
from .styles import tikz
from .trees import node_labels, plot, read, scale_bar, time_axis, tip_labels
from .trees.layout import ORIENTATIONS


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="phyl", description="Draw a phylogenetic tree from a Newick file.")
    p.add_argument("tree", help="Newick tree file")
    p.add_argument("-o", "--output", metavar="FILE",
                   help="save here (.svg/.pdf/.png); default: a temporary PDF, opened")
    p.add_argument("--layout", choices=["rectangular", "radial", "unrooted", "diagonal"],
                   default="rectangular")
    p.add_argument("--orientation", choices=list(ORIENTATIONS), default="right",
                   help="which way a diagonal tree grows; 'down' puts the root at the top")
    p.add_argument("--radial", action="store_const", const="radial", dest="layout",
                   help="shortcut for --layout radial")
    p.add_argument("--unrooted", action="store_const", const="unrooted", dest="layout",
                   help="shortcut for --layout unrooted")
    p.add_argument("--tikz", action="store_true",
                   help="draw it as a LaTeX/TikZ diagram: serif text, fine black lines, flat ends")
    p.add_argument("--no-labels", action="store_true", help="hide tip labels")
    p.add_argument("--node-labels", action="store_true", help="also label internal nodes")
    p.add_argument("--no-stem", action="store_true", help="start at the crown (hide the root stem)")
    p.add_argument("--no-open", action="store_true", help="do not open the temporary file")
    p.add_argument("-V", "--version", action="version", version=f"phyl {__version__}")
    return p


def _open(path: Path) -> None:
    try:
        if sys.platform == "darwin":
            subprocess.run(["open", str(path)], check=False)
        elif sys.platform.startswith("win"):
            os.startfile(str(path))  # type: ignore[attr-defined]  # noqa: S606
        else:
            subprocess.run(["xdg-open", str(path)], check=False)
    except OSError:
        pass  # opening is a convenience; the path is printed regardless


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)

    try:
        tree = read(args.tree)
    except (FileNotFoundError, ValueError) as exc:
        parser.error(str(exc))

    if args.orientation != "right" and args.layout != "diagonal":
        parser.error(f"--orientation is for --layout diagonal; {args.layout} always grows right")
    figure = plot(tree, layout=args.layout, stem=not args.no_stem,
                  orientation=args.orientation, style=tikz() if args.tikz else None)
    if not args.no_labels:
        figure = figure + tip_labels()
    if args.node_labels:
        figure = figure + node_labels()
    # the axis runs along the bottom, so it reads only on a tree whose time runs across the page
    flat = args.layout == "rectangular" or (args.layout == "diagonal"
                                            and args.orientation in ("right", "left"))
    # a turned tree has a tip at every bottom corner, so its bar goes outside the panel
    figure = figure + (time_axis() if flat else
                       scale_bar(loc="below" if args.layout == "diagonal" else "bottom-right"))

    if args.output:
        out = figure.save(args.output)
        print(out)
        return 0

    # No -o: a genuinely throwaway file in the system temp dir.
    tmp = Path(tempfile.mkdtemp(prefix="phyl_")) / "tree.pdf"
    out = figure.save(tmp)  # may return a .svg sibling if cairosvg is absent
    print(out)
    if not args.no_open:
        _open(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
