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
  routed as a harness piece. The Phase 3 hand-off lists what each spec gains. Review: Tier B (checked 2026-11-10: the `MonItemPercent` no-reader claim stays `[I]`, the dead-code and no-other-reference lines retagged from `[C]`).

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

### 2026-11-10 — Phase 2 (reverser, `lane/n68r`)

Done: [data/0006](../findings/data/0006-loaded-tables-and-bundles.md), items 1–5, 29 `re/symbols.csv` rows (3 `C`,
26 `I`; the lane's request said 6 and 23), `tools/n68r_bundles.py` (the bundle check), kept outputs in `workspace/logs/n68r/` (manifest passes
`sha256sum -c` there). data/0001 § 3's superseded `sounds.bin` sentence and its H3b clause "the full `sounds` table
loads in every run" carry dated corrections pointing to data/0006 § 2.4.

1. **`MonItemPercent` is no gap in the drop chain.** Loaded in every run `[C]` (the six H3b runs that reach it log
   the call), read by nothing: its record getter 0x00654FE0 and table getter 0x00654FD0 have no caller in either tool,
   and no instruction names its globals or their `g_DataTables + 0x1850/0x1854` form outside the loader and the free.
   So no row choice, no draw, no step in `TC_ResolveDrops`' order `[I]`. Field widths: `TreasureClassPercent` u8 at
   `+0x2` `[C]` (descriptor and data), the other three u8 at `+0x0`, `+0x1`, `+0x3` `[I]` (descriptor). No kept log
   holds a read, so the run-time absence is a harness piece:
   [backlog](../backlog/2026-11-10-reverser-reverser-plan-0068-monitempercent-read-watch.md).
2. **`BodyLocs`, `PlayerClass`, `Events`** are index spaces; every reader of a stored index is listed with its spec.
   New: the 17 `UNIT_DispatchEvent` calls never pass ids 4 (`doactive`) or 8 (`domissileattack`), so stat 195's
   `itemevent2` handler never runs; item-stat registration needs an id `> 0`, skill registration `≥ 0`; id 13 is
   dispatched at a monster's death with no Events row. **`Sounds`:** no call loads `sounds.bin` in a stock run; only
   the client's text read at 0x00481950 happens, and only with sound on (the H3b stock runs, `-ns`, read no `sounds`
   file `[C]`).
3. **`SkillDesc` is rule-bearing:** `sub_00644180_SkillLevelBonus`, the bonus in every effective skill level, adds stat
   188 by the skill's `SkillPage`; § 3.2 has the whole formula (stats 127, 83, 188, 97 with its cap of 3 on own-class
   skills, 126, 107, state 134), `[I]`, which no spec states. Its return is logged in play (`CUL`, 1 339 values) but
   not its inputs: [harness piece](../backlog/2026-11-10-reverser-reverser-plan-0068-skill-level-bonus-check.md).
   `Overlay` (the server reads only the count, as an id bound), `Composit`, `MonSounds`, `AutoMap`: client only.
   `Arena`: read by the server's kill and death scoring in every game (`sub_0053F720_ArenaScoreKill`), into a
   per-player score no core-area rule reads in this reading.
4. **The COF bundles feed only the client's COF cache.** The client opens `cmncof_a1..a4.d2` and `cmncof_a6.d2` at
   an act load; `chars_cof.d2`, `cmncof_a5.d2` and `cmncof_a7.d2` are named nowhere. The loader's record layout parses
   all eight to the byte (6 726 COFs, 0 errors) `[C]`; 11 COFs differ from `animdata.d2` in frames and 2 in event
   frames, client drawing only.
5. **`lut.dn1` and `a1npc.txt`..`a5npc.txt` are never opened**; the colour `.dat` files, the `.key` maps and
   `gateways.txt` are client-only.

**Phase 3 (archivist) must document:**
- the COF bundles: by ADR-0005 they are presentation, read by the client only, so a format doc is optional. The
  ledger row needs the reason (client COF cache, data/0006 § 4) and the never-opened files (`chars_cof.d2`,
  `cmncof_a5.d2`, `cmncof_a7.d2`). If a doc is written, data/0006 § 4 gives the layout and `tools/n68r_bundles.py`
  already parses all eight with 0 errors; the parser belongs in the archivist's tools.
- `lut.dn1`: not rule-bearing (never opened); ledger reason only. Same for `a1npc.txt`..`a5npc.txt` (never opened),
  the colour `.dat` files (client colour transforms; one `GreenBlood.dat` loader has no caller), the `.key` maps
  (client input) and `gateways.txt` (client Battle.net setup).
- Table docs: [MonItemPercent](../tables/MonItemPercent.md) layout (the split above) and "no reader"; [Sounds](../tables/Sounds.md)'s
  open question answered (§ 2.4); [Events](../tables/Events.md) the dispatch ids, the never-dispatched 4 and 8, and the
  registrars' `> 0` / `≥ 0` tests; [SkillDesc](../tables/SkillDesc.md) `SkillPage`'s server use; [Arena](../tables/Arena.md),
  [Overlay](../tables/Overlay.md), [Composit](../tables/Composit.md), [MonSounds](../tables/MonSounds.md),
  [AutoMap](../tables/AutoMap.md) their readers (§ 3's table); [BodyLocs](../tables/BodyLocs.md),
  [PlayerClass](../tables/PlayerClass.md) the reader tables of § 2.1–2.2.

**Phase 4 (spec-writer) gains:**
- **items/tc:** one sentence, `[I]`: `MonItemPercent` is loaded and read by no code, so it adds nothing to the drop
  order (data/0006 § 1.3). No golden-trace field is needed (the plan's open question).
- **skills/dispatch** (§ K) **or data/calc** (where `SKILLS_GetSkillLevel`'s `withBonus` is): the skill-level bonus
  formula of data/0006 § 3.2, `[I]`; § K: the event ids are Events row indices, the dispatch table of § 2.3, ids 4 and
  8 never dispatched (stat 195's second registration inert), the `> 0` / `≥ 0` registration tests, id 13.
- **items/inventory, player/creation, monsters/stats:** nothing new; the location and class indices they use are the
  row indices (§ 2.1–2.2), which they already state. A one-line index-space note is optional.
- **save/d2s:** `0x00627AF0` gets its name and meaning (`SkillHasDesc`) where the legacy stat 107 row cites it.
- **data/excel:** the loader list gains `MonItemPercent` (no reader), `Arena` (server scoring), `SkillDesc`, `Overlay`
  (count only), `Composit`, `MonSounds`, `AutoMap` (client), and the `-txt`-only code lists with `sounds`.
- **anim/timing:** nothing; the bundles do not feed the server's mode lengths (data/0006 § 4).
- **The skill-level bonus formula is a rule no spec states** (data/0006 § 3.2, stat 188's param `8·class + SkillPage − 1` among its terms): Phase 4 must carry it, not treat it as optional. Backlog: `2026-11-10-architect-spec-writer-plan-0068-p2-spec-corrections`.
- `docs/specs/data/excel.md` B1 says "the full `sounds` table loads in every run"; data/0006 § 2.4 withdraws it, so Phase 4 corrects it (same backlog entry). The table-doc answers are in `2026-11-10-architect-archivist-plan-0068-p2-table-doc-corrections`.
- Arena scoring (§ 3.3) has no core-area spec; it is named for plan 0061 P1's `-arena` reader, not carried.

Open, for the record: the two harness pieces above; whether a missile attack reaches event 7; the runtime registrar
0x005C377B's id; the arena score's readers. Review: Tier B.

### 2026-11-10 — Phase 3 (archivist, `lane/n68f`)

Done:
- **COF bundles documented:** [cofbundle.md](../formats/cofbundle.md) (24-byte record header, `size` bytes of COF, no file header or index; runtime slots `0xFFFFFFFF`/0/`0xFFFFFFFF` on disk; content against the loose files and `animdata.d2`; the 63 leftover bytes are the three `f9` COFs' 3 extra bytes in seven bundles). Parser `tools/cofbundle.py` (moved from `tools/n68r_bundles.py` with `git mv`, `survey` and `dump`), full-tier survey `cofbundle` registered in `tools/gate.py` with baseline `tools/gate/baselines/cofbundle.txt`: 8 files, 6 726 records, 0 errors, 0 COF parse errors.
- **Coverage ledger** (`docs/formats/README.md` § Coverage): rows for `.d2` bundles, `.cof`, `.dn1` (`lut.dn1` never opened), the colour `.dat` files (client colour transforms), `.key`, `gateways.txt` and the `a1..a5npc.txt` files now carry Phase 2's reasons and `[I]` tags; `data/local/use` is described by data/0002, `data/iamexpansion` stays undescribed (Phase 2 did not examine it; not rule-bearing).
- **Table-doc answers** (the backlog entry `2026-11-10-architect-archivist-plan-0068-p2-table-doc-corrections`, closed): Sounds (open question answered), MonItemPercent (loaded, no reader `[I]`, layout from the descriptor), Events (registration tests, dispatch ids, never-dispatched 4 and 8, id 13), SkillDesc (`SkillPage`'s server use, `SkillHasDesc`), Arena (scoring), Overlay, Composit, MonSounds, AutoMap (client only), BodyLocs, PlayerClass (reader tables).

Statements taken from a finding (Tier A, ADR-0027): the bundle open and its callers, the loader's refusals (name over 7 characters, directions over 0x40) and the 512-bucket hash, which bundles are never opened; every reader sentence in the table docs; the ledger reasons. Data statements (record walk, header values, counts, comparison with loose files and `animdata.d2`) are this lane's survey `[C]`.

Left: Phase 4 (specs); `data/iamexpansion` unexamined. Spec routes are unchanged (the Phase 2 hand-off above).
