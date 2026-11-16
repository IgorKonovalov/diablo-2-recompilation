---
from: spec-writer
to: spec-writer
date: 2026-11-16
status: open
context:
  - ../plans/0066-simulation-inferred-claims-sweep.md
  - ../specs/README.md
resolution: ""
---

Plan 0066 Phase 3, frame cluster (lane/n66pf), updated sim/frame, path/README, path/search, drlg/lifecycle, player/party, drlg/collision (E4), monsters/spawn (K1's gate, review-fixes 8) and quirks on 2026-11-16, so the wiki pages based on them carry W4: server-frame, pathing, levels, monsters, objects, seed-to-world, characters (with the combat refresh entry) and quirks (with the anim refresh entry). What changed for a reader: the frame windows and second tools now confirm most of the tick's order (ranks 5, 10 to 13 and the open-server thread stay read), a one-byte 0xB0 send leaves the frame inside AutosaveTick; the wanderer gate's tests are the code's map (the spawn never met); RoomActivateB has a fifth caller family (a unit spawn at coordinates); ItemPlaceOnGround has four more callers; the wraith's test mask is creation's own branch and vultures plan with test mask 0; two AI removals read a monster's SizeY. Refresh the pages against the specs (spec-writer review-fixes 1: a wiki page follows the spec that carries the raise) and bump based_on. Not blocking.
