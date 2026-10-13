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
- **2026-10-12 — Phase 0 landed (archivist).** No layout work was needed: `itemratio` (68 B), `itemtypes` and the
  shared item record were already complete in `tools/excel_layouts.py`, and `excel_bin.py diff` reports 0 unexplained
  mismatches for every mapped column (itemratio 114 cells, itemtypes 3 605, weapons 58 140, armor 38 380, misc
  28 690). Every offset items/0001 §10 quotes now has its `.txt` column, or "no column", in a new section
  *Fields the quality roll reads* of [ItemRatio](../tables/ItemRatio.md#fields-the-quality-roll-reads-plan-0010-phase-0),
  [ItemTypes](../tables/ItemTypes.md#fields-the-quality-roll-reads-plan-0010-phase-0),
  [Weapons](../tables/Weapons.md#fields-the-quality-roll-reads-plan-0010-phase-0), [Armor](../tables/Armor.md#fields-the-quality-roll-reads-plan-0010-phase-0)
  and [Misc](../tables/Misc.md#fields-the-quality-roll-reads-plan-0010-phase-0): itemtypes `+0x14` `Magic`, `+0x15`
  `Rare`, `+0x16` `Normal`; item `+0x129` `unique`, `+0x12A` `quest`, `+0x0FD` `level`. Surprises: the item side of
  the uber and class-specific keys has **no column** (no tier byte in the record; the tier shows only as `code` =
  `normcode`/`ubercode`/`ultracode`); the expansion `itemratio` rows ignore `Uber` (identical pairs), so with stock
  data only the class-specific key matters there; `vip` is the only quest item of a `Magic` type. Questions for
  Phase 1 in the backlog (archivist → reverser, 2026-10-12).
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
- **2026-10-12 — Phase 1 reviewed (architect): accept with fixes F1–F2, applied.** Checked: r2 at 0x00558696 (type
  `+0x16` → 2), 0x00558610 (threshold 110 = mf + 100), 0x00637910 (`Version ≤ arg`, tie to the later row, no match →
  0) and 0x005586E6 (`0xE8D` in the caller); the QIN/QOUT recount (266 rolls, six forced `q=4` without QIN, so the
  review's "4 ×25" was 19 rolls plus 6 forced); `tc.py replay` reruns 328/328 and asserts every `SEL`, so items/0001
  §5.1 expansion `[C]` stands. F1: the `[C]` on "codes 1–7, no other value" covered return paths the run never took
  (0, 5, 7); split into `[C]` observed codes and `[I]` range. F2: the offline check was a scratch script; it is now
  `tools/quality.py check` (no resync, MF 0 stated), rerun by the architect: 266/266, exit 0. Open for Phase 2: MF is
  assumed 0 and the MF path, the `*Min` clamp, codes 5/7 and classic are untested by these logs; the owner-of-killer
  cases decide the minion/summon run. Next: Phase 1b (cross-check), then Phase 2 (quality run, owner may play).
- **2026-10-12 — Phase 0 review fix F1 (archivist).** Reconciled with items/0002 (merged from main): ItemRatio gains
  *Row selection* (keys, `Version ≤` argument, highest version, later row on a tie, all `[I]` from items/0002 §2), with
  the consequence that drops always use the `Version` 1 rows, so with stock data the `Uber` key changes no drop (the
  `Version` 0 rows, the only ones that differ by `Uber`, are reachable only from the creation-side roll); ItemTypes'
  role column now cites items/0002, `Class` < 7 is the class-specific key and the `StaffMods` candidate is dropped;
  the own-type-only reading replaces the Equiv-walk question; Weapons states the computed uber/class keys (328 uber
  bases, 111 class-specific). The reverser → archivist entry is struck, and the archivist → reverser Phase 1 entry is
  struck as answered (a, b, c).
- **2026-10-12 — Phase 0 reviewed (architect): accept with fix F1, applied (f2fa745).** Checked: `excel_bin.py survey`
  reruns 467 861 cells, 0 unexplained (itemratio, itemtypes, weapons, armor, misc all 0); each §10 offset names its
  column or "no column"; the new `excel_layout` gate survey goes RED on a shifted offset (the lane's proof, reported).
  F1: items/0002 landed in parallel and settles the row key (`Class` < 7, the ubercode/ultracode rule, `Version ≤ 100`
  in classic drops too) and the own-type-only flag tests, so the `[L]` candidates (StaffMods) and the
  "uber matters in classic" reading were replaced by `[I]` links to items/0002 and the archivist → reverser questions
  struck as answered.
- **2026-10-12 — Phase 1b done (reverser).** [items/0002 § Leads used](../findings/items/0002-quality-roll.md#leads-used):
  `src:pd-item-generation` and `src:hrus-mf-guide` re-fetched in-session (ADR-0007; "Used for" notes in
  [sources.md](../sources.md)), compared after the Phase 1 reading; no code on either page. Verdicts: chance formula
  **held with refinement** (both; 1.14d adds the `< 1` no-draw win, `RNG_RangeB`, `ilvl` rather than mlvl); test order
  **held with refinement** (pd: early returns, rare skip, always-magic, superior before normal) / **held** (hrus);
  MF diminishing returns **held with refinement** (both: 1.14d is linear for `mf ≤ 10`, `cmp ecx,0x6E` at 0x00558613),
  MF before the minimum **held**, mercenary MF sum **held** (hrus); row selection **held** (pd key; hrus LoD lines) and
  **contradicted** once: pd says classic games use the two `Version` 0 rows, 1.14d's drop roll pushes a constant 100
  (0x005586D7), so classic drops use the `Version` 1 rows. Re-read (push, `ITEMRATIO_Select` loop, unfiltered loader,
  the only other reader being the creation roll): unchanged, stays `[I]`. Backlog reverser → reverser 2026-10-12.
  No tag moved. **Phase 2 input (added by this entry):** required cases for the quality run: (1) **classic rows**: a
  classic (non-expansion) character's drops, at least ~50 non-`Normal`-type rolls replayed with the `Version` 1 model
  and no oracle (the `Version` 0 rows fail 39 of the expansion set, so the case discriminates); (2) **small MF**: one
  magic-find value in 1–10 (linear in 1.14d, `mf·k/(mf+k)` in both sources), alongside the two non-zero values the
  plan already asks for. Also done on this branch (drlg backlog, plan 0008 closed so noted in docs/findings/drlg/):
  `tools/drlg.py` PE section offsets fixed and the merge tables re-read, `Bit2TileMerge` tags split, drlg/0003 cell
  position and `LvlSubRoll` −1, drlg/0002 release/re-activation, drlg/0001 `LvlTypes` columns. Next: architect review.
- **2026-10-12 — Phase 1b reviewed (architect): accept.** Every claim the plan names carries a verdict with a `src:` id;
  no tag moved on agreement. The one `contradicted` claim (classic games use the `Version` 0 rows, src:pd-item-generation)
  was re-read: r2 confirms the drop roll pushes a constant 100 (0x005586D7) and the creation-side roll builds 0 or 100
  (0x00556FBD–0x00556FD9); it is a required Phase 2 case (classic character, ≥ 50 non-`Normal` rolls, no oracle), as is
  an MF of 1–10 (the linear branch below 0x6E). The same branch fixed `tools/drlg.py exe_read` (PE section fields read
  out of order): r2 at 0x006EF620 matches the re-read 20-entry row table; roomk and gen rerun at 0 mismatches on every
  recorded log (the 94 of `roomk-test1.log` predate the fix, a development log outside the record); the unreached
  Bit2 merge branches went to `[I]` in drlg/0002, spec update sent to the spec-writer.
- **2026-10-13 — Phase 2 partial (reverser).** Record [run:2026-10-12-quality](../findings/items/experiments.md#run2026-10-12-quality)
  re-runs two owner-played sessions (single player, expansion, Nightmare, `LightSorc`): session A
  (`tc-champion-1.log`, run:2026-10-12-tc-champion) and session B (`tc-quality-1.log`, `-seed 1012`, sha256
  `f115a1a1…2121`). No wine run by the reverser. Magic find is an input from the save, not logged: `d2s.py dump` gives
  no character stat 80 and stat 80 = 50 on Harlequin Crest and on Wartraveler, so MF 100; both post-session copies keep
  the same ten equipped items. Tools: `tools/quality.py check` gains `--mf-linear` (counterfactual), killer-aware MF
  (0 with no killer) and the new logger lines; `tools/tc.py replay --quality model [--mf N] [--mf-linear]` replaces the
  QIN/QOUT oracle by the model (QOUT only asserted); `tools/gdb/tc-drops.gdb` logs `QROW` (itemratio row, 0x005586E0),
  `QKMF`/`QOWN`/`QOMF` (killer's and owner's stat 80 as the game's own `UnitGetStat` returned them, 0x005585E4,
  0x005585F1, 0x005585FB) and `QMF` (the sum used, 0x00558719), **untested under wine** (gdb parses it; the checkers
  pass a synthetic log). Numbers: `quality.py check` B 782/782 at MF 100 (751 at MF 0, 751 linear), A 65/65 (63 at MF 0,
  62 linear), old logs 266/266 at MF 0; each of A and B reproduces at MF 100 and no other value from −150 to 400;
  `tc.py replay --quality model`: B 1269/1269, A 124/124, run:2026-10-11-tc-drops 328/328 with no oracle (killers' MF 0
  read from `seedtest-strong`, `seedtest-played` and `testsorc`: no stat 80 anywhere). Linear vs diminishing: 34 rolls
  change (B 31, A 3; by first diverging test unique 9, set 13, rare 12), e.g. B QIN#53 a unique (c 30091, draw 1) that
  the linear model turns into a low-quality item. Promoted to `[C]` in items/0002 (scope Nightmare/Normal, expansion,
  single player, player killer, MF 0 and 100): codes 1–7, the `Normal`-type early return, the test order, the chance
  arithmetic except the clamp, the ratio-1024 no-draw win, the rare skip, the always-magic return, MF diminishing
  (MF > 10) and the linear magic term, the four `Version` 1 itemratio rows (records 2 ×186, 3 ×41, 4 ×27, 5 ×6), and
  superior/normal/low; items/0001 §10 is now a link, and the hand-off to the roll (item, `ilvl`, the four ratio words,
  killer, returned code) is `[C]`. Still `[I]`: MF 1–10, MF < 0, the owner's MF, the `*Min` clamp (never acted), the
  unique-flag and quest early returns, the classic rows, Hell.
  **Done-when status.** Met: the 328 calls with no oracle (killers' MF 0 from the saves); ≥ 100 new calls without the
  oracle (1269 + 124); diminishing returns change outcomes against a linear model (34 rolls); unique/set wins (7 ×5,
  5 ×10 rolled); `Uber` and class-specific bases, four itemratio rows; superior and low results; claims promoted and
  §10 replaced. **Not met:** MF at **two** non-zero values (only 100), the Phase 1b **small MF** case (1–10), the
  Phase 1b **classic rows** case, and the minion/summon kill (Phase 1 says the owner's MF counts). Characters needed
  for the architect to build: (1) an expansion character with MF in 1–10 from gear and nothing else (e.g. one
  item with `item_magicbonus` 5–10), Nightmare, no mercenary, which also gives the second non-zero value; (2) a
  **classic** (non-expansion) character, MF 0, any difficulty, enough kills for ≥ 50 non-`Normal`-type rolls; (3) a
  summoner or a character with a hireling, with MF on the player (e.g. `LightSorc`'s 100 plus a mercenary, or a
  Necromancer with skeletons), with the new logger so `QOWN`/`QOMF` show the owner path. A run with the updated
  `tc-drops.gdb` also tests its new breakpoints. Next: architect review; the remaining Phase 2 session(s).
- **2026-10-13 — Phase 2 (partial) reviewed (architect).** Verdict: **accept**. Rerun: `tc.py replay
  workspace/logs/tc-quality-1.log --quality model --mf 100` 1269/1269 with no oracle; `quality.py check --mf 100
  --mf-linear` 751/782 (31 rolls decided by the diminishing step, plus 3 in session A). MF 100 is a save input (two
  equipped items with stat 80 = 50, gear unchanged in both post-session copies), not a logged value; the scan over
  −150…400 fitting only 100 corroborates it. r2: the new logger points 0x005585E4, 0x005586E0, 0x00558719 each follow
  a call's return (`mov reg, eax`), and 0x00625518 is `ret 0xC`; the lines are **untested** until the next run. The
  `[C]` scope (Normal/Nightmare, expansion, single player, player killer, MF 0 and 100) matches the logs. Remaining
  for Phase 2: MF 1–10 (also the second non-zero value), a classic character (≥ 50 non-`Normal` rolls), a
  minion/summon kill; all three need owner-played sessions with characters the architect builds, under the new logger.
- **2026-10-13 — Characters for the remaining Phase 2 cases ready (architect).** Built by `tools/d2s.py build` from
  `tools/d2s_recipes/mfnecro.json` and `classicsorc.json` into `workspace/runtime/owner-chars/`; rebuilt today
  byte-identical (sha256 `da6ee2f5…` MfNecro, `d9fb35b5…` ClassicSorc), `d2s.py survey` clean. **MfNecro**
  (expansion, clvl 80, all waypoints and acts, no mercenary): stat 80 = 10 from one item only (Wisp, `roll: min`),
  which covers the small-MF case at the linear boundary (`mf ≤ 10`) and the second non-zero value; Raise Skeleton 20
  covers the summon kill with MF on the owner. **ClassicSorc** (status 0 = classic, clvl 40, Normal, MF 0) covers
  the classic-rows case. Install with `tools/saves.py aside/install/restore`; run with the updated `tc-drops.gdb`.
