# Plan 0038 inventory: player/creation

- **Spec:** [player/creation.md](../../specs/player/creation.md), read at `main` `e1c807a` (last change to the spec: `d307bb2`).
- **Front matter `I`:** 39; the *count* column sums to 39.
- **Finding:** [player/0001](../../findings/player/0001-creation.md) (sections given as `§n`; other subsystems' findings named in full).
- **Cluster:** 0c (monsters, hirelings, player). Classes, tiers and batches as in [plan 0038](../0038-inferred-claims-sweep.md#classes).
- Guard rows marked (a-logs) with "0 → d-none" are re-read first: a guard the later logs never took is reclassified d-none by the batch, not raised.

| # | Spec section | Claim | Finding anchor | Class | Route | Tier | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | [Entry points](../../specs/player/creation.md#entry-points) | Version < 92 reader and PlayerLoad reach the same steps | NewCharLegacy 0x00532590 | b | old-version save; save family | T3 | H1a | 1 |
| 2 | [Entry points](../../specs/player/creation.md#entry-points) | Capped grant 1.4M / 20M / 40M | ExpGrantCapped 0x0058C5C0 | b | name the trigger statically, then a session; may fall to d-owner | T3 | H6g | 1 |
| 3 | [Entry points](../../specs/player/creation.md#entry-points) | Death | PLAYER_DeathExpLoss 0x005359F0 | b | logger line at the loss; a Hell session without Energy Shield | T2 | H6g | 1 |
| 4 | [Entry points](../../specs/player/creation.md#entry-points) | Attribute point spent | PLAYER_SpendStatPoint 0x00570D60 | b | pilot action: the stat buttons after a level-up; logger line | T2 | H6g | 1 |
| 5 | [Constants](../../specs/player/creation.md#constants) | Kill experience clamp 0x7FFFFF | 0x0057E480 | d (d-owner) | d-owner: needs a Hell act boss at `/players 8` | T3 | - | 1 |
| 6 | [Constants](../../specs/player/creation.md#constants) | Party distance and bonus | XP_PartyShare 0x0057E6C0 | d (d-2c) | d-2c | T2 | - | 1 |
| 7 | [A. The stub and the server's checks](../../specs/player/creation.md#a-the-stub-and-the-servers-checks) | Stub checksum added when written | StubWrite 0x0043C6B0 | a-logs | RHDR stubs of the 9 newchar logs: recompute the checksum | T2 | S3a | 1 |
| 8 | [A. The stub and the server's checks](../../specs/player/creation.md#a-the-stub-and-the-servers-checks) | D2S_ReadHeader checks and their order | D2S_ReadHeader 0x0056A090 | b | malformed saves (length, checksum, size, version, name, class); `d2s-io.gdb` reader codes | T3 | H1a | 1 |
| 9 | [A. The stub and the server's checks](../../specs/player/creation.md#a-the-stub-and-the-servers-checks) | Bytes after the header: load error 9 | 0x0056B1C6 | b | as above | T3 | H1a | 1 |
| 10 | [A. The stub and the server's checks](../../specs/player/creation.md#a-the-stub-and-the-servers-checks) | Hardcore bit 0x04; screen ORs 0x20 for classes 5, 6 | 0x00436360 | a-logs | stub status bytes of the hardcore (34109) and Druid/Assassin stubs | T2 | S3a | 1 |
| 11 | [A. The stub and the server's checks](../../specs/player/creation.md#a-the-stub-and-the-servers-checks) | No failure observed; class 7 passes | 0x0056A172 | b | as the header-check row | T3 | H1a | 1 |
| 12 | [B. NewCharFromStub: the order of a new…](../../specs/player/creation.md#b-newcharfromstub-the-order-of-a-new-character) | client.flags3D4 bit 1 | 0x00537970 | b | logger read of client +0x3D4 at NCX | T3 | H6g | 1 |
| 13 | [B. NewCharFromStub: the order of a new…](../../specs/player/creation.md#b-newcharfromstub-the-order-of-a-new-character) | act from client.act | CLIENT_GetAct 0x005382B0 | a-logs | the `-act N` sessions 34105–34108: the logged act | T2 | S3a | 1 |
| 14 | [B. NewCharFromStub: the order of a new…](../../specs/player/creation.md#b-newcharfromstub-the-order-of-a-new-character) | act not from the stub; g_StartAct | g_StartAct 0x00883D44 | a-logs | as above | T2 | S3a | 1 |
| 15 | [C. Starting attributes — PLAYER_InitBa…](../../specs/player/creation.md#c-starting-attributes--player_initbasestats) | act ≥ 5 → 0 never fires | 0x007326B4 | d (d-none) | d-none | T3 | - | 1 |
| 16 | [D. Starting skills](../../specs/player/creation.md#d-starting-skills) | Existing entry raised by 1 | SKILLS_AddSkill 0x00647110 | c | second caller: the skill-point spend path reads and raises the same entry | T2 | S3b | 1 |
| 17 | [E. Starting items — PLAYER_GiveStartIt…](../../specs/player/creation.md#e-starting-items--player_givestartitems) | Belt full or equip fails: inventory (two lines) | StartItemSlot 0x00534D60 | d (d-none) | d-none: stock kits fill neither | T3 | - | 2 |
| 18 | [E. Starting items — PLAYER_GiveStartIt…](../../specs/player/creation.md#e-starting-items--player_givestartitems) | Belt column search path | BeltFreeSlot 0x0063C600 | b | pick up a potion matching a belt column; logger line | T3 | H6g | 1 |
| 19 | [E. Starting items — PLAYER_GiveStartIt…](../../specs/player/creation.md#e-starting-items--player_givestartitems) | Quiver quantity 250 / 100 | StartItemSlot | d (d-none) | d-none: no stock kit has one | T3 | - | 1 |
| 20 | [F. The experience table](../../specs/player/creation.md#f-the-experience-table) | Class outside 0..6 reads column 0 | EXP_GetThreshold 0x00611800 | b | class-7 save; save family | T3 | H1a | 1 |
| 21 | [F. The experience table](../../specs/player/creation.md#f-the-experience-table) | MaxLvl from Experience row 0 | ExpMaxLevel 0x00611830 | c | second path: EXP_GetRatio reads the same cell (F4, run-backed) | T2 | S3b | 1 |
| 22 | [G. Kill experience — XP_Compute](../../specs/player/creation.md#g-kill-experience--xp_compute) | Input is the killed monster's experience | XP_OnMonsterKill 0x0057E990 | b | log the monster's stat 21 at the kill (or chain `mon-stats.gdb`) | T2 | H6g | 1 |
| 23 | [G. Kill experience — XP_Compute](../../specs/player/creation.md#g-kill-experience--xp_compute) | Clamp, non-positive and level-cap returns | 0x0057E480 | b | level-99 built save (cap return 0); a kill of an Exp-0 class if one is killable; the clamp stays d-owner | T3 | H6g | 1 |
| 24 | [G. Kill experience — XP_Compute](../../specs/player/creation.md#g-kill-experience--xp_compute) | ExpRatio overflow branch | 0x0057E390 | d (d-owner) | d-owner: needs > 2M experience per kill at level ≥ 97 | T3 | - | 1 |
| 25 | [G. Kill experience — XP_Compute](../../specs/player/creation.md#g-kill-experience--xp_compute) | Stat 85 bonus | 0x0057E480 | b | recipe with an `item_addexperience` item | T2 | H6g | 1 |
| 26 | [G. Kill experience — XP_Compute](../../specs/player/creation.md#g-kill-experience--xp_compute) | 0x0057E3F0 no change for a player | 0x0057E3F0 | a-logs | the 32 kills: the value after the call equals the input | T2 | S3a | 1 |
| 27 | [G. Kill experience — XP_Compute](../../specs/player/creation.md#g-kill-experience--xp_compute) | Clamp, cap, overflow, stat 85 not reached (note) | XP_Compute | b | as the rows above | T3 | H6g | 1 |
| 28 | [H. Adding experience — PLAYER_AddExper…](../../specs/player/creation.md#h-adding-experience--player_addexperience) | Cap at the threshold of MaxLvl (two statements) | PLAYER_AddExperience 0x0057E510 | b | level-98 built save one kill below the level-99 threshold | T3 | H6g | 2 |
| 29 | [J. Other level and experience changes](../../specs/player/creation.md#j-other-level-and-experience-changes) | ExpGrantCapped | ExpGrantCapped | b | as the Entry points row | T3 | H6g | 1 |
| 30 | [J. Other level and experience changes](../../specs/player/creation.md#j-other-level-and-experience-changes) | Death experience loss | PLAYER_DeathExpLoss | b | as the Entry points row | T2 | H6g | 1 |
| 31 | [J. Other level and experience changes](../../specs/player/creation.md#j-other-level-and-experience-changes) | Party share | XP_PartyShare | d (d-2c) | d-2c | T2 | - | 1 |
| 32 | [J. Other level and experience changes](../../specs/player/creation.md#j-other-level-and-experience-changes) | SpendStatPoint | PLAYER_SpendStatPoint | b | as the Entry points row | T2 | H6g | 1 |
| 33 | [J. Other level and experience changes](../../specs/player/creation.md#j-other-level-and-experience-changes) | J2–J5 not run (note) | player/0001 §11 | b | as the rows above; the party half stays d-2c | T2 | H6g | 1 |
| 34 | [J. Other level and experience changes](../../specs/player/creation.md#j-other-level-and-experience-changes) | Class 7 gets nothing; class 0 experience column | 0x005706FD | b | class-7 save; save family | T3 | H1a | 1 |
| 35 | [Reimplementation notes](../../specs/player/creation.md#reimplementation-notes) | XP_Compute returns 1 for non-positive input | XP_Compute 0x0057E480 | b | as the G1 row | T3 | H6g | 1 |
| 36 | [Reimplementation notes](../../specs/player/creation.md#reimplementation-notes) | Shift count 10 or 11 with stock ExpRatio | XP_ApplyExpRatio 0x0057E390 | c | data behaviour over every Experience row | T2 | S3b | 1 |
| 37 | [Reimplementation notes](../../specs/player/creation.md#reimplementation-notes) | StatPerLevel read as i8 | struct CharStatsRec+0x50 | d (d-none) | d-none: stock 5 for every class | T3 | - | 1 |

**Totals by class:** a-logs 5, b 22, c 3, d-2c 2, d-none 5, d-owner 2 (sum 39).
