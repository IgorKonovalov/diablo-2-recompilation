---
from: reverser
to: spec-writer
date: 2026-10-16
status: open
context:
  - ../specs/items/cube.md#l-the-special-outputs-kinds-1-2-3
  - ../findings/items/0008-cube.md#plan-0038-batch-s2c-2026-10-16
  - ../specs/items/quest-drops.md#a-the-quest-record-and-the-quest-seed
  - ../findings/items/0010-quest-drops.md#plan-0038-batch-s2c-2026-10-16
  - ../specs/items/quest-drops.md#draw-order-on-the-quest-seed
resolution: ""
---

[2026-10-16] from reverser → spec-writer: plan 0038 S2c corrections for Phase 3 (after the S2c review). (a) [items/cube § L](../specs/items/cube.md#l-the-special-outputs-kinds-1-2-3) L2 and § M: the spot search `0x00545340` draws nothing; the portal object draws (171, 173 and 171 game-seed steps in the three logged openings) ([items/0008 § Plan 0038 batch S2c](../findings/items/0008-cube.md#plan-0038-batch-s2c-2026-10-16), cube 55). (b) [items/quest-drops § A](../specs/items/quest-drops.md#a-the-quest-record-and-the-quest-seed) A1: `g_QuestDescs` `+0x14` is the word `QuestsPlayerJoin` uses; the objects' own word (`Quest+0xE0`, set by their init functions) equals it except object 28 (16, not 32) and object 30 (29, not 41) ([items/0010 § S2c](../findings/items/0010-quest-drops.md#plan-0038-batch-s2c-2026-10-16), qd 8). (c) [items/quest-drops § Draw order](../specs/items/quest-drops.md#draw-order-on-the-quest-seed): add Baal's death (0x0058DF20, `RNG_RandLoHi` at 0x0058E05C) to the non-item quest-seed draws (qd 49). (d) [items/vendors § Entry points](../specs/items/vendors.md#entry-points) L73: `NPCSTORE_Reset` is reachable from quest code only through Baal's death → `0x0052E2A0` → a dropped client (game types 1 and 2) → `NPCSTORE_ActStale` ([items/0009 § S2c](../findings/items/0009-vendors.md#plan-0038-batch-s2c-2026-10-16), vend 4). (e) [items/sockets-runewords § C](../specs/items/sockets-runewords.md#c-what-a-gem-rune-or-jewel-brings) L306: 422 rows (265 weapons, 157 armours), not 384. (f) [items/cube § I](../specs/items/cube.md#i-the-crafted-builder--sub_005c21d0_itembuildcrafted) L681: stock data reaches a crafted pick of 0 on rows 72 and 90 (`sst`), 83 (`lbt`) and 84 (`lgl`) at output ilvl ≤ 5 (cube 49). Each raise and remainder is named per line in the S2c sections. **Review addition (architect):** (g) [items/sockets-runewords § A](../specs/items/sockets-runewords.md#a-the-client-test) L187: the logged case is `[C]`, but "the client unit lacks the socketed flag until the item is identified" stays `[I]` (sock 14 split at the review); (h) items/affixes: aff 27's low-builder false return for a non-weapon, non-armour base is `[C]` (items/0005 § S2c).
