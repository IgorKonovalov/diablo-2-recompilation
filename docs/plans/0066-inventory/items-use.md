# Plan 0066 inventory: items/use

- **Spec:** [items/use](../../specs/items/use.md), read at `main` `b5999f5e`.
- **Front matter `I`:** 64; the *Count* column sums to 64.
- Classes, batches and conventions as in [the inventory README](README.md#conventions).

| # | Line | Section | Claim (excerpt) | Anchor | Class | Route or reason | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | 36 | Entry points | Client packet , use an inventory item (13 bytes: … — → | `fn:sub_0054B1E0_Pkt20UseInvItem@0x0054B1E0` | ? | ? | ? | 1 |
| 2 | 37 | Entry points | Client packet , use a belt item (13 bytes: … — → | `fn:sub_0054B560_Pkt26UseBeltItem@0x0054B560` | ? | ? | ? | 1 |
| 3 | 38 | Entry points | Client packet , an item on an item (9 … — → | `fn:sub_0054B280_Pkt27ItemOnItem@0x0054B280` | ? | ? | ? | 1 |
| 4 | 39 | Entry points | Client packet , the mercenary button (3 bytes) — → | `fn:sub_0054D430_Pkt61MercItem@0x0054D430` | ? | ? | ? | 1 |
| 5 | 40 | Entry points | Skill do 113 reaches the first two as well … | `fn:sub_005BF3D0_SkillDo113UseBookScroll@0x005BF3D0` | ? | ? | ? | 1 |
| 6 | 75 | Constants | request position reach — 50 per axis, as u16 | `fn:sub_00548EF0_PktPosFar@0x00548EF0` | ? | ? | ? | 1 |
| 7 | 84 | How to read the tags | … to a named callee's entry. The callee and everything after it are not covered, "after, | – | ? | ? | ? | 1 |
| 8 | 94 | How to read the tags | : a code reading no case reaches, with the addresses read. | `fn:sub_0055E170_PlayerUseInvItem@0x0055E170` | ? | ? | ? | 1 |
| 9 | 115 | A. The drain and the gate | A1. Drain (queue 1, FIFO, all clients and games): | `fn:sub_006BEAD0_NetQueuePop@0x006BEAD0` | ? | ? | ? | 1 |
| 10 | 128 | A. The drain and the gate | if it returned non-zero: fatal | `0x0054D7E6` | ? | ? | ? | 1 |
| 11 | 129 | A. The drain and the gate | return row(op).fn(…) | `0x0054D818` | ? | ? | ? | 1 |
| 12 | 132 | A. The drain and the gate | Two item requests in one drain run in arrival order, to completion, and see each … | – | ? | ? | ? | 1 |
| 13 | 137 | A. The drain and the gate | A "refusal" return (2, 3) has no effect beyond the handler's own. So in this … | – | ? | ? | ? | 1 |
| 14 | 139 | A. The drain and the gate | What leaves the drain is a pickup out of reach: it starts a walk, and … | – | ? | ? | ? | 1 |
| 15 | 147 | A. The drain and the gate | : the import's result, the fatal branch, the handler's call. The import (slot , KERNEL32!IsBadCodePtr) … | `0x006CC34C` | ? | ? | ? | 1 |
| 16 | 150 | A. The drain and the gate | Not reached: Game+ above 1, where the gate first overwrites that word with 's return. | `0x00410A80` | ? | ? | ? | 1 |
| 17 | 152 | A. The drain and the gate | The gate draws nothing on this path: PlayerModeAllowed(1, 0, 0) returns before its RNG line … | – | ? | ? | ? | 1 |
| 18 | 161 | B. The use requests |  — Length 13, else 3. PktInvItemBad (the item exists, mode … | `fn:sub_00549150_PktInvItemBad@0x00549150` | ? | ? | ? | 1 |
| 19 | 162 | B. The use requests |  — Length 13. Fields: guid (+1), flag (+5). The position … | `fn:sub_005492F0_PktBeltItemBad@0x005492F0` | ? | ? | ? | 1 |
| 20 | 163 | B. The use requests |  — Length 9. +1 is the target, +5 the used … | `fn:sub_00549220_PktOwnedItemBad@0x00549220` | ? | ? | ? | 1 |
| 21 | 164 | B. The use requests |  — Length 3; expansion games only (game+), else 3. With … | `0x0054D430` | ? | ? | ? | 1 |
| 22 | 200 | C. The dispatch: ItemUse | C2. After either boundary: | `0x005BF320` | ? | ? | ? | 1 |
| 23 | 227 | D. Consumption, in the callers | (all of D1; , , ) | `fn:sub_0055E170_PlayerUseInvItem@0x0055E170` | ? | ? | ? | 1 |
| 24 | 243 | D. Consumption, in the callers | D2. Quest codes, with r = 0 (not through pSpell): | `0x0055E263` | ? | ? | ? | 1 |
| 25 | 250 | D. Consumption, in the callers | (all of D3; , , ) | `fn:sub_00562390_PlayerUseBeltItem@0x00562390` | ? | ? | ? | 1 |
| 26 | 261 | D. Consumption, in the callers | (all of D4; , ) | `fn:sub_00561ED0_PlayerUseItemOnItem@0x00561ED0` | ? | ? | ? | 1 |
| 27 | 276 | D. Consumption, in the callers | D5. MercGiveCursorItem (packet ): | `fn:sub_0054D230_MercGiveCursorItem@0x0054D230` | ? | ? | ? | 1 |
| 28 | 282 | D. Consumption, in the callers | What clears the marks. InvClearUseMarks has 36 direct calls, 35 of them in 24 other … | `fn:sub_0055BF50_InvClearUseMarks@0x0055BF50` | ? | ? | ? | 1 |
| 29 | 289 | E. The kinds | 2 — 0 in the entry's own body, direct calls; the … | `fn:ITEMUSE_TownPortal@0x005BE290` | ? | ? | ? | 1 |
| 30 | 293 | E. The kinds | 6 — 0 in the entry's own body, direct calls | `fn:sub_005BEF90_ItemUseCure@0x005BEF90` | ? | ? | ? | 1 |
| 31 | 296 | E. The kinds | 9 — 0 in the entry's own body, direct calls | `fn:sub_005BEDA0_ItemUseTimedState@0x005BEDA0` | ? | ? | ? | 1 |
| 32 | 297 | E. The kinds | 10, 11 — Cast skill 47 at level 1 | `0x005BF170` | ? | ? | ? | 1 |
| 33 | 351 | F. Kinds 3 and 4: the amount and the two draws | F1g. After the loop, when stat 6 got an amount, on a player: | `0x005BE6F0` | ? | ? | ? | 1 |
| 34 | 354 | F. Kinds 3 and 4: the amount and the two draws | … reached F1e's add or passed F1f's allocation, len + rem ≤ 0 included; else 0 | `0x005BE6D4` | ? | ? | ? | 1 |
| 35 | 357 | F. Kinds 3 and 4: the amount and the two draws | F2. A fresh list: | `0x005BE5E8` | ? | ? | ? | 1 |
| 36 | 379 | F. Kinds 3 and 4: the amount and the two draws | What the boundaries' callees do: every effect of STATLIST_Alloc, UnitQueueEvent, STATLIST_SetStat, UnitAddStat. | – | ? | ? | ? | 1 |
| 37 | 388 | F. Kinds 3 and 4: the amount and the two draws | The mp1 doubled branch is not observed in a game. It is the code's map, … | – | ? | ? | ? | 1 |
| 38 | 390 | F. Kinds 3 and 4: the amount and the two draws | The chance for n: Σ min(100, r >> 1) ÷ (100 n) over r < … | – | ? | ? | ? | 1 |
| 39 | 395 | F. Kinds 3 and 4: the amount and the two draws | A second potion within the first's duration: the reading is that it uses the same … | – | ? | ? | ? | 1 |
| 40 | 400 | F. Kinds 3 and 4: the amount and the two draws | Stock totals, in stored units (calc1 << 8, the class factor): hp1 30 gives 7 … | `fn:sub_005BE3F0_ItemUsePotion@0x005BE3F0` | ? | ? | ? | 1 |
| 41 | 402 | F. Kinds 3 and 4: the amount and the two draws | Healing and mana potions do not run the group clear: kind 3 has no call … | `0x005BE3F0` | ? | ? | ? | 1 |
| 42 | 416 | G. Kind 5: rejuvenation | G2. After the loop, when stat 6 got an amount, on a player, always: | `0x005BED5E` | ? | ? | ? | 1 |
| 43 | 418 | G. Kind 5: rejuvenation | G3. Returns 1 when any slot passed the tests, else 0: | `0x005BED42` | ? | ? | ? | 1 |
| 44 | 423 | G. Kind 5: rejuvenation | MulDiv is sub_00483360_MulDiv, of three branches, so above it may be (max ÷ 100) × … | `fn:sub_00483360_MulDiv@0x00483360` | ? | ? | ? | 1 |
| 45 | 424 | G. Kind 5: rejuvenation | A kind-5 use from the belt (rvs, ) did not move the player's seed, 1 … | run:2026-11-04-inventory-2 | ? | ? | ? | 1 |
| 46 | 434 | H. The other kinds | After that boundary: | `0x005BE165` | ? | ? | ? | 1 |
| 47 | 442 | H. The other kinds | ItemIdentify: | `fn:sub_00562590_ItemIdentify@0x00562590` | ? | ? | ? | 1 |
| 48 | 452 | H. The other kinds | After: | `0x0055FA40` | ? | ? | ? | 1 |
| 49 | 456 | H. The other kinds | H3. Kinds 6 and 9: | `fn:sub_005BEF90_ItemUseCure@0x005BEF90` | ? | ? | ? | 1 |
| 50 | 477 | H. The other kinds | the player keeps v − returned | `fn:sub_005C5F10_GolemHeal@0x005C5F10` | ? | ? | ? | 1 |
| 51 | 486 | H. The other kinds | A first identify through D1 has r = 0, so it falls to D2's codes … | `0x0055E263` | ? | ? | ? | 1 |
| 52 | 487 | H. The other kinds | v = 0 sets the golem to full. Kind 3 tests v > 0 first; … | `fn:sub_005C5F10_GolemHeal@0x005C5F10` | ? | ? | ? | 1 |
| 53 | 488 | H. The other kinds | key has useable 0 and no pSpell. Its callers: OBJOP_Chest and the case at . | `0x00581DC1` | ? | ? | ? | 1 |
| 54 | 492 | I. What the columns gate | useable (+) is a required test of both use requests, and , and it does … | `fn:sub_00628C20_ItemIsUseable@0x00628C20` | ? | ? | ? | 1 |
| 55 | 493 | I. What the columns gate | above: no family of enters either handler. (static.txt of , , , the a69 route) | run:2026-11-03-use-emu | ? | ? | ? | 1 |
| 56 | 494 | I. What the columns gate | belt (+), durwarning and qntwarning gate no use among direct calls; indirect callers and table … | `fn:sub_00621ED0_ItemBeltByte@0x00621ED0` | ? | ? | ? | 1 |
| 57 | 495 | I. What the columns gate | sub_0063C830_BeltBoxQuery tests useable and belt both 1 with size 1 × 1, called only from … | `0x004979AD` | ? | ? | ? | 1 |
| 58 | 503 | J. Draws per seed | Kinds 2, 6, 9 — 0 in the entry's own body | `fn:sub_005BEDA0_ItemUseTimedState@0x005BEDA0` | ? | ? | ? | 1 |
| 59 | 504 | J. Draws per seed | The gate — 0 on this path | `0x0057EEFB` | ? | ? | ? | 1 |
| 60 | 506 | J. Draws per seed | No bound past the boundaries. The counts hold only up to each entry's first callee, … | `0x0055E000` | ? | ? | ? | 1 |
| 61 | 531 | Reimplementation notes | … on an unidentified item in the user's inventory, does. does not clear the marks first. | `0x00561F60` | ? | ? | ? | 1 |
| 62 | 532 | Reimplementation notes | … and a used belt scroll on a target not in a grid is removed unused. | `0x00561F60` | ? | ? | ? | 1 |
| 63 | 533 | Reimplementation notes | consumes the cursor item whatever ItemUse returned. | `0x0054D3FD` | ? | ? | ? | 1 |
| 64 | 534 | Reimplementation notes | Don't refuse on a handler's "3" at the drain: the return is discarded. | `0x0053F459` | ? | ? | ? | 1 |
