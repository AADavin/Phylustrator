"""Phylustrator — a lean, composable plotter for phylogenetics: **trees** and **genomes**.

Two domains, one grammar (``plot(x) + layer + …``), one shared drawing backend:

    import phylustrator as ph

    # trees
    tree = ph.trees.loads("((A:1,B:1)C:2,D:3)R;")
    (ph.trees.plot(tree) + ph.trees.color_branches(vals) + ph.trees.time_axis()).save("tree.pdf")

    # genomes
    G = ph.zombi.read_genomes("run")
    (ph.genomes.plot(G["n12"], layout="circular") + ph.genomes.genes(by="family")).save("ring.png")

    # bridge: a matrix beside a tree
    ph.beside(ph.trees.plot(tree) + ph.trees.tip_labels(), ph.genomes.heatmap(ph.zombi.read_profiles("run")))

``ph.zombi`` is the only ZOMBI2-format-aware module; ``trees`` / ``genomes`` are general.
"""

from __future__ import annotations

from . import genomes, trees, zombi
from .compose import Composite, beside
from .style import Style

__version__ = "0.1.0"

__all__ = ["trees", "genomes", "zombi", "beside", "Composite", "Style", "__version__"]
