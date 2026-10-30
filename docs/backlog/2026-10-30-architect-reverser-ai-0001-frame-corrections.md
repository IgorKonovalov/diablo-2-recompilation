---
from: architect
to: reverser
date: 2026-10-30
status: open
context:
  - ../findings/ai/0001-machinery.md#1-the-tick-its-caller-and-the-order
  - ../findings/frame/0001-tick-and-messages.md#2-gametick
  - ../plans/0055-server-frame.md#implementation-log
resolution: ""
---

Correct ai/0001 §§ 1 and 11 from frame/0001 (plan 0055 P1.1 review, lane/r55). Not edited at that review because lane/r52c (plan 0052 batch 2) is active in docs/findings/ai/; apply in the next lane that edits ai/0001 after lane/r52c merges (lane/r52c itself may take it), as a dated note per bullet. (1) § 1 'The frame': the two act passes are sub_0052D7B0_ActsClockPass (0x0052D8DF) and sub_0052D720_GameFpsStats (0x0052D8E6); after the room sync come sub_0053B000_ActUnitsFrameReset (0x0052D900) and sub_0053A820_ActsRoomRemovalsClear (0x0052D907); GameRunUnitEvents is called at 0x0052D8F2 (0x0052D8EB is NewRoomsUpdate's call); ServerGamesFrame's call to GameTick is 0x0052FD19 (0x0052FD17 is the mov before it); GameTickAlt is GameTick's other caller (0x00564603) but is unreached: its only caller is the unreferenced stub 0x00564C70 (frame/0001 § 1). (2) § 11 'The room unit lists': Room+0x1C (next Unit+0xE0) holds only the units marked updated this frame (sub_0064C040_UnitMarkUpdated, bit 0x2000 of Unit+0xC4, pushed on the front) that are still in that room (0x0064C370 unlinks at 0x0064C42D), and ActUnitsFrameReset walks it only for acts whose dirty word is set (frame/0001 § 3.3, run:2026-10-30-frame-emu). Keep ai/0001's tags as they are ([I]).
