# 0068 — Game files coverage: the last loaded tables, the COF bundles, and a ledger for every file kind

> **Status:** approved (2026-11-10, by the owner; second in the 2026-11-10 run order, after 0063; not started: the owner starts it)
> **Created:** 2026-11-10
> **Owner skill(s):** archivist, reverser, spec-writer
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0002-scope-creation-paths-and-enablers, 0005-presentation-formats-tools-only, 0014-scope-game-simulation, 0031-constants-of-the-code-image

## TL;DR

**Question:** which files in the game's archives does the project still not describe, and does any of them feed a game
rule? Today 77 table docs and 17 format docs cover the excel tables, maps, tiles, sprites, saves, strings and
animation data. Still undescribed are 12 excel tables the game loads, four the game never loads, two COF bundle
formats, and a handful of small files. One of the loaded tables, `MonItemPercent`, has columns named for drops
(`HeartPercent`, `BodyPartPercent`, `TreasureClassPercent`, `ComponentPercent`) and no spec mentions it. That makes it
a possible gap in core area 1. When this plan is done:
- every file kind in `workspace/merged/` has a line in a coverage ledger: the doc that describes it, or the ADR that
  puts it out of scope;
- the loaded tables have table docs, with their code readers;
- the rule-bearing ones are carried into the specs.

## Context

- **Survey on 2026-11-10** (`workspace/merged/`, the 1.14b reference archives as plan 0001 built them; the
  `patch_d2.mpq` question stays parked):
  - **Excel tables loaded by 1.14d with no table doc** ([data/0001](../findings/data/0001-excel-loader.md) gives
    each loader's record size):

    | Table | Record | Loader call | First read |
    |---|---|---|---|
    | `MonItemPercent` | 4 | `0x00654FA8` | possible drop rule (core) |
    | `BodyLocs` | 4 | `0x006128AC` | equip slots (items/inventory) |
    | `PlayerClass` | 4 | `0x00612833` | class codes (player/creation, save/d2s) |
    | `Events` | 2 | `0x00612E8E` | skill and item event names (skills/dispatch, stats/states) |
    | `Arena` | 28 | `0x00664A98` | the arena scoring (cut content, plan 0062) |
    | `MonSounds` | 148 | `0x00656F45` | sound: out of scope unless a column changes a rule |
    | `Overlay` | 132 | `0x00664514` | presentation, except any timing a state reads |
    | `Composit` | 52 | `0x0065B33E` | composite layers (anim/timing builds COF names through `COMPOSIT_BuildCofName`) |
    | `AutoMap` | 44 | `0x0061FE62` | client automap: out (ADR-0014) |
    | `SkillDesc` | 288 | `0x006178E1` | the skill tree's text and its calc columns (data/calc's `skilldesccode`) |
    | `Sounds` | 2 | `0x00659C16` | sound: out |

  - **Not loaded, no doc:** `Aiparms`, `MonName`, `TreasureClass` and `WeaponClass` (data/excel B1 says they have no
    loader); `SoundEnviron`; `CubeMod` and `CubeType` (not loaded, data/0001).
  - **Formats with no doc:**
    - `chars_cof.d2` (1.2 MB; named only in mpq.md's origin count);
    - seven `cmncof_a1..a7.d2` (about 95–100 KB each);
    - `lut.dn1` (Act II town);
    - the monster and unit colour `.dat` files (`palshift.dat` per monster, `greenblood.dat`, `randtransforms.dat`);
    - `gateways.txt`;
    - the `.key` key maps (one of them `defaultdebug.key`);
    - `data/local/docs/eng/a1npc.txt`–`a5npc.txt` (dialogue sound scripts);
    - the Mac resources.
- **What matters for a rule.** anim/timing takes a mode's length and event frames from `animdata.d2`. Whether 1.14d
  also reads the COF bundles, for a unit's layer list or its frames, is not known. If it does, a unit's animation inputs
  have a source no spec names.
- **Out of scope stays out.** Presentation formats are tools-only (ADR-0005), and sound, fonts, video and input are
  out (research map § Out of scope). This plan only records them in the ledger with their reason, so that "not
  described" never means "not looked at".

## Phases

### Phase 1 — Table docs and the ledger
- **Owner skill:** archivist (no Ghidra, no slot)
- **What:**
  - write a table doc, from the table template, for each of the 12 loaded tables above. Each doc gives column
    shape, types, `.bin` layout, record count and the loader, with code meaning left to Phase 2's findings links;
  - write short "not loaded" docs for the seven unloaded tables, each citing data/0001 for the absence of a loader;
  - write a coverage ledger, `docs/formats/README.md` § Coverage. It has one row per file kind or folder in
    `workspace/merged/`: the extension, the count, and the doc that describes it or the ADR or rule that puts it out.
    Every one of the 20 extension kinds in the survey gets a row.
- **Outputs:** 19 table docs under `docs/tables/`, the ledger, `tools/excel_survey.py` updated if its survey needs the new tables.
- **Done when:**
  - every excel basename in `workspace/merged/data/global/excel/` has a table doc;
  - every file kind in the survey has a ledger row;
  - the full-tier survey checks the new docs' record counts;
  - review is Tier B, or Tier A if a doc states a code meaning taken from a finding (ADR-0027).

### Phase 2 — Readers and the bundles
- **Owner skill:** reverser (static, Ghidra; no slot)
- **What:**
  1. **`MonItemPercent`:** every reader of the loaded table. What decides which row a monster uses (the row names are
     `Composited` and `NonComposited`)? What do the four percentages select at a monster's death or drop, and in what
     order against `TC_ResolveDrops`? Does any draw happen? The reader also settles the record's field widths: the
     data ties only byte +0x2 (20 in both rows) and the doc's four `u8` are the probe's first fit (P1 review).
  2. **`BodyLocs`, `PlayerClass`, `Events`:** the readers of each column, against the specs that already use them
     (items/inventory, player/creation, save/d2s, skills/dispatch). These three `.bin` files are `-txt`-only in a stock
     run (data/0001 H3b `[C]`), so the readers to find are of the compiled tables' stored row indices. And `Sounds`: data/0001 § 4
     lists only the `-txt`-only 2-byte call `0x00659C16`, while its H3b entry says the full table loads in every run;
     name the call that loads it, or show that only `sub_00481950_SoundTablesLoad`'s text read does (P1 review).
  3. **`Composit`, `Overlay`, `SkillDesc`, `Arena`:** the readers, and whether any column reaches a server-side rule
     (an overlay's timing, a `SkillDesc` calc the server runs, the arena's score). Columns read only by the client are
     named and marked presentation.
  4. **The COF bundles:** does 1.14d open `chars_cof.d2` and `cmncof_a*.d2`? Find the open, the layout it parses, and
     what the parsed records feed. If they feed a unit's layer list, frame count or event frame, compare those with
     `animdata.d2`'s records for the same names.
  5. **`lut.dn1`, the colour `.dat` files and the `.key` files:** the opener and the reader only, enough for the
     ledger's reason column.
- **Outputs:** a findings file `docs/findings/data/00NN-loaded-tables-and-bundles.md` (or one per subject), `re/symbols.csv`.
- **Done when:** each item is answered at `[I]` or better with anchors, or names the step not followed. A rule-bearing
  reader is backed by a kept-log check where a kept log already holds the value (the frame corpus, the chain logs), else
  routed as a harness piece. The Phase 3 hand-off lists what each spec gains. Review: Tier B.

### Phase 3 — Formats
- **Owner skill:** archivist (no slot)
- **What:** if Phase 2 finds the COF bundles loaded, document their format in `docs/formats/` (header, index, the
  embedded COF records against [cof.md](../formats/cof.md)), with a parser in `tools/` and a survey over all eight
  files. Do the same for `lut.dn1` if it is read for a rule. Otherwise, add each one's ledger row with Phase 2's reason.
- **Done when:** each loaded bundle has a format doc whose survey parses every file with 0 errors, or the ledger says
  why none is needed. Review: Tier B, or Tier A if a format statement comes from a finding (ADR-0027).

### Phase 4 — Specs
- **Owner skill:** spec-writer
- **What:** carry the rule-bearing readings into the specs:
  - **`MonItemPercent`:** items/tc or monsters/special, wherever the drop path is, with its draw order;
  - **`BodyLocs`:** items/inventory;
  - **`PlayerClass`:** player/creation and save/d2s;
  - **`Events`:** skills/dispatch;
  - **the bundles:** anim/timing, if they feed it;
  - **data/excel:** its loader list gains the new tables.

  Readings that are only presentation get no spec text.
- **Done when:** each rule-bearing reading is in its spec at its finding's tag, or ruled out with a reason, and
  `python3 -I tools/gate.py --full` is green. Review: Tier A, and the review closes the plan.

## Open questions

- If `MonItemPercent` changes what a monster drops, the chain's golden traces (plan 0059) may need a new field, and
  plan 0064's S2 slice would test it. That is routed at Phase 4's review, not here.
- Whether the 1.14d `patch_d2.mpq` differs in any of these files. The question stays parked, by the owner's decision.

## Implementation log

_(lanes append dated entries as phases land: what was found, the confidence reached, surprises)_

### 2026-11-10 — Phase 1 (archivist, `lane/n68a`)

Done:
- **22 table docs** under `docs/tables/` (the plan said 19). Loaded or with a `.bin`: [MonItemPercent](../tables/MonItemPercent.md), [BodyLocs](../tables/BodyLocs.md), [PlayerClass](../tables/PlayerClass.md), [Events](../tables/Events.md), [Arena](../tables/Arena.md), [Composit](../tables/Composit.md), [MonSounds](../tables/MonSounds.md), [Overlay](../tables/Overlay.md), [AutoMap](../tables/AutoMap.md), [SkillDesc](../tables/SkillDesc.md), [Sounds](../tables/Sounds.md). Not loaded: [Aiparms](../tables/Aiparms.md), [MonName](../tables/MonName.md), [TreasureClass](../tables/TreasureClass.md), [WeaponClass](../tables/WeaponClass.md), [SoundEnviron](../tables/SoundEnviron.md), [CubeMod](../tables/CubeMod.md), [CubeType](../tables/CubeType.md). Added beyond the plan's list, so that every excel basename has a doc: the four bytecode pools [ItemsCode](../tables/ItemsCode.md), [MissCode](../tables/MissCode.md), [SkillsCode](../tables/SkillsCode.md), [SkillDescCode](../tables/SkillDescCode.md) (short; the format is [calc.md](../formats/calc.md)). `leveldefs` stays in [Levels](../tables/Levels.md#leveldefsbin-156-b). The tables README rows now link them.
- **Layouts for the full tier:** `tools/excel_layouts.py` gained layouts for the 10 tables above that have a `.bin` and a `.txt` (not skilldesc's formula part, which existed), for `cubemod` and `cubetype`, and the rest of `skilldesc` (113 mapped fields, was the 42 calc offsets). Each was found with `excel_bin.py probe` and checked by `diff` over every record: 0 unexplained. The `excel_layout` baseline moved from 76 to 88 tables (cells 956 215 to 1 019 249); `excel`, `excel_layout`, `calc_bytes` and `calc` are green. This is the "full-tier survey checks the new docs' record counts"; `tools/excel_survey.py` needed no change (it already lists every basename).
- **Coverage ledger:** `docs/formats/README.md` § Coverage, one row per kind (20 kinds, 30 488 files; the sum of the row counts is checked).

Judgment calls and facts the review should look at:
1. **Four of the plan's "loaded" tables are `-txt`-only code lists** in a stock run (data/0001 § 3, § 4 ᵗ marks): `BodyLocs`, `PlayerClass`, `Events` and the 2-byte `Sounds` call. Their docs say so `[I]` and cite data/0001; the plan's table says "loaded" for all. Phase 2 item 2 should check the readers against that (a stock run reads the compiled tables' stored row indices, not these `.bin` files). Stock-loaded by call-site evidence: `MonItemPercent`, `Arena`, `Composit`, `MonSounds`, `Overlay`, `AutoMap`, `SkillDesc`. `SoundEnviron` has no table loader but is read as text by the client sound code.
2. **`MonItemPercent`'s `.bin` layout is not forced by the data**: both rows hold 0, 0, 20, 0, so only `TreasureClassPercent` (+0x2) is certain; the other three `u8` offsets are the probe's first fit (a `u16` at +0x0 also fits). The doc says so. Phase 2 item 1 should settle the widths from the reader.
3. **Code meaning stated from a finding (Tier A, ADR-0027):** the "stock run does not load it" statements for the `-txt`-only code lists (data/0001 § 3, `[I]`), `SoundEnviron` text read at `0x00481950` (data/0001 § 3), the loader call sites and record sizes (data/0001 § 4), `Composit` as the row source of the items' worn layers and `sub_0065B5E0_CompositRecord` (items/0003 `[I]`), the byte pools' `DATATBLS_LoadCodeBin` loading (data/0001 § 3). No column's meaning is taken from code; column meanings by name are `[L]`.
4. Layout surprises worth Phase 2's attention: `Sounds.bin` holds only the row index (every other column is text-only); `Events.bin` is just the row index; `MonSounds` convert triples are two `u8` + 2 pad + `s32` skill; `AutoMap`'s four `Type` columns are not in the record; `SkillDesc`'s text-key slots run all `a` parts then all `b` parts.

Left for later phases: every reader (Phase 2 items 1-5), the format docs of the COF bundles, `lut.dn1` and the colour `.dat` files (Phase 3, if Phase 2 finds them read for a rule), and the spec carry-over (Phase 4). The ledger rows for `chars_cof.d2`, `cmncof_a*.d2`, `lut.dn1`, the 72 colour `.dat` files, the two marker files and `a1npc.txt`..`a5npc.txt` say "undescribed" or "not examined" and are Phase 2/3's to close. Review tier: Tier A (code meanings taken from findings, point 3).

### 2026-11-10 — Phase 1 review (architect, Tier A, ADR-0027)

**Verdict: accept with fixes (10), applied in the review commit.** Done when: met. The tables README has a doc for all
97 basenames (the 4 `*code` docs are the right call, since the Done-when names every basename; `leveldefs` stays in Levels). The ledger's 20 rows and
every count were recounted over `workspace/merged/` (30 488 files; the `.txt` split 92 + 98, the `.dat` and `.d2` sizes).
`excel_bin.py diff` re-run on `monsounds`, `overlay`, `automap`, `skilldesc` and `monitempercent`: 0 unexplained;
`gate --full excel,excel_layout,calc_bytes,calc` green, the baseline unchanged. No doc dumps data (Arena's one row and
Events' 13 names are the whole of tiny tables, given as identity).

Fixes:
1. *under-claim:* BodyLocs, PlayerClass and Events said `[I]` "read only under `-txt`". The data/0001 H3b entry raised that to `[C]`
   (run:2026-10-27-sweep-data-load). They now say `[C]` and cite it.
2. *overclaim:* Sounds said `[I]` "the `.bin` is not the run-time source". The H3b entry that the doc cites also says "the full `sounds` table loads
   in every run", and § 4 lists no such call. The 2-byte call is now `[C]`, and the question went to Open questions and Phase 2 item 2.
   Judgment call 1 is therefore right for BodyLocs, PlayerClass and Events, and open for Sounds.
3. *overclaim:* MonItemPercent's four-`u8` layout was tagged `[C]`. Only byte +0x2 is tied to the data, and a `u16` at +0x2 fits too. The layout is now `[I]`,
   and the false "every other table follows its `.txt` order" is corrected (MonSounds does not). Judgment call 3, the widths, is accepted as
   written up. The widths were added to Phase 2 item 1.
4. *misread:* Composit said "`COMPOSIT_BuildCofName` … no finding yet". anim/0001 § 2 documents it at `[C]`/`[I]`. That finding names no composit row read.
5. *wrong anchor:* Composit's `Token` `[I]` had no anchor. It now cites items/0003 (`sub_0065B5E0_CompositRecord`).
6. *stale cross-reference:* the `skilldesc` layout in `tools/excel_layouts.py` was still `partial=True` under a "formula columns only"
   comment. It is now a full layout with `eol` as `txt_only`.
7. *bookkeeping splice:* SoundEnviron, TreasureClass and WeaponClass had two survey sentences run together. The template's `excel_layout` clause
   also did not apply to a table with no `.bin`.
8. *omission:* the Phase 2 inputs were in this log only, not in Phase 2's items (archivist rule 9). They are now in items 1 and 2.
9. *other:* the ledger's "20 kinds (18 extensions and 2 files with none)" now reads as 20 rows.
10. *other:* the `a1npc.txt` reason rested on the plan's name for the files. The first lines were read at review: UTF-16 text pairing NPC
    speech `.wav` paths with the spoken lines.

Input for Phase 2: items 1 and 2 as amended. data/0001 § 3 still says "`sounds.bin` is also loaded through the
table loader (`0x00659C16`)". Its H3b entry supersedes that, and Phase 2 should settle the sentence in the finding.
