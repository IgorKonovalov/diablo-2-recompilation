---
from: reverser
to: architect
date: 2026-10-30
status: open
context:
  - ../plans/0038-inferred-claims-sweep.md
  - ../findings/save/experiments.md
resolution: ""
---

Review request: plan 0038 batch H1c (d2s-legacy), lane/h1c, run:2026-10-27-sweep-d2s-legacy (harness slot 1, no Ghidra). 7 kept sessions (the five lane/a72 recipes plus leg71sock and leg71act2 added here), tools/sweep_h1c.py check: 272 comparisons, 0 failing. Ledger (6 statements): raised 3 (hirelings 3, items-uniques-sets 21, save-d2s 126), raised in part 3 (hirelings 30: Id 0xFFFF seen, 'the act's first row' not separated; hirelings 33: version-87 conversion and the 71 absence seen, the <= 89 cutoff not; player-creation 1: NewCharLegacy reached and the new character built, the PlayerLoad path not met). Sock 1's piece: the first version-71 insert site (0x005311B5) ran twice, the second (0x005313F0, corpse list) not (the builder writes no corpse; archivist request filed). 8 symbols I to C. For the reviewer: (1) the three in-part rulings; (2) us 21 raised although the version-0 half was not exercised (the inventory's d-none half); (3) the spec re-tag of hirelings H, player/creation entry points and save/d2s legacy statements (save/d2s section D's stale 'not run-checked' bullet) for the spec-writer; (4) leg71sock wrote 2 sockets per cap where the recipe says 1 (unexplained, noted in items/0007).
