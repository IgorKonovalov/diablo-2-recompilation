# 0010 — Items: the quality roll

> **Status:** approved (2026-10-11)
> **Created:** 2026-10-11
> **Owner skill(s):** archivist, reverser, spec-writer
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0002-scope-creation-paths-and-enablers, 0003-runtime-experiments, 0004-boundary-oracles-in-reproduction

## TL;DR

**Question:** once the treasure class has picked an item, how does the game decide whether it is unique, set, rare,
magic, superior, normal or low quality, and what does it draw to decide? Plan 0004 left this roll
(`sub_00558640_DropRollQuality`) as a boundary oracle in 328 recorded resolver calls. This plan reads it, models it in
`tools/quality.py` and plugs that model into `tools/tc.py`, so the existing logs replay with no oracle at all
(ADR-0004's hand-back). When it's done, `docs/findings/items/0002-quality-roll.md` has the roll at `[C]` on the drop
path, the 328 calls and a new magic-find set reproduce bit for bit, and `docs/specs/items/quality.md` is drafted.

## Context

- Research-map row `items/quality` (core), status `not started`. Dependencies: `rng` reviewed; `items/tc` Phase 2
  accepted with fixes (plan 0004, 2026-10-11): the resolver side of the hand-off is `[C]` for its scope, the hand-off
  arguments stay `[I]` until this plan consumes them (ADR-0004 § Negative).
- What [items/0001 §10](../findings/items/0001-tc-resolution.md) already says, all `[I]`: three no-draw early returns
  (itemtypes `+0x16` → 2, item `+0x129` → 7, itemtypes `+0x14` with `quest` → 7); `ITEMRATIO_Select` by uber,
  class-specific and `Version ≤ 100`; tests in the order unique, set, rare (if itemtypes `+0x15`), magic, then
  superior and normal/low, each `RNG_RangeB(&src->seed, chance) < 128`, a chance < 1 winning **without a draw**;
  chance `(base − (ilvl − qlvl) / divisor) × 128`, magic find from stat 80 of the killer plus its owner with
  diminishing returns (250/500/600), the row's minimum, then `chance × ratio / 1024` from the TC frame.
- Data: [ItemRatio](../tables/ItemRatio.md) (layout `[C]`, the four `*Min` columns `[I]` because they are constant,
  row selection and arithmetic `[L]`), [ItemTypes](../tables/ItemTypes.md), [Weapons](../tables/Weapons.md)/
  [Armor](../tables/Armor.md)/[Misc](../tables/Misc.md).
- Logs: `workspace/logs/tc-run{2,4,5,6,9,10,13,16,17,18,19}.log` (sha256s in
  [run:2026-10-11-tc-drops](../findings/items/experiments.md#run2026-10-11-tc-drops)). Every QIN/QOUT pair there is a
  free test case once the killer's magic find is known (it was 0 on every character used, to be confirmed in Phase 2).
- Leads: `src:pd-item-generation` and `src:hrus-mf-guide` (1.10/1.11) cover the quality formula and magic find.
- Scope edge: what happens *after* the roll (a unique roll with no eligible unique becomes a rare, a set roll becomes
  magic, the ×3 durability) is item creation, and belongs to `items/uniques-sets`. This plan records where those
  fallbacks are and stops there. Other callers of the roll (vendors, gambling, cube, quest drops) are named only.

## Phases

### Phase 0 — Fields the roll reads
- **Owner skill:** archivist
- **What:** make every table field Phase 1 needs readable through `tools/excel_bin.py`, with a meaning column where
  the data alone settles it.
- **Outputs:** `tools/excel_layouts.py` (itemratio complete; itemtypes `+0x14`, `+0x15`, `+0x16`; the items record
  fields behind `+0x129`, `quest`, `level`/`qlvl`, the uber/exceptional and class-specific flags the row selection
  needs), updated [ItemRatio](../tables/ItemRatio.md), [ItemTypes](../tables/ItemTypes.md) and the item table docs.
- **Done when:** `excel_bin.py diff` shows 0 mismatches for each newly laid-out column, and each table doc names the
  `.txt` column (or "no column") for every offset quoted in items/0001 §10.

### Phase 1 — Read the roll
- **Owner skill:** reverser
- **What:** read `sub_00558640_DropRollQuality`, `ITEMRATIO_Select` and the magic-find helper to the instruction.
- **Outputs:** `docs/findings/items/0002-quality-roll.md`, `re/symbols.csv` rows (subsystem `items/quality`).
- **Done when:** the finding states, with addresses and `[I]` or better:
  - the early returns and the item/itemtype fields they test;
  - `ITEMRATIO_Select`: the key (uber, class-specific, version), what happens with no match, and whether it differs
    in classic games;
  - each test in order: the chance expression with operand widths, signedness and rounding of every division, the
    clamp, the ratio reduction, the draw (`RNG_RangeB` range form) and the comparison; when a test is skipped;
  - magic find: which units' stat 80 is summed (killer, owner, minion, hireling cases), the diminishing-returns
    formula with its integer arithmetic, and whether it is applied before or after the minimum;
  - how the low/normal/superior split is decided (one draw or two), and the returned code for each quality;
  - the callers of the roll other than `TC_ResolveDrops`, named with addresses and left to their rows;
  - where item creation handles an impossible unique/set (named, left for `items/uniques-sets`).
- **Input (from the plan 0004 Phase 3 review):** the returned quality is a code starting at 1, not 2–7 as items/0001 says:
  run:2026-10-11-tc-drops logged codes 1 ×8, 2 ×231, 3 ×4, 4 ×25, 6 ×4. The finding must give the full range and the
  meaning of each code (backlog spec-writer → reverser, 2026-10-12).

### Phase 1b — Community cross-check
- **Owner skill:** reverser
- **What:** compare Phase 1's claims with the registered sources, per `evidence-rules.md` § Community cross-checks
  (blind first; agreement never promotes a tag).
- **Outputs:** verdicts in the finding's *Leads used*, `docs/sources.md` entries for any new source, backlog entries
  for each `contradicted` verdict.
- **Done when:** the quality chance formula, the test order, the magic-find diminishing returns and the ratio-row
  selection each carry a verdict with a `src:` id (or `not covered`). Every `contradicted` claim is re-read and made a
  required case of Phase 2.

### Phase 2 — Bit-exact reproduction, oracle removed
- **Owner skill:** reverser
- **What:** write `tools/quality.py` (tables through `tools/excel_bin.py`, draws through `tools/rng.py`) and give
  `tools/tc.py replay` a switch that uses it in place of the QIN/QOUT oracle (ADR-0004: the oracle becomes a switch, the
  old logs are re-run).
- **Logging:** extend `tools/gdb/tc-drops.gdb` at QIN with the killer's and its owner's stat 80 and the selected
  `itemratio` row; keep QOUT, so a new log can still be replayed with the oracle.
- **Producing drops:** as in plan 0004 (ADR-0003; agent or a human on `:7`). Magic find is set with
  `tools/d2s.py setstat` stat 80 on a copy of `seedtest`, original restored. The kill-harness scripts from plan 0004
  should be in `tools/` by then (backlog); if not, record what was used.
- **Done when:**
  - all 328 recorded calls of `run:2026-10-11-tc-drops` replay with the model and **no oracle**: every quality, every
    seed after the roll, and the final seed (after confirming from the saves that the killers had no magic find);
  - a new run `run:YYYY-MM-DD-quality` adds at least 100 calls reproduced without the oracle, including magic find at
    two non-zero values, one of them high enough that the unique/set/rare diminishing returns change the outcome
    against a linear model; a uniques/sets roll that wins (quality 7 or 5 returned); an `Uber` (exceptional or elite)
    base and a class-specific base, so at least three `itemratio` rows are used; a superior and a low-quality result;
    and a kill by a minion or summon, if Phase 1 says the owner's magic find counts;
  - the Phase 1b cases are included;
  - in-scope claims are promoted to `[C]` citing the run; items/0001 §10 is replaced by a link to items/0002, and the
    `[I]` hand-off arguments in items/0001 are raised to `[C]` where the replay consumes them (ilvl, item, the four
    ratio words, killer).
  Classic games stay `[I]` unless a classic character is also run.

### Phase 3 — Spec: items/quality
- **Owner skill:** spec-writer
- **What:** write `docs/specs/items/quality.md` and extend `docs/specs/items/README.md` with the roll's place in the
  chain (TC → quality → creation).
- **Done when:** the spec follows the template, every statement is tagged, it includes a worked example from the
  quality run (seed in, draws, quality out), and the architect's review passes.

## Open questions

- Do vendors, gambling and the cube call the same roll with other arguments (forced ilvl, no ratios)? Phase 1 names
  the callers; their rows decide.
- Is the item `+0x129` early return (→ unique) the "always unique" flag of quest items, or something else? Phase 0/1.
- The full chain TC → quality → affixes is only proven end to end when `items/affixes` and `items/uniques-sets`
  replace the creation side. That is out of scope here.

## Implementation log

_(lanes append dated entries as phases land)_

- **2026-10-11 — Drafted (architect).** From the plan 0004 Phase 2 review: the 328 recorded calls are this plan's
  first test set.
- **2026-10-11 — Approved (human).** No changes to the draft.
- **2026-10-12 — Phase 1 done (reverser).** [items/0002](../findings/items/0002-quality-roll.md): the drop roll read to
  the instruction (0x00558640–0x00558986), `ITEMRATIO_Select`, the magic-find sum `sub_005585D0_DropMagicFind` and the
  diminishing-returns helper `sub_00558610_MagicFindDiminish`; 12 new `re/symbols.csv` rows and 2 moved to
  `items/quality`. The returned quality is a code 1–7 (1 low, 2 normal, 3 superior, 4 magic, 5 set, 6 rare, 7 unique;
  0 on a missing record), the range `[C]` (return paths plus the run's QOUT codes), the rest `[I]`. Recount of
  run:2026-10-11-tc-drops: 266 rolls with codes 1 ×8, 2 ×231, 3 ×4, 4 ×19, 6 ×4, plus six forced `q=4` QOUT lines
  without a roll (tc-run19, `fq=4`), which make the review's 25. An offline scratch model of the reading reproduces all
  266 QIN/QOUT pairs (code and exit seed) with magic find assumed 0; it uses itemratio records 2–5 and does not reach
  the minimum clamp or any magic-find branch, so Phase 2's magic-find run is the real test of those. Findings for later
  phases: the drop roll passes a constant version 100 (classic drops use the `Version` 1 rows); its only caller is
  `TC_ResolveDrops`; item creation has its own roll (`sub_00556F60_ItemRollQualityCreate`, item seed) and its
  unique → rare → magic → superior → normal and set → magic → … fallbacks in `sub_00557450_ItemCreateByQuality`, named
  for `items/uniques-sets`. Phase 0 had not landed; the reading used the existing table docs and `excel_bin.py dump`.
  The backlog entry spec-writer → reverser of 2026-10-12 is done (items/0001 F1, F4 and stale points). No harness run
  was needed. Next: architect review; Phase 1b and Phase 2.
- **2026-10-12 — Phase 1 review fixes F1–F2 applied (reverser).** F1: items/0002's summary splits the range claim:
  `[C]` for the observed codes 1, 2, 3, 4, 6 and for code 1 as the last test's loss (run:2026-10-11-tc-drops), `[I]` for
  0, 5, 7 and the "no other value" closure (disassembly only); items/0001 §10 split the same way. F2: the offline check
  is now `tools/quality.py check` (first cut of the Phase 2 model; MF assumed 0, stated in its help, `--mf` to change),
  which asserts code and exit seed per QIN/QOUT pair with no resync: `266 pairs, 266 reproduced, 0 failed (mf=0)` over
  the eleven logs. It corrected one figure of the scratch count: the 188 early returns select no itemratio row, so
  record 2 serves 66 rolls, not 254. Still support only, no promotion.
