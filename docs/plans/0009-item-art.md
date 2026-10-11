# 0009 — Item art: classic-class merge, item art index, colour shifts, per-item sheets (tools-only)

> **Status:** approved (owner request 2026-10-11)
> **Created:** 2026-10-11
> **Owner skill(s):** archivist
> **Related ADRs:** 0005-presentation-formats-tools-only, 0007-fetched-leads-only

## TL;DR

What does each item look like, on the ground, in the inventory and on a character? Plan 0006 rendered
every DC6 and DCC frame, but nothing yet ties an item to its pictures. Unique and set items still show
the base icon untinted, and the classic classes can't be composed because `d2char.mpq` is not in the
merged tree. This plan adds `d2char` to the merge, builds an item art index (every base item, unique
and set item mapped to its inventory icon, ground-drop animation and worn layer), decodes the item
colour shifts (`items/palette/*.dat` with `colors.txt`), and renders one contact sheet per item. When
it's done, one command regenerates `workspace/render/items/`, and `docs/formats/` and `docs/tables/`
describe everything the index reads. Like plan 0006, none of this is a deliverable spec (ADR-0005), and
no image enters git.

## Context

- **Scope.** ADR-0005 already brings palettes, DC6, DCC and COF in as tooling. Item colour shifts are
  palette remaps and the index only joins tables to files, so no new ADR is needed. Renders are a
  sanity check, never evidence.
- **Ready now.** `tools/dc6.py`, `tools/dcc.py` and `tools/cof.py` (`compose`), plus palettes and the
  PNG writer, from plan 0006. 465 `inv*` icons and 256 `flp*` drop animations are rendered under
  `workspace/render/dc6/global/items/`. The table docs for `Weapons`, `Armor`, `Misc` and `ItemTypes`
  are `[C]` for layout, including the art columns `invfile`, `flippyfile`, `uniqueinvfile`,
  `setinvfile`, `normcode`, `wclass`, `2handedwclass`, `Transform` and `InvTrans`.
- **Missing.**
  - `d2char.mpq` (classic-class art: 524 COFs, about 10 000 DCCs) is extracted under
    `workspace/mpq/d2char/` but left out of `merged/` by design (backlog entry, plan 0006 close).
  - There are no table docs for `UniqueItems`, `SetItems`, `colors`, `compcode` or `armtype`.
  - `items/palette/` holds 8 files of 5 376 bytes (`brown`, `gold`, `grey`, `grey2`, `greybrown`,
    `invgrey`, `invgrey2`, `invgreybrown`). 5 376 = 21 × 256, and `colors.txt` has 21 rows, which
    suggests 21 colour maps of 256 indices per file. That is a lead from the sizes alone, to be
    checked in Phase 3.
- **Leads.** None registered. Per ADR-0007, anything community-sourced must be fetched in-session and
  registered first. Otherwise it's "no lead; derived from data".
- **Priority.** Archivist lane, after any plan 0008 phase that is waiting on the archivist (the
  `LvlSub` table doc, P2 support). Phases 1–2 are independent and can start at once.

## Phases

### Phase 1 — Merge `d2char` into `merged/`
- **Owner skill:** archivist
- **What:** Add `d2char.mpq` to the merge at its game priority. That is 1000, with d2data
  (data/0002 `[I]`), giving the insertion order d2data, d2char → d2exp → patch_d2, so the 94
  overlapping `chars/ne` COFs come from d2exp. Then refresh everything that counts the merged tree.
  This closes the backlog entry "workspace/merged/ omits d2char.mpq by design".
- **Outputs:**
  - `tools/mpq_dump.py merge` change;
  - `docs/formats/mpq.md` (file counts, origins, overrides, manifest sha256);
  - regenerated `cof` and `dcc` survey baselines in `tools/gate/baselines/`, with the reason in the
    commit body;
  - updated counts in `cof.md` and `dcc.md`;
  - a re-render of `workspace/render/dcc/` and `units/` for the added files.
- **Done when:**
  - the merged tree gains exactly d2char's non-overlapping files (expected cof files 3 082 → 3 512);
  - every other survey baseline (ds1, dt1, d2s, excel, dc6) is unchanged;
  - `gate.py --full` and `--full=dcc` are GREEN after the baseline refresh;
  - one classic class (for example `ba`) composes by eye in two directions with `cof.py compose`, and
    the result is logged.

### Phase 2 — Item art index
- **Owner skill:** archivist
- **What:**
  - Document the art and identity columns of `UniqueItems` and `SetItems` (layout `[C]` against
    every record). The full stat columns are out of scope; leave them for the items/uniques work.
  - Build an index that maps every base item (Weapons, Armor, Misc), unique and set item to its
    files and transforms:
    - inventory icon: `invfile`, or `uniqueinvfile`/`setinvfile`, or the unique or set row's own
      `invfile`;
    - ground-drop animation: `flippyfile`;
    - colour transforms: `Transform`/`InvTrans` on the base, `chrtransform`/`invtransform` on
      unique and set rows;
    - for weapons and armour, the worn-art keys: `wclass`/`2handedwclass` for weapons, the
      `compcode`/`armtype` path parts for armour.
- **Outputs:**
  - `docs/tables/UniqueItems.md`, `docs/tables/SetItems.md`, `docs/tables/colors.md`,
    `docs/tables/compcode.md` and `docs/tables/armtype.md`. These are art and identity columns only,
    each saying so in its Purpose. Layouts go in `tools/excel_layouts.py`.
  - `tools/item_art.py index <root>`, which writes `workspace/render/items/index.tsv`.
  - An *Item art index* section in `docs/tables/README.md`, saying what the index joins.
- **Done when:**
  - `excel_bin.py diff` reports 0 mismatches for each new table;
  - every row of Weapons, Armor, Misc, UniqueItems and SetItems has an index line;
  - every referenced DC6 or DCC file is resolved to a path in `merged/`, or listed as missing with
    its row (target zero after Phase 1);
  - which file the game *chooses* when a unique has no own `invfile` is a heuristic (base
    `uniqueinvfile`, then base `invfile`), tagged `[L]` and owned by the reverser through the backlog.

### Phase 3 — Item colour shifts
- **Owner skill:** archivist
- **What:** Decode `items/palette/*.dat` and `colors.txt`, then render tinted icons and drop
  animations by remapping palette indices before the palette lookup.
- **Outputs:**
  - `docs/formats/item-palette.md`;
  - a `shift` option in `tools/dc6.py render` and `tools/dcc.py render`, or one shared helper in
    `tools/palette.py`;
  - tinted renders under `workspace/render/items/`;
  - a survey line `SURVEY itempal files=… maps=… errors=…` registered in the gate.
- **Done when:**
  - every `.dat` is accounted for byte for byte. The 21 × 256 split is `[C]` only if the data rules
    out the alternatives: each 256-byte map must be a plausible index remap (values within 0..255,
    for example identity outside a hue band), and the count must match `colors.txt`. Otherwise the
    split is tagged `[L]`.
  - The pairing of a `colors.txt` code with a map index, and of transform type 1..8 with a `.dat`
    file (`inv*` for the inventory, plain for worn or ground), is a data-only interpretation and stays
    `[L]` unless code is anchored (backlog to the reverser).
  - Five well-known tinted uniques are checked by eye against their in-game appearance, and the
    result is logged. A matching render does not promote a tag (ADR-0005).

### Phase 4 — Per-item sheets and one regenerate command
- **Owner skill:** archivist
- **What:** For every index line, render one contact sheet: the tinted inventory icon, the first
  frame of each direction of the drop animation, and (weapons and armour) the worn layer composed on
  one reference character with `cof.py compose`. The reference is a fixed class and mode, chosen and
  documented as a heuristic. Add an `items` step to `tools/render_all.py`.
- **Outputs:**
  - `workspace/render/items/<code-or-unique-id>.png`;
  - `workspace/render/items/index.html`, a local browsing page that is never published and never
    committed;
  - the `render_all.py` `items` step;
  - a short *Item sheets* note in `docs/formats/README.md` covering what the sheets simplify (no
    animation, one reference class, flat lighting).
- **Done when:**
  - every index line yields a sheet, or a logged reason it can't (for example, no worn art for a
    ring);
  - `render_all.py` regenerates `items/` with no exception;
  - a sample of 10 sheets is checked by eye: 3 weapons, 3 armours, 2 uniques with tints and 2 set
    items. The results are logged.

## Open questions

- Which inventory file a unique uses when its row has none, how transforms combine (base vs unique),
  and which `.dat` serves which view are game behaviour. They stay `[L]` until the reverser anchors
  the item-graphics code. Add them to the backlog in Phase 2/3; they don't block this plan.
- Socketed and ethereal appearance (the ethereal translucency, socket overlays in the inventory) is
  not modelled. Defer it.
- Player colour tinting from `.pl2` (light and blend tables) stays out, as in plan 0006.
- If Phase 4's worn-art composition pulls toward per-class or per-mode variation, keep one reference
  class and record the rest as open, rather than growing the phase.

## Implementation log

_(lanes append dated entries as phases land)_

- **2026-10-11 — Phase 1 (archivist): d2char merged.** `tools/mpq_dump.py` `MERGE_ORDER` is now
  d2data, d2char, d2exp, patch_d2. Tie order in the 1000 band: `d2char` after `d2data`, `[I]` from
  data/0002 (equal priorities: the later-opened archive is searched first; `d2char` is opened by
  `MPQ_OpenGameArchives` after `MPQ_OpenCoreArchives` opened `d2data`). `[C]` d2char ∩ d2data = 0
  paths, so the tie order changes no file today. Built as `workspace/merged.new/`, validated there,
  then swapped in (`merged` → `merged.old`, `merged.new` → `merged`); `merged.old` removed after the
  gate passed on the swapped tree.
  - Merge: 30 483 files (was 20 569), +9 914 from d2char (430 `.cof`, 9 484 `.dcc`), 394 overrides
    (was 300; +94 d2char→d2exp `chars/ne` COFs, 37 changed, 57 identical). All 20 569 earlier
    manifest rows identical. Manifest sha256 then `f18f6cd6…0362b`, superseded by `b22abd9f…50bdf` in the follow-up entry below (mpq.md holds the current one).
  - Surveys unchanged: ds1, dt1, d2s, excel, dc6 (exact baseline lines).
  - cof: `files=3082 layers=7727 frames=161768` → `files=3512 layers=11295 frames=242312`
    (errors 0, leftover_bytes 9 unchanged). dcc: `files=12233 directions=119448 frames=1396764` →
    `files=21717 directions=271176 frames=3305132` (errors 0, leftover_bits 0). Baselines refreshed.
  - cof.md and dcc.md: headline counts and survey lines updated. Their per-field distributions were
    **not** re-tallied; both docs now say they cover the pre-d2char tree (a follow-up if the
    architect wants them refreshed).
  - Re-render: `dcc.py render --only global/chars/<c>/` for am, ba, ne, pa, so: 9 737 files,
    1 961 376 frames, 0 failures. `cof.py compose workspace/merged chars/ba a1 1hs --dirs 0,4` and
    `… nu 1hs --dirs 0,4`: by eye, a complete barbarian with axe and shield, all nine layers in place,
    sensible draw order, facing differently in direction 0 and direction 4. Sanity check only, not
    evidence.
  - Gate: `gate.py --full` GREEN (6 surveys); `--full=dcc` GREEN (322 s).
- **2026-10-11 — Phase 1 follow-up (archivist): five patch_d2 item icons named and merged.** The
  Phase 2 review traced five "missing" icons to unnamed `patch_d2` entries (`File00000205..209.dc6`).
  `mpq_dump.py names --excel <dir>` now derives `data\global\items\<x>.dc6` from every `invfile`,
  `uniqueinvfile`, `setinvfile` and `flippyfile` cell of weapons, armor, misc, uniqueitems and
  setitems (6 new candidates); `extract` takes an optional archive subset. Re-extracting both
  patches names `inv{toa,tes,ceh,bet,fed}.dc6` (`[C]`): patch_d2 209/209, patch_d2-classic 1142/1146.
  The candidate tie-break between case variants was hash-order dependent; it is now
  (lower-case, code-point), which changed the original-name column of 47 manifest rows (path, size
  and sha256 unchanged) and makes the manifest reproducible (two builds, same hash).
  - Re-merged through `merged.new`, validated, swapped; `merged.old` removed after the gate.
    30 488 files (+5, all new paths under `data/global/items/`, origin patch_d2 209), 394 overrides
    unchanged. Manifest sha256 `b22abd9f…50bdf`.
  - dc6: `files=1676 frames=24527` → `files=1681 frames=24532` (errors 0, leftover 0); baseline
    refreshed. ds1, dt1, d2s, excel, cof and dcc unchanged.
  - Phase 2 `item_art.py index` on the new tree (scratch output): `missing=1`, only `flptail` on the
    unused Misc row `tal`.
  - Gate: `--full` GREEN, `--full=dcc` GREEN.
- **2026-10-11 — P1 reviewed (architect): accepted with fixes 1–4; applied.**
- **2026-10-11 — Phase 2 (archivist): item art index.**
  - Table docs, art and identity columns only: [UniqueItems](../tables/UniqueItems.md),
    [SetItems](../tables/SetItems.md), [colors](../tables/colors.md), [compcode](../tables/compcode.md),
    [armtype](../tables/armtype.md). Layouts in `tools/excel_layouts.py`; the two big tables are
    `partial` layouts (record head only), and `excel_bin.py diff` now names unmapped columns of a
    partial layout as out of scope. `excel_bin.py diff`: uniqueitems 402 × 18 = 7 236 cells,
    setitems 127 × 16 = 2 032, colors 21 × 1, compcode 115 × 1, armtype 3 × 2, **0 mismatches** each.
    Layout `[C]` by data except the SetItems pairs the data can't separate (`chrtransform`/`invtransform`
    equal in every row; `flippyfile`, `invfile`, sounds blank in every row), which are `[L]`.
  - `tools/item_art.py index <root>` → `workspace/render/items/index.tsv` (1 188 lines: weapons 306,
    armor 202, misc 151, uniqueitems 402, setitems 127) and `missing.tsv`. Missing references: **6**
    on the pre-`d2char` tree (`merged.old`, 3 082 COFs) and **6** on the merged tree with `d2char`
    (3 512 COFs): five Misc inventory icons (`invtoa`, `invtes`, `invceh`, `invbet`, `invfed`) and
    Misc `tal`'s `flptail`. They are in no extracted archive, so Phase 1 could not fix them; the plan's
    target of zero is not reachable from the data. Worn keys all resolve on both trees; players per
    key rose from 2 to 7 with `d2char`.
  - Surprises: no set item has its own `invfile` or `flippyfile` (all blank), so every set icon comes
    from the base (35 via `setinvfile`, 92 via `invfile`); only 1 unique falls back to a base
    `uniqueinvfile` (140 own, 248 base `invfile`, 13 label or base-less rows with none). UniqueItems
    `index` is not unique (`Rainbow Facet` ×8, `Azurewrath` ×2). `colors.bin` is loaded only under
    `-txt` [I], so tables carry colour row indices; `compcode` lists 115 codes but 69 DCC component
    codes (for example `cap`) are not in it. `WeaponClass.txt` has no loader [I] (data/0001).
  - **2026-10-11 correction (review):** "not reachable from the data" was wrong. The five icons were
    unnamed `patch_d2.mpq` entries; Phase 1 (`ac8f5ce`) names and merges them, and
    `item_art.py index workspace/merged` now reports `missing=1` (`flptail`, unused Misc row `tal`,
    in no archive). Also fixed: `--out` accepts a directory.
  - Backlog: archivist → reverser entry for the unique/set file fallback, transform combination,
    `.dat` per view, and the worn-layer keys.
