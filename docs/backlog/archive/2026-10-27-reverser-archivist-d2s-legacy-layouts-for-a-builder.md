---
from: reverser
to: archivist
date: 2026-10-27
status: done
context:
  - ../../findings/save/0001-d2s-io.md#plan-0038-lanerlg-the-legacy-and-version-92-readers-static-2026-10-27
  - ../../formats/d2s.md#legacy-versions-7191
  - 2026-10-27-reverser-archivist-h1a-d2s-legacy-layouts-and-parser-gaps.md
resolution: "lane/a72 (archivist): tools/d2s.py builds save_version 71, 87 and 92, opt-in, and reads them back (parse_legacy, the extended parser); d2s.md § Legacy versions (71..91), § Versions 92..95 (with the version-92 property encodings), the version row, § Legacy builder and Open questions updated, all [I]; test_d2s.py LegacyTest; recipes leg71merc, leg71uniq, leg87merc, leg87new, leg92props staged, not run [../formats/d2s.md#legacy-builder-versions-71-87-92]"
---

The layouts the archivist asked for (the legacy and version-92 readers entry, now closed) are read, statically, in
[save/0001 § Plan 0038 lane/rlg](../../findings/save/0001-d2s-io.md#plan-0038-lanerlg-the-legacy-and-version-92-readers-static-2026-10-27).
For [d2s.md § Legacy versions](../../formats/d2s.md#legacy-versions-7191), § Versions 92..95 and a `tools/d2s.py` builder of
versions 71, 87 and 92, which the H1a rows need (hirelings 3, 30, 33; player-creation 1; items-uniques-sets 21;
save-d2s 126; the H1a entry stays open for it). All `[I]`, no run:

1. **No legacy version is refused**: 71..91 with the layout below load (0..70 are sent to the same reader and fail its header's version test with code 1; *corrected at the `lane/rlg` review*) (§ (a), "Which versions load"). So ruling 3
   leaves the legacy rows as shortfalls; a builder is what they need.
2. **Section order and framing** (§ (a) table): header `0x82` bytes (its own length word `+0x20` = `0x82`); `Woo!` u32 6
   (`0x12A`); `WS` (`0x50`, only the tag and the markers tested); `01 77` (`0x34`); `gf` + a **3-byte** mask over
   stats 0..15 + u32 values (5 + 4n bytes); `if` + one byte per class skill; `JM` items; `JM` corpses (12 unread bytes
   each, then a list); the mercenary (version 71: `JM` u32 seed u16 name; 72+: one 0 byte, or `0x12` bytes then its
   item list, no `jf`); for ≥ 73 the hotkey tail (8 × 6 bytes, plus 8 for ≥ 82). No checksum, no `file_size`, no
   padding; failures after the skills do not fail the load (a builder's mistakes there pass silently: check by the
   write-back).
3. **Header fields** (§ (a) header table): offsets, widths and tests; the skill-byte encoding (`0x9C`..`0xD8` →
   +`0x41`, `0xFF` none) shared by the header hotkeys, the left/right skills and the tail; the legacy status codes
   (final, not mapped; Hell needs progression 8 in an expansion save, not 10); class at `+0x22` (u16), level at `+0x24`
   only for the character screen.
4. **Item lists**: the list version is the save's. 71: the 25-byte record table (four forms, the 10-bit classic index,
   the ear form) and the duplicate skip; 72..91: the current bitstream with the version tests of § (c)/(b).
5. **Version 92** (§ (b)): `1.09-Save Bits`/`Add` for every `ItemStatCost` width including defense, durability and
   sockets; **no param** in the generic property path (record `+0x28` = 0); the per-id encodings of the ≤ 92 table
   (83..87/179/180 → stat 83 by class, 107 group, 188, 195/198/201, 204, 126, the 92→93 … remaps) and the fold into
   stat 127; a set item's 12 bits are a `Sets` id matched by item code; no stat 356 on simple quest items; `nec `.
6. **The 92..96 version-test list** is complete for the 42 functions scanned (§ (c) table), so d2s.md can say a 93..95
   file differs from 96 in the stat form, stat 72 and the third realm word only.
7. **The old stat form** (§ (d)): ⌈`0x029`/8⌉ mask bytes; `d2s.py` may widen `stat_slots` beyond 9..16 (0 gives no
   mask). Bits at or above `0x029` in the last byte count in the bound test only.
8. **Ears** (§ (e)): the reader takes the realm bit after the name (test state of `d2s.py`'s extended form confirmed
   by the reading, still `[I]`); the writer writes realm data only when item data `+0x20` ≠ 0, and always 0 as the
   third word.

Not blocking anything else. A run on built saves (pieces in save/0001's Open questions) would raise these.

**Architect review note (`lane/rlg` review, 2026-10-27).** Ruled precise enough to build from: the section order,
tags and lengths, the header table, the 25-byte version-71 record forms, the mercenary's two forms, the hotkey tail,
the version-92 widths and per-id encodings and the 92..96 version-test list were checked against objdump of the pinned
`Game.exe`, and `tools/rlg_static.py` reproduces `static.txt` byte for byte. Three additions made at the review are in
the finding, and a builder needs them: the header's left and right skills (`+0x56`, `+0x57`) are applied after the
skills section, and only when non-zero; for 72..88 the two affix bases are lowered by per-version constants (§ (a), *The
base adjustment*: 74..79 take none); and versions 0..70 fail with code 1. **The archivist updates d2s.md** (§ Legacy
versions (71..91), § Versions 92..95, the version row, Open questions) and `tools/d2s.py` from the finding. This lane
and the review edited d2s.md only to repoint backlog links, and § Legacy versions still says the layout is not read.
Everything stays `[I]` until a built save is loaded (save/0001 Open questions lists the pieces).
