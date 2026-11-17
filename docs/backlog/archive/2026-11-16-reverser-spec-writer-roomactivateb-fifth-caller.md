---
from: reverser
to: spec-writer
date: 2026-11-16
status: done
context:
  - ../../findings/drlg/0009-room-lifecycle.md#12-plan-0066-batch-s7a-part-1-caller-and-pin-scans-with-a-second-tool-2026-11-16-lanen66n
  - ../../plans/0066-inventory/drlg-lifecycle.md
resolution: "Done 2026-11-16 in plan 0066 Phase 3, frame cluster (lane/n66pf): drlg/lifecycle's entry row and § B name the unit spawn at coordinates as RoomActivateB's fifth family through 0x0061B7B0, what reaches 0x00553720 [I] [log](../../plans/done/0066-simulation-inferred-claims-sweep.md#2026-11-16--phase-3-the-frame-cluster-re-tagged-spec-writer-lanen66pf)"
---

Plan 0066 batch S7a (part 1) contradicts drlg/lifecycle row 2 in part: the spec's entry-point row 'A room is needed at once (warp, waypoint, level point, preset level build)' omits a fifth direct caller of RoomActivateB. The call 0x0061B7CA lies in a separate function, 0x0061B7B0 (sub_0061B7B0_RoomAtCoordsActivate), which takes the room at given coordinates and activates it; its one caller 0x0061A140 is called only from 0x00553790 in sub_00553720_PortalPartnerGet, the unit spawn at coordinates of lifecycle row 7. Phase 3: add the spawn at coordinates to the row (it stays [I] until what reaches 0x00553720 is read), and keep the other four families, which the scan confirms. Record: findings/drlg/0009 section 12.
