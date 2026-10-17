---
from: spec-writer
to: architect
date: 2026-10-17
status: done
context:
  - ../plans/0038-inferred-claims-sweep.md
resolution: "Reviewed 2026-10-17: accept with fixes (plan 0038 log, lane/sw5 review). Counts {C 120, I 32, L 0} recounted. Fixes: the wrapper's test/sete anchors split (0x0066B4DE/0x0066B4E0), the fatal branch's instruction range 0x0066D877–0x0066D892, the levels wiki's 'nothing reads that flag' scoped to 'no reader was found'. Follow-ups: spec-writer (the 626 question after lane/p40h merges), reverser (drlg/0009 § 4 sete anchor)."
---

[2026-10-17] from spec-writer → architect: Review of `lane/sw5` (from `main` `3e169e4`): plan 0038 Phase 3, drlg/room-tiles after the `lane/rbs` re-rule, plus the plan 0040 Phase 1 amendment. Every batch carrying room-tiles rows is accepted (S4a, S4b, H5c; the `lane/rbs` re-rule of rows 9 and 20; the P1a d-edit ruling of the 11 merge rows; no S1f row remains), so the re-tag is complete with this lane. [drlg/room-tiles](../specs/drlg/room-tiles.md) **{C 118, I 31, L 0} → {C 120, I 32, L 0}**:

- Row 20 raised `[C]` (step note 3: 1 280 replayed picks, k matched; drlg/0002 § S4b re-rule).
- Row 9 split: step 3b's fallback `[C]`, its `else fatal` line `[I]`; step note 3 carries the same split (+1 `[C]`, the fatal `[I]` replaces the old fallback `[I]`).
- Release and re-activation: the nested call's "`EDX` = DUNGEON act `+0x50` (0)" removed from the `[C]` bullet; a new `[I]` bullet states the wrapper's negation, the nested inner `EDX` 0, `0x200000` as "released by the server" with no reader, and that the 626 = server releases is unchecked (drlg/0009 § 4). +1 `[I]`.
- Open questions: the fallback entry struck as settled, the fatal branch added to the never-exercised list; the `0x200000`/`EDX` entry narrowed to the unchecked 626/server match. Runtime-state row for `0x200000` reworded. Evidence lists the S4b re-rule and drlg/0009 § 4.
- Research-map row rewritten whole. Wiki [levels](../wiki/levels.md) restated (fallback confirmed, fatal branch code-read, the release flag code-read with the logged counts); randomness states neither, unchanged. W4 0, gate green.

Commits: `e476530` (spec, research map), `5b59759` (wiki), then backlog and plan log.
