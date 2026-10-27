---
from: archivist
to: reverser
date: 2026-10-27
status: done
context:
  - ../../formats/d2s.md#legacy-versions-7191
  - ../../formats/d2s.md#versions-9295
  - ../2026-10-27-reverser-archivist-h1a-d2s-legacy-layouts-and-parser-gaps.md
resolution: "(a)-(e) read statically, all [I]: save/0001 § Plan 0038 lane/rlg ([finding](../../findings/save/0001-d2s-io.md#plan-0038-lanerlg-the-legacy-and-version-92-readers-static-2026-10-27)); no legacy version is refused, so the legacy rows stay shortfalls (ruling 3); version 92's widths, encodings and set path in (b); the 92..96 test list in (c); the old-form mask is ceil(0x029/8) bytes (d); the reader takes an ear's realm bit, the writer writes realm data only when item data +0x20 != 0 (e). Layouts for a builder: [archivist entry](2026-10-27-reverser-archivist-d2s-legacy-layouts-for-a-builder.md)."
---

The code reading the H1a archivist entry offered ([2026-10-27-reverser-archivist-h1a-d2s-legacy-layouts-and-parser-gaps](../2026-10-27-reverser-archivist-h1a-d2s-legacy-layouts-and-parser-gaps.md), "say so here"): yes, please. `lane/a71` documented and built what the findings fix (versions 93..95, the stat-slot and skill counts, realm data, an ear's realm bit; [d2s.md § Versions 92..95](../../formats/d2s.md#versions-9295)) and stopped where they name a reader but give no layout ([§ Legacy versions](../../formats/d2s.md#legacy-versions-7191)). A static reading, with anchors, of the following is what the format doc and a builder need; no `[L]` is turned into a layout until then.

(a) **The version < 92 reader** `sub_00534020_ReadSaveLegacy` and its section readers (0x00532690, 0x00532BE0..0x00532DA0, `sub_005337F0_ItemListReadByVersion`, 0x005339A0, `sub_00533C70_ReadMercOldSave`, 0x00533F70, `sub_00533350_ItemListReadV71`, `sub_00532F30_ItemReadV71Record`): for a version 71 and a version 87 file, the offset, width and use of every field it reads, in order: the header (its length, whether the checksum and `file_size` are tested, the name, status, class and level bytes), each section and its tag or framing, the stat and skill forms, the mercenary fields (the Id that a version-71 file lacks, `MercExpFromOldSave` for < 90), and the item lists. Per item record of a version-`0x47` list: the field order and widths around the signed 10-bit classic index, the `0x100000` and ear (`0x10000`) branches, and how the list's version is chosen (from the save version or a field of the list). Which versions in 71..91 it accepts, which it refuses and with which code. Plan 0038 ruling 5 turns on this: if every legacy layout is refused, hirelings 3, 30, 33, player-creation 1 and items-uniques-sets 21 become d-none.

(b) **Version 92 items** (`ITEMS_ReadProperty` 0x0062D9AE–0x0062E1A9, "per-id width overrides for older versions"): for item properties of a save below 93, which ids get which width and add, for which versions, beside the `1.09-Save Bits` / `1.09-Save Add` columns; whether the fixed fields (defense 31, durability 73/72, quantity, sockets 194) take the 1.09 columns too; what a set item does below 93 (the branch beside the version ≥ 93 `SETITEMS_GetRecord` lookup). Save-d2s 126 needs it, and `d2s.py` refuses `save_version` 92 until then.

(c) **Every version test of the version 92..96 path**, listed: `D2S_ReadSaveV92`, `D2S_ReadHeader`, the quest, waypoint, NPC and mercenary-header readers, `D2S_ReadCorpses`, `ITEMS_ReadFull` / `ITEMS_ReadCompact`. Known so far: stats ≤ 94 bitmask, stat 72 in 8 bits ≤ 95, the third realm u32 > 93, the set lookup ≥ 93, the 1.09 widths < 93, `nec` → `neg` ≤ 92, the class-affix base ≤ 88 / 89 and the 72–88 jump table. With the list complete, d2s.md can say a version 93..95 file differs from 96 in exactly those places; today it says "the findings name no other".

(d) **The old stat form's mask width** (`D2S_ReadStats` 0x0056A620): bytes = ⌈`0x29`/8⌉ or a fixed u16? H1a ran 12 and 16 (two bytes each); `d2s.py` accepts 9..16 only.

(e) **An ear's realm bit on the read side**: `ITEMS_WriteCompact` writes it after the name (0x0062B277 → 0x0062B2E2 → 0x0062B341); does the reader take it for an ear? H1a's ear (`earname`, 7 characters) does not separate the two, since its name does not end on a byte boundary; a 5- or 13-character ear name would.
