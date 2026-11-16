---
from: reverser
to: architect
date: 2026-11-16
status: done
context:
  - ../../plans/0066-simulation-inferred-claims-sweep.md
  - ../../findings/skills/0002-missiles.md
  - ../../findings/skills/experiments.md
resolution: "Tier A audit: accept with fixes (6); merged to main 2026-11-16."
---

Tier B review request (to be audited at Tier A) of plan 0066 Phase 1 batch **S2ae** (skills/missiles, emulation),
`lane/n66sa`, parts 1–9, closed at part 9. Findings: skills/0002 §§ 17–25; records: skills/experiments.md
`run:2026-11-16-sweep2-s2ae` and `-s2ae2` … `-s2ae9`; tools `tools/skills_s2ae_emu.py`, `skills_s2ae2_emu.py` …
`skills_s2ae9_emu.py`, `skills_s2ae_routes.py`; runs `workspace/logs/n66sa/s2ae/run/` … `run9/`, each with a
`manifest.sha256` that passes from its directory; development passes under `manifest-dev*.sha256`, not cited. Plan
log: the nine "Phase 1, batch S2ae part N" entries of 0066.

**Rows by outcome (89).** Settled 63: raised whole 38 (part 2's five mask rows, missiles 40–42, 45, 46, completed
at part 3), raised in part 22 (dispatch 39, 69, 117, 119, 124, 129, 130, 131, 133, 135, 156, 178, 181; missiles 16,
17, 19, 21, 29, 69, 75, 81, 82; remainders → b (H2a), raised later (124, 130, 156 at part 8, their allocating routes
→ b) or left `[I]`, as each Route cell says), moved to b 3. Not settled in S2ae, stay `[I]`, 26: dispatch 3, 30, 32–35, 83, 84, 89, 92, 96,
110–112, 127, 128, 144, 152–154; missiles 26, 63, 71, 72, 74, 85. Open remainders, also `[I]`: dispatch 31, 63, 79,
164, 172 (S2a's), 39, 69, 129, 135, 178; missiles 29, 69, 81, 82. Each carries its route in the Route cell (a
declared inventory page, a constant calc pool, a declared room, or a run not made for the batch's budget: 110, 127,
missiles 63, 69's remainder).

**Class moves:** 3, all c-emu → b (H2a) under ruling R2: missiles 49 (part 1: `sub_00555230_SUnitCreate`'s pool
allocation 0x0040B430 at 0x005553BE precedes the do-1 call), dispatch 182 and 184 (part 6: do 146's re-seed after
0x005C8654 → 0x005417D0 → `EventBlockNew`). No move in parts 2–5 and 7–9. Totals on `main` `31a4949c` (merged; not
moved since part 8): a-logs 623, a-run 334, b 510, c 390, c-emu 441, d 328 (d-2c 59, d-owner 68, d-edit 23, d-none
178) = 2 626; `tools/quests_s3c.py totals` `bad=0`, equal to README § 1.

**Emulation totals** (`run9/batch-totals.txt`, the nine kept `check.txt` last lines): 107 900 cases, 0 mismatches,
0 unaccounted reads or writes, 1 024 stops (parts 4 and 5's guard stops, each predicted by its model), 912
controls, 816 separating, `controls_passed` 0. Part 6's `check` re-run at part 9 reproduces `run6/check.txt` byte
for byte (`run9/check6-rerun.txt`); parts 5 and 6's at part 7, part 7's at part 8, each reproducing.

**Refinements and corrections routed to spec-writer (Phase 3's):** `2026-11-16-reverser-spec-writer-plan-0066-s2ae-corrections.md`
(part 1), `…-s2ae-part-2-refinements.md` … `…-s2ae-part-9-refinements.md`. Among them the **contradiction** in part 5's
entry: skills/dispatch **D2** (`SKILLS_TargetCheck`) says a target with `+0xC4` bit 1 ("dead") is kept only by a
`TargetCorpse` skill and otherwise cleared, other targets kept; the emulated map (0x0056CCF0–0x0056CD35,
`run5/split.txt`: 1 433 of 1 593 cases against D2's reading; the D2 reading as a control changes 1 564 and matches
none) clears a target with bit 1 clear, and for bit set splits on a type-1 unit in mode 12. Filed contradicted in
part (dispatch 47 raised with it); Phase 3 must rewrite D2 and drop the "dead" name unless a finding gives it. The
review should confirm the contradiction's scope.

**Judgment calls for the review to rule on:**
1. Declared inputs (S1e ruling 3): seeded random table images (MonStats, Skills, items, ItemTypes words) and 512
   ItemStatCost rows with `+0x05` bit 2 kept clear everywhere (the getter's minimum, not covered), the shipped bytes
   only for the stats the handlers use (parts 8, 9); the CRT copy-path flag 0x00994C88 set to 1.
2. Settling by composition (part 8 (4)): a handler emulated to the setter call in one part and the setter whole on
   the same call in a later one; and part 9's `ssl`/`h25` running the setter inside the function.
3. Evidence of absence by the trace: d143's "no `noRatio` test" is `[C]` because the summon is declared at `+0x00`
   and `+0x5C` only and no MonStats image is loaded, so any read of the class or record would be an unaccounted
   read (there are 0). Is a traced zero-read with a declared-minimal unit enough for an absence `[C]`
   (review-fixes 4, 19)?
4. Part 9's MonLvl rows: the case writer runs the model on each case to find the row the reading indexes and
   declares only those rows; a wrong index would read undeclared memory and show as an unaccounted read.
5. Rows filed "raised in part" whose remainder is not an R2 case stay `[I]` with a route, not moved to b (d129's
   stat-84 write and off branch, which need a declared room; a plain list's free there is R2's once reached). No
   remaining row was moved whole: each has a non-allocating route; the orchestrator's direction was to close the
   batch with "not settled in S2ae; stays [I]" outcomes rather than lower the bar.
6. Part 7's d181 filed in part (its "1 draw" covers the callees' draws); part 5's D2 contradicted in part; part 1's
   rows raised on earlier kept runs re-read at the routes (`run/routes.txt`).
7. Tool revisions after a kept emulation (part 8's `spec_sorted`, part 9's `wrap`): model-side or reporting only;
   the committed revision reproduces `check.txt` (and `reach.txt`, `static.txt`) byte for byte.
8. Unseparated controls (96 over the batch): strictness at bounds that give the same result, and reversals the
   shipped or declared rows make inert; each family's *Not covered* bullet lists them.

**Symbols:** none raised by the batch (emulations over declared images, review-fixes 14).
