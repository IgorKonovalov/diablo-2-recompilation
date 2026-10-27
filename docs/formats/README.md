# Formats

One file per container or binary format (`mpq.md`, `installer.md`, `excel-bin.md`, `ds1.md`, `dt1.md`,
`palette.md`, `item-palette.md`, `dc6.md`, `dcc.md`, `cof.md`, `animdata.md`, `d2s.md`). Owned by `archivist`. Each file covers layout tables with offsets and
sizes, endianness, the confidence of every field, and which `tools/` parser implements it.

| format | doc | parser | status |
|---|---|---|---|
| MPQ archives | [mpq.md](mpq.md) | `tools/mpq_dump.py`, `mpq_verify.py` | done |
| installer | [installer.md](installer.md) | — | done |
| excel `.bin` | [excel-bin.md](excel-bin.md) | `tools/excel_bin.py` | done |
| string tables | [tbl.md](tbl.md) | `tools/tbl.py` | plan 0005 Phase 3, awaiting review |
| DS1 preset maps | [ds1.md](ds1.md) | `tools/ds1.py` | plan 0005 Phase 1, reviewed |
| DT1 tiles | [dt1.md](dt1.md) | `tools/dt1.py` | plan 0005 Phase 2, reviewed |
| D2S saves | [d2s.md](d2s.md) | `tools/d2s.py` | plan 0005 Phase 4 |
| COF composite descriptors | [cof.md](cof.md) | `tools/cof.py` | plan 0006 Phase 5, awaiting review |
| animation data (`animdata.d2`) | [animdata.md](animdata.md) | `tools/animdata.py` | plan 0050 Phase 0, awaiting review |
| item colour shifts | [item-palette.md](item-palette.md) | `tools/palette.py` (`itempal`) | plan 0009 Phase 3, awaiting review |
| calc formula pools (`*code.bin`) | [calc.md](calc.md) | `tools/calc_survey.py` | plan 0035 Phase 0, awaiting review |

## Item sheets

`python3 -I tools/render_all.py <root> --only items` (or `tools/item_art.py render <root>`) regenerates
`workspace/render/items/`: the item art index ([tables/README § Item art index](../tables/README.md#item-art-index)),
the colour-shift swatches and tints ([item-palette.md](item-palette.md)), and one contact sheet per index line
(`<code>.png` for a base item, `unique_<row>_<slug>.png` and `set_<row>_<slug>.png` otherwise), with
`sheets.tsv` giving each sheet's panels or the reason a panel or sheet is missing. `index.html` there is a
local browsing page: it is never published and never committed (plan 0009 Phase 4).

A sheet is a sanity check, not evidence (ADR-0005). It simplifies the game's look in these ways:

- **No animation.** The inventory icon is frame 0. The drop animation shows the first and the last
  (resting) frame of each direction. The worn panel is one frame.
- **One reference character.** The worn layer is composed with `cof.compose_frame` on the barbarian (`ba`),
  mode `NU`, direction 4 (facing the viewer), frame 0, with the other body layers at `lit` and no other
  weapon or shield layer drawn. Weapons use their `wclass` COF (`banu<wclass>.cof`), armour uses `hth`.
  Items whose worn art exists only for another class get no worn panel and a logged reason: claws
  (`ht1`, no barbarian COF), sorceress orbs, Amazon bows and spears, druid pelts, paladin shields and
  necromancer heads (no barbarian DCC for the code). Other classes, modes and two-handed grips
  (`2handedwclass`) are not drawn.
- **Flat lighting and one palette.** Every panel uses the `units` palette with index 0 transparent, no
  light level, no `.pl2` blend or player colours, no shadow layer, no ethereal or socket overlay.
- **Colour shifts are leads.** Unique and set panels are shifted with the Phase 3 pairing (transform type
  → `.dat` file, colour row → map, `[L]` in [item-palette.md](item-palette.md)): the icon by (base
  `InvTrans`, `invtransform`), drop and worn by (base `Transform`, `chrtransform`). Base items are drawn
  unshifted. The unique and set file fallback is the index's heuristic.

## Maze renders

`python3 -I tools/maze_render.py log <root> <drlg-gen log> <out>` draws the maze levels a
`tools/gdb/drlg-gen.gdb` log recorded (the MZ1 room rectangles, with the preset files its PRC lines name).
`python3 -I tools/maze_render.py gen <root> <out> <level> <seed> …` generates them offline with the
`tools/maze_replay.py` reading model ([drlg/0006](../findings/drlg/0006-maze.md)) and writes `gen.json` beside
the images. Each level gives `-iso.png` (a tile composite) and `-map.png` (top-down: floor, wall, room borders).
The `gen` seeds are illustrative inputs, not the level seeds a game seed produces. Like the item sheets, a
render is a sanity check, not evidence (ADR-0005); `<out>` belongs under `workspace/render/`.

## Docs gate

`python3 -I tools/gate.py --full` reruns every survey registered in `SURVEYS` in `tools/gate.py`
against `workspace/`. It compares each survey's last line,
`SURVEY <tool> key=value …` (integer counts only), key by key with `tools/gate/baselines/<tool>.txt`
(ADR-0006). `--full=<tool>` runs one survey. A missing `workspace/` prints `SKIPPED: workspace absent`
and exits 0 unless `--require-workspace` is given.

To refresh a baseline after a deliberate parser change:

1. Run the gate. On a mismatch it prints the survey's new line after `now:`.
2. Copy that line, and nothing else, into `tools/gate/baselines/<tool>.txt`.
3. Commit the baseline with the parser change, and say in the commit message which count moved and why.

To register a new survey, end its output with a `SURVEY <tool> …` line, add one `Survey(...)` line to
`SURVEYS` and commit its baseline. A survey that takes over 60 s gets `opt_in=True`.

`python3 -I tools/gate.py --staged [--also PATH …]` runs the fast tier on what a commit would contain:
the git index exported to a temporary directory, with each `--also` path (the paths a chained
`git add` names) overlaid from the working tree. Another writer's unstaged edits in the same worktree
are not seen, and a link to a doc added on the same command line resolves. The commit hook does not
call it yet (backlog).
