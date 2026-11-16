---
from: reverser
to: architect
date: 2026-11-16
status: done
context:
  - ../../plans/0066-simulation-inferred-claims-sweep.md
  - ../../findings/anim/experiments.md
resolution: "Tier B check 2026-11-16: accept with fixes (2); movement 22/43 to c-emu (H6d 19), timing 62 provisional in H6d pending S6g, timing 49 schedule half to S6g; merged into main."
---

Tier B review of plan 0066 Phase 1 batch S6f (`lane/n66s`): the five rows the `lane/n66l` check left unsettled and
the room-walk attempt of its ruling (c). Emulation run:2026-11-16-sweep2-s6f (`tools/anim_s6f_emu.py`;
`workspace/logs/n66s/s6f/run/check.txt` `55040b7a…`, `knock.txt` `e39c661d…`, `manifest.sha256` `83e3c276…`, passes
from that directory; 16 100 cases, 0 mismatches, 81 of 88 controls separating, the 7 others named). Outcomes, class
moves (movement 22, 43 b → c-emu; H6d 21 → 19), totals and judgment calls are in the plan log entry of 2026-11-16
(S6f). Refinements to the spec-writer in
[2026-11-16-reverser-spec-writer-plan-0066-s6f-corrections](2026-11-16-reverser-spec-writer-plan-0066-s6f-corrections.md).
Not blocking.
