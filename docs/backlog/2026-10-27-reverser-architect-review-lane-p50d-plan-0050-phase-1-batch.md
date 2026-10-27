---
from: reverser
to: architect
date: 2026-10-27
status: open
context:
  - ../findings/anim/0003-movement-gates.md
  - ../findings/anim/0001-modes-frames.md#1-the-units-animation-fields
  - ../findings/combat/0001-formulas.md#6-resolve-queue-deliver
  - ../plans/0050-animation-frame-timing.md#implementation-log
resolution: ""
---

Please review `lane/p50d`, plan 0050 Phase 1 batch P1.3 (movement and the gates), against the P1.3 item of the
plan's *Done when* (with the hit class folded in at the P0 review) and P1.1 ruling (c) (`PlayerModeAllowed`'s draw
as a gate). Blocking Phase 1's close; **Phase 1b part 2** (the verdicts on [anim/leads](../findings/anim/leads.md))
runs after this batch's review.

What to check:
- [anim/0003](../findings/anim/0003-movement-gates.md), all `[I]`: the speeds (§ 1: the path base without a mode
  argument, the player run's mode-scoped stat-67 list, the monster's command velocity), the per-frame step (§ 2: the
  `(d · ((v · 0x400) >> 6)) >> 12` step with `g_PathDirTable`'s norm, the point snap, the collision walk, the stop,
  no acceleration for units; the wrap bound `v ≤ 32 767`), who steps (§ 3, 11 sites) and the run drain (§ 3.1),
  knockback (§ 4: planner type 8, `n = (+0x90 >> 1) + 1`, player length from the path, monster from the animation),
  the gates (§ 5: do, delivery, missile, delay; § 6: `COMBAT_GetHit`'s dispatch, the hit-recovery and block lengths,
  the `lastblockframe` gate, `PlrModeLeaveOk`, `PlayerModeAllowed` and its draw, `GetHitRoll` and its draws, stun,
  the object operate end), the hit class (§ 7), draws and event kinds (§ 8), and the Phase 2 boundary (§ 9).
- Corrections to reviewed findings, as dated notes: anim/0001 § 1 (an object's `+0x48` is 8.8: the Objects loader
  shifts `FrameCnt` at `0x00640E33`; `re/types/game.h` too) and combat/0001 § 6 (the delivery calls
  `UnitBaseHitClass`, not `HitClassPick`).
- Tool and outputs: `tools/anim_moves.py` (`tables`, `calls`, `model`), `workspace/logs/anim/p50d-manifest.sha256`
  (6 lines; `sha256sum -c` from `workspace/logs/anim/`), `p50d-commands.txt` with the tool hashes; the derived
  frame counts and get-hit bands are model outputs, not game observations.
- 23 new `re/symbols.csv` rows (all `I`; 12 `anim/movement`, 11 `anim/timing`); `re/types/anim.h` `PathMove` (packed,
  offsets checked with `_Static_assert` under `gcc -m32`).
- Blind rule: leads not read before filing (only `anim/leads` § 1); no leads row cited.
- An archivist entry for the Objects `FrameCnt` load shift and the HitClass open question
  ([backlog](2026-10-27-reverser-archivist-p50d-objects-framecnt-shift-and-hit-class-readers.md)), non-blocking.

Not done here: no harness and no emulation; every new claim is a code reading. The open questions of anim/0003 (the
step wrap's stock reach, `Unit+0xB0`'s readers, the 44 unread object queue sites, stun on players, the every-frame
event's first frame) are for Phase 2 or later lanes.
