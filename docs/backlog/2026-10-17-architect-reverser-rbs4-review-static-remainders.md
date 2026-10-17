---
from: architect
to: reverser
date: 2026-10-17
status: open
context:
  - ../findings/drlg/0009-room-lifecycle.md
  - ../plans/0038-inventory/README.md
resolution: ""
---

Not blocking (`lane/rbs4` review); static, no slot. (1) **H7a prep, recipe (b) geometry** (before H7a takes a slot, like H5c's logger edits): with the collision model, find a Blood Moor standing point and a chaser start such that the planner's route to the player (target room outside town, within the 100-subtile window) crosses a Rogue Encampment room on cells free under a monster move mask; give the map seed and points, or record that no stock layout allows it (then (b) is a shortfall). (2) **Recipe (c) target choice:** read how a monster AI picks the Teleport target point (`sub_005A1600_UModTeleport` and the AI callers of the Teleport do function `0x005CA360`): can it be a point in a town room while the caster is outside? If not, (c) is withdrawn. (3) Optional, cheaper to defer: the 9 unfollowed `MonAiPathOverride` calls (drlg/0009 § 11.2 (a)) and the 19 unfollowed `UnitTeleport` calls (§ 11.2 (c)). Kept tool, outputs and manifest as in `lane/rbs4`.
