# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.17.0] - 2026-10-25

### Added

- **`ph.page(rows, …)`** — several independent figures on one page, nested as vectors. `beside` and
  `below` each pair one tree with one companion panel, so two trees side by side — the same tree
  under two analyses, the commonest comparison there is — had to leave the library and be stitched
  together as images, losing the shared axis and the shared scale. Every figure keeps its own
  layers and style and is re-rendered at its cell's size where it can be, so the text stays the
  size it was asked for rather than being scaled with the drawing. A cell may be `None` to leave a
  gap (#30, #17).
- `page(title=…)` is centred over the whole page, which a title on a figure inside it cannot be:
  on a 45/55 split that one sits left of the middle. A `beside` composite can go on a page, which
  is what gives it a title at last (#41).
- `page(letters=True)` writes A, B, C … at the corner of each panel in reading order, or takes the
  labels outright. An empty cell is a gap and does not eat a letter.
- `page(units="pt")` (also `"mm"`, `"cm"`, `"in"`) sets the page's physical size and leaves the
  drawing in pixels underneath, so a figure can hit a journal's column width exactly (#17).
- `trees.legend(loc="right")` and `loc="below"` — put the key **outside** the panel, a column in
  the right margin past the tip labels or a row under the time axis, instead of in a corner over
  the tree. Which corner is free depends on the tree, and on one whose tips reach the right edge at
  every row and whose root sits low there is no free corner at all: `loc="auto"` still has to pick
  one. Outside, nothing is covered whatever the tree's shape, and a script drawing many trees needs
  no corner chosen by eye (#40).
- `trees.note` takes the same two places, and `branch_events(legend_loc=…)` with them.
- `trees.tube()` — the species tree drawn as a **tube**: a wide branch with an outline and rounded
  bends, with room inside it for a gene's history. The usual picture of a reconciliation, and the
  one shape the library could not draw: the workaround wrote the paths by hand and spliced them
  into the output of `as_svg()`. Each branch is drawn twice, wide in the outline colour and
  narrower in the fill, so the outlines of two branches leaving one node merge into one tube
  instead of crossing it. Rectangular and diagonal layouts, where a branch is a segment across the
  page; a radial tube would be an annulus, which is a different drawing, and it says so (#42).
- `trees.gene_path(segments)` — a lineage along part of the tree, the gene inside the tube. A
  segment is a branch name, or `{"branch": …, "from": depth, "to": depth}` for part of one, on the
  same depth scale `branch_events` takes. A segment that starts at the top of its branch is drawn
  through the bend out of its parent, so the line follows the tube round the corner instead of
  cutting across it; one that starts part-way down begins there, which is what a copy born inside a
  branch looks like. `offset` runs two copies side by side in one tube, and `dash` draws a lineage
  that is inferred rather than observed (#42).
- `trees.branch_markers(values, at=…)` — a mark on a branch coloured by a **number**, through the
  same colormap `color_branches` uses, recording the scale so a `colorbar` added after it reads the
  right range. `branch_events` colours a mark by its *kind* and reads from a key; a rate, a support
  or a posterior wants a scale instead, and there was no layer for it. `at` is how far along the
  branch the mark sits, from the parent (0) to the node (1), following the branch as drawn — the
  horizontal run of a rectangular branch, the radial step of a circular one, the slanted segment of
  a diagonal or unrooted one (#43).
- `branch_markers(spread=True)`, the default, parts marks that land on top of each other. Near the
  centre of a radial tree neighbouring branches are a few pixels apart, so two marks cover each
  other and the figure shows one value where it has two. `gap` sets how close they may come;
  `spread=False` leaves every mark exactly where its branch is. Two marks on exactly one point are
  parted in a fixed direction, so a figure drawn twice comes out the same.
- `branch_markers(labels=…)` writes beside the marks, **across** the branch rather than along it —
  above it on a rectangular tree, outward on a circular one. Along the branch the text runs into
  the tip's own name on any branch that ends at a tip, which is where a figure labelling every
  branch puts half of them.
- `trees.node_points(intervals={node: (low, high)})` — the uncertainty on a value, drawn as a
  whisker through its point. A value measured on a tree usually comes with one, and the panel could
  draw the estimate and not the interval: the expected number of events per branch went on the tree
  happily and its 95% interval had nowhere to go. The y range grows to hold the whiskers, since a
  range taken from the estimates alone cuts the bars off at the edge of the panel, which reads as
  an interval that stops there. An end the axis does not reach loses its cap, for the same reason.
  An interval given backwards, or one for a node with no value, is refused rather than drawn (#12).
- `Canvas.embed_svg(svg, x, y)` — nest another figure's SVG as vectors, the twin of `embed_png` and
  the one to prefer. Every id in the nested document is renamed first: drawsvg numbers them from
  zero in every figure, so without that the second figure's gradients would answer to the first
  one's name and quietly draw the wrong colours.
- `Canvas.physical_size(units)`.
- `Canvas.raw_path(d, …)` — an arbitrary SVG path in pixel space. Everything else on the canvas
  draws one named shape, and a figure that needs a rounded bend, a tube's outline or a lineage cut
  to part of a branch has none to ask for; the alternative was splicing hand-written paths into the
  output of `as_svg()`, which is outside the library and breaks whenever the rest of it changes.
  `join` sets how two segments meet (`"miter"` for the angular corners of a LaTeX diagram), `cap`
  defaults to the style's `line_cap`, and `dash` takes an SVG dash array. The `d` string is passed
  through as written — the one place here where the geometry is the caller's (#42).
- `Canvas.claim(side, edge)` / `Canvas.claimed(side, default)` — how far into a margin the layers
  drawn so far have written. `tip_labels`, `tip_track` and `time_axis` claim what they use, and a
  key placed outside starts past it, so it lands beside the figure rather than on its own tip
  labels. Two blocks placed outside stack, in the order they were added.
- A margin too thin to hold the block warns and says what `margin_right` or `margin_bottom` it
  would need. The canvas size is fixed before any layer runs, so the key cannot widen it itself.

### Changed

- `beside` nests its tree as **vectors** instead of rendering it to a PNG and pasting it in. A
  composite for a journal was half a picture, and building one needed cairosvg at all (#17).

### Fixed

- `trees.legend(loc="auto")` measured the four corners against the **branches** only, so on a tree
  whose long tips reach the right margin it would take a corner that was free of branches and
  covered several tip names, with nothing said. It counts the names now, and a corner that still
  covers something warns and says what — branches by name, names by number. A key placed before
  `tip_labels` sees nothing, because the names are measured by the layer that writes them; the
  natural order is the right one, and the docstring says so (#36).
- The tube's tips end **on** the tip. A round cap reaches half the tube's width past the end of its
  path, so a tube drawn to the tip overhung it and ran under the tip's own label; a free end is
  pulled back by that much now. An inner branch keeps its cap, because that is what fills the wedge
  between two branches leaving a node at an angle — squared off, a diagonal tree showed a notch at
  every fork.
- The missing-font check added in 0.16.0 reported **Helvetica** as missing. A family the renderer
  cannot find is drawn in the fallback face, and on most machines that face *is* Helvetica, so the
  two renderings matched and the check called the fallback missing — on nearly every default
  figure. The faces a renderer falls back to are now answered as installed: asking for Helvetica
  and getting Helvetica is the figure that was asked for. The cost is that a machine genuinely
  missing one of those names is not warned, which is written down beside the list.
## [0.16.0] - 2026-10-25

### Added
- The **`diagonal`** layout — each parent joined to each child by one straight slanted segment,
  instead of the right-angle pair the rectangular layout draws. It is the shape of a textbook or
  TikZ diagram, and it was the one tree picture the library could not draw: the workaround took the
  coordinates from `layout.rectangular` and drew the branches by hand on a bare `Canvas`, which
  gives up every layer. The coordinates are the rectangular ones, so a diagonal phylogram still
  carries its lengths — the depth projection of a segment is its length, while the slanted segment
  itself is longer (#44).
- `trees.plot(orientation=…)` — `"right"` (the default), `"down"`, `"left"` or `"up"`, for the
  `diagonal` layout. A `"down"` tree has the root at the top and the tips along the bottom, the
  usual teaching diagram. This is a layout and not a rotation of the finished drawing, because
  rotating the drawing lays every tip label on its side: here the geometry turns and the text stays
  upright. `tip_labels`, `node_labels` and `tip_track` follow the orientation; the other layouts
  refuse the argument rather than ignoring it (#44, and #18, which was closed on the grounds that a
  caller could rotate the drawing themselves).
- **`ph.styles`** and `styles.tikz()` — the look of a LaTeX/TikZ diagram as one `Style`: serif text,
  fine black lines, squared-off branch ends, a white page. It is a style, so it works with every
  layout and every layer, and every field it sets is an ordinary `Style` field left available to
  the caller. `styles.TIKZ_EVENTS` is the matching set of event marks in ink, for
  `branch_events(styles=…)`, since a kind's colour belongs to the layer and not to a style (#44).
- `Style.line_cap` — how a branch ends. `"round"` (unchanged) or `"butt"`, which squares it off. A
  round cap adds half the stroke width at each end, so a wide or short branch reads as longer than
  it is. A dashed line is still always squared off, or each dash grows a cap and the gaps close up.
- `phyl --layout diagonal --orientation down --tikz` — the same from the command line.
- `trees.node_dots()` — the dot a textbook diagram puts on a node, so a branch ends in a point
  rather than trailing off. `where` takes a group (`"tips"`, `"internal"`, `"root"`, `"all"`) and a
  list of names takes them one by one, for the single node a figure is about: `node_dots(["ab"],
  shape="star")`. It carries no data, which is what separates it from `node_points` (#44).
- `Canvas.raw_marker` draws a `"star"`, the five-pointed mark for the one node a diagram is about.
- `Style.label_style` — the face a node's own label is written in, `"normal"` or `"italic"`. A
  LaTeX figure sets its taxon names in maths, which is italic, while its title stays roman, so this
  is the label's face alone and the title, key and axis are not dragged along with it. `tikz()`
  sets it to italic (#44).
- `trees.plot(align_tips=True)` — end every lineage on the furthest tip's row, which is how a
  teaching diagram lines its taxa up: the picture is about the topology, and a tip left short reads
  as a shallower lineage rather than as a shorter branch. The internal nodes keep their own depth,
  so it is a drawing choice and not a transformation of the tree. Rectangular, radial and diagonal;
  the unrooted layout has no tip row and refuses it (#44).
- `trees.tip_labels(upright=True)` — keep a radial or unrooted tree's names horizontal instead of
  turning them along the branch. A fan of turned names is what a large circular tree needs; a
  diagram of five taxa wants them read straight (#44).
- `styles.maths(text)` and `styles.tikz_math()` — a figure whose labels match a LaTeX document
  exactly rather than closely. LaTeX sets `$a$` in Computer Modern's **maths** italic (cmmi), which
  is a different face from text italic (cmti), and asking for italic gets the second one. `maths()`
  writes the Mathematical Italic characters themselves, so the first is what the renderer uses.
  `tikz_math()` sets the text in Latin Modern Math, whose upright letters are the roman text face
  and whose italic letters are the maths ones — one font for a roman title and italic labels. The
  slot for italic *h* is reserved in Unicode and its character is U+210E, PLANCK CONSTANT; a label
  with an `h` in it comes out blank without that, and `maths()` handles it (#44).
- `Style.label_family` — the family a node's own label is written in, where it differs from the
  title's. A LaTeX figure takes its title from the text font and its names from the maths font, and
  those are two different files (#44).
- A **missing font is now reported** when a PNG or PDF is saved. A family the renderer cannot find
  is substituted silently, and the figure comes back set in the fallback face — usually a sans one,
  which is the opposite of what a serif figure asked for. There is no asking the renderer, so the
  family is drawn twice, once as asked and once under a name nothing can have, and the two images
  are compared. Any failure of the check answers "installed", since a check that cannot run must
  not stop a figure from being saved; the answer is remembered per family. SVG says nothing: it
  carries the name and is resolved wherever it is opened.
- `Layout.depth(node)`, `Layout.orientation` and `Layout.grows_along_x` — a node's distance along
  the tree whichever way it is drawn, and which way that is. A layer that needs a distance (an
  event part-way down a branch) asks for it instead of reading a coordinate that only means depth
  on an untarned tree.

### Fixed
- `branch_events` clamped a point marker to its branch by reading the layout's x coordinate, which
  is the distance only on a rectangular tree. The same code on a turned tree clamped every marker
  to a tip index and drew it off the tree. It reads the branch's own depth range now, which is the
  same number on every layout (#44).

### Known limits
- Two font traps, on the PNG/PDF path only (cairosvg), now written down in `styles`: a CSS font
  stack is read as one family name, so `"Latin Modern Roman, serif"` matches nothing and falls back
  to a **sans** face; and the generic `"serif"` resolves to a face that renders **bold** at every
  weight. `tikz()` therefore names one real family, Times, and says what to pass on a machine
  without it. An `.svg` for a browser or Inkscape is unaffected.
- `node_intervals` and `highlight_clade` raise on the `diagonal` layout, and `time_axis` draws on a
  right- or left-facing diagonal tree and warns on a turned one: an axis along the bottom cannot
  carry a time that runs down the page. Each says so rather than drawing something wrong.

## [0.15.0] - 2026-10-25

### Added
- `trees.plot(cladogram=True)` — space the nodes by topological depth and ignore the branch lengths.
  The three layouts had always taken it and the figure could not pass it, so a large tree whose deep
  branches are short had to be drawn with every length rewritten to 1 first. On a radial tree to
  scale, those deep branches collapse onto the centre and the topology cannot be read (#43).
- `trees.tip_track(label=…)` — name the column, written above its top chip. Three tracks at three
  `offset` values are three columns, and nothing wrote which was which, so a figure comparing a
  truth column with two tools needed a hand-written layer for the headers alone. The header is
  turned upright by default (`label_angle=-90`), because a column is one chip wide and a horizontal
  header runs over its neighbour at once; `label_angle=0` writes it flat and centred. Above a
  ragged column — a tree that is not ultrametric — it goes over the rightmost chip, so a column
  gets one header rather than a staircase. A radial layout has no column to head: the header is
  dropped with a warning and the chips are drawn as usual (#38).

### Fixed
- `trees.branch_events` showed a horizontal arrow in the key for a transfer it had drawn as a
  vertical one. A transfer from an unsampled donor arrives onto the branch from above or below, and
  the key kept the donor-to-recipient glyph, so the reader had only the colour to match the mark to
  its name. The key now draws the form that was used — down for `outside_side="above"`, up for
  `"below"` — and a kind drawn both ways shows both glyphs on its row (#37).
- `trees.colorbar` painted its box over whatever branches ran through its corner and said nothing,
  while `legend` had warned since 0.14.0. On a ladderized tree whose first two tips are long, the
  branch to their ancestor runs exactly under the bar, and that pair then looks detached from the
  tree. The bar now warns the same way, naming the corner and the branches, and names the other
  left corner to move to — `loc="auto"` is the legend's answer and the bar has none (#39).
- `trees.colorbar(loc=…)` raises on a right-hand corner instead of accepting it and drawing on the
  left. The bar is anchored on the left margin, so `loc="top-right"` silently gave a figure that
  was not what it asked for (#39).

## [0.14.0] - 2026-10-12

### Added
- `trees.legend(loc="auto")` — measure all four corners and take the one covering the least of the
  tree. The key paints the page colour behind itself, so that a branch under the letters does not
  make both unreadable, and nothing checked what that patch covered: on a tree whose lowest clade
  joins near the root, a bottom-left key with long labels hid the branch leading to a tip, and that
  tip looked detached from the tree (#35).

### Changed
- A `legend` in any corner that still covers a branch warns, naming the corner and the branches. A
  branch counts as covered only when two sampled points fall inside the block, so a corner clipping
  a line is not worth a warning. Every explicit corner draws exactly where it did (#35).

## [0.13.0] - 2026-10-12

### Added
- `trees.time_axis(at=…, labels=…)` — place the ticks and say what each one reads, instead of taking
  the round values the axis chooses. `at="nodes"` puts a tick under every internal node, numbered
  from the oldest, so the axis reads as the order of the nodes rather than as a distance; two nodes
  at the same distance share a tick. `at` and `step` are two ways to place the same ticks, so giving
  both raises, as does `labels` without `at` (#29).
- `trees.node_intervals({node: (low, high)})` — the uncertainty on a node's age, drawn as a bar at
  the node's row: an HPD from a clock, or bounds from any other method. `colors` tints one node's
  own bar, and the bar is translucent and squared off, since one wider than the branch is the normal
  case and must not hide the tree. `before_present=True` reads the pair as **ages** counted back
  from the furthest tip, which is how a clock quotes an HPD; given as distances by mistake, every
  bar lands elsewhere on the tree and still looks plausible. On a radial tree the bar runs along the
  node's own angle, since there the radius is the time axis; the unrooted layout raises (#31).
- `Canvas.line` gains `opacity` and `cap`.

## [0.12.0] - 2026-10-12

### Added
- `zombi.read_alignment` also reads a run written with ZOMBI2's `--bundle`, where every family's
  alignment is in one `alignments.fasta` and each header ends with ` fam<N>`.
- Any colormap name takes an `_r` suffix and runs the other way, as it does in matplotlib —
  `cmap="viridis_r"`. Reversing a scale is routine when the low values are the interesting ones: a
  track of differences from a reference wants zero to be the strongest colour. The error for an
  unknown name still lists the base names rather than a doubled set (#32).
- `genomes.heatmap(label=…)` names what the colour bar measures, and `""` leaves it unlabelled (#33).

### Fixed
- The heatmap's colour bar was labelled `copies` whatever the matrix held, so a scale running 88 to
  100 still said `copies` beside it and a reader who trusted the bar misread the figure. The default
  is unchanged for the gene-family case it was written for (#33).

## [0.11.0] - 2026-09-30

### Added
- `trees.color_history` accepts a segment whose state is a **pair**, `("marine", "freshwater")`,
  drawn as a fade from the first colour to the second along that segment — a trait that shifts
  gradually after an event, rather than switching at an instant. Both members take their colour from
  the same palette or colormap and both reach the key, and the branch ends in the second, so the
  connector below it follows. A dashed branch is drawn in the state it ends in, since a dashed line
  cannot carry a gradient. Rectangular and radial alike (#23).

## [0.10.0] - 2026-09-30

### Added
- `trees.node_labels(values=…)` and `trees.tip_labels(values=…)` — write a value worked out for each
  node instead of its name, keyed by node name as `color_branches` is, or `text=` for a callable.
  The library could colour by a dict and not label by one, so an ancestral estimate, a support value
  or a node age could be painted onto a tree but not written on it. A node with no value of its own
  is left unlabelled, and `node_labels(leaves=True)` covers the tips as well (#14).
- `trees.tip_track(stroke=…, stroke_width=…)` — outline the chips. The outline was fixed white, so
  in a black-and-white presence column the absent chip was white on white and vanished; an ink
  outline draws it as an open square (#15).
- `trees.branch_events` draws a transfer whose donor is not in the tree — an unsampled lineage — as a
  short straight arrow onto the recipient's branch, `outside_length` long and arriving from
  `outside_side`; one event may name its own `side`. It used to be skipped without a word. `Canvas`
  gains `raw_arrow`, the pixel-space twin of `arrow` (#16).
- `trees.time_axis(before_present=True, step=…)` — count back from the tips, which is how a dated
  tree reads: 0 under the tips and the root at its age. The ticks anchor at the present, so they
  land on round ages rather than round distances from the root. A `step` of 0 or less raises (#21).

## [0.9.0] - 2026-09-30

### Added
- `trees.highlight_clade(..., stroke=…, stroke_width=…)` — outline a clade instead of, or as well as,
  filling it. `color="none"` with a stroke leaves the outline alone, the usual mark for "this clade
  is drawn enlarged in the next panel" (#24).
- `Figure.clade_box(name)` — the clade box's pixel corners, computed from the layout before anything
  is drawn, so the zoom lines into another panel can be laid out first. `highlight_clade` draws that
  same box, from the same helper (#24).
- `highlight_clade` now marks a clade in every layout, each in the shape that layout has: a box where
  y is tip order, a wedge between the clade's first and last tip angles in the radial layout, and a
  hull around the clade's own branches in the unrooted one. It used to draw on the rectangular layout
  and return silently on the other two. `pad_px` is the room left in the direction with no tip
  spacing to measure against (#26).

### Changed
- `highlight_clade` raises on a clade name the tree does not have, instead of drawing nothing:
  silence there reads as a clade not worth marking rather than as a typo.

## [0.8.0] - 2026-09-30

### Added
- `trees.color_branches(width={node: width})` — a width per branch, not one for the layer. A branch
  with no width of its own takes the style's. The drop into a child follows the child's width, as it
  already follows the child's colour, so a thick lineage no longer fattens the whole bar at every
  node it passes through (#25, #28).
- `trees.color_branches(others="keep")` — leave a branch with no value exactly as the base plot drew
  it. Two layers, each mapping a few branches, need it: otherwise the second repaints the first's
  work in the default colour, and the only way out was `branch_color="none"`, which silently hides
  branches nobody mapped. The default, `"repaint"`, is unchanged (#25).
- `trees.lineage(tree, name)` — the named nodes from the root down to that node, ready to feed a
  width or a colour map. `trees.highlight_lineage(name, width=…)` draws that path thicker in one
  line: after a colouring layer it paints over it, before one it reads as an outline (#28).

## [0.7.0] - 2026-09-30

### Added
- `trees.color_branches(values, gradient=...)` — `False` paints each branch flat in its own colour,
  for a number that belongs to the branch as a whole: a count of events on it, a rate fitted for it,
  a support value. A gradient misreads those twice, shading the branch by its *parent's* value and
  suggesting a change along a branch the data says nothing about. The colormap and the colorbar are
  unaffected, which the hand-rolled workaround could not manage. Left unset, nothing changes (#13).

### Fixed
- The connector from a node down into a child is where that child's branch begins, so it is now
  painted in the child's colour. A map covering every branch leaves out the root, which has no
  branch of its own, and the root's bar went unpainted: the two clades floated apart with nothing
  joining them. Under a gradient the child's branch starts in the parent's colour, so there the drop
  keeps it and no gradient figure moves. The radial ring is cut per child only when they differ (#27).

## [0.6.0] - 2026-09-30

### Added
- `trees.branch_spindles(marks)` — a lens drawn along a branch at a time, sitting on a stretch of
  branch in the mark's colour that fades into the branch's own colour at both ends, so the mark
  grows out of the line instead of floating on it. `into` names the colour it fades into, for a
  branch painted by `color_branches`. Rectangular and radial layouts (#19).
- `trees.node_halves({node: (left, right)})` — a disc at a node split in two, each half a colour or
  open, for two states at once at every ancestor (#20).

### Fixed
- `branch_spindles` on a branch too short for the lens shortened the lens but kept its height, so
  the spindle stood up as a sliver taller than it was long. The height now shrinks by the same
  factor, and every spindle in a figure keeps one shape (#22).

## [0.5.1] - 2026-09-21

### Fixed
- `trees.branch_events` drew a transfer arrow wherever the time said, even when the donor or the
  recipient no longer existed then. The arrow sat on a row whose branch had already ended, which
  reads as a transfer that never happened. Such a transfer is now refused, and the message names the
  window where the two lineages do exist — a figure of times measured from the present, or without
  the root stem, misses it the same way, and the window is what says so. Two lineages that never
  coexist say that instead. This is the `clamp` argument, which already kept point markers on their
  branch; `clamp=False` places everything exactly as given. A transfer is refused rather than moved,
  because moving it would redraw it at a time the caller never gave.

## [0.5.0] - 2026-09-21

### Added
- An event given to `trees.branch_events` may carry its own style. `weight` (0-1) scales the arrow's
  width, the glyph's size and the opacity of both, between a floor and the kind's full style — the
  figure this is for is transfers summed over gene families, where every pair carries a count and a
  few hundred arcs only read if width follows it (`weight = n / n_max`). `color` and `size` override
  the kind's colour and the layer's size for that one event. An event with no override is drawn
  exactly as before, and the legend keeps showing the kind's own colour. `weight_floor` (default
  0.25) is how much of the style a weight of 0 keeps, so the lightest mark stays on the page (#11).
- `Canvas.arrow` and `Canvas.raw_marker` take an `opacity`. A fully opaque arrow or glyph writes no
  opacity attribute, so every figure drawn before this renders byte for byte as it did.

## [0.4.0] - 2026-09-21

### Added
- `trees.title(text)` — a title centred over the panel, in the top margin above the tree. `note`
  pins text to a corner, which is where something *about* a figure belongs; a title belongs over the
  middle of it. `size`, `dy` and `color` set the rest, and the title stays on the page even on a
  thin top margin (#9).
- `trees.legend` gains `loc`, the four corners `branch_events` already takes. The default stays
  `"top-left"`, so no existing figure moves its legend. A right corner right-aligns the block on the
  right margin, and a bottom corner ends it on the bottom margin. A rectangular tree fills the upper
  left of its panel, so the top left is often the one corner a legend cannot share (#10).

### Changed
- `note` and `legend` raise on a `loc` that is not one of the four corners, at the point it is
  written. `note(loc="top-centre")` used to fall through the `"left" in loc` test and print
  right-aligned; the message names `title()` for the centred case.

## [0.3.1] - 2026-09-17

### Fixed
- `trees.time_marker` drew nothing on the radial and unrooted layouts, silently. It now draws a
  circle at that distance from the centre on a radial tree, with the same colour, width and dash
  arguments. A radial time is shifted by the root stem, as `branch_events` already shifts its
  events, because the radial layout starts at the crown. The unrooted layout raises instead of
  skipping: it places branches by angle, so a distance from the origin is not a place on it (#8).

## [0.3.0] - 2026-09-14

### Added
- `ph.below(tree, panel)` — the x-axis twin of `beside`: a panel under a rectangular tree that shares
  its time axis, with an optional time axis under the panel. The tree keeps its size and margins,
  every node stays on its pixel, and the composite is drawn as vectors, so it needs no cairosvg (#7).
- `trees.node_points({node: value})` — the panel for it: one point per named node, internal nodes
  included, at the node's time. Options: per-node `colors`, `line=True` to join the points, a zero
  line when the range crosses 0, and round y ticks. A name not in the tree raises an error.
- `Figure.geometry()` now also gives `nodes` (every node's pixel position, internal ones included)
  and `px(x)`, the time-to-pixel mapping, so other panels can line up with the x axis.
- `Style` gains `margin_left`, `margin_right`, `margin_top` and `margin_bottom`. Each defaults to
  `margin`, so existing figures render byte for byte as before. The tree guides use the side they sit on.

## [0.2.17] - 2026-08-23

### Added
- `trees.color_history` works on the radial layout. Each branch is painted as its state mosaic,
  running outward along the node's angle, and the arc at a speciation takes the branch's end state.
- `trees.branch_events` works on the radial layout. Point marks and transfer arrows are placed in
  polar coordinates, and each glyph turns to follow its branch.
- `trees.ring` gains `edge` and `edge_width`, which outline every sector in one colour, so a white
  sector still shows as a cell.
- `trees.legend` gains `entries`, an explicit `{label: colour}` list, for a figure whose scale slot
  holds a continuous ring. It also gains `dy`, to sit below a `colorbar` in the same corner.
- `trees.legend` and `trees.colorbar` gain `inset`, which anchors the corner at a fixed distance
  instead of the figure margin. A figure with a large margin keeps its guides in the corner, clear
  of its rings.
- `CITATION.cff`, the citation metadata for the Zenodo DOI.

### Fixed
- On a radial tree, `branch_events` marks landed one stem length too far out. The radial layout
  drops the root stem, and the event distances now drop it too.
- On a radial tree, a state-switch triangle puts its tip at the event's time, with its body over the
  state it leaves, and has a thin dark outline. Before, its wide base read as the point.

## [0.2.16] - 2026-08-22

### Added
- `trees.ring(values)` — an outer ring of coloured arcs around a radial tree, one contiguous segment
  per tip merging same-coloured neighbours into a band; `radius_pct` sets where the ring sits.
- `trees.tip_track(..., shape=…)` — the tip chip can now be any marker glyph (`"circle"`, `"square"`,
  …), not only a square.
- `trees.rubberband(values)` — a smooth, round population band wrapped around a radial tree, coloured
  by `values` like `color_branches`. It traces the tree's outline from the root, holds it a constant
  distance out from the branches (so the margin is even all the way around), rounds it by smoothing
  over angle, and clamps it so it never crosses a branch. `gap` sets that constant distance, `smooth`
  the roundness (fraction of the turn averaged over), `width` the band thickness.

## [0.1.4] - 2026-08-03

### Added
- `genomes.grid(matrix)` — a `Matrix` as a standalone figure, rows x columns of coloured cells with
  no tree beside it. `heatmap` is a *panel*: `beside()` hands it one pixel row per tree tip, so it
  only exists next to a tree, and a phyletic profile of a few hundred families sorted by prevalence
  is a companion to nothing. `palette` colours values as categories (presence/absence), and
  `borders` draws the line between cells — a colour, `False`, or by default by size, since at a few
  hundred rows a hairline is a tenth of a cell and a solid block reads as criss-crossed.

## [0.1.3] - 2026-08-02

### Added
- `genomes.tracks()` — genomes as a panel beside a tree, with homologues joined by ribbons.
- Circular genomes: chunky strand-arrows, a `gene_style` option (`"wedge"` restores the classic thin
  ring), and a curved highlight band.
- `colorbar` gains `loc` (`"top-left"` default, or `"bottom-left"`) and `labels=` for the two ends.
- `color_branches` gains `limits=`, so several figures can share one colour scale.
- Colour maps: `magma`, `cividis`, and a diverging `coolwarm`.

### Changed
- `read_alignment` accepts genome-qualified FASTA headers.
- The arrowhead flare is capped on a gene-dense ring.

### Fixed
- The README's figure and LICENSE link now use absolute GitHub URLs. PyPI does not rewrite relative
  paths, so on the project page the figure rendered as a broken image and the link 404'd.

## [0.1.2] - 2026-07-27

### Added
- `genomes.bars()`, a bar panel; `trees.time_axis` gains a bold toggle.

## [0.1.1] - 2026-07-27

### Added
- Automated PyPI releases via trusted publishing.

### Changed
- `branch_events` scales the transfer arrow with `size`.

## [0.1.0] - 2026-07-27

### Added
- `phyl`, a one-shot command-line viewer: `phyl tree.nwk` renders a Newick tree to a temporary PDF
  and opens it; `-o FILE` saves to SVG/PDF/PNG instead. Flags for layout (`--radial`/`--unrooted`),
  labels (`--no-labels`/`--node-labels`), and `--no-stem`.
- The `genomes` domain (merged in from Genustrator): genome maps, synteny, and `states()` /
  `heatmap` / `alignment` panels placed beside a tree.
- Tree layers `branch_events`, `color_history`, `color_lanes`, `note`, `legend`, `time_marker`, and
  dashed branches for extinct lineages.

### Changed
- **Full rewrite** into a small, composable tree plotter. Read a tree with `loads`/`read`, build a
  figure with the layer grammar (`plot(tree) + color_branches(...) + tip_labels() + colorbar() + …`),
  and save to SVG/PDF/PNG. Own Newick parser (differential-tested against ete3), stem-aware layouts
  (`rectangular`, `radial`, `unrooted`), and a matplotlib-free viridis/palette colour module.
- `drawsvg` is now the only runtime dependency (cairosvg stays optional, for PDF/PNG).

### Removed
- The ete3-based `TreeStyle` / `VerticalTreeDrawer` API, the `phylustrator.zombi2` reconciliation
  bridge, and the `ete3` and `pandas` dependencies. ZOMBI2 support will return on the new core.

## [0.0.1] - 2025-01-01

### Added
- Initial release of Phylustrator
- VerticalTreeDrawer class for drawing phylogenetic trees in vertical orientation
- RadialTreeDrawer class for drawing phylogenetic trees in radial orientation
- TreeStyle dataclass for customizable tree visualization
- SVG export functionality
- PNG export functionality
- PDF export functionality
- Trait mapping visualization via heatmaps
- Categorical trait visualization support
- Continuous trait visualization support
- Horizontal Gene Transfer (HGT) visualization
- Clade highlighting and styling
- Leaf shape customization
- Node shape customization
- Time axes support
- Scale bars for distance reference
- Legends for trait and style information
- Jupyter notebook integration and display support
