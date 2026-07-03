# ZOMBI2 Integration API Reference

`phylustrator.zombi2` reads [ZOMBI2](https://github.com/AADavin/zombi2) output and draws
gene-family reconciliations on the time-calibrated species tree. See the
[ZOMBI2 Reconciliations guide](../guide/zombi2.md) for a walkthrough.

## `zombi2.load(output_dir)`

Parse a ZOMBI2 `Genomes.write()` output folder.

**Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `output_dir` | `str` or `Path` | Folder containing `species_tree.nwk` and `gene_family_events/` |

**Returns:** `Zombi2Data`

**Raises:** `FileNotFoundError` if `species_tree.nwk` is missing.

## `Zombi2Data`

A dataclass with the parsed output.

| Attribute | Type | Description |
|-----------|------|-------------|
| `species_tree` | `ete3.Tree` | Species tree; every node annotated with `time_from_origin` (root = 0, cumulative branch length) |
| `events` | `pandas.DataFrame` | All events — columns `family, time, event, branch, donor, recipient, nodes` |
| `transfers` | `pandas.DataFrame` | Transfers — columns `from, to, time, family, freq` |

**Methods**

- `families() -> list[str]` — family ids present, in natural order.

## `zombi2.draw_reconciliation(data, family, ...)`

Draw one family's reconciliation on the time-calibrated species tree.

**Parameters**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `data` | `Zombi2Data` or `str`/`Path` | — | Parsed data, or a folder path (loaded on the fly) |
| `family` | `str` or `int` | — | Family id to draw |
| `style` | `TreeStyle` | a sensible default | Tree style |
| `event_types` | tuple | `("O", "D", "L")` | Point events to mark (transfers are always arcs) |
| `show_transfers` | `bool` | `True` | Draw transfer arcs (`mode="time"`) |
| `leaf_names` / `node_names` | `bool` | `True` | Label tips / internal nodes |
| `title` | `str` | `"ZOMBI2 gene family <family>"` | Figure title |
| `transfer_colors` | tuple | `("#984EA3", "#4DAF4A")` | Departure → arrival gradient |

**Returns:** [`VerticalTreeDrawer`](vertical.md) — keep customising, then `save_svg` / `save_png`.

## `zombi2.event_markers(data, family, ...)`

Return `add_branch_shapes` specs for a family's point events, each placed at its true time
along its species branch. Events whose branch is not in the tree (e.g. on the root stem) are
skipped.

## `zombi2.transfer_records(data, family)`

Return `plot_transfers` records (`from, to, time, freq`) for a family; use with `mode="time"`.

## `zombi2.EVENT_STYLE`

A `dict` mapping ZOMBI event codes (`O, D, T, L, S, I, P`) to `(shape, colour)` defaults.
