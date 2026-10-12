# 0015 — Backlog sweep: static loose ends from the closed plans

> **Status:** in-progress (approved 2026-10-12; Phases 1–4 started 2026-10-12)
> **Created:** 2026-10-12
> **Owner skill(s):** archivist, reverser, spec-writer
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0003-runtime-experiments

## TL;DR

**Question:** which of the open `docs/backlog.md` entries can be closed by reading code, data or existing logs, with
no new harness run? Plans 0004, 0005, 0008, 0009, 0012 and 0013 left small questions behind: table converters
and unknown fields in the excel loader, the item-graphics code behind plan 0009's heuristics, save-format details
the save spec lists as open, and links and tag promotions that other lanes' work made possible. This plan sweeps
them in one pass per lane, so each entry ends struck through, narrowed with a pointer to the plan that owns the
rest, or answered with a finding. Nothing here needs the wine harness, so it runs next to plan 0011 (which holds
`:7`) and plan 0014.

## Context

- The backlog had 17 unstruck entries on 2026-10-12. Triage (this plan's input):

| Entry (date, from → to) | Topic | Where it goes |
|---|---|---|
| 2026-10-12 spec-writer → archivist | `d2s.py survey` property tally over every list | Phase 1 |
| 2026-10-11 archivist → reverser | excel loader cell converters (case-insensitive lookup, digit parsing, defaults, key lookup, 4-char codes, string keys) | Phase 2 |
| 2026-10-11 archivist → reverser | unknown no-column fields (TCEx, items, monstats, levels): padding or runtime-filled | Phase 2 |
| 2026-10-11 spec-writer → reverser | `specs/data/excel` open points; only (c), run-time string lookup, left | Phase 2 (check against data/0003, likely strike) |
| 2026-10-12 archivist → reverser | data/0003 5382 rule promotion; cite MonStats2 in monsters/0001 | Phase 2 |
| 2026-10-11 archivist → reverser | `LvlTypes`/`lvlmaze` columns; only `Expansion` read width and the `lvlmaze` columns left | Phase 2 (`lvlmaze` columns → `drlg/maze`) |
| 2026-10-12 spec-writer → reverser | save spec gaps: property framing details, `has_class`, `body`/`store` for modes 3/5, ear field position, `D2S_ReadMercHeader` order | Phase 3 |
| 2026-10-11 archivist → reverser | D2S fields; open: (d) runeword id, (e) affix ids, bit 13's clearer | Phase 3 (bit 13 static); (d) → `items/sockets-runewords`, (e) → `items/affixes` |
| 2026-10-11 archivist → reverser | item graphics: inventory file fallback, transform combination, `.dat` per view, Armor `component` | Phase 4 |
| 2026-10-12 archivist → reverser | item colour shifts: palette file order, map layout, identical files | Phase 4 |
| 2026-10-12 reverser → spec-writer | `rng/seeds` game-seed consumer order | Phase 5 |
| 2026-10-12 archivist → spec-writer | links to MonStats2 and tbl § Override order | Phase 5 |
| 2026-10-11 archivist → architect (+human) | 1.14d `patch_d2.mpq` vs 1.14b | out: needs the owner |
| 2026-10-11 archivist → reverser | `*code.bin` formula bytecode | out: a future `data/calc` plan |
| 2026-10-11 reverser → reverser | DS1/DT1 open bits, object flags, `0x004E6C50`, collision bits | out: `drlg/preset`, `drlg/collision` plans |
| 2026-10-11 reverser → architect, architect → reverser | party NoDrop case, kill harness | out: plan 0011 (running) |
| 2026-10-12 reverser → reverser | classic `itemratio` rows contradicted | out: plan 0010 Phase 2 |

- Each phase's input is the entry text; the phase may narrow an entry when the answer needs a run, naming the case
  for a later plan instead of running it.

## Phases

### Phase 1 — Survey tally
- **Owner skill:** archivist
- **What:** make `tools/d2s.py survey` count property ids over every property list (main, set bonus, runeword) and
  the grouped ids (17, 48, 50, 52, 54, 57).
- **Outputs:** `tools/d2s.py`, the `d2s` gate baseline if its line changes, a note in [d2s.md](../formats/d2s.md).
- **Done when:** one command prints the counts quoted in [specs/save/d2s § J](../specs/save/d2s.md#j-property-list-framing)
  (25 full saves: 143 lists, 137 properties, 18 with a param, 44 distinct ids; groups 17 ×5, 50 ×2, 48 ×1, 54 ×1),
  or the spec's numbers are corrected through the backlog; `gate.py --full` green; the entry struck.

### Phase 2 — Excel loader and string-table loose ends
- **Owner skill:** reverser
- **What:** read the excel loader's cell converters and the readers of the no-column fields; close the data/excel
  and data/0003 follow-ups.
- **Outputs:** an update to [data/0001](../findings/data/0001-excel-loader.md) (or a new `data/0004` if it outgrows
  it), [data/0003](../findings/data/0003-string-tables.md), [monsters/0001](../findings/monsters/0001-level-pool.md)
  § Data touched, `re/symbols.csv`.
- **Done when:**
  - each converter rule the archivist's entry lists has an address and `[I]`, or `[C]` where `excel_bin.py diff`
    over every laid-out table is the second source (evidence rule 2), or is contradicted with the code shown;
  - each listed no-column field is named padding (no reader or writer found, with the search stated) or
    runtime-filled (writer named);
  - the 5382 rule is promoted or kept with a reason, and the string-lookup point (c) of the data/excel entry is
    struck with a link to data/0003, or narrowed;
  - the `LvlTypes` `Expansion` read width is stated; the `lvlmaze` columns are handed to `drlg/maze` in the entry.

### Phase 3 — Save-format details
- **Owner skill:** reverser
- **What:** settle statically the save spec's open framing and field questions, and find what clears item flag
  bit 13 between a drop's creation and its save.
- **Outputs:** [save/0001](../findings/save/0001-d2s-io.md), `re/symbols.csv`.
- **Done when:** each point of the spec-writer → reverser entry (follower without head, missing follower, shift kind,
  the fixed-field encoder, `has_class`, `body`/`store` in modes 3/5, the ear fields, `D2S_ReadMercHeader` order) is
  answered `[I]` with an address, or narrowed to a named run case; the four bit-13 clear sites are each attributed
  to a caller path, and the pickup path's site is named `[I]` or ruled out, with the breakpoint that would confirm it
  written down for the next save run. The D2S entry is narrowed to (d)/(e) with their owning rows.

### Phase 4 — Item graphics
- **Owner skill:** reverser
- **What:** read the item-graphics code behind plan 0009's heuristics.
- **Outputs:** `docs/findings/items/0003-item-graphics.md` (new), `re/symbols.csv` (subsystem `items/graphics`).
- **Done when:** the finding states, with addresses and `[I]` or better: which inventory and ground file a unique or
  set item with no file of its own uses; how base `Transform`/`InvTrans` and the row's `chrtransform`/`invtransform`
  combine; which of the eight `items/palette` files serves which transform type and view, and whether map `c` is the
  256 bytes at `c·256` with index 0 remapped; whether `brown`/`gold`/`grey` are ever treated differently; Armor
  `component` and the `armtype` pairing; who reads `compcode.bin`. Each answer is checked against plan 0009's
  index (`tools/item_art.py`): agreements noted, disagreements sent to the archivist through the backlog. Both item
  art entries struck or narrowed. (The tint pairing `[L]` of item-palette.md becomes `[I]` or is contradicted.)

### Phase 5 — Spec links and small updates
- **Owner skill:** spec-writer
- **What:** apply the backlog links and the Phase 2–3 answers to the specs they touch.
- **Outputs:** [rng/seeds](../specs/rng/seeds.md) (game-seed consumer order), [monsters/pool](../specs/monsters/pool.md)
  (MonStats2 link), [data/excel](../specs/data/excel.md) (I2 and open questions), [save/d2s](../specs/save/d2s.md)
  (open questions answered in Phase 3).
- **Done when:** every spec-writer entry is struck; each touched spec keeps its status (review-driven corrections),
  its tag counts are right, and each tag raised cites the finding that raised it.

## Open questions

- Phases 2–4 may find answers that need a run. They narrow the entry to a named case instead; the case joins the
  next plan that holds the harness (0014 Phase 2 or a later save run).
- Phase 4 could grow into an `items/graphics` subsystem. If it does, the reverser says so and the architect decides
  whether to open a research-map row; tools-only rendering stays under ADR-0005.

## Implementation log

_(lanes append dated entries as phases land)_

- **2026-10-12 — Drafted (architect).** From the open backlog after plans 0012 and 0013 closed and the archivist
  backlog pass merged; owner request to turn the backlog into a plan.
- **2026-10-12 — Approved (human).** No changes to the draft; not started yet.
- **2026-10-12 — Phase 1 landed (archivist).** `tools/d2s.py survey` tallies every property list (main, set bonus,
  runeword): lists, properties, those with a param, distinct ids and the grouped ids 17/48/50/52/54/57, in three
  summary lines and in the gate `SURVEY d2s` line (new keys; `tools/gate/baselines/d2s.txt` updated, 23 gate saves:
  108 extended items, 111 lists, 83 properties, 10 with a param, 43 ids, groups 17 ×3, 50 ×2, 48 ×1, 54 ×1). The
  spec's 25 full saves are the gate's 21 plus the four run:2026-10-12-d2s-io saves; the same command over them
  prints exactly the § J counts (140 extended, 143 lists, 137 properties, 18 with a param, 44 ids; 17 ×5, 50 ×2,
  48 ×1, 54 ×1), so no correction goes to the spec-writer. Surprise: [d2s.md](../formats/d2s.md#property-lists)'s
  "30 distinct ids" was the histogram's 30-entry print limit, corrected to 43. Backlog entry struck.
- **2026-10-12 — Phase 4 done (reverser).** [items/0003](../findings/items/0003-item-graphics.md), static, all `[I]`: inventory and ground cel choice (`ITEMGFX_SelectCelName` `0x004DABC0`), the colour decision (`ITEMGFX_GetItemShift` `0x0062C100`: inventory `InvTrans` × `invtransform`, ground and worn `Transform` × `chrtransform`; magic/rare affix, gem and state colours), type *n* → file *n*, map *c* at `c·256`, `gold`/`brown` never served, worn layers from `component` and the `armtype` part pairing, `compcode` read only for monster components. 46 `re/symbols.csv` rows (`items/graphics`). Checked against `tools/item_art.py`: agrees on file order, map, view pairing, ground cel, worn keys; disagrees on the inventory fallback for 41 rows (`VarInvGfx`) and on types 3/4 (backlog → archivist). Both item-art backlog entries struck; index 0 and the composite `+1` stay open as named cases. The finding suggests the architect decide on an `items/graphics` research-map row.
- **2026-10-12 — Phases 1 and 4 reviewed (architect).** Phase 1: **accept** (merged with gate rule E9 in the same
  branch): the § J counts reproduce from the 21 gate saves plus the four run:2026-10-12-d2s-io saves; the d2s.md "30
  ids" correction is right. Phase 4: **accept**. Spot-checked in r2: `0x00600C20` returns no map for type 0, ≥ 9,
  colour ≥ 21 and types 3–4 (gold, brown); `0x004DAC69` `jle` after the unique-row lookup `0x00629DA0`; `0x00505525`
  `imul 0x6900` / `push 0x1500` / `+0x842710`. All `[I]`, no `[C]` claimed; the index-0 remap and the composite +1 are
  named cases, which meets the Done when ("narrowed to a named case"). No research-map row for `items/graphics`:
  presentation stays tools-only under ADR-0002/0005; the finding is the reference for `tools/item_art.py`, and its
  disagreements (41 inventory rows, types 3/4) are with the archivist on the backlog.
- **2026-10-12 — Phase 2 landed (reverser).** New finding [data/0004](../findings/data/0004-cell-converters.md): every converter rule of the archivist entry has its code (column map `0x006BCE20`, cell pass `0x006BD780`, missing-column defaults pass `0x006BDFA0` / jump table `0x006BE128`, string keys `0x006117B0`) and is `[C]` with `excel_bin.py survey` (28 tables, 555 659 cells, 0 unexplained) as the data source. No-column fields: items `+0x0F0`/`+0x114`/`+0x122` are compiled columns (`gemoffset`, `missile`, `subtype`) and `+0x0F0` is rewritten by `GEMS_Load`; monstats `+0x02A`, `+0x036`/`+0x038`, `+0x04A`/`+0x04B` and levels `+0x16E`/`+0x1BE` are runtime-filled (writers named); items `+0x12E`, monstats `+0x00A` and `+0x00F` bits 5–7, levels `+0x00A` are padding with the search stated `[I]`. Also found: `Levels` `camt1..4` all compile into `+0x0DC`. The 5382 rule is `[C]` in data/0003; data/excel point (c) struck; monsters/0001 cites MonStats2 and the `+0x025` compiler callback; `LvlTypes` `Expansion` is an s32 read as a dword, the `lvlmaze` columns narrowed to drlg/maze. Backlog: five entries struck or narrowed, two new (archivist table docs, spec-writer Phase 5 input). Static only; nothing needs a run.
- **2026-10-12 — Phase 3 landed (reverser).** [save/0001 §8](../findings/save/0001-d2s-io.md), all `[I]` with addresses: a follower without its head is written and read as an ordinary property, a missing follower is written as its `Save Add`, `>> ValShift` is arithmetic, the fixed fields use their stat's `Save Bits`/`Save Add` without `ValShift` (sockets, gold, quantity without `Save Add`), clamps are unsigned; `has_class` = an automagic affix at item data `+0x36` (expansion item, not set/unique, base `auto prefix`); modes 3/5 write no `body`/`store`; ear fields replace `code` in the simple form; `D2S_ReadMercHeader` runs after the corpses. Bit 13: the four clear sites attributed (per-frame unit pass, gold-pile spawn, item copy ×2); the pickup is ruled out, the ground pass `0x00553351` clears a drop; run case for the next save run: breakpoint `0x00553357` (§8). D2S entry narrowed to (d)/(e) with their rows; spec-writer entry struck, a new one for Phase 5.
- **2026-10-12 — Phase 2 review fixes F1–F2 (reverser).** data/0004 now tags each converter sub-rule `[C]` only with the cells that exercise it (absent columns of types 1, 2, 3, 4, 6, 9, 0x0D, 0x0F, 0x14, 0x16, 0x19; the space cells of misc `TMogMin`/`TMogMax`; misc `rarity` 999; `staff`/`ring `; blank itemtypes refs and `cr_lancer8`/`seq_*` duplicates; each string-table precedence pair and 15 unknown keys) and `[I]` for the rest (defaults of types 5, 7, 8, 0x0A–0x0C, 0x0E, 0x10–0x13, 0x15, 0x17, 0x18, 0x1A; bytes ≥ 0x80; type 5). `Lilith` is `patchstring.tbl` entry 1154 (index 11154), not entry 0, so it stays the `[L]` exception; the 5382 rule stays `[C]`.
- **2026-10-12 — Phases 2 and 3 reviewed (architect).** Phase 3: **accept** (r2: `sar` at 0x00630ED9, the unsigned
  clamp at 0x0062AF50, the clear site 0x00553351 `push 0x2000` for 0x006280D0). Phase 2: **accept with fixes F1–F2
  (applied, `ca82c1a`)**. F1: each converter sub-rule is `[C]` only where a named cell exercises it, else `[I]`
  (checked: misc `rarity` 999 ×7, `TMogMin`/`TMogMax` blank in 3 rows, magicprefix `itype1` `staff` ×9). F2: `Lilith`
  is patchstring entry 1154 (index 11154), not entry 0, so it stays the `[L]` exception, with its index recorded.
  Merge note: both lanes named 0x006372C0. Kept `GEMS_GetRecord` (data/excel) and renamed
  `sub_006372C0_GemsRecord` in items/0003. Phase 5 (spec-writer) is next, with its inputs on the backlog.
- **2026-10-12 — Phase 5 landed (spec-writer).** Branch `p0015e`, one commit per spec; statuses unchanged.
  [rng/seeds](../specs/rng/seeds.md): game-seed draw 1 = `MonRegionsInit` `[C]`, the next callers `[I]`; consumer-order
  question narrowed; {C: 54, I: 17, L: 6} → {55, 18, 6}. [monsters/pool](../specs/monsters/pool.md): MonStats2 cited,
  `+0x025` compiled sum `[I]` (data/0004) with the 609-record stock match `[C]`, `TotalPieces`; one `[L]` folded;
  {75, 31, 5} → {76, 32, 4}. [data/excel](../specs/data/excel.md): new § J (`.txt` compiler, the data/0004 `[C]`/`[I]`
  split kept per sub-rule), I3 index → text `[I]`, the 5382 converter `[C]`, H3 observed for the pool `[C]`; two open
  questions folded, `Lilith` kept `[L]`, the padding-search limit added `[L]`; {20, 71, 8} → {40, 93, 8} (after review fix F1).
  [save/d2s](../specs/save/d2s.md): save/0001 §8, all `[I]`: unsigned clamp, followers raw, fixed fields, `has_class`,
  modes 3/5, ears, merc header order, bit-13 sites (I6, state diagram); two open questions folded, bit 13 narrowed to
  the `0x00553357` run case; {82, 118, 9} → {82, 144, 7}. Open questions left: rng/seeds 6, monsters/pool 4,
  data/excel 8, save/d2s 7. Backlog: four spec-writer entries struck; review request to the architect.
