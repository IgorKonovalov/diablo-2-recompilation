---
from: reverser
to: architect
date: 2026-10-27
status: done
context:
  - ../../plans/0038-inferred-claims-sweep.md#implementation-log
  - ../../plans/0038-inventory/README.md#26-moves-made-by-the-batch-reviews
  - ../../findings/items/experiments.md#run2026-10-27-sweep-quest-items
  - ../../findings/items/0010-quest-drops.md#plan-0038-batch-h6e2-run2026-10-27-sweep-quest-items
resolution: "Reviewed 2026-10-27: accept with fixes (3: misread 1, tool not kept 1, other 1). Rulings, fixes and totals in the plan 0038 log; spec-writer entry released; two entries routed (archivist test_d2s h3brare, reverser d2pilot descend by destination)."
---

Review plan 0038 batch H6e2 (`quest-items`; items/quest-drops rows 1, 30, 33, 34, 35 and objects row 48;
`lane/h6e2`), run:2026-10-27-sweep-quest-items. 11 kept sessions on slot 1 (expansion, one player; Normal and one
Nightmare; agent-driven), 19 launches, 8 development logs (`dev-` names). Manifests `workspace/logs/h6e2/manifest-final.sha256`
(10 resume logs, pilot outputs, `check-final.txt`), `manifest-ckpt1.sha256` (the gate session and its check) and the
two `manifest-dev-*.sha256`, all `sha256sum -c` from `workspace/logs/h6e2`. Check: `python3 -I tools/sweep_h6e2.py check
workspace/merged/data/global/excel $(ls workspace/logs/h6e2/quest-items-*.log)` → chest 6, object 2, event7 19, dup 8,
gate 8, death 3 (listed), 0 mismatches.

Ledger of the 24 statements: **raised 3, raised in part 14, shortfall 7** (inventory § 2.6 H6e2 block; items/0010's
ledger table gives each part).

Points for the ruling:
- (a) **The E1 correction.** The heart chest drew its quest seed and 8 gold piles before `qhr` and before
  `ObjectChestDrop`, as the checkpoint's static read said; qd 33 and the objects chests row are filed raised in part
  *with the correction*. The eye and brain chests are the same read shape but not run.
- (b) **qd 30 Wirt's gold** was already `[C]` in the spec (run:2026-10-19-economy2, plan 0043) before this batch; it is
  counted raised here (met again, with the event-7 route). Say if it should be counted otherwise.
- (c) **The orifice row** is raised in part from a kept log of run:2026-10-16-quest-drops
  (`quests-s3-3364-duriel-normal.log`, two `QS` writes inside `StaffPlaced`), as the inventory's a-logs route allows.
- (d) **The second clicks** on Wirt's body and the Inifuss tree logged no operate, so the "mode ≠ 0: nothing" halves of
  `leg` and `bks` were not run (they stay `[I]`); whether the game offers a used object to a click is not read.
- (e) **Map seeds and saves.** The Act II and III sessions start in the Act IV town from three new recipes (header act
  bytes 131); `cube4`/`cube-held4` share map seed 4911 and `staff4b`/`staff-nm4b` 4916, so each pair has the same quest
  seed and the same `k`.
- (f) **Rule 14:** eleven symbols I → C (plan log). `OBJ_EventDispatch`, the thunk, `ObjEventsRun`,
  `GameRunUnitEvents`, the lever target and the two death scripts are met as call sites or listed only, so left I.
- (g) **Totals** against `main` `147e5ca3` after merging it: unchanged, static 567, harness 519, c-emu 0, blocked 421,
  deferred 2, raised 17: 1 526.
- (h) **Released with the review:** the spec-writer entry
  [2026-10-27-reverser-spec-writer-h6e2-quest-items-raises-and-the-khalim-chest](2026-10-27-reverser-spec-writer-h6e2-quest-items-raises-and-the-khalim-chest.md)
  (held until then).
