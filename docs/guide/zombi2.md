# ZOMBI2 Reconciliations

Phylustrator reads the output of [ZOMBI2](https://github.com/AADavin/zombi2) — a simulator of
species trees and gene families — and draws a gene family's history **on the time-calibrated
species tree**. Because the species tree is laid out with `x = time`, transfers are drawn at
their true time and come out *horizontal in time*, and duplications/losses/originations are
placed at the exact time they happened along a branch.

Phylustrator never imports ZOMBI2; it only reads the files ZOMBI2 writes.

## What it reads

Point Phylustrator at a folder written by ZOMBI2's `Genomes.write(outdir)`:

```
<outdir>/
  species_tree.nwk                        # named internal nodes, branch lengths = time
  gene_family_events/<family>_events.tsv  # time, event, branch, donor, recipient, nodes
  Transfers.tsv                           # optional; transfers are also read from the events
```

## Quick start

```python
from phylustrator import zombi2

data = zombi2.load("out/")                     # parse the ZOMBI2 output folder
print(data.families())                          # -> ['1', '2', '10', ...]

drawer = zombi2.draw_reconciliation(data, family="10")
drawer.save_svg("family10.svg")                 # or .save_png("family10.png") with [export]
```

`draw_reconciliation` also accepts a folder path directly:

```python
zombi2.draw_reconciliation("out/", family="10").save_svg("family10.svg")
```

The returned object is a regular
[`VerticalTreeDrawer`](../api/vertical.md), so you can keep customising it — add a time axis,
highlight clades, change the title, etc. — before saving.

## What gets drawn

| Event | Shown as | Placement |
|-------|----------|-----------|
| Origination (`O`) | purple dot | at its time along the originating branch |
| Duplication (`D`) | blue square | at its time along the branch |
| Loss (`L`) | red dot | at its time along the branch |
| Transfer (`T`) | gradient arc (donor → recipient) | at the transfer time on **both** branches |
| Speciation (`S`) | not drawn (it *is* the tree topology) | — |

Transfers use `plot_transfers(mode="time")` under the hood, so each arc endpoint sits at the
transfer's time on the donor and recipient branches — a contemporaneous transfer therefore
renders as a near-vertical arc.

## Customising

```python
from phylustrator import TreeStyle, zombi2

data = zombi2.load("out/")

style = TreeStyle(width=900, height=500, branch_stroke_width=5,
                  branch_color="#444", font_size=16, node_r=4)

drawer = zombi2.draw_reconciliation(
    data, family="10",
    style=style,
    event_types=("O", "D", "L"),   # which point events to mark
    show_transfers=True,
    title="My favourite gene family",
)
drawer.add_time_axis(ticks=[0, 1, 2, 3], label="Time (Ma)")
drawer.save_svg("family10.svg")
```

## Lower-level helpers

If you want to overlay ZOMBI2 events on a tree you are already drawing:

```python
from phylustrator import VerticalTreeDrawer, zombi2

data = zombi2.load("out/")
drawer = VerticalTreeDrawer(data.species_tree)   # already time-annotated
drawer.draw()
drawer.add_branch_shapes(zombi2.event_markers(data, family="10"))
drawer.plot_transfers(zombi2.transfer_records(data, family="10"), mode="time")
```
