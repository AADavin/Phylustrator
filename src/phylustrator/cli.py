"""``phyl`` — a one-shot tree viewer.

    phyl tree.nwk                 # render to a temporary PDF and open it
    phyl tree.nwk -o fig.svg      # save instead (format from the extension)
    phyl tree.nwk --radial --no-labels

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
from .trees import node_labels, plot, read, scale_bar, tip_labels, time_axis


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="phyl", description="Draw a phylogenetic tree from a Newick file.")
    p.add_argument("tree", help="Newick tree file")
    p.add_argument("-o", "--output", metavar="FILE",
                   help="save here (.svg/.pdf/.png); default: a temporary PDF, opened")
    p.add_argument("--layout", choices=["rectangular", "radial", "unrooted"], default="rectangular")
    p.add_argument("--radial", action="store_const", const="radial", dest="layout",
                   help="shortcut for --layout radial")
    p.add_argument("--unrooted", action="store_const", const="unrooted", dest="layout",
                   help="shortcut for --layout unrooted")
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

    figure = plot(tree, layout=args.layout, stem=not args.no_stem)
    if not args.no_labels:
        figure = figure + tip_labels()
    if args.node_labels:
        figure = figure + node_labels()
    figure = figure + (time_axis() if args.layout == "rectangular" else scale_bar())

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
