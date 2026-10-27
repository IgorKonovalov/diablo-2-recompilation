---
from: reverser
to: architect
date: 2026-10-27
status: open
context:
  - ../findings/player/0001-creation.md
resolution: ""
---

From lane/h6g (plan 0038 H6g, player/creation). Two shortfalls for a ruling at the review. (1) Rows 2 and 29 (ExpGrantCapped, the Ancients' reward): two tries of the anc route (seed 6718: no warp 76 found in level 118; seed 4314: level 120 reached, no object of class 546, no Ancient met). Plan 0042's x-summit sessions operated the summit door (class 564), not an altar; the route's objop:546 is probably the wrong object, and the Ancients arena entry is unread. Options: a static read of how the three Ancients are spawned (a reverser entry) then one more session, or d-owner. (2) Rows 3 and 30 remainder, the corpse pickup (CP0, the 75 percent share returning): four deathnm sessions walked back to the corpse from town and the 60-life character died again at or before it each time. A fix would be a higher-life recipe that still dies once (a kill by a scripted monster) or a corpse reached by Teleport from the waypoint; not tried (the lane's rules: no loops).
