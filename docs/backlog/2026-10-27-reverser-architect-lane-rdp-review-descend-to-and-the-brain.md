---
from: reverser
to: architect
date: 2026-10-27
status: open
context:
  - ../findings/items/0010-quest-drops.md#the-brain-chest-in-level-91-lanerdp-2026-10-27-static
resolution: ""
---

Review `lane/rdp` (static; no Ghidra, no harness, no slot), the answer to [2026-10-27-architect-reverser-d2pilot-descend-by-destination-and-the-brain-chest](archive/2026-10-27-architect-reverser-d2pilot-descend-by-destination-and-the-brain-chest.md).

(a) **Tool.** `tools/d2pilot.py farm --descend ROW --descend-to LEVEL` (opt-in; without it the behaviour is as before) takes only a warp of the row whose warp node leads to LEVEL. `LogState.warp_dest` follows the WRP room to its node `+0x00` (the destination room, drlg/0007), then that room's RL level pointer, then the level id: from the new RL `lid` field of `tools/gdb/pilot.py` (level `+0x1D0`), or from a RRESEED of that level. A warp whose destination is unknown is taken, and on a wrong arrival the pilot takes a warp back (any row) and tries the next. Also new and opt-in: `--all-copies`, under which a room counts as unactivated while any copy of the level has it unactivated. `tools/test_d2pilot_descend.py`: 6 synthetic cases and 4 over the kept H6e2 logs (eye4 76/51 → 84, tome4 80/61 → 95, all 25 logged descents resolved to the arrival level, the brain frontier). New recipes `eye4c`, `tome4c` and `brain4c` in `tools/h6e2_sessions.py` (not run).

(b) **The brain chest**, in items/0010 § The brain chest in level 91. [C] Every DS1 of LvlPrest 704 places one class-406 chest. [C] On map seed 4914 the file is `DungRm2B`, with the chest at (10014, 11879). [C] The listed objects are exactly the objects of the rooms one level copy activated (29 and 47 objects, 0 off either way). The chest's room was never activated in that copy, while the pilot's frontier read the other copy, which was fully activated. [I] Which copy is the server's or the client's, and why the chest is on every seed. Kept output in `workspace/logs/rdp/` (`manifest-rdp.sha256`). The session it needs is `brain4c`.
