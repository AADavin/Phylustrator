"""Performance benchmarks for Phylustrator rendering.

Usage: python benchmarks/bench_rendering.py
"""
from __future__ import annotations

import tempfile
import time
from pathlib import Path

import ete3
import phylustrator as ph


def generate_tree(n_leaves: int) -> ete3.Tree:
    """Generate a random binary tree with n leaves.

    Args:
        n_leaves: Number of leaf nodes to generate.

    Returns:
        An ete3.Tree with random branch lengths and binary splits.
    """
    t = ete3.Tree()
    t.populate(n_leaves, random_branches=True)
    return t


def bench_draw(n_leaves: int, drawer_class: type, repeats: int = 3) -> dict:
    """Benchmark tree drawing.

    Times the following operations:
    - Initialization of the drawer
    - Drawing the tree
    - Adding leaf names
    - Saving to SVG

    Args:
        n_leaves: Number of leaves in the generated tree.
        drawer_class: The drawer class to benchmark (VerticalTreeDrawer or RadialTreeDrawer).
        repeats: Number of times to repeat the benchmark.

    Returns:
        A dictionary with timing results for init, draw, labels, svg, and total.
    """
    times = {"init": [], "draw": [], "labels": [], "svg": []}

    with tempfile.TemporaryDirectory() as tmpdir:
        for _ in range(repeats):
            # Generate a fresh tree for each repetition
            tree = generate_tree(n_leaves)

            # Benchmark initialization
            start = time.perf_counter()
            drawer = drawer_class(tree)
            times["init"].append(time.perf_counter() - start)

            # Benchmark drawing
            start = time.perf_counter()
            drawer.draw()
            times["draw"].append(time.perf_counter() - start)

            # Benchmark adding leaf names
            start = time.perf_counter()
            drawer.add_leaf_names()
            times["labels"].append(time.perf_counter() - start)

            # Benchmark SVG export
            output_path = Path(tmpdir) / f"tree_{_}.svg"
            start = time.perf_counter()
            drawer.save_svg(output_path)
            times["svg"].append(time.perf_counter() - start)

    # Average the timings
    avg_times = {key: sum(values) / len(values) for key, values in times.items()}
    avg_times["total"] = sum(avg_times.values())

    return avg_times


def main() -> None:
    """Run benchmarks and print formatted results."""
    sizes = [50, 100, 500, 1000]

    # Print header
    print(f"{'Leaves':>8} {'Layout':>10} {'Class':>20} {'Init':>10} {'Draw':>10} {'Labels':>10} {'SVG':>10} {'Total':>10}")
    print("-" * 98)

    for n in sizes:
        for cls_name, cls in [
            ("VerticalTreeDrawer", ph.VerticalTreeDrawer),
            ("RadialTreeDrawer", ph.RadialTreeDrawer),
        ]:
            result = bench_draw(n, cls)
            layout = "Vertical" if "Vertical" in cls_name else "Radial"
            print(
                f"{n:>8} {layout:>10} {cls_name:>20} "
                f"{result['init']:>10.4f} {result['draw']:>10.4f} {result['labels']:>10.4f} "
                f"{result['svg']:>10.4f} {result['total']:>10.4f}"
            )


if __name__ == "__main__":
    main()
