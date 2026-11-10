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
     order against `TC_ResolveDrops`? Does any draw happen?
  2. **`BodyLocs`, `PlayerClass`, `Events`:** the readers of each column, against the specs that already use them
     (items/inventory, player/creation, save/d2s, skills/dispatch).
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
