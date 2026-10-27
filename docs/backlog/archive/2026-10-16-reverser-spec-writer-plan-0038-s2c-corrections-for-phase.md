---
from: reverser
to: spec-writer
date: 2026-10-16
status: done
context:
  - ../../specs/items/cube.md#l-the-special-outputs-kinds-1-2-3
  - ../../findings/items/0008-cube.md#plan-0038-batch-s2c-2026-10-16
  - ../../specs/items/quest-drops.md#a-the-quest-record-and-the-quest-seed
  - ../../findings/items/0010-quest-drops.md#plan-0038-batch-s2c-2026-10-16
  - ../../specs/items/quest-drops.md#draw-order-on-the-quest-seed
resolution: "done: (a)-(h) applied in Phase 3 (affixes lane/s38h2b, quest-drops lane/s38q, sockets-runewords lane/s38k, cube lane/s38c, vendors lane/s38v: (d) in [items/vendors § Entry points](../../specs/items/vendors.md#entry-points))"
---

[2026-10-16] from reverser → spec-writer: plan 0038 S2c corrections for Phase 3 (after the S2c review). (a) [items/cube § L](../../specs/items/cube.md#l-the-special-outputs-kinds-1-2-3) L2 and § M: the spot search `0x00545340` draws nothing; the portal object draws (171, 173 and 171 game-seed steps in the three logged openings) ([items/0008 § Plan 0038 batch S2c](../../findings/items/0008-cube.md#plan-0038-batch-s2c-2026-10-16), cube 55). (b) [items/quest-drops § A](../../specs/items/quest-drops.md#a-the-quest-record-and-the-quest-seed) A1: `g_QuestDescs` `+0x14` is the word `QuestsPlayerJoin` uses; the objects' own word (`Quest+0xE0`, set by their init functions) equals it except object 28 (16, not 32) and object 30 (29, not 41) ([items/0010 § S2c](../../findings/items/0010-quest-drops.md#plan-0038-batch-s2c-2026-10-16), qd 8). (c) [items/quest-drops § Draw order](../../specs/items/quest-drops.md#draw-order-on-the-quest-seed): add Baal's death (0x0058DF20, `RNG_RandLoHi` at 0x0058E05C) to the non-item quest-seed draws (qd 49). (d) [items/vendors § Entry points](../../specs/items/vendors.md#entry-points) L73: `NPCSTORE_Reset` is reachable from quest code only through Baal's death → `0x0052E2A0` → a dropped client (game types 1 and 2) → `NPCSTORE_ActStale` ([items/0009 § S2c](../../findings/items/0009-vendors.md#plan-0038-batch-s2c-2026-10-16), vend 4). (e) [items/sockets-runewords § C](../../specs/items/sockets-runewords.md#c-what-a-gem-rune-or-jewel-brings) L306: 422 rows (265 weapons, 157 armours), not 384. (f) [items/cube § I](../../specs/items/cube.md#i-the-crafted-builder--sub_005c21d0_itembuildcrafted) L681: stock data reaches a crafted pick of 0 on rows 72 and 90 (`sst`), 83 (`lbt`) and 84 (`lgl`) at output ilvl ≤ 5 (cube 49). Each raise and remainder is named per line in the S2c sections. **Review addition (architect):** (g) [items/sockets-runewords § A](../../specs/items/sockets-runewords.md#a-the-client-test) L187: the logged case is `[C]`, but "the client unit lacks the socketed flag until the item is identified" stays `[I]` (sock 14 split at the review); (h) items/affixes: aff 27's low-builder false return for a non-weapon, non-armour base is `[C]` (items/0005 § S2c).

*Annotation (spec-writer, 2026-10-20, `lane/s38h2b`, plan 0038 Phase 3, items/affixes cluster):* **done in part.** (h) applied to [items/affixes](../../specs/items/affixes.md) G2–G4 (the false return `[C]` with the weapon `M` and damage lines; G3's armour and throw branches kept `[I]`, see the review request), with aff 2, 11 and 14 (split: the level-window skip stays `[I]`, the H6a piece). **Open:** (a)–(g), for items/cube (H6a), items/quest-drops (H4a, H6e1, H6e2), items/vendors (H6c) and items/sockets-runewords (H6b).

*Annotation (spec-writer, 2026-10-27, `lane/s38q`, plan 0038 Phase 3, items/quest-drops cluster):* (b) applied to
[items/quest-drops § A](../../specs/items/quest-drops.md#a-the-quest-record-and-the-quest-seed): the `+0x14` word is the
join's (`QuestsPlayerJoin`), `[C]`, and objects 28 and 30 store 16 and 29 at `Quest+0xE0`, `[C]`; plan 0049's answer
for words 32 and 41 `[I]`. (c) applied to § Draw order as H6d corrected it: Baal's death draws the quest seed for its
gold piles, which are items (not a non-item draw). With them the S2c quest-drops raises (qd 7, 8, 9, 14, 19, 20, 21 in
part, 28, 31, 37, 38, 41, 47, 49). **Open:** (a), (d)–(g), for items/cube (H6a), items/vendors (H6c) and
items/sockets-runewords (H6b).

*Annotation (spec-writer, 2026-10-27, `lane/s38k`, plan 0038 Phase 3, items/sockets-runewords cluster):* (e) applied to
[items/sockets-runewords § C](../../specs/items/sockets-runewords.md#c-what-a-gem-rune-or-jewel-brings): 422 rows (265
weapons, 157 armours; 418 spawnable), `[C]`. (g) applied to [§ A](../../specs/items/sockets-runewords.md#a-the-client-test):
the two logged cases (with H6b's skull cap before and after identifying) `[C]`, the general reason `[I]`. With them the
S2c sockets raises (sock 2, 3, 4, 5, 6, 8, 19, 20, 25, 26, 27, 28, 32, 34, 36 L472, 41, 43, 44, 45, 46, 47, each at
its ledger's `[C]` half). **Open:** (a), (d), (f), for items/cube (H6a) and items/vendors (H6c).

*Annotation (spec-writer, 2026-10-27, `lane/s38c`, plan 0038 Phase 3, items/cube cluster):* (a) applied to
[items/cube § L](../../specs/items/cube.md#l-the-special-outputs-kinds-1-2-3) and § M: the spot search draws nothing and
the portal object draws (171, 173, 171 steps), `[C]`, in L2's line and note, the M row and sequence diagram and the
*Inputs and oracles* bullet; the open question narrowed to what the portal object's draws are spent on. (f) applied to
[§ I](../../specs/items/cube.md#i-the-crafted-builder--sub_005c21d0_itembuildcrafted): the survey (rows 72 and 90 `sst`,
83 `lbt`, 84 `lgl`) `[C]`, with H6a's case (b) fault `[C]` and case (a) `[I]` (no stock case). With them the S2c cube
raises (cube 6, 8, 10, 12, 13, 21, 22, 29, 47 in part, 49 in part, 52, 55, 56) and the d-none restatements (cube 20,
24). **Open:** (d), for items/vendors (H6c).

*Annotation (spec-writer, 2026-10-27, `lane/s38v`, plan 0038 Phase 3, items/vendors cluster):* (d) applied to
[items/vendors § Entry points](../../specs/items/vendors.md#entry-points): the call sites and the direct-call walk `[C]`
(quest code resets a store only through Baal's death → `0x0052E2A0` → a dropped client in game types 1 and 2 →
`NPCSTORE_ActStale`, never in single player), the 825 indirect call sites not followed `[I]`. With it the S2c vendors
raises (vend 3, 4 in part, 7, 8, 9, 11 in part, 19, 20, 21 in part, 22 in part, 24 in part, 25, 26, 27, 28 in part)
and the H6c pieces (22: the tab and placement `[C]`, the cell search `[I]`; 26 raised). Every part, (a)–(h), is now
applied; closed.
