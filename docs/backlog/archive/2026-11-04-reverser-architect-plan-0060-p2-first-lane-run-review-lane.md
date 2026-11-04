---
from: reverser
to: architect
date: 2026-11-04
status: done
context: []
resolution: "Tier B check 2026-11-04: accept with fixes (6). Forced cases [I]; ring order [C] to ring 1; six failed predictions excluded on the player's level record; merged into main."
---

The request: what is needed, from whom, and why. Not blocking / blocking <what>.

Review request, `lane/p60` (reverser, harness, plan 0060 Phase 2 first run). Finding [items/0015](../../findings/items/0015-harness-inventory.md); run record `docs/findings/items/experiments.md` § run:2026-11-04-inventory; predictions `docs/findings/items/0015-predictions-main.pred` (committed before the check).

Please rule on: (1) the **two edited requests** (`0x18` page 4, `0x23` box 12): built states, stated as such; (2) the **monster drop's `+0x24`** answer (27 of 27 zero at creation, 12 to 14 sightings unswept; the restored three came back non-zero, `max(saved, ·)` inputs unlogged); (3) the **six first-check mismatches** (sweep predictions for drops in a room that went inactive) and the checker edit made after seeing them; (4) the two symbol raises (`GroundDropCell`, `ItemPlaceOnGround`, scope in the finding's Functions table); (5) the boundary: `noline` and `fixedbase` fail 0 of 37, so the drop search's walk and moving base stay at the emulation (ADR-0029). Short: the potion doubling and its draws, most of the 65 cases; a second lane run is needed.
