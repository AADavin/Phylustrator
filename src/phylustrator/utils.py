from __future__ import annotations

import ete3


def add_origin_if_root_has_dist(tree: ete3.Tree, origin_name: str = "Origin") -> ete3.Tree:
    """If `tree.dist` is non-zero, interpret it as a stem and add an explicit origin node.

    This avoids layout shifts when a rooted Newick encodes a stem length as the root's `dist`.

    Returns the (possibly new) root tree.
    """
    stem = float(getattr(tree, "dist", 0.0) or 0.0)
    if stem <= 0.0:
        tree.dist = 0.0
        return tree

    origin = ete3.Tree()
    origin.name = origin_name
    origin.dist = 0.0

    tree.dist = stem
    origin.add_child(tree)
    return origin
