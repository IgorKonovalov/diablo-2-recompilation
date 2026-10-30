---
from: reverser
to: archivist
date: 2026-10-30
status: done
context:
  - ../../findings/items/0007-sockets-runewords.md
resolution: "Built: recipe key \"corpse\" for save_version 71 and 87, tests in test_d2s.py [d2s.md](../../formats/d2s.md#legacy-versions-7191); versions 72-86 and 88-91 stay unbuilt"
---

The legacy builder writes an empty corpse list at versions 71 and 87, so the corpse reader (0x005339A0), sub_00531390_OldItemPlaceCorpse and the second version-71 socket insert site (0x005313F0) were not exercised by plan 0038 H1c. A builder key for one corpse (the 12 unread bytes and an item list, optionally with a socketed item) at save_version 71 would let a harness batch run them. Also unbuilt: versions 72-86 and 88-91 (hirelings 33's <= 89 cutoff needs a 90 or 91 file).
