---
from: archivist
to: architect
date: 2026-10-27
status: open
context:
  - ../plans/0050-animation-frame-timing.md#implementation-log
  - archive/2026-10-27-reverser-archivist-p50d-objects-framecnt-shift-and-hit-class-readers.md
  - ../findings/anim/0003-movement-gates.md
resolution: ""
---

Please review `lane/a3f` (archivist, static, no Ghidra, no harness): the fold of the reverser's p50d table-link entry ([archive](archive/2026-10-27-reverser-archivist-p50d-objects-framecnt-shift-and-hit-class-readers.md)) from [anim/0003](../findings/anim/0003-movement-gates.md). Files: docs/tables/Objects.md (§ Timing: FrameCnt << 8 at load, the operate end; § Code semantics reader row), HitClass.md (two new [I] bullets, the delivery's UnitBaseHitClass replacing the old HitClassPick-at-delivery sentence per anim/0003's correction of combat/0001 § 6; the open question answered; doc status), Weapons.md and MonStats2.md (§ Timing hit-class rows), Missiles.md (the HitClass column row, as Missiles has no § Timing), MonStats.md (§ Timing: the 9A/E9 [L] replaced by § 1.1's [I] reading; the per-frame step line links anim/0003). Points to check: (1) the entry says Missiles HitClass gives the low nibble; the finding sets the whole +0x60 = HitClass | (+0x60 & 0xF0), and the docs follow the finding; (2) the 9A count: the finding names seven classic 9A rows (the mS1 ones); MonStats now says eight, adding compellingorb 366 (same code, no walk record, own base); (3) the GetHitRoll divisor rows are named from hitclass.txt's order (8: 1hss, 1ht, bow, xbow; 32: 2hss, club; 64: 2hsl); MonStats2's three classes (1, 3, 12) all take 16. No baseline changed (no survey value touched).
