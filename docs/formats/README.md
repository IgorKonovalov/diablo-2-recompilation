# Formats

One file per container or binary format (`mpq.md`, `installer.md`, `excel-bin.md`, `ds1.md`, `dt1.md`,
`palette.md`, `item-palette.md`, `dc6.md`, `dcc.md`, `cof.md`, `cofbundle.md`, `animdata.md`, `d2s.md`, `expfield.md`). Owned by `archivist`. Each file covers layout tables with offsets and
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
| COF bundles (`chars_cof.d2`, `cmncof_a1..a7.d2`) | [cofbundle.md](cofbundle.md) | `tools/cofbundle.py` | plan 0068 Phase 3, awaiting review |
| animation data (`animdata.d2`) | [animdata.md](animdata.md) | `tools/animdata.py` | plan 0050 Phase 0, reviewed |
| item colour shifts | [item-palette.md](item-palette.md) | `tools/palette.py` (`itempal`) | plan 0009 Phase 3, awaiting review |
| expanding-field table (`expfield.d2`) | [expfield.md](expfield.md) | `tools/expfield.py` | plan 0060, `lane/a69`, reviewed |
| golden traces (`.jsonl` conformance cases) | [golden-trace.md](golden-trace.md) | `tools/golden.py` | plan 0059 Phases 1-2, awaiting review |
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

## Coverage

One row per file kind in `workspace/merged/` (the merged tree of [mpq.md](mpq.md)): 30 488 files in 20 rows: 18 extensions
(`.txt` split into two rows) and one row for the 2 files with no extension. The status is **described** (a format or table doc covers it), **out of scope** (an ADR or the
research map's out-of-scope list puts it out; the reason is named) or **undescribed** (no doc yet; the plan that owns
it is named). Counts are `[C]`: `find workspace/merged -xdev -type f` grouped by lower-cased extension and by folder
(plan 0068 Phase 1, survey of 2026-11-10); a doc's own count, where it has one, is over the same files. "Out of scope"
here means the content was not examined beyond its size and place; the doc rules of
[ADR-0005](../adrs/0005-presentation-formats-tools-only.md) (presentation formats are tools-only) and the research map's
[Out of scope](../specs/README.md#out-of-scope-adr-0002-adr-0005-adr-0014-adr-0025-adr-0026) list apply.

| Kind | Files | Where | Status and doc or reason |
|---|---:|---|---|
| `.dcc` | 21 717 | `chars` 14 421, `monsters` 4 773, `objects` 1 748, `missiles` 391, `overlays` 384 | described: [dcc.md](dcc.md) (tooling only, ADR-0005) |
| `.cof` | 3 512 | `objects` 1 461, `monsters` 1 295, `chars` 756 | described: [cof.md](cof.md). The client reads the loose files too (a COF cache fed by the bundles at an act load, and the loose `%s\%s\COF\%s%s%s.COF` path, [data/0006 § 4](../findings/data/0006-loaded-tables-and-bundles.md#4-the-cof-bundles-plan-item-4)); presentation, no server rule reads one |
| `.ds1` | 2 276 | `tiles` | described: [ds1.md](ds1.md) |
| `.dt1` | 263 | `tiles` | described: [dt1.md](dt1.md) (pixels tooling only, ADR-0005) |
| `.dc6` | 1 681 | `global/items` 737, `global/ui` 495, `local/ui` 354, `monsters` 56, `local/font` 14, `objects` 13, `uncompoverlays` 11, `overlays` 1 | described: [dc6.md](dc6.md) (tooling only, ADR-0005) |
| `.wav` | 579 | `sfx`: `monster` 450, `skill` 52, `ambient` 24, `combat` 23, `object` 14, `cursor` 6, `item` 6, `quest` 4 | out of scope: sound (research map, out-of-scope list) |
| `.txt` (excel) | 92 | `data/global/excel/` | described: one doc per table in [tables/README.md](../tables/README.md): 97 table basenames, 92 with a `.txt`; of the 5 `.bin`-only ones the 4 `*code.bin` pools have docs and `leveldefs` is in [Levels](../tables/Levels.md#leveldefsbin-156-b) |
| `.txt` (other) | 98 | `local/lng` 72, `local/ui` 13, `local/font` 6, `local/docs/eng` 5, `global/gateways.txt` 1, `local/color.txt` 1 | `local/lng` (language-folder text such as `english.txt`, `*input.txt`) and `local/ui` (menu, credits, level-name lists): out of scope, localisation and UI text; the strings the game shows come from the `.tbl` files ([tbl.md](tbl.md)). `local/font` (glyph-width lists and a `readme.txt`): out of scope, fonts. `local/docs/eng/a1npc.txt`..`a5npc.txt` (103 112 B for act 1): out of scope: UTF-16 text that pairs each NPC's speech `.wav` path with the spoken line (sound). `[I]` Never opened: no `npc.txt` name in the image ([data/0006 § 5](../findings/data/0006-loaded-tables-and-bundles.md#5-lutdn1-the-colour-dat-files-the-key-maps-gatewaystxt-the-npc-dialogue-files-plan-item-5)). `gateways.txt` (418 B): out of scope, `[I]` the client's Battle.net gateway setup (`DATA\GLOBAL\gateways.txt` named at 0x00518313, client network code). `color.txt` (3 B): out of scope, presentation |
| `.dat` | 98 | `palette` 18, `items/palette` 8, `monsters/*/cof/palshift.dat` 70 (2 048 B each), `monsters/randtransforms.dat` 1 (7 680 B), `monsters/greenblood.dat` 1 (256 B) | `palette` 18: described, [palette.md](palette.md). `items/palette` 8: described, [item-palette.md](item-palette.md). `palshift.dat`, `randtransforms.dat` and `greenblood.dat` (72 files): out of scope, presentation (ADR-0005); `[I]` client colour transforms: `GreenBlood.dat` and `RandTransforms.dat` are loaded once by `0x00476EA0` from the client start-up function `0x0044E200` (a second `GreenBlood.dat` loader, `0x00476E30`, has no caller), and `\Cof\palshift.dat` is appended to a monster's directory by `0x00477170`, called from client code ([data/0006 § 5](../findings/data/0006-loaded-tables-and-bundles.md#5-lutdn1-the-colour-dat-files-the-key-maps-gatewaystxt-the-npc-dialogue-files-plan-item-5)); no rule reads them |
| `.bin` | 93 | `data/global/excel` 92, `data/global/realms.bin` 1 (97 B) | excel 92: described, [excel-bin.md](excel-bin.md) and [tables/README.md](../tables/README.md). `realms.bin`: out of scope, realm and network (research map, out-of-scope list) |
| `.tbl` | 36 | `local/lng` 20 (`string.tbl`, `patchstring.tbl`, `expansionstring.tbl` per language), `local/font/latin` 16 | `local/lng`: described, [tbl.md](tbl.md). `local/font/latin`: out of scope, font metrics (tbl.md says it does not cover them) |
| `.pl2` | 16 | `palette` | described: [palette.md](palette.md) (tooling only) |
| `.d2` | 11 | `global/animdata.d2`, `global/eanimdata.d2`, `global/expfield.d2`, `global/chars_cof.d2` (1 278 822 B), `global/cmncof_a1..a7.d2` (79 910 to 190 815 B each) | `animdata.d2`, `eanimdata.d2`: described, [animdata.md](animdata.md). `expfield.d2`: described, [expfield.md](expfield.md). `chars_cof.d2` and the seven `cmncof_a*.d2`: described, [cofbundle.md](cofbundle.md) (tooling only, ADR-0005). `[I]` The client opens `cmncof_a1..a4` and `cmncof_a6` into its COF cache at an act load; `chars_cof.d2`, `cmncof_a5.d2` and `cmncof_a7.d2` are named nowhere in the image ([data/0006 § 4](../findings/data/0006-loaded-tables-and-bundles.md#4-the-cof-bundles-plan-item-4)) |
| `.rsrc` | 4 | `local/macui/<lang>/d2resources.rsrc` (13 661 B for `eng`) | out of scope: Mac client UI resources (presentation), not examined |
| `.pcx` | 4 | `local/macui` (logos, about 1.2 MB each) | out of scope: Mac client logos (presentation), not examined |
| `.scc` | 2 | `local/macui`, `local/macui/eng` (`vssver.scc`, 48 B) | out of scope: a source-control sidecar with no game content, not examined |
| `.key` | 2 | `local/cmd/eng/default.key` (1 126 B), `defaultdebug.key` (1 336 B) | out of scope: key maps (input handling). `[I]` `default.key` is read only by the client's key configuration (`0x00469650`, `0x00469780`, `0x004698D0`); `defaultdebug.key` is named nowhere ([data/0006 § 5](../findings/data/0006-loaded-tables-and-bundles.md#5-lutdn1-the-colour-dat-files-the-key-maps-gatewaystxt-the-npc-dialogue-files-plan-item-5)) |
| `.map` | 1 | `local/font/latin/default.map` (1 168 B) | out of scope: font map |
| `.dn1` | 1 | `global/tiles/act2/town/lut.dn1` (16 758 B) | out of scope: `[I]` never opened, no string `lut.dn1` or `.dn1` in the whole image in any case ([data/0006 § 5](../findings/data/0006-loaded-tables-and-bundles.md#5-lutdn1-the-colour-dat-files-the-key-maps-gatewaystxt-the-npc-dialogue-files-plan-item-5)); no rule reads it, so no format doc |
| (no extension) | 2 | `data/iamexpansion` (32 B), `data/local/use` (1 B) | `data/local/use`: described in [data/0002](../findings/data/0002-mpq-precedence.md) (`[I]` its first byte is the language id that fills the `%s` of `data\local\lng\%s\string.tbl`; values above 13 become 0). `data/iamexpansion` (a sentence of text): undescribed, plan 0068 Phase 2 did not examine it; whether the game tests it is not known, `[L]`; not rule-bearing (text marker), left open |
