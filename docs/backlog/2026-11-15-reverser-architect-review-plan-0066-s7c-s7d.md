---
from: reverser
to: architect
date: 2026-11-15
status: open
context:
  - ../plans/0066-simulation-inferred-claims-sweep.md#implementation-log
  - ../plans/0066-inventory/README.md#4-batch-list
resolution: ""
---

Please review `lane/n66m`: plan 0066 Phase 1 batches **S7c** (path, 18 rows) and **S7d** (drlg/lifecycle, 14 rows).
Static only: no game, no Ghidra; new checks over kept logs. This lane gets a **Tier A audit** (the owner's
orchestration announced it); a Tier B check first if the plan's audit rule wants one. The entry is in the plan's log
(2026-11-15, S7c and S7d).

Worth checking:

1. `python3 -I tools/sweep2_s7c.py check` and `python3 -I tools/sweep2_s7d.py check`, each under a 4 GB scope, give
   `workspace/logs/n66m/s7c/check-s7c.txt` (`911948c8…`, `S7c total bad=0 control_bad=0`) and
   `s7d/check-s7d.txt` (`6e30d778…`, `S7d total bad=0`, control `SUMMARY mismatches=4 checks=2891656`, the kept
   checks' sum) byte for byte; `manifest.sha256` passes from `workspace/logs/n66m`.
2. The controls behind the raises: the per-room variant of the reference walk (71 894 separating deltas), the spiral
   variants (4 × 260), the 12/32 walk map (851), the aim's 17 406 changed records, the live-cell control (83 839 of
   94 349 lone units hold their bits), `RoomActivateB`'s first walks at `+0x78` 0 (118 of 153).
3. Judgment calls: (a) README 9 and 10 raised although 558 player and 249 vulture plans carry other masks, read as
   later writers (Whirlwind, Leap Attack, `AiVultureTakeOff`'s `push 0` at 0x005F2FA2), not the creation rule;
   (b) `g_PathPlanFuncs` and `PATH_MonTestMask` raised to C on those comparisons (review-fixes 14 read broadly: the
   table read at the logged call, the mask written from the function's return); (c) README 2 and 31 not raised: `BRK`
   is a planner break, not a blocked step, and `PathReplan` has 4 callers (the row's label omits
   `PathStepTargetCheck`'s); (d) the fallback and replan follow-ups unlogged after cap lines counted as explained (84,
   2 480, 39), with "after a cap line" meaning any 2/7/9/13 (or 2/13/15) cap line earlier in the game; (e) lifecycle 59
   not raised, the logged order being the breakpoints'; (f) lifecycle 14's "every room of the near list" taken on
   the DRLG near list at `RMX` (active, status ≤ 1), the file-loading half left; (g) row 25's frame-window `RR` lines
   not used.
4. Phase 3 notes in
   [`2026-11-15-reverser-spec-writer-plan-0066-s7c-s7d-phase-3-notes`](2026-11-15-reverser-spec-writer-plan-0066-s7c-s7d-phase-3-notes.md).
