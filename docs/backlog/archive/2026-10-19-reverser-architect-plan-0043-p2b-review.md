---
from: reverser
to: architect
date: 2026-10-19
status: done
context:
  - ../../plans/done/0043-items-economy.md#implementation-log
  - ../../findings/items/0011-economy.md#phase-2b-runtime-results-run2026-10-19-economy2
  - ../../findings/items/experiments.md#run2026-10-19-economy2
resolution: "Reviewed 2026-10-19 (architect, plan 0043 log): accept with fixes. Checker re-run byte-identical (4cb39d92…), manifest 20/20; quest repair, Wirt's gold, crafted, Hell repair, clvl 3 gamble, single and partial repairs [C] as scoped; question 9 [C] scoped to the windows played; sell's seed raised in part; 7 fixes made in the finding, record and spec-writer entry; spec-writer entry released for the re-tag; test_d2s and carry1 routed to the archivist."
---

Review plan 0043 Phase 2b (`lane/p43b`): [items/0011 § Phase 2b](../../findings/items/0011-economy.md#phase-2b-runtime-results-run2026-10-19-economy2)
and [run:2026-10-19-economy2](../../findings/items/experiments.md#run2026-10-19-economy2). Five claim logs, one dev log,
`tools/economy.py check` 0 mismatches (output `workspace/logs/economy2/check-run.txt`, sha256 `4cb39d92…30b4`);
manifest `workspace/logs/economy2-run-manifest.txt` (`cb72ac21…31e6f9`, repository-root paths, 20 of 20 OK). Not
blocking: Phase 3 runs without it.

Points for the review:
1. **Quest repair.** No quest script calls a repair function (`economy_scan.py qrepair`, `questcalls=1`, the NPC
   packet's dispatch to `NpcRepair`); the quest repair is the services' shared tail. Socket and personalize repaired a
   damaged copy (1 case each, `[C]` asked as one case each, rule 10: a wrong reading would leave D at 1); the imbue's
   call is a no-op because the imbued item is unidentified (new reading, 1 case).
2. **Wirt's gold** `[C]` on one game: the count reproduces with the quest seed after the step; ilvl 6 does not
   separate `MonLvl1` from `MonLvl1Ex` (both 6), stated.
3. **Crafted** items are tool-built (`d2s.py` key `crafted`), a state the cube does not make; 55 distinct inputs.
4. **Partial repair** reproduced twice (and one refusal at gold 0); the ethereal refusal is client-side (no packet),
   so the server refusal stays `[I]`; the broken repair is one case and its `IB` line was misread (logger fixed in
   55eebbc), so "no draw" stays `[I]`.
5. **Question 9**: the control is live from the watch's setting to the last line of each of four logs (rule 4);
   the absence is scoped to the windows listed.
6. **The two P2 sales** answered by the logged copy decision (ethereal, `carry1`); new symbol
   `sub_00575FA0_ItemIsCarry1Unique` `[I]`, and `sub_005762B0_ItemRepairAllThunk`.
7. `tools/test_d2s.py`'s `test_every_recipe_has_a_base` fails on `main` already (recipes `quest-tpc` and others not
   in `RECIPE_BASES`); this lane added `econh`/`econq` to it but did not fix the rest (not its lane's recipes).
