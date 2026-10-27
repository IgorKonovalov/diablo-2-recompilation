---
from: reverser
to: architect
date: 2026-10-27
status: done
context:
  - ../../plans/0050-animation-frame-timing.md#implementation-log
  - ../../findings/anim/0001-modes-frames.md
resolution: "2026-10-27 architect: accept with fixes (7); rulings (a)-(f) and the blind check in the plan 0050 log; P1.2 may start after the merge"
---

Review plan 0050 Phase 1, batch P1.1 (`lane/p50a`, static, Ghidra copy `ghidra-p50a`): the new finding
[anim/0001](../../findings/anim/0001-modes-frames.md), 75 new `re/symbols.csv` rows (subsystem `anim/timing`, all `I`),
the Unit animation fields in `re/types/game.h` and the new `re/types/anim.h`, `tools/anim_scan.py` and the `stop@`
root of `RngCallGraph.java`. Kept outputs: `workspace/logs/anim/p50a-manifest.sha256` (`sha256sum -c` passes from
`workspace/logs/anim`). Every claim is `[I]`; no run, no raise. Blocking P1.2 (the next batch).

Done-when items of P1.1 and where they are: `UNIT_SetMode`/`UNIT_AnimInit` per unit type (§ 3), the record and its
fallback (§ 2), the frame fields and their widths (§ 1), the per-frame advance and the event byte (§ 8), the server
schedule and the mode end (§ 7), the transitions (§§ 9–10), the monster mode table per row (§ 10), sequences (§ 5),
every draw with its seed (§ 11), the event kinds (§ 11), a preliminary boundary note (§ 12).

Points for the ruling:
- (a) **Two clocks.** Most server modes are scheduled once at their start (`SUNIT_ScheduleModeEvents`), not advanced
  per frame; only monster every-frame modes advance (`UNIT_AnimAdvance`). Phase 2's log windows and P1.2's "does a
  rate change apply to a mode in progress" both follow from this (a scheduled mode keeps its events unless a catalogue
  function reschedules, § 7.1).
- (b) **The monster frame event ignores the 2** (`0x005A7BA0`); an every-frame monster attack or skill mode
  (`*mv`) has no end of its own in the code read (open question 1). Ask: keep as an open question for Phase 2 to
  log, or route to plan 0052 (the AI command)?
- (c) **The RNG claim's scope.** "The only draw of the animation machine" rests on a static graph (171 functions,
  29 roots) with stops at the fatal/allocator entries and at `0x005544B0` (reached only from the event queue's kind-2
  branch, which the schedulers never take: `QEV` lines). Three indirect calls (stat-list callbacks) are not followed;
  their targets are stats/states'. The mode-function graph (39 roots, 128 RNG functions) is reported by entry, not
  classified function by function.
- (d) The archivist entry for `animdata.d2`, `monseq` and the token tables is filed
  ([2026-10-27-reverser-archivist-p50a-animdata-monseq-readers](../2026-10-27-reverser-archivist-p50a-animdata-monseq-readers.md)).
- (e) Two answered questions of other findings were annotated with dated notes: skills/0001's `Unit+0x38` and
  "which frame carries code 1 or 2", skills/0002's missile pass order.
- (f) The five Phase 0 data surprises (`lane/p50z`, relayed by the orchestrator) are answered from the code in
  anim/0001 § 2.1: the first same-named record in the block wins; objects never use their `animdata.d2` record on the
  server; a sequence's frame and event come from the sequence record, never the `animdata.d2` byte; no load of
  `eanimdata.d2` exists. All `[I]`.
