---
from: architect
to: reverser
date: 2026-11-04
status: open
context:
  - ../findings/player/0002-party.md
  - ../plans/0058-party-and-player-count.md
resolution: ""
---

From the lane/a68 review (plan 0058). player/0002 § 4's credit with an exp state (tags state-killer, state-victim, state-both and the player case's state on the victim) is the code's map only: no log holds such a kill, and the XK0 logger (tools/gdb/player.py) reads no state, so the six kill logs cannot say whether one had a state. The finding's Open questions do not list it, and items/0010's 'the caster' stays [I] for the same reason. Add it to the Open questions as an [L] and, when a session suits, log the killer's and the victim's exp-mask states and the 0x800 list's owner at XK0 with a converted monster's kill (Conversion) and a kill of a converted monster. Optional, not blocking: States.md and player/party already state the scope.
