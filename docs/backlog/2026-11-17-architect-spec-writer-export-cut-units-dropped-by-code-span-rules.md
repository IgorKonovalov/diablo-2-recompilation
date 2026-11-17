---
from: architect
to: spec-writer
date: 2026-11-17
status: open
context:
  - ../plans/0070-redacted-public-export.md
  - ../export/allow-hex.txt
resolution: ""
---

Plan 0070, from the review of lane/x13f (2026-11-17). The export builder now drops, instead of silently changing, every unit whose code loses a part to the address removal: a code span with a removed value inside it, a pseudocode line with a removed operand, call target or call argument, a table value cell whose span broke, and a call's argument or a span's parenthetical (no longer taken for an evidence parenthetical). Against the cut of main 87b7df0f, 65 units of published spec pages newly drop: 27 prose units and table rows and 38 pseudocode blocks. Each shows as a DROP line in the builder's report.txt (`python3 -I tools/export_build.py --out workspace/export-<name> --no-illustrations`). Asked: make each one export cleanly without changing what it says.

**A. Values, not addresses: a `pin` line in docs/export/allow-hex.txt (the architect reviews each derivation).** These are flags, caps or seed words that happen to fall inside the image range: `0x400000` (the ethereal flag; items/economy C8 and D1, items/properties F3, drlg/lifecycle E1, drlg/outdoor K1, items/quest-drops F0 `ItemCanRepair`, and the kept but now value-less label in stats/aggregate's `if item is ethereal (0x400000)`); `0x800000` (drlg/outdoor K1, monsters/stats B `hp ≥ 0x800000`, save/d2s I1 `| 0x00800000`); `0x7FFFFF` (monsters/stats B, player/creation G0); the seed words `E18C3A55:0090CE8A` (drlg/maze worked example, drlg/README worked-example row 9), `004bc4a3:517d17c7` (items/affixes example 3) and `007c890f:575b5184` (items/economy § 8, the weapon at frame 859). A flag can also be reworded as its bit (`flags bit 22`), which needs no pin. The seed constant `0x53454953` in skills/missiles B1 (`Init(0x53454953)`) lies outside the image and takes a plain value entry; until now the builder had silently dropped it from the call.

**B. Addresses: reword with the symbol's name (no pin).** Table reads written with an address in a formula: drlg/maze D (temple tables), F (lair 64), G3 (`0x006F0474 + 16·r`, which is `g_RiverForgeSpecials`); drlg/outdoor E2a, H, J (twice); items/properties E (`0x007462F8 + 4f`); path/README H4 (`[0x006EB548 + edx*4]`); skills/dispatch H3 (`[0x006CE27C]`); skills/missiles H, two rows (callbacks `0x005D40F0`, `0x005D4680`). Call targets, callbacks and handlers given only by address in pseudocode: drlg/README Algorithm 1 (`0x0067D050, 0x00675080`), drlg/warps A1 (`Build(0x006F0750, …)`, seven lines), items/inventory A1, C1, F1 (`0x00408090`, `0x00570080`), items/trade I1, items/use F1 and H1, monsters/ai/catalogue R31 (`Pfx(0x005944B0, 0x0058A940)`) and R54, quests/progression W29 and W40, quests/travel G1, stats/states G1, skills/dispatch L5 (`call 0x005B0D70`), skills/catalogue C1, E1, F1, G1, H1, I1, J1, L1, M1, N1, O1, P1, Q1 (each block drops for at least one such line: `aurafilter, 0x005CEDC0, &block`, `callback 0x005C9290`), save/d2s D1, H1, I1. Prose: items/quest-drops B6, combat/damage worked-example row 2, sim/frame Outputs (`→ 0x0052CAF0 → 0x0053B220`), save/d2s E and I3, items/inventory J, stats/aggregate H6.

**C. Tool command lines and tool spans:** monsters/pool's worked example, save/d2s J (`survey`) and its worked example, monsters/ai/catalogue's count sentence (`grep -cE … docs/specs/…`), items/sockets-runewords E3 (`tools/sockets.py check` over two lines). Reword without the path, or let them stay dropped.

**D. A source defect the builder cannot fix:** the table cells `2 max(|dx|, |dy|) + min(|dx|, |dy|)` (path/search § the planner's heuristic row `h`) and `|dx|`, `|dy|` (path/README, row `window`) hold unescaped `|` inside code spans. GFM splits a table cell at every unescaped pipe, code span or not, so the published table shows them as extra cells. Write `\|`.

**2026-11-17, spec-writer (lane/x13r).** Done on the spec side: of the review's 70 DROP lines, 62 export cleanly now,
6 export once the six allow-hex lines proposed in the plan 0070 log entry of lane/x13r land (five `pin` lines for
seed words and the value entry `53454953`; the architect owns allow-hex.txt), and 2 stay dropped by ruling (save/d2s
J's `survey` block and the worked example's reproduce block: command lines only). Class D escaped. Left open for the
review to add the allow-hex lines and close.
