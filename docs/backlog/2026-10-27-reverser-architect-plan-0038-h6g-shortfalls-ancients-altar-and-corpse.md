---
from: reverser
to: reverser
date: 2026-10-27
status: open
context:
  - ../findings/player/0001-creation.md
resolution: ""
---

From lane/h6g (plan 0038 H6g, player/creation). Two shortfalls for a ruling at the review. (1) Rows 2 and 29 (ExpGrantCapped, the Ancients' reward): two tries of the anc route (seed 6718: no warp 76 found in level 118; seed 4314: level 120 reached, no object of class 546, no Ancient met). Plan 0042's x-summit sessions operated the summit door (class 564), not an altar; the route's objop:546 is probably the wrong object, and the Ancients arena entry is unread. Options: a static read of how the three Ancients are spawned (a reverser entry) then one more session, or d-owner. (2) Rows 3 and 30 remainder, the corpse pickup (CP0, the 75 percent share returning): four deathnm sessions walked back to the corpse from town and the 60-life character died again at or before it each time. A fix would be a higher-life recipe that still dies once (a kill by a scripted monster) or a corpse reached by Teleport from the waypoint; not tried (the lane's rules: no loops).

**Routed (architect, 2026-10-30, owner decision; [plans README](../plans/README.md) § Owner decisions (2026-10-30), [plan 0038 log](../plans/0038-inferred-claims-sweep.md#implementation-log)):** owner play is postponed, so this entry goes to a **reverser static read now** (lane `lane/h6gs`, static, objdump or Ghidra headless, no harness slot). The entry is re-addressed `to: reverser` and stays **open** at this path until that lane's review closes it. What the read answers:

1. **The Ancients (rows 2 and 29, `ExpGrantCapped` on the Ancients' reward).** How the three Ancients are spawned and the reward granted: what starts the encounter on the Arreat Summit (level 120: the altar or another object, its class and OperateFn, the object the `anc` route should operate in place of `objop:546`), how the three are created (superunique rows, the spawn call, positions), what ends the encounter and calls the experience grant, and the quest bits read and written on the way. Named functions with addresses and tags; the reading may raise rows 2/29 to `[C]` only by the evidence rules (a second source), else it gives the next harness session a correct route.
2. **The corpse pickup (rows 3 and 30 remainder, `CP0`, the 75 percent share returning).** The pickup path from the client's click on the corpse to the experience or gold returned: the server handler, its gates (distance, the owner check, difficulty), the share arithmetic, and whether a corpse can be reached by Teleport from the waypoint (no walk back). Also whether a recipe can die exactly once (a scripted kill) without a death loop.
3. **Output:** the reading in `findings/player/0001-creation.md` (or a new player finding), symbols in `re/symbols.csv`, and a routed next step per row: raised statically, a harness session with the corrected route (one slot, the queue's next free one), or the **owner-play option**, which **stays open as a later choice** (d-owner), not dropped.

Plan 0038's H6g totals stay as the `lane/h6g` check left them until this read is reviewed.
