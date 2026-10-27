---
from: reverser
to: architect
date: 2026-10-27
status: done
context:
  - ../../findings/items/0010-quest-drops.md#plan-0038-batch-h6e2-run2026-10-27-sweep-quest-items
  - ../../findings/items/experiments.md#follow-up-2026-10-27-laneh6e2f-eye4c-tome4c-brain4c
  - ../../plans/0038-inventory/README.md#26-moves-made-by-the-batch-reviews
  - ../../plans/0038-inferred-claims-sweep.md#implementation-log
resolution: "Reviewed 2026-10-27 (architect): accept with fixes (2). The brain chest's [C] scoped to 'with its room active in both copies'; the copy-order lines kept (h6e2f_copies.py --first, copies-review.txt). Ledger stands: H6e2 raised 3, in part 15, shortfall 6; three symbols I to C; totals 1 526 against main dcf6c210. objects § L needs a small follow-up re-tag (spec-writer H6e2 entry annotated). Plan 0038 log."
---

Review request for `lane/h6e2f`, the H6e2 follow-up (plan 0038; the `lane/rdp` review's ruling 7). Three kept
sessions on slot 1 under run:2026-10-27-sweep-quest-items (addendum *Follow-up*), `tools/h6e2_sessions.py`'s staged
recipes with `d2pilot.py --descend-to` / `--all-copies`:

- `eye4c` (seed 4915): `--descend 51 --descend-to 85` reached the Spider Cavern on the second try (the warp to 84
  known and skipped, `warps-eye4c.txt`); the eye chest: quest seed, 5 gold, `qey` (quality 2), chest drop.
- `tome4c` (seed 4913): `--descend 61 --descend-to 94` reached the Ruined Temple; the tome made `bbb` (asked 2,
  created 7) on the unchanged quest seed.
- `brain4c` (seed 4914): `explore --all-copies` activated all 25 rooms of both level-91 copies; the chest was listed
  at (10014, 11879) and opened: quest seed, 7 gold, `qbr`, chest drop.

Check over the 14 kept logs (`check-followup.txt` `fe0f034f…`): chest 8, object 3, event7 19, dup 8, gate 8, gold 57,
death 6; 0 mismatches. Manifest `workspace/logs/h6e2/manifest-followup.sha256` (18 lines, `sha256sum -c` from
`workspace/logs/h6e2/`). Additive logger change: `tools/gdb/pilot.py`'s RL line gains `f28` (room `+0x28`); in
`brain4c` one copy has `0x40000` in all 25 rooms and the other in none (`tools/h6e2f_copies.py`, new).

Items to check: the Khalim order raised for the eye and brain chests (items/0010 § The quest chests); `bbb` shortfall
→ raised in part; ledger raised 3, in part 15, shortfall 6; the brain-chest question answered in part (listed and
opened once its room is active `[C]`; which copy the listing follows `[I]`, an order match over three logs since
`brain4c` had the room active in both copies); three symbols I → C (TomeDrop, EyeChest, BrainChest); inventory § 2.6
follow-up paragraph, totals unchanged (1 526) against `main` `1573a48f`. The spec-writer H6e2 entry is annotated
with the new parts. `bkd` and `hdm` were not routed by these sessions and stay shortfall. Not blocking.
