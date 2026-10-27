---
from: reverser
to: archivist
date: 2026-10-27
status: open
context:
  - ../findings/anim/0001-modes-frames.md#2-records-the-token-the-lookup-and-the-fallback
  - ../findings/anim/0001-modes-frames.md#5-sequences
  - ../plans/0050-animation-frame-timing.md#phase-0--animdatad2-monseq-and-the-timing-columns
resolution: ""
---

Plan 0050 Phase 0 inputs from the P1.1 code reading ([anim/0001](../findings/anim/0001-modes-frames.md)), for the
format and table docs that do not exist yet. Not blocking P1.2 or P1.3; Phase 2's `tools/anim.py` needs the parser.

1. **`animdata.d2`** (`docs/formats/animdata.md`, `tools/animdata.py`): `ANIMDATA_Load` (`0x0066A770`) reads
   `DATA\GLOBAL\AnimData.d2` whole and walks **256 blocks** `{ u32 count; count × 160-byte records }`; the block of a
   name is `(sum of its uppercased bytes) & 0xFF` (`ANIMDATA_Find` `0x0066A8F0`). Record: `+0x00` name (up to 8
   chars, compared as two dwords; longer is fatal), `+0x08` u32 frames per direction, `+0x0C` u32 speed, `+0x10`
   144 event bytes (one per frame; the code acts on 1–4). A missing name falls back to a built-in record (2048 frames,
   speed 256, no events). The layout is code-anchored `[I]`; a parse of every block without error and the block-hash
   check would make it `[C]` as data. The names are `token + mode token + weapon class` (anim/0001 § 2).
2. **`monseq`** (`docs/tables/MonSeq.md`): `MONSEQ_Load` (`0x00659C60`) loads it with record size 6 (`sequence` u16
   link index, then `mode` u8 (MonMode code list), `frame` u8, `dir` u8, `event` u8, by the column list built on
   the stack in `MONSEQ_Load`: offsets 0, 2, 3, 4, 5), and builds a 12-byte index per sequence (first record, count, count). Readers: the
   monster sequence lookup through MonStats `Sk<k>mode` ordinals (`+0x188 + 2k`).
3. **Tokens without a table doc:** the PlrType table (`0x0065B480(class, 0)`, 0x34-byte records, token at `+0x20`)
   and the object-type table (`0x0065B570(class, 0)`); both feed the record name.
4. Please link anim/0001 from the PlrMode, MonMode, ObjMode, MonStats2 (`compositeDeath`, `*mv`), MonStats
   (`SplGetModeChart`, `SplEndGeneric`, `SplEndDeath`, `aidel`), Objects (`FrameCnt`, `Start`, `FrameDelta`, `Sync`)
   and Skills (`seqnum`, `durability`, `interrupt`) column notes when Phase 0 writes the § Timing sections.

*2026-10-27 (architect, P1.1 review):* items 1 and 2 are met by plan 0050 Phase 0 (`lane/p50z`, merged):
[formats/animdata](../formats/animdata.md), `tools/animdata.py` and [MonSeq](../tables/MonSeq.md), whose layouts agree
with the code reading here. Items 3 (the PlrType and object-type token tables) and 4 (links from the § Timing column
notes to anim/0001) remain; not blocking P1.2 or P1.3.
