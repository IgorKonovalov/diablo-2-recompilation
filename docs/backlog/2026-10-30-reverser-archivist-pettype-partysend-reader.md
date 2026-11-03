---
from: reverser
to: archivist
date: 2026-10-30
status: open
context:
  - ../findings/frame/0003-timers-activation.md
  - ../tables/PetType.md
resolution: ""
---

A code reader for PetType `partysend` (`+0x004` bit 2) to link from [PetType](../tables/PetType.md): `sub_00575630_PlrPetsStatusSend` (player event kind 11, every 30 frames) sends packet 0x7F for each of the player's pets of a type whose row has the bit (`byte [rows + 0xE0·type + 4] & 4`), and `sub_00575590_PetListPrune` skips type 7 (`hireable`) when it removes missing or dead pets ([frame/0003 § 6](../findings/frame/0003-timers-activation.md#6-player-kind-11-frame0002-open-question-2); fn:sub_00575630_PlrPetsStatusSend@0x00575630). The column's meaning in the table doc already agrees; the request is the reader link. Not blocking.
