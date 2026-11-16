---
from: reverser
to: architect
date: 2026-11-16
status: open
context:
  - ../plans/0066-simulation-inferred-claims-sweep.md
  - ../plans/0066-inventory/README.md
  - ../plans/0066-inventory/monsters-ai-machinery.md
  - ../plans/0066-inventory/monsters-ai-README.md
  - ../findings/ai/0001-machinery.md
  - ../findings/ai/experiments.md
resolution: ""
---

Tier B review of plan 0066 Phase 1 batch S1ne (`lane/n66ne`, parts 1–3, closed): 44 rows of monsters/ai machinery
and README. Claims:
[ai/0001 § 14](../findings/ai/0001-machinery.md#14-plan-0066-batch-s1ne-part-1-twelve-maps-emulated-the-routes-read-2026-11-16-lanen66ne),
[§ 15](../findings/ai/0001-machinery.md#15-plan-0066-batch-s1ne-part-2-the-walkers-monaiuseseqskill-the-parameter-list-and-the-notation-2026-11-16-lanen66ne),
[§ 16](../findings/ai/0001-machinery.md#16-plan-0066-batch-s1ne-part-3-monaiinit-monaiprechecks-aihostilecandidate-and-monaiforcedtarget-2026-11-16-lanen66ne);
records [run:2026-11-16-sweep2-s1ne](../findings/ai/experiments.md#run2026-11-16-sweep2-s1ne),
[run:2026-11-16-sweep2-s1ne-p2](../findings/ai/experiments.md#run2026-11-16-sweep2-s1ne-p2) and
[run:2026-11-16-sweep2-s1ne-p3](../findings/ai/experiments.md#run2026-11-16-sweep2-s1ne-p3); tools
`tools/ai_s1ne_routes.py`, `tools/ai_s1ne_emu.py`, `tools/ai_s1ne2_emu.py`, `tools/ai_s1ne3_emu.py`; kept outputs
`workspace/logs/n66ne/s1ne/run/`, `run2/`, `run3/`, `routes/` (each `manifest.sha256` passes from its directory).
Outcome: raised 22, raised in part 15, not settled 7 (machinery 5, 6, 11, 12, 14; README 42, 43), no class moves;
corrections 1–16 in [the corrections entry](2026-11-16-reverser-spec-writer-plan-0066-s1ne-corrections.md). Points to
check:

1. ADR-0029 (c) used for `MonAiInit` (README 29, 31): the cases stop at the call instructions 0x005B0F18 (the row's
   init, indirect) and 0x005B0F30 (`IsBadCodePtr`), and the class and state rows are read from `game.exe`'s `.data` by
   the tool as image constants; the stores after a non-zero init and the import's fatal branch are left `[I]`.
2. The raised-in-part rows of part 3 (machinery 13, 16; README 29, 31, 39): each remainder lies after an observed
   boundary and is named in its Route cell → b.
3. `UNIT_GetSizeX`'s type-3 case added in `tools/ai_s1ne3_emu.py`'s own process (part 1's map raised on types 0, 1, 2,
   4, 5): size 0 on the declared image, DataTables `+0xB6C` 0.
4. The seven not-settled rows, each with its route; the target search (`MonAiFindTarget`, `MonAiFindHostile`) was not
   reached within the closing part's budget.
5. Machinery 51 and 52 raised on 48 and 7 seed-compared draws (52's player draws: 5 below 80, 2 at or above; control
   `cand player` separates 16).

This is the first check since the S2be audit restarted the count. Not blocking.
