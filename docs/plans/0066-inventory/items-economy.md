# Plan 0066 inventory: items/economy

- **Spec:** [items/economy](../../specs/items/economy.md), read at `main` `b5999f5e`.
- **Front matter `I`:** 86; the *Count* column sums to 86.
- Classes, batches and conventions as in [the inventory README](README.md#conventions).

| # | Line | Section | Claim (excerpt) | Anchor | Class | Route or reason | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | 60 | Entry points | A charged skill is cast | `fn:sub_0056BEC0_UseCharge@0x0056BEC0` | ? | ? | ? | 1 |
| 2 | 63 | Entry points | NPC classes. Repair is accepted for MonStats classes 154, 178, 253, 257 and 511; resurrection … | – | ? | ? | ? | 1 |
| 3 | 71 | Entry points | The client copy. The client calls the same price and repair-cost functions (six call sites … | – | ? | ? | ? | 1 |
| 4 | 132 | Constants | NO_PRICE — (no player, no item, not an item) | `0x0062EFBA` | ? | ? | ? | 1 |
| 5 | 133 | Constants | R_CAP — 99 (item_reducedprices cap) | `0x0062F02C` | ? | ? | ? | 1 |
| 6 | 134 | Constants | GOLD_PER_LEVEL — 10 000: carried gold cap = L × 10 … | `fn:PLAYER_GoldCap@0x00622E70` | ? | ? | ? | 1 |
| 7 | 135 | Constants | STASH_CAP — 2 500 000, not by level | `fn:PLAYER_StashGoldCap@0x00623460` | ? | ? | ? | 1 |
| 8 | 136 | Constants | PILE_MAX, PILES_MAX — 2 000 000 000 per pile, 32 piles | `fn:sub_0055A090_DropGoldAmount@0x0055A090` | ? | ? | ? | 1 |
| 9 | 139 | Constants | CAIN_COST — 100 per unidentified item | `fn:NPC_CainIdentify@0x00578460` | ? | ? | ? | 1 |
| 10 | 140 | Constants | CORPSE_MAX — 16 corpses (cmp eax, ; jbe) | `0x0057F72D` | ? | ? | ? | 1 |
| 11 | 143 | Constants | REPLENISH_BASE, REPLENISH_MIN — 2500 frames; requeue floor 125 frames | `fn:ITEMEVENT_Replenish@0x00562D30` | ? | ? | ? | 1 |
| 12 | 164 | A. The scaling primitive | At the other steps that have it (the affix, set and unique terms of AddTerm, … | – | ? | ? | ? | 1 |
| 13 | 189 | B. The price core: early returns and the base | … if player = none or item = none or item is not an item: return | `0x0062EFBA` | ? | ? | ? | 1 |
| 14 | 190 | B. The price core: early returns and the base | B2. if mode = 3 and not ItemCanRepair(item): return 0 | `0x0062EFBA` | ? | ? | ? | 1 |
| 15 | 191 | B. The price core: early returns and the base | B3. if item.flags & : return 1 ; every mode | `0x0062EFBA` | ? | ? | ? | 1 |
| 16 | 208 | B. The price core: early returns and the base | starting item was priced). | `0x0062EFBA` | ? | ? | ? | 1 |
| 17 | 211 | B. The price core: early returns and the base | The ear (earLevel at ItemData+) and body-part bases were not priced in the run. A … | – | ? | ? | ? | 1 |
| 18 | 213 | B. The price core: early returns and the base | The ear, body-part and tome bases leave R at 0, and the armour step overwrites … | – | ? | ? | ? | 1 |
| 19 | 216 | B. The price core: early returns and the base | The tome base is CostPerCharge × q + cost, with cost the Misc row's; Books … | – | ? | ? | ? | 1 |
| 20 | 274 | C. The value terms (modes 0, 1, 3) | A unique with no file index or no record (the magic branch) was not priced … | – | ? | ? | ? | 1 |
| 21 | 276 | C. The value terms (modes 0, 1, 3) | Unique and set items get no per-stat terms; superior and tempered items do. (jump table … | `0x0062FD9C` | ? | ? | ? | 1 |
| 22 | 307 | C. The value terms (modes 0, 1, 3) | 4 (by time) — (jump table , ) | `0x006292DC` | ? | ? | ? | 1 |
| 23 | 311 | C. The value terms (modes 0, 1, 3) | No stock item with an Encode 4 stat was priced in the run. (jump table … | `0x006292DC` | ? | ? | ? | 1 |
| 24 | 326 | C. The value terms (modes 0, 1, 3) | For every stock skill cost mult ≤ 896, so the large form reduces to cost … | – | ? | ? | ? | 1 |
| 25 | 332 | D. Mode steps, the NPC row, quantity and the result | … = 1 and item.flags & and ItemHasDurability(item) and M ≠ 0 and D ≤ 0: | `0x0062F9B6` | ? | ? | ? | 1 |
| 26 | 352 | D. Mode steps, the NPC row, quantity and the result | D5. if mode = 3 and not (item.flags & ): R ← R + RechargeCost(item) | `0x0062FCD6` | ? | ? | ? | 1 |
| 27 | 358 | D. Mode steps, the NPC row, quantity and the result | RechargeCost(item): | `fn:sub_00628D30_RechargeCost@0x00628D30` | ? | ? | ? | 1 |
| 28 | 370 | D. Mode steps, the NPC row, quantity and the result | No broken ethereal item was sold in the run. | `0x0062FA60` | ? | ? | ? | 1 |
| 29 | 372 | D. Mode steps, the NPC row, quantity and the result | repair input at full durability or with stat 252, so those two branches stay | – | ? | ? | ? | 1 |
| 30 | 380 | D. Mode steps, the NPC row, quantity and the result | S's large form tests sell mult ≠ 0, not buy mult | `0x0062FAEE` | ? | ? | ? | 1 |
| 31 | 384 | D. Mode steps, the NPC row, quantity and the result | The recharge cost is added after the NPC step, so rep mult and the quest … | – | ? | ? | ? | 1 |
| 32 | 390 | D. Mode steps, the NPC row, quantity and the result | It lowers the repair price too; no repair input with r ≠ 0 was met. | `0x0062FD07` | ? | ? | ? | 1 |
| 33 | 415 | E. The gamble price (mode 2) | The +1 and the floor at 0 apply after the division (sar 1, sar 2, … | – | ? | ? | ? | 1 |
| 34 | 422 | E. The gamble price (mode 2) | No version-0 item was gambled; none is expected on stock data. | `0x0062F062` | ? | ? | ? | 1 |
| 35 | 440 | F. Callers: buy, sell, repair | F1. ItemCanRepair(item): | `fn:sub_0062E660_ItemCanRepair@0x0062E660` | ? | ? | ? | 1 |
| 36 | 446 | F. Callers: buy, sell, repair | … base.nodurability = 0 and base.durability ≠ 0 and M ≠ 0 and full(152) < 1 | `fn:sub_00629930_ItemHasDurability@0x00629930` | ? | ? | ? | 1 |
| 37 | 454 | F. Callers: buy, sell, repair | … order, every one evaluated (no early exit): ; tests 2, 5, 7 , the rest | `0x0057962B` | ? | ? | ? | 1 |
| 38 | 467 | F. Callers: buy, sell, repair | charges; M ≠ 0 and D < M ; | `0x0057822C` | ? | ? | ? | 1 |
| 39 | 473 | F. Callers: buy, sell, repair | F7. ItemRepairAll(game, item, player) ; repairs ONE item despite the name | `fn:sub_005761C0_ItemRepairAll@0x005761C0` | ? | ? | ? | 1 |
| 40 | 483 | F. Callers: buy, sell, repair | The test reads the item's own ItemTypes row. On stock data the Equiv closure gives … | – | ? | ? | ? | 1 |
| 41 | 501 | F. Callers: buy, sell, repair | The other four tests (Cracked , base type 7 , flag , | `0x00579630` | ? | ? | ? | 1 |
| 42 | 513 | F. Callers: buy, sell, repair | The entry refusals, the partial branch's tests other than gold > 0 (the bounds on … | – | ? | ? | ? | 1 |
| 43 | 516 | F. Callers: buy, sell, repair | An ethereal item gets no repair box from the client, so no packet and no … | – | ? | ? | ? | 1 |
| 44 | 523 | F. Callers: buy, sell, repair | ItemRepairBroken reaches drawing code through its callees | `0x0055C5C0` | ? | ? | ? | 1 |
| 45 | 535 | F. Callers: buy, sell, repair | No quest script repairs. A call-site scan of the six repair functions finds ItemRepairAll called | – | ? | ? | ? | 1 |
| 46 | 551 | F. Callers: buy, sell, repair | D2S_WriteCorpses sums mode-0 prices with difficulty 3 and class 513 (Malah) to choose the most … | – | ? | ? | ? | 1 |
| 47 | 561 | G. Gold: payment, caps, piles and the death loss | G2. caps: carried ≤ L × 10 000 (PLAYER_GoldCap); stash ≤ 2 500 000 (PLAYER_StashGoldCap) | `fn:PLAYER_GoldCap@0x00622E70` | ? | ? | ? | 1 |
| 48 | 562 | G. Gold: payment, caps, piles and the death loss | G3. UnitAddGoldStat(player, stat 14 or 15, delta): | `fn:sub_0053FF00_UnitAddGoldStat@0x0053FF00` | ? | ? | ? | 1 |
| 49 | 564 | G. Gold: payment, caps, piles and the death loss | G4. PlayerGiveGold(n): add min(n, cap − gold); drop the rest as piles (DropGoldAmount) | `fn:sub_0055B060_PlayerGiveGold@0x0055B060` | ? | ? | ? | 1 |
| 50 | 565 | G. Gold: payment, caps, piles and the death loss | GoldPickup(pile): take min(pile, cap − gold); re-drop the remainder (DropGold) | `fn:sub_0055C850_GoldPickup@0x0055C850` | ? | ? | ? | 1 |
| 51 | 566 | G. Gold: payment, caps, piles and the death loss | StashGoldMove: deposit at most cap − stash; a withdrawal needs the room | `fn:sub_00564D50_StashGoldMove@0x00564D50` | ? | ? | ? | 1 |
| 52 | 573 | G. Gold: payment, caps, piles and the death loss | In a party with another member in the level, a pickup goes through PartyGoldShare (a … | – | ? | ? | ? | 1 |
| 53 | 587 | G. Gold: payment, caps, piles and the death loss | … monster drop: amount ← (amount × aux) >> 8 when the TC entry has mul= | `fn:ITEMS_UnitIsType@0x00629BB0` | ? | ? | ? | 1 |
| 54 | 608 | G. Gold: payment, caps, piles and the death loss | The case "monster level 1 or less", the floor of 1 on DropItemAtUnit's ilvl | `0x00559AE3` | ? | ? | ? | 1 |
| 55 | 617 | G. Gold: payment, caps, piles and the death loss | Which Levels column LevelMonLvl read for Wirt's piles is not separated: Tristram's MonLvl1 and | – | ? | ? | ? | 1 |
| 56 | 623 | G. Gold: payment, caps, piles and the death loss | G9. DropGoldAmount(unit, amount, out, maxPiles = 32): | `fn:sub_0055A090_DropGoldAmount@0x0055A090` | ? | ? | ? | 1 |
| 57 | 632 | G. Gold: payment, caps, piles and the death loss | Baal's quest gold (items/quest-drops D6) and every overflow drop use | – | ? | ? | ? | 1 |
| 58 | 664 | G. Gold: payment, caps, piles and the death loss | G11. PlayerDropGold(amount): | `fn:sub_00535510_PlayerDropGold@0x00535510` | ? | ? | ? | 1 |
| 59 | 673 | G. Gold: payment, caps, piles and the death loss | PvP deaths, game types other than 3 and hardcore were not met. Hardcore is not … | – | ? | ? | ? | 1 |
| 60 | 677 | G. Gold: payment, caps, piles and the death loss | The game type is written once, at game creation: GameCreate stores the byte from the … | – | ? | ? | ? | 1 |
| 61 | 682 | G. Gold: payment, caps, piles and the death loss | The switches. -gametype N is a source of g_ClientGameMode (launcher and multiplayer code write it … | – | ? | ? | ? | 1 |
| 62 | 688 | G. Gold: payment, caps, piles and the death loss | The corpse. When the corpse is made, the remaining carried gold (0 after a non-PvP … | – | ? | ? | ? | 1 |
| 63 | 701 | G. Gold: payment, caps, piles and the death loss | G14. Cain's identify: cost ← 100 × CountUnidentified(player) | `fn:NPC_CainIdentify@0x00578460` | ? | ? | ? | 1 |
| 64 | 712 | G. Gold: payment, caps, piles and the death loss | A refused resurrection also revives nothing: the test at jumps to the common exit , | `0x00579CAE` | ? | ? | ? | 1 |
| 65 | 715 | G. Gold: payment, caps, piles and the death loss | The same cost is sent to the client when the mercenary dies. | `fn:PETS_OnDeath@0x005751A0` | ? | ? | ? | 1 |
| 66 | 716 | G. Gold: payment, caps, piles and the death loss | One paid identify was met in the run (100 for one item, quest word 4 … | – | ? | ? | ? | 1 |
| 67 | 718 | G. Gold: payment, caps, piles and the death loss | sub_00578ED0_NpcHealDead would charge L × ((ΔHP >> 8) + (Δmana >> 8)) >> 2 for … | – | ? | ? | ? | 1 |
| 68 | 767 | H. Wear: durability, quantity, charges, replenish | Only a melee delivery reaches this function (one call site, from COMBAT_DeliverQueued); a missile or … | – | ? | ? | ? | 1 |
| 69 | 778 | H. Wear: durability, quantity, charges, replenish | The classic throwing weapon, the stack refill and version-0 items are read from the code; … | – | ? | ? | ? | 1 |
| 70 | 783 | H. Wear: durability, quantity, charges, replenish | A melee weapon whose durability reaches 0 gets D = 0 and quantity 0 but … | – | ? | ? | ? | 1 |
| 71 | 789 | H. Wear: durability, quantity, charges, replenish | H3. PLAYER_UseAmmo(player), from the missile-launch functions: | `fn:PLAYER_UseAmmo@0x0056C3F0` | ? | ? | ? | 1 |
| 72 | 794 | H. Wear: durability, quantity, charges, replenish | H5. UseCharge(caster, skill, level): the item carrying that charged skill and level: | `fn:sub_0056BEC0_UseCharge@0x0056BEC0` | ? | ? | ? | 1 |
| 73 | 796 | H. Wear: durability, quantity, charges, replenish | H6. SkillWeaponWear (from ), with the skill's calcs + chance and + amount: | `fn:sub_005DAA40_SkillWeaponWear@0x005DAA40` | ? | ? | ? | 1 |
| 74 | 805 | H. Wear: durability, quantity, charges, replenish | Bows, crossbows and quivers were not met in the run. | `fn:PLAYER_UseAmmo@0x0056C3F0` | ? | ? | ? | 1 |
| 75 | 806 | H. Wear: durability, quantity, charges, replenish | The missile gates. The line and lob missile creators take a useAmmo argument; with it … | – | ? | ? | ? | 1 |
| 76 | 817 | H. Wear: durability, quantity, charges, replenish | No charge was used and no skill wear was met in the run. | `fn:sub_0056BEC0_UseCharge@0x0056BEC0` | ? | ? | ? | 1 |
| 77 | 819 | H. Wear: durability, quantity, charges, replenish | Wear is Impale's. SkillWeaponWear has one caller, start function 7 (Impale), which calls it after … | – | ? | ? | ? | 1 |
| 78 | 825 | H. Wear: durability, quantity, charges, replenish | … item event 3 at frame + 2500 ÷ r + 1 ; 64-bit signed ÷ | `fn:sub_00558530_ItemReplenishDurTimer@0x00558530` | ? | ? | ? | 1 |
| 79 | 839 | H. Wear: durability, quantity, charges, replenish | The value written per tick, the floor of 125 frames (it binds only above r … | – | ? | ? | ? | 1 |
| 80 | 850 | I. Draws and seeds per event kind | sell, refused by the gamble-view test or one of … — none (the refusal skips ItemCopy) | `0x0057962B` | ? | ? | ? | 1 |
| 81 | 851 | I. Draws and seeds per event kind | PlayerGiveGold — +2 in 3 of 46 (a re-drop over the … | `fn:sub_0055B060_PlayerGiveGold@0x0055B060` | ? | ? | ? | 1 |
| 82 | 858 | I. Draws and seeds per event kind | skill wear (Impale) — one step of the caster's seed when the weapon … | `fn:sub_005DAA40_SkillWeaponWear@0x005DAA40` | ? | ? | ? | 1 |
| 83 | 859 | I. Draws and seeds per event kind | charge use — none (no drawing callee within depth 6) | `fn:sub_0056BEC0_UseCharge@0x0056BEC0` | ? | ? | ? | 1 |
| 84 | 875 | Outputs |  | `fn:sub_005761C0_ItemRepairAll@0x005761C0` | ? | ? | ? | 1 |
| 85 | 981 | Reimplementation notes | differs only on paths that skip the clip (the PvP death write). | `fn:sub_0053FF00_UnitAddGoldStat@0x0053FF00` | ? | ? | ? | 1 |
| 86 | 985 | Reimplementation notes | sub_005761C0_ItemRepairAll repairs one item; the repair-all is RepairCost with a callback. | – | ? | ? | ? | 1 |
