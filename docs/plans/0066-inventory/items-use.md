# Plan 0066 inventory: items/use

- **Spec:** [items/use](../../specs/items/use.md), read at `main` `b5999f5e`.
- **Front matter `I`:** 64; the *Count* column sums to 64.
- Classes, batches and conventions as in [the inventory README](README.md#conventions).

| # | Line | Section | Claim (excerpt) | Anchor | Class | Route or reason | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | 36 | Entry points | Client packet , use an inventory item (13 bytes: … — → | `fn:sub_0054B1E0_Pkt20UseInvItem@0x0054B1E0` | a-logs | the `pot` log of run:2026-11-04-inventory-2: each PKT 0x20 line followed by its UP0 at `ItemUsePotion` | S4b | 1 |
| 2 | 37 | Entry points | Client packet , use a belt item (13 bytes: … — → | `fn:sub_0054B560_Pkt26UseBeltItem@0x0054B560` | a-logs | as row 1 for the PKT 0x26 belt uses | S4b | 1 |
| 3 | 38 | Entry points | Client packet , an item on an item (9 … — → | `fn:sub_0054B280_Pkt27ItemOnItem@0x0054B280` | b | `inventory.gdb`'s PKT range extended to 0x27; a pilot identify (scroll on an item) | H4c | 1 |
| 4 | 39 | Entry points | Client packet , the mercenary button (3 bytes) — → | `fn:sub_0054D430_Pkt61MercItem@0x0054D430` | b | a pilot mercenary-potion action (cursor potion on the mercenary button) with PKT/PKR 0x61 lines | H4c | 1 |
| 5 | 40 | Entry points | Skill do 113 reaches the first two as well … | `fn:sub_005BF3D0_SkillDo113UseBookScroll@0x005BF3D0` | c | exhaustive xref scan with a second tool (r2 `axt`) from skill do 113 to the two use functions | S4b | 1 |
| 6 | 75 | Constants | request position reach — 50 per axis, as u16 | `fn:sub_00548EF0_PktPosFar@0x00548EF0` | c-emu | `PktPosFar` emulated (new family in `tools/use_emu.py`): the 50 bound and the `u16` compare | S4e | 1 |
| 7 | 84 | How to read the tags | … to a named callee's entry. The callee and everything after it are not covered, "after, | – | d-none | a convention note (what "after" means), no behavioural claim | – | 1 |
| 8 | 94 | How to read the tags | : a code reading no case reaches, with the addresses read. | `fn:sub_0055E170_PlayerUseInvItem@0x0055E170` | d-none | the tag legend, no behavioural claim | – | 1 |
| 9 | 115 | A. The drain and the gate | A1. Drain (queue 1, FIFO, all clients and games): | `fn:sub_006BEAD0_NetQueuePop@0x006BEAD0` | c | the drain loop read with a second tool (r2): no test of `eax` after `SrvPacketDispatch` | S4b | 1 |
| 10 | 128 | A. The drain and the gate | if it returned non-zero: fatal | `0x0054D7E6` | d-none | the fatal branch after the import: a guard stock play never fails | – | 1 |
| 11 | 129 | A. The drain and the gate | return row(op).fn(…) | `0x0054D818` | a-logs | the PKT lines of the kept inventory logs: the table row's handler runs after the dispatch (opcode to entry) | S4b | 1 |
| 12 | 132 | A. The drain and the gate | Two item requests in one drain run in arrival order, to completion, and see each … | – | b | a pilot step putting two item requests in one drain (0x17 then 0x16 on one item) with PKT/PKR lines | H4c | 1 |
| 13 | 137 | A. The drain and the gate | A "refusal" return (2, 3) has no effect beyond the handler's own. So in this … | – | c | as row 9: the return is discarded at 0x0053F459 | S4b | 1 |
| 14 | 139 | A. The drain and the gate | What leaves the drain is a pickup out of reach: it starts a walk, and … | – | b | a pickup out of reach with PKT 0x16/0x17 and a new line at the later mode-pass pickup | H4c | 1 |
| 15 | 147 | A. The drain and the gate | : the import's result, the fatal branch, the handler's call. The import (slot , KERNEL32!IsBadCodePtr) … | `0x006CC34C` | d-none | the import's result is not evidenced (ADR-0029); the fatal branch is a guard stock play never fails | – | 1 |
| 16 | 150 | A. The drain and the gate | Not reached: Game+ above 1, where the gate first overwrites that word with 's return. | `0x00410A80` | d-none | a scope note: the writer of `Game+0x1DC4` is unread; no known session raises it | – | 1 |
| 17 | 152 | A. The drain and the gate | The gate draws nothing on this path: PlayerModeAllowed(1, 0, 0) returns before its RNG line … | – | a-logs | the PKT/PKR seed pairs of run:2026-11-04-inventory-2 (0x17 40, 0x19 40 unchanged) | S4b | 1 |
| 18 | 161 | B. The use requests |  — Length 13, else 3. PktInvItemBad (the item exists, mode … | `fn:sub_00549150_PktInvItemBad@0x00549150` | c-emu | `Pkt20UseInvItem` with `PktInvItemBad` and `PktPosFar` emulated up to the use function (new family) | S4e | 1 |
| 19 | 162 | B. The use requests |  — Length 13. Fields: guid (+1), flag (+5). The position … | `fn:sub_005492F0_PktBeltItemBad@0x005492F0` | c-emu | `Pkt26UseBeltItem` and `PktBeltItemBad` emulated up to the use function | S4e | 1 |
| 20 | 163 | B. The use requests |  — Length 9. +1 is the target, +5 the used … | `fn:sub_00549220_PktOwnedItemBad@0x00549220` | c-emu | `Pkt27ItemOnItem` and `PktOwnedItemBad` emulated up to the use function | S4e | 1 |
| 21 | 164 | B. The use requests |  — Length 3; expansion games only (game+), else 3. With … | `0x0054D430` | c-emu | `Pkt61MercItem` emulated up to `MercGiveCursorItem` (expansion word, cursor item, pet state declared) | S4e | 1 |
| 22 | 200 | C. The dispatch: ItemUse | C2. After either boundary: | `0x005BF320` | c-emu | `ItemUse` emulated with the test and use functions as observed boundaries returning chosen values (ADR-0021) | S4e | 1 |
| 23 | 227 | D. Consumption, in the callers | (all of D1; , , ) | `fn:sub_0055E170_PlayerUseInvItem@0x0055E170` | b | a tome and scroll session (TP, identify, a book at stat 70 below 1) with a new line for stat 70 and `ItemUse`'s return | H4c | 1 |
| 24 | 243 | D. Consumption, in the callers | D2. Quest codes, with r = 0 (not through pSpell): | `0x0055E263` | b | tool-built saves holding `ass`, `xyz`, `tr2`, `toa`; their uses with a new stat line at 0x0055E263 | H4c | 1 |
| 25 | 250 | D. Consumption, in the callers | (all of D3; , , ) | `fn:sub_00562390_PlayerUseBeltItem@0x00562390` | b | belt uses with and without the mercenary flag (a new pilot action), PKR inventory lists for the column shift | H4c | 1 |
| 26 | 261 | D. Consumption, in the callers | (all of D4; , ) | `fn:sub_00561ED0_PlayerUseItemOnItem@0x00561ED0` | b | as row 3: 0x27 uses (identify, a belt scroll on an item, a target not in a grid) | H4c | 1 |
| 27 | 276 | D. Consumption, in the callers | D5. MercGiveCursorItem (packet ): | `fn:sub_0054D230_MercGiveCursorItem@0x0054D230` | b | as row 4 | H4c | 1 |
| 28 | 282 | D. Consumption, in the callers | What clears the marks. InvClearUseMarks has 36 direct calls, 35 of them in 24 other … | `fn:sub_0055BF50_InvClearUseMarks@0x0055BF50` | c | exhaustive xref scan with a second tool on `InvClearUseMarks` (36 calls) | S4b | 1 |
| 29 | 289 | E. The kinds | 2 — 0 in the entry's own body, direct calls; the … | `fn:ITEMUSE_TownPortal@0x005BE290` | c | `rngcallgraph` rerun with an r2 LCG scan on `ITEMUSE_TownPortal`'s own body | S4b | 1 |
| 30 | 293 | E. The kinds | 6 — 0 in the entry's own body, direct calls | `fn:sub_005BEF90_ItemUseCure@0x005BEF90` | c | as row 29 on `ItemUseCure` | S4b | 1 |
| 31 | 296 | E. The kinds | 9 — 0 in the entry's own body, direct calls | `fn:sub_005BEDA0_ItemUseTimedState@0x005BEDA0` | c | as row 29 on `ItemUseTimedState` | S4b | 1 |
| 32 | 297 | E. The kinds | 10, 11 — Cast skill 47 at level 1 | `0x005BF170` | d-edit | no stock Misc row has kind 10 or 11 | – | 1 |
| 33 | 351 | F. Kinds 3 and 4: the amount and the two draws | F1g. After the loop, when stat 6 got an amount, on a player: | `0x005BE6F0` | d-edit | no stock kind-3 potion names stat 6 (the rejuvenations are kind 5, row 42) | – | 1 |
| 34 | 354 | F. Kinds 3 and 4: the amount and the two draws | … reached F1e's add or passed F1f's allocation, len + rem ≤ 0 included; else 0 | `0x005BE6D4` | c-emu | the kind-3 family extended to the return with scratch amounts at and below 0 (callees observed) | S4e | 1 |
| 35 | 357 | F. Kinds 3 and 4: the amount and the two draws | F2. A fresh list: | `0x005BE5E8` | a-logs | the UAL, UQE and USS lines of the `pot` log of run:2026-11-04-inventory-2 for the fresh lists | S4b | 1 |
| 36 | 379 | F. Kinds 3 and 4: the amount and the two draws | What the boundaries' callees do: every effect of STATLIST_Alloc, UnitQueueEvent, STATLIST_SetStat, UnitAddStat. | – | d-none | a scope note: the callees' effects are not read | – | 1 |
| 37 | 388 | F. Kinds 3 and 4: the amount and the two draws | The mp1 doubled branch is not observed in a game. It is the code's map, … | – | a-run | `inventory_sessions.py pot` with more `mp1` uses (InvSor2, energy 150; the chance is about 37 per cent) | H4c | 1 |
| 38 | 390 | F. Kinds 3 and 4: the amount and the two draws | The chance for n: Σ min(100, r >> 1) ÷ (100 n) over r < … | – | c-emu | the doubling draw emulated over r for each n against `double_chance`, and a non-player user | S4e | 1 |
| 39 | 395 | F. Kinds 3 and 4: the amount and the two draws | A second potion within the first's duration: the reading is that it uses the same … | – | b | a new line at the second use: the lists `STATLIST_Find` returns (the open question's log) | H4c | 1 |
| 40 | 400 | F. Kinds 3 and 4: the amount and the two draws | Stock totals, in stored units (calc1 << 8, the class factor): hp1 30 gives 7 … | `fn:sub_005BE3F0_ItemUsePotion@0x005BE3F0` | a-run | `inventory_sessions.py pot` with an Amazon and a Barbarian save (another class) | H4c | 1 |
| 41 | 402 | F. Kinds 3 and 4: the amount and the two draws | Healing and mana potions do not run the group clear: kind 3 has no call … | `0x005BE3F0` | c | call-graph scan with a second tool: kind 3 never calls `STATE_GroupClear` | S4b | 1 |
| 42 | 416 | G. Kind 5: rejuvenation | G2. After the loop, when stat 6 got an amount, on a player, always: | `0x005BED5E` | b | a new entry line at `ItemUseRejuv` (kind 5 has none), rejuvenation uses with stat 352 | H4c | 1 |
| 43 | 418 | G. Kind 5: rejuvenation | G3. Returns 1 when any slot passed the tests, else 0: | `0x005BED42` | b | as row 42, a rejuvenation at full life | H4c | 1 |
| 44 | 423 | G. Kind 5: rejuvenation | MulDiv is sub_00483360_MulDiv, of three branches, so above it may be (max ÷ 100) × … | `fn:sub_00483360_MulDiv@0x00483360` | d-edit | the other `MulDiv` branch and the timed path need values or a `len` no stock row has | – | 1 |
| 45 | 424 | G. Kind 5: rejuvenation | A kind-5 use from the belt (rvs, ) did not move the player's seed, 1 … | run:2026-11-04-inventory-2 | b | as row 42 (the entry line gives the seed) | H4c | 1 |
| 46 | 434 | H. The other kinds | After that boundary: | `0x005BE165` | b | as row 3: a first and second identify request | H4c | 1 |
| 47 | 442 | H. The other kinds | ItemIdentify: | `fn:sub_00562590_ItemIdentify@0x00562590` | b | as row 3 with a new line at `ItemIdentify` (item flags before and after) | H4c | 1 |
| 48 | 452 | H. The other kinds | After: | `0x0055FA40` | a-run | `inventory.gdb` PKT/PKR 0x20 on a right-click of the cube in the inventory (the pot session's use action) | H4c | 1 |
| 49 | 456 | H. The other kinds | H3. Kinds 6 and 9: | `fn:sub_005BEF90_ItemUseCure@0x005BEF90` | b | antidote and thawing uses with a new entry line at `ItemUseCure` and `ItemUseTimedState` | H4c | 1 |
| 50 | 477 | H. The other kinds | the player keeps v − returned | `fn:sub_005C5F10_GolemHeal@0x005C5F10` | b | a Necromancer with a golem drinking potions; a new line at `GolemHeal` | H4c | 1 |
| 51 | 486 | H. The other kinds | A first identify through D1 has r = 0, so it falls to D2's codes … | `0x0055E263` | b | as row 46 | H4c | 1 |
| 52 | 487 | H. The other kinds | v = 0 sets the golem to full. Kind 3 tests v > 0 first; … | `fn:sub_005C5F10_GolemHeal@0x005C5F10` | c-emu | `GolemHeal` emulated with v = 0 and v > 0 (the kind-5 maximum-0 case is edited data only) | S4e | 1 |
| 53 | 488 | H. The other kinds | key has useable 0 and no pSpell. Its callers: OBJOP_Chest and the case at . | `0x00581DC1` | c | full-table check of Misc (`key`: `useable` 0, no `pSpell`) and an xref scan with a second tool | S4b | 1 |
| 54 | 492 | I. What the columns gate | useable (+) is a required test of both use requests, and , and it does … | `fn:sub_00628C20_ItemIsUseable@0x00628C20` | c-emu | rows 18 and 19's handler families run through the `useable` gate | S4e | 1 |
| 55 | 493 | I. What the columns gate | above: no family of enters either handler. (static.txt of , , , the a69 route) | run:2026-11-03-use-emu | d-none | a mention of row 54's tag inside a data line tagged confirmed; no claim of its own | – | 1 |
| 56 | 494 | I. What the columns gate | belt (+), durwarning and qntwarning gate no use among direct calls; indirect callers and table … | `fn:sub_00621ED0_ItemBeltByte@0x00621ED0` | c | exhaustive xref scan with a second tool on the three getters, indirect callers and table pointers included | S4b | 1 |
| 57 | 495 | I. What the columns gate | sub_0063C830_BeltBoxQuery tests useable and belt both 1 with size 1 × 1, called only from … | `0x004979AD` | c | xref scan with a second tool: `BeltBoxQuery`'s only caller is client code | S4b | 1 |
| 58 | 503 | J. Draws per seed | Kinds 2, 6, 9 — 0 in the entry's own body | `fn:sub_005BEDA0_ItemUseTimedState@0x005BEDA0` | c | as row 29 for kinds 2, 6, 9 | S4b | 1 |
| 59 | 504 | J. Draws per seed | The gate — 0 on this path | `0x0057EEFB` | a-logs | as row 17 | S4b | 1 |
| 60 | 506 | J. Draws per seed | No bound past the boundaries. The counts hold only up to each entry's first callee, … | `0x0055E000` | d-none | a scope note: no bound past the boundaries | – | 1 |
| 61 | 531 | Reimplementation notes | … on an unidentified item in the user's inventory, does. does not clear the marks first. | `0x00561F60` | b | as row 46 | H4c | 1 |
| 62 | 532 | Reimplementation notes | … and a used belt scroll on a target not in a grid is removed unused. | `0x00561F60` | b | as row 26 | H4c | 1 |
| 63 | 533 | Reimplementation notes | consumes the cursor item whatever ItemUse returned. | `0x0054D3FD` | b | as row 4, with a refused `ItemUse` | H4c | 1 |
| 64 | 534 | Reimplementation notes | Don't refuse on a handler's "3" at the drain: the return is discarded. | `0x0053F459` | c | as row 9 | S4b | 1 |

**Totals by class:** a-logs 6, a-run 3, b 21, c 13, c-emu 10, d-edit 3, d-none 8 (sum 64).
