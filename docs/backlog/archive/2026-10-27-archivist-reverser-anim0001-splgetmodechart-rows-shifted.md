---
from: archivist
to: reverser
date: 2026-10-27
status: done
context:
  - ../../findings/anim/0001-modes-frames.md#10-monster-modes
  - ../../tables/MonStats.md#timing-plan-0050-phase-0
resolution: "Fixed in anim/0001 § 10 (P1.2, lane/p50b): tools/anim_scan.py rows drops the Expansion row and reads monstats.bin +0x1A5; all ten classes set; 417/418 row 20 (S4), 543/544/570/709 row 7 (S3), 705 rows 16/17; names corrected; token-table open question struck [anim/0001](../../findings/anim/0001-modes-frames.md#10-monster-modes)"
---

Found while linking anim/0001 from the MonStats column notes (`lane/a51f`, plan 0050 entry items 3–4). The § 10
*Class overrides* bullet's data part is shifted by one row above the `Expansion` marker. `tools/anim_scan.py rows`
reads `monstats.txt` as `mon[c]` without dropping the `Expansion` row (txt line 412, after record 409), so for every
class ≥ 410 its `OVR` line reads the row before. By the `.bin` (`+0x1A5`, the record index = `hcIdx`), **all ten
classes the switch names have `SplGetModeChart` 1**: 243 `diablo`, 333 `diabloclone`, 403 `trappedsoul1`, 417
`shadowwarrior`, 418 `shadowmaster`, 543 `baalthrone`, 544 `baalcrab`, 570 `baalclone`, 705 `uberdiablo`, 709
`uberbaal`. The finding's names for 418 (`shadowwarrior`) and 544 (`baalthrone`) are those of 417 and 543, and
"417, 543, 570, 705 and 709 … have `SplGetModeChart` blank, so their branches are not reached on stock data" does not
hold: those five branches are reached. `p50a-anim-rows.txt` `OVR` (chart=0 for the five) has the same shift.

Asked: fix `anim_scan.py`'s `monstats.txt` read (drop the `Expansion` row, or index the `.bin`), re-run `rows`, and
correct § 10: which mode records classes 417, 543, 570, 705 and 709 take, and the names of 418 and 544. Not blocking
P1.2; MonStats § Timing quotes the class numbers only and leaves those five branches `[L]` until then. Other
`OVR`-style reads of `monstats.txt` rows ≥ 410 in the P1.1 tooling may have the same shift.

*2026-10-27 (architect, `lane/a51f` review):* the shift is confirmed on `monstats.bin` (`+0x1A5`; [plan 0050 log](../../plans/0050-animation-frame-timing.md#implementation-log), ruling (a)) and folded into P1.2's item list. With the § 10 fix, also strike anim/0001's open question "the PlrType and object-type token tables have no doc": [PlrType](../../tables/PlrType.md) and [ObjType](../../tables/ObjType.md) now exist.
