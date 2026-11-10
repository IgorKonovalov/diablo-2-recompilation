---
from: architect
to: spec-writer
date: 2026-11-10
status: done
context:
  - ../../plans/0064-clean-room-test.md#implementation-log
  - ../../plans/0064-cleanroom/S4.md
  - ../../specs/drlg/outdoor.md
resolution: "Items 1–4 done in drlg/outdoor (H6d table, H7a OneOrTwo, H1a A1CliffMark, C1 Vis ≠ 0) from drlg/0008 § Plan 0064; items 5 onward done by lane/n64x; the routed items (7)–(11), (14) and the before-head insert stay in [plan-0064-outdoor-unstated-steps](../2026-11-10-spec-writer-reverser-plan-0064-outdoor-unstated-steps.md)."
---

**Spec defects, drlg/outdoor (plan 0064 P3 triage, S4).** Each fix states what the implementer could not know and cites the finding that holds the answer; where none does, route to the reverser instead of writing it. (1) **H6d** (row 13): `g_A1SearchDx` is `+1, 0, −1, 0` (dir 0 E, 1 S, 2 W, 3 N), not `−1, 0, +1, 0`; the spec copies a wrong finding statement. Waits for reverser entry plan-0064-drlg-outdoor-statements (b). (2) **H7 and the Act I draw sequence step 9** (row 14): the `s` step and `Near(49)` belong to the else branch only; "each OneOrTwo one Step, plus one more when s is 1" is wrong for the `(r & 3) = 0` branch. Waits for (c). (3) **H1 `A1CliffMark`** (rows 15–16): replace the one-line comment with the rule once (a) lands; until then mark it as the gap it is. (4) **§ C, C1** (row 6): "one node per Vis slot whose Warp is −1" also matches empty slots; waits for (d). (5) **§ C note on `LevelAdjInsert`** (row 7): say what the insert does when the list holds more than one node (drlg/0008 § Plan 0038 batch S4a), or that C2's full order is what a reimplementation uses. (6) **J2a** (row 8): `RectGapTest` is used undefined; define it here or link it (`RectGapTest(A, B, 0) = 0` ⇔ both per-axis gaps negative: drlg/0007 § validators, drlg/0006 § 2; maze B2's overlap). (7) **G3–G4** (row 9): G4 is prose only; give pseudocode: which wall and floor layer, how variant `v + 1` is located, what a sub-index 63 cell does in a replacement variant, which cells "the others" are, whether `N ≤ 0` skips; and reconcile "63 means any" with G2's `wildcard ← 62` (the `baseDef + 62` form). (8) **L5** (row 10): whether G4's seam-opening test applies to the Act V match callback. (9) **L4, L6** (row 11): which row or column is each edge, the scan direction, and the prisons' fallback order. (10) **J5** (row 12): the omitted `hi`/`max` of `Fill(635 …)`, `Fill(633, 634)`, `Fill(632)` and level 81's, `OutFillRandom`'s shuffle width, fit pad and sides, and `PlaceRandom(631, 0)`'s pad and sides. (11) **H3** (row 17): which cells are "beside" the bridge row. (12) **H6 vs H6e** (row 18): H6 calls the jitter "if found" while H6e draws before its path test; make them one statement. (13) **F1** (row 19): whether the level-3 seam rule falls through to the shuffle when no cell matches. (14) **C5** (row 21): which vertex survives a merge and what its `type` becomes. Rows 9–12 and 17 were guessed right; rows 19 and 21 are unreached by any case.

**Added 2026-11-10 (orchestrator, plan 0064 Phase 3 fresh-reader probes):**
- **S4 row 7 (§ C):** spec defect. A reader put a side-2 node between sides 1 and 3 only by inferring that a list of
  two or more nodes gets the full sorted walk ("only while … one node" is the only hint), and could not say where the
  one-node quirk puts a node (before or after the head). State both, and reconcile the `[C]` on C2 with the `[I]`
  quirk note.
- **S4 row 20 (§ H0):** spec defect. The `not1`/`not2` cells shown as "—" in `g_LinkOutdoorFlags` rows 6–14 have no
  legend; the reader guessed 0 ("no exclusion"). Give the stored values (or a legend).

*Annotated 2026-11-10 (reverser, lane/n64r):* the reverser entry this waits for is closed. The statements are in [drlg/0008 § Plan 0064 statements](../../findings/drlg/0008-outdoor.md#plan-0064-statements-2026-11-10): (a) `A1CliffMark` as pseudocode, `[C]`; (b) `g_A1SearchDx` `+1, 0, −1, 0`, corrected in place in § 16.3; (c) `OneOrTwo` with the `s` step in the else branch only, `[C]`; (d) `LevelBorderAdj`'s `Vis ≠ 0` test, `[C]` with a separating control (drlg/0007's table row raised too).

**2026-11-10, spec-writer (`lane/n64x`, plan 0064 Phase 4): items 5 onward and the two probe rows, from the findings; items
1–4 untouched.** Items 1–4 (H6d, H7, H1 `A1CliffMark`, C1) **wait** for the reverser lane n64r and
[drlg-outdoor-statements](2026-11-10-architect-reverser-plan-0064-drlg-outdoor-statements.md) (a)–(d); the spec still
carries the old H6d table, H7 sentence, H1 comment and C1 wording. Done in [drlg/outdoor](../../specs/drlg/outdoor.md):
(5) and probe row 7, § C: `LevelAdjInsert`'s one-node compare and its skipped head, C2's full order as the
reimplementation's rule with the 177/19/5 count and the side 1, 3 + 2 example, and C2's `[C]` scoped to the compare and the
within-side order (drlg/0008 § 13, § S4a); (6) J2a: `RectGapTest(A, B, 0) = 0` ⇔ both gaps negative (drlg/0007 § 3, drlg/0006
§ 2, maze B2); (7) in part, G4: the variant stride `(g.w + 1)·(v + 1)` and "63 means any" = `baseDef + wildcard 62`
(drlg/0008 § 7); (12) H6/H6e: `A1Paths` calls the jitter only for a found path, so a failed search draws nothing (drlg/0008
§ 8, § 16.3); (13) F1: level 3 falls through to the shuffle when no cell matches (drlg/0008 § 6), unreached; probe row 20,
H0: rows 6–14 store `not1` = `not2` = 0, a legend with the stored value. **Routed, no finding holds the answer:** (7)'s
layer, the 63 cell of a replacement, "the others" and `N < 0`; (8) L5; (9) L4, L6; (10) J5; (11) H3; (14) C5, all in
[plan-0064-outdoor-unstated-steps](../2026-11-10-spec-writer-reverser-plan-0064-outdoor-unstated-steps.md) and under
drlg/outdoor *Open questions*. Left open: items 1–4, then the routed items once that entry lands.

**2026-11-10, spec-writer (`lane/n64y`, plan 0064 Phase 4 part 3): items 1–4 done from [drlg/0008 § Plan 0064 statements](../../findings/drlg/0008-outdoor.md#plan-0064-statements-2026-11-10); the entry closes.** In [drlg/outdoor](../../specs/drlg/outdoor.md): (1) H6d's search-table note gives `g_A1SearchDx` `+1, 0, −1, 0` (bytes `01 00 FF 00`, dir 0 E, 1 S, 2 W, 3 N) from (b); what the implementer could not know: the spec copied § 16.3's sign-flipped bytes. (2) H7a writes `OneOrTwo` as pseudocode with the `s` step on the else branch only, and draw-sequence step 9 says the second `Step` comes only when `(r & 3)` ≠ 0, `[C]` on (c)'s 26 separating calls; what they could not know: the one-line definition read as if the `s` step followed both branches. (3) H1a gives `A1CliffMark` as pseudocode (start tests `A`/`B`, the run's exits, `last`, the marking, the `done` flag set before the exits, signed compares), `[C]` with (a)'s branch counts, and the exits no log takes `[I]`; H1's comment points at it; what they could not know: H1 held a one-line summary of the rule. (4) C1, its § C sentence and the Inputs `Vis`/`Warp` row test `Vis ≠ 0` before `Warp` −1, with a step note on the empty slot and (d)'s separating control `[C]`; what they could not know: an empty slot also has `Warp` −1. Two Reimplementation notes added (the empty slot; `OneOrTwo`'s one-branch draw), quirks Q528–Q529. **Still open in the reverser entry** [plan-0064-outdoor-unstated-steps](../2026-11-10-spec-writer-reverser-plan-0064-outdoor-unstated-steps.md): (7)'s layer, sub-index-63 cell, "the others" and `N < 0`; (8) L5; (9) L4, L6; (10) J5; (11) H3; (14) C5; and where the insert puts a node that sorts before the head. Those come back to the spec-writer when that entry closes.
