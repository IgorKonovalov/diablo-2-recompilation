# Plan 0066 inventory: quests/progression

- **Spec:** [quests/progression](../../specs/quests/progression.md), read at `main` `b5999f5e`.
- **Front matter `I`:** 322; the *Count* column sums to 322.
- Classes, batches and conventions as in [the inventory README](README.md#conventions).

| # | Line | Section | Claim (excerpt) | Anchor | Class | Route or reason | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | 32 | Entry points | an item is placed / dropped (e4 / e5) — (7 sites) / → QUESTS_DispatchUnitEvent | `fn:QUESTS_DispatchUnitEvent@0x005439A0` | ? | ? | ? | 1 |
| 2 | 33 | Entry points | a hooked monster dies (e8) — sub_0057CCB0_UnitKilled → QUESTS_MonsterDeathEvent | `fn:QUESTS_MonsterDeathEvent@0x00543A30` | ? | ? | ? | 1 |
| 3 | 34 | Entry points | a player leaves (e9 per quest item carried, then … — sub_00543BD0_QuestsInvItemEvent | `fn:sub_00543BD0_QuestsInvItemEvent@0x00543BD0` | ? | ? | ? | 1 |
| 4 | 36 | Entry points | every 20th game frame — QUESTS_TimersRun from sub_0052D870_GameTick | `fn:QUESTS_TimersRun@0x00543E10` | ? | ? | ? | 1 |
| 5 | 37 | Entry points | a quest object is operated, or its timed object … — g_ObjOperateFns[OperateFn], QUESTS_ObjectEvent | `data:g_ObjOperateFns@0x00732D18` | ? | ? | ? | 1 |
| 6 | 38 | Entry points | an NPC menu service (imbue, socket, personalise, Hell respec, … — NPC_MenuAction | `fn:NPC_MenuAction@0x00579D60` | ? | ? | ? | 1 |
| 7 | 72 | Constants | quest objects — 37 main-table + 4 NPC-introduction objects (ids 37–40) | `data:g_QuestDescs@0x00731510` | ? | ? | ? | 1 |
| 8 | 74 | Constants | timer cadence — every 20th frame (frame mod 20 = 0) | `fn:sub_0052D870_GameTick@0x0052D870` | ? | ? | ? | 1 |
| 9 | 81 | Inputs and oracles | the trigger: a kill, an operate, a level change, … — game simulation decides when it happens | `fn:QUESTS_DispatchEvent@0x005438E0` | ? | ? | ? | 1 |
| 10 | 83 | Inputs and oracles | party membership, the players' rooms and near lists, held … — read by credit passes and item tests | `fn:sub_00540510_PartyForEach@0x00540510` | ? | ? | ? | 1 |
| 11 | 85 | Inputs and oracles | the log state bytes +/+ where they gate no … — presentation of the quest log | `fn:QUESTS_SetState@0x00544300` | ? | ? | ? | 1 |
| 12 | 86 | Inputs and oracles | GetTickCount in Diablo's end timer — input | `fn:sub_005B4BE0_A4Q2_Timer@0x005B4BE0` | ? | ? | ? | 1 |
| 13 | 120 | A. The quest record | … s) = bit 16q + s of rec; SetState / ClearState set or clear it | `fn:QUESTRECORD_GetState@0x0065C310` | ? | ? | ? | 1 |
| 14 | 135 | A. The quest record | 0 — only word 9's first-join check | `fn:QUESTRECORD_SetState@0x0065C360` | ? | ? | ? | 1 |
| 15 | 136 | A. The quest record | 1 — the completing event (QUESTS_ListSetPending sets 13 and 1 together) | `fn:QUESTS_ListSetPending@0x005455F0` | ? | ? | ? | 1 |
| 16 | 137 | A. The quest record | 2–11 — ClearSteps at most rewards | `fn:QUESTRECORD_ClearSteps@0x0065C3E0` | ? | ? | ? | 1 |
| 17 | 140 | A. The quest record | 14 — for the loader ; for the writers | `0x0059AAB7` | ? | ? | ? | 1 |
| 18 | 141 | A. The quest record | 15 — for the loader ; for word 9 | `0x00599293` | ? | ? | ? | 1 |
| 19 | 156 | A. The quest record | The game record has the same shape. It is written only through GameQuestSet (and the … | – | ? | ? | ? | 1 |
| 20 | 161 | A. The quest record | Words written by no quest object as its own word: 7, 15, 23, 28 (the … | – | ? | ? | ? | 1 |
| 21 | 172 | The registry | 0 — 0 | `data:g_QuestDescs@0x00731510` | ? | ? | ? | 1 |
| 22 | 173 | The registry | 1–6 — 1–6 | `data:g_QuestDescs@0x00731510` | ? | ? | ? | 1 |
| 23 | 175 | The registry | 8 — 7 | `data:g_QuestDescs@0x00731510` | ? | ? | ? | 1 |
| 24 | 176 | The registry | 9–14 — 8–13 | `data:g_QuestDescs@0x00731510` | ? | ? | ? | 1 |
| 25 | 177 | The registry | 15, 16 — 26, 27 | `data:g_QuestDescs@0x00731510` | ? | ? | ? | 1 |
| 26 | 178 | The registry | 17 — 14 | `data:g_QuestDescs@0x00731510` | ? | ? | ? | 1 |
| 27 | 179 | The registry | 18–23 — 15–20 | `data:g_QuestDescs@0x00731510` | ? | ? | ? | 1 |
| 28 | 180 | The registry | 24 — 16 in +; the code uses word 32 | `0x005BD368` | ? | ? | ? | 1 |
| 29 | 181 | The registry | 25 — 21 | `data:g_QuestDescs@0x00731510` | ? | ? | ? | 1 |
| 30 | 182 | The registry | 26–28 — 22–24 | `data:g_QuestDescs@0x00731510` | ? | ? | ? | 1 |
| 31 | 184 | The registry | 30 — 29 | `data:g_QuestDescs@0x00731510` | ? | ? | ? | 1 |
| 32 | 185 | The registry | 31–36 — 31–36 | `data:g_QuestDescs@0x00731510` | ? | ? | ? | 1 |
| 33 | 186 | The registry | second table — 42, never written | `0x0073188C` | ? | ? | ? | 1 |
| 34 | 188 | The registry | QUESTS_InitGame builds one object per main-table row, then one per second-table row (ids 37–40), each … | – | ? | ? | ? | 1 |
| 35 | 202 | Events | e4 item placed — item, + player | `0x00543D80` | ? | ? | ? | 1 |
| 36 | 203 | Events | e5 item dropped — the item's hooks, unforced | `0x00543DB0` | ? | ? | ? | 1 |
| 37 | 204 | Events | e8 hooked death — monster, + killer player | `fn:QUESTS_MonsterDeathEvent@0x00543A30` | ? | ? | ? | 1 |
| 38 | 205 | Events | e9 quest item of a leaving player — item, + player | `fn:sub_00543BD0_QuestsInvItemEvent@0x00543BD0` | ? | ? | ? | 1 |
| 39 | 206 | Events | e10 player leaves — all, forced, any act | `0x00543C96` | ? | ? | ? | 1 |
| 40 | 230 | Events | B3. QUESTS_DispatchUnitEvent(block, force): the same over the unit's hook list (+, head-inserted) | `fn:QUESTS_DispatchUnitEvent@0x005439A0` | ? | ? | ? | 1 |
| 41 | 238 | Events | e4, e5 and e8 outside the forced list) was not logged and stays | `fn:QUESTS_DispatchEvent@0x005438E0` | ? | ? | ? | 1 |
| 42 | 240 | Events | B2. | `0x00543C96` | ? | ? | ? | 1 |
| 43 | 242 | Events | Forced deaths. QUESTS_MonsterDeathEvent forces the dispatch when the dead monster is a superunique whose | – | ? | ? | ? | 1 |
| 44 | 247 | Events | Hooks. QUESTS_HookMonster(questId, unit) adds the quest to the unit's list (for quest 4 with object … | – | ? | ? | ? | 1 |
| 45 | 251 | Events | Events 1, 6, 7 and 12 have no live raiser (the wrappers and have no … | `0x00543CE0` | ? | ? | ? | 1 |
| 46 | 297 | C. The join and the game creator's history | The branches with the byte clear or a rejoin were not met with a deactivation … | `fn:sub_00546270_QuestsPlayerJoin@0x00546270` | ? | ? | ? | 1 |
| 47 | 303 | C. The join and the game creator's history | per handler | `fn:sub_0059AF50_A2Q4_NpcMessage@0x0059AF50` | ? | ? | ? | 1 |
| 48 | 310 | C. The join and the game creator's history | The version < 92 reader joins twice the same way; PlayerLoad's own no-save branch joins … | – | ? | ? | ? | 1 |
| 49 | 312 | C. The join and the game creator's history | The FirstJoin callbacks restore each quest's log state from the creator's step bits (bit 4 … | – | ? | ? | ? | 1 |
| 50 | 320 | D. Shared shapes of the quest scripts | StepBits (per player, when bits 0 and 1 are clear): set the step bit chosen … | – | ? | ? | ? | 1 |
| 51 | 323 | D. Shared shapes of the quest scripts | Near credit: every player whose room is the event's room or in that room's near … | – | ? | ? | ? | 1 |
| 52 | 326 | D. Shared shapes of the quest scripts | PartyCredit: for a credited player in a party, each member whose bits 0 and 1 … | – | ? | ? | ? | 1 |
| 53 | 329 | D. Shared shapes of the quest scripts | FailOthers: every other player whose bits 0 and 1 are clear gets bit 14 and … | – | ? | ? | ? | 1 |
| 54 | 331 | D. Shared shapes of the quest scripts | ChainNext (+): if the quest is active and below its last log state, start it … | – | ? | ? | ? | 1 |
| 55 | 334 | D. Shared shapes of the quest scripts | The NPC gate (+): when a talk starts with an NPC whose MonStats + bit … | – | ? | ? | ? | 1 |
| 56 | 337 | D. Shared shapes of the quest scripts | Reward pattern (most quests): a completing event sets bits 13 and 1 (or 13 and … | – | ? | ? | ? | 1 |
| 57 | 357 | E. Timers | A timer whose run returns 0 runs again every p + 1 boundaries (20·(p + … | – | ? | ? | ? | 1 |
| 58 | 362 | F. NPC interaction, server side | A talk raises e0 at the start (after the hireling list and the store), e11 … | – | ? | ? | ? | 1 |
| 59 | 370 | F. NPC interaction, server side | Item services and the Hell respec are NPC_MenuAction actions: imbue (word 3 bit 1), socket … | – | ? | ? | ? | 1 |
| 60 | 396 | G. The draws | e0 talk to NPC 377 — player unit seed | `0x0059E1CE` | ? | ? | ? | 1 |
| 61 | 399 | G. The draws | first use of bkd (or first cairn-stone operate, ) | `0x00592E90` | ? | ? | ? | 1 |
| 62 | 402 | G. The draws | the Zoo (InitFn 79) — 1–10 RandLoHi(1, nMonStats) (W40; object 567 is placed by … | `fn:sub_0058E830_A5Q6_ZooInit@0x0058E830` | ? | ? | ? | 1 |
| 63 | 404 | G. The draws | every other quest event — none in quest code | `fn:QUESTS_DispatchEvent@0x005438E0` | ? | ? | ? | 1 |
| 64 | 409 | G. The draws | G3. RandLoHi(s, lo, hi) = lo + Range(s, hi − lo) | `fn:RNG_RandLoHi@0x004BC500` | ? | ? | ? | 1 |
| 65 | 420 | G. The draws | Chaining. The quest seed is one object per game: its value at any draw depends … | – | ? | ? | ? | 1 |
| 66 | 424 | G. The draws | Spawns, objects, portals and items that quest events create draw on their own seeds (SpawnAtPos … | – | ? | ? | ? | 1 |
| 67 | 452 | Act I | b0 — e11 NPC 155, message 1 | `fn:sub_0058FA90_A1Q0_NpcMessage@0x0058FA90` | ? | ? | ? | 1 |
| 68 | 454 | Act I | Word 0 bit 0 gates only NPC 155's quest message (e0 and the NPC gate). … | – | ? | ? | ? | 1 |
| 69 | 472 | Act I | b13, b1 — e8: the level-8 monster region has every monster dead … | `fn:sub_00590260_A1Q1_MonsterDeath@0x00590260` | ? | ? | ? | 1 |
| 70 | 473 | Act I | b13, b1 — for a partied member in the Rogue Encampment ( … | `fn:sub_00590120_A1Q1_PartyCreditMember@0x00590120` | ? | ? | ? | 1 |
| 71 | 474 | Act I | b14 — the same kill: fail others | `fn:sub_00590080_A1Q1_FailOthers@0x00590080` | ? | ? | ? | 1 |
| 72 | 475 | Act I | G b13 — the same kill | `fn:sub_00590260_A1Q1_MonsterDeath@0x00590260` | ? | ? | ? | 1 |
| 73 | 478 | Act I | b2, b3, b4 — StepBits by log state (2; 3; 4 when + … | `fn:sub_0058FC90_A1Q1_StepBits@0x0058FC90` | ? | ? | ? | 1 |
| 74 | 484 | Act I | In the same run, the host's entry into the Den set b4 (the site) on … | `0x0058FD0A` | ? | ? | ? | 1 |
| 75 | 487 | Act I | The reward also adds 1 to stat 5 of the player (UnitAddStat(player, 5, 1, 0) … | `0x0058FF5A` | ? | ? | ? | 1 |
| 76 | 503 | Act I | b13, b1 — NPC_MenuAction in Hell (game+ = 2): w1 b1 set … | `fn:sub_0058FD20_A1Q1_RespecOffer@0x0058FD20` | ? | ? | ? | 1 |
| 77 | 504 | Act I | b0; b1 clear — NPC_MenuAction in Hell with w41 b1 set: the respec … | `fn:sub_0058FD50_A1Q1_RespecDone@0x0058FD50` | ? | ? | ? | 1 |
| 78 | 506 | Act I | Every write of word 41 is quest object 1's. Over every call of the record … | – | ? | ? | ? | 1 |
| 79 | 526 | Act I | b13, b1 — e8 hooked monster: near credit (the dead monster's room … | `fn:sub_00590C40_A1Q2_CreditNearBoss@0x00590C40` | ? | ? | ? | 1 |
| 80 | 527 | Act I | b13, b1 — party members in Act I | `fn:sub_00590D60_A1Q2_PartyCreditMember@0x00590D60` | ? | ? | ? | 1 |
| 81 | 528 | Act I | b14 — set | `fn:sub_00590DD0_A1Q2_FailOthers@0x00590DD0` | ? | ? | ? | 1 |
| 82 | 529 | Act I | G b13 — set | `fn:sub_00590EC0_A1Q2_MonsterDeath@0x00590EC0` | ? | ? | ? | 1 |
| 83 | 531 | Act I | b2, b3, b4 — set | `fn:sub_00590890_A1Q2_StepBits@0x00590890` | ? | ? | ? | 1 |
| 84 | 533 | Act I | The death registers timer (period 15). No draw in the quest. | `0x00590BF0` | ? | ? | ? | 1 |
| 85 | 549 | Act I | b6 — e4 on the hooked hdm (Malus), first time | `fn:sub_00591960_A1Q3_MalusPickup@0x00591960` | ? | ? | ? | 1 |
| 86 | 550 | Act I | b13, b1 — e11 NPC 154 (charsi) message , b0 clear, the … | `fn:sub_00591490_A1Q3_NpcMessage@0x00591490` | ? | ? | ? | 1 |
| 87 | 551 | Act I | b13, b1 — party members in Act I | `fn:sub_00591430_A1Q3_PartyCreditMember@0x00591430` | ? | ? | ? | 1 |
| 88 | 552 | Act I | G b13 — the same message when the log state + = … | `fn:sub_00591490_A1Q3_NpcMessage@0x00591490` | ? | ? | ? | 1 |
| 89 | 553 | Act I | b0; b1 clear — NPC_MenuAction imbue done (items/quest-drops § F); if b15 is … | `fn:sub_00591790_A1Q3_ImbueDone@0x00591790` | ? | ? | ? | 1 |
| 90 | 554 | Act I | b2, b3 — set | `fn:sub_00591340_A1Q3_StepBits@0x00591340` | ? | ? | ? | 1 |
| 91 | 556 | Act I | The talk offers the hand-in (message 3) only at clvl (stat 12) > 7 with … | – | ? | ? | ? | 1 |
| 92 | 575 | Act I | b4 — operate of the fifth cairn stone in the drawn … | `fn:sub_00593710_A1Q4_StoneOperate@0x00593710` | ? | ? | ? | 1 |
| 93 | 576 | Act I | b13, b1 — Gibbet operate (object 26, OperateFn 10) by a player … | `fn:sub_00593480_A1Q4_GibbetOperate@0x00593480` | ? | ? | ? | 1 |
| 94 | 577 | Act I | b13, b1 — the Gibbet's object event 7 (frame + 17): every … | `fn:sub_00593130_A1Q4_CreditTristram@0x00593130` | ? | ? | ? | 1 |
| 95 | 578 | Act I | b14 — the same event: fail others | `fn:sub_005931C0_A1Q4_FailOthers@0x005931C0` | ? | ? | ? | 1 |
| 96 | 580 | Act I | b14, G b13 — Cain lost, the other paths: e3 entry to level … | `fn:sub_00592B10_A1Q4_FailPlayer@0x00592B10` | ? | ? | ? | 1 |
| 97 | 582 | Act I | G b13 — the same message: if G w4 b13 was clear … | `fn:sub_00592250_A1Q4_NpcMessage@0x00592250` | ? | ? | ? | 1 |
| 98 | 583 | Act I | G b13 — FirstJoin when the creator has b0 | `fn:sub_00597030_A1Q4_FirstJoin@0x00597030` | ? | ? | ? | 1 |
| 99 | 584 | Act I | b10 — the Cow King's death: the killer has b10 clear … | `fn:sub_00593E70_A1Q4_CowKingDeath@0x00593E70` | ? | ? | ? | 1 |
| 100 | 585 | Act I | b10 — the same death: every player then in level 39 | `fn:sub_00593E30_A1Q4_CowLevelCredit@0x00593E30` | ? | ? | ? | 1 |
| 101 | 586 | Act I | G b11 — the cow portal opened (items/cube) | `fn:CUBE_CowPortalOpen@0x00594140` | ? | ? | ? | 1 |
| 102 | 587 | Act I | b2, b3 — set | `fn:sub_00592130_A1Q4_StepBits@0x00592130` | ? | ? | ? | 1 |
| 103 | 610 | Act I | The first stone operate draws the order the same way (not reached), and 's trs … | `0x00544840` | ? | ? | ? | 1 |
| 104 | 612 | Act I | MissileCreateAt(a, b, missile, x, y) (game in ECX, the source unit in EDX) creates a … | – | ? | ? | ? | 1 |
| 105 | 636 | Act I | With the stock rows. 288 cairnstones scatters cairnstonessky (289) every second frame while | – | ? | ? | ? | 1 |
| 106 | 642 | Act I | Items. Message with bks held removes it and gives bkd (QUESTS_GiveItem(bkd, 0, 2, 1)); message | – | ? | ? | ? | 1 |
| 107 | 646 | Act I | Tristram in a later game. The stones' init (object class 17) registers timer (period 1) … | `0x00592D50` | ? | ? | ? | 1 |
| 108 | 650 | Act I | Cain. The Gibbet event spawns monster 146 at the gibbet (+3, +3) by SpawnAtPos, retried … | – | ? | ? | ? | 1 |
| 109 | 669 | Act I | b13, b0; b1 clear — e8 the Countess: every player in level 25 with … | `fn:sub_00594F10_A1Q5_CreditAtDeath@0x00594F10` | ? | ? | ? | 1 |
| 110 | 670 | Act I | b14 — the same death: players elsewhere; fail others | `fn:sub_00595320_A1Q5_FailOthers@0x00595320` | ? | ? | ? | 1 |
| 111 | 671 | Act I | b0, b13 — the same death: players in level 25 with b0, … | `fn:sub_00594DD0_A1Q5_CreditInLevel@0x00594DD0` | ? | ? | ? | 1 |
| 112 | 672 | Act I | b13, b0 — the same death: players in the private list + … | `fn:sub_00595420_A1Q5_CreditList@0x00595420` | ? | ? | ? | 1 |
| 113 | 673 | Act I | b13, b0 — party members in Act I | `fn:sub_00595370_A1Q5_PartyCreditMember@0x00595370` | ? | ? | ? | 1 |
| 114 | 674 | Act I | G b13 — the same death (twice) | `fn:sub_00595710_A1Q5_CountessDeath@0x00595710` | ? | ? | ? | 1 |
| 115 | 675 | Act I | b2–b6 — StepBits by log state | `fn:sub_00594890_A1Q5_StepBits@0x00594890` | ? | ? | ? | 1 |
| 116 | 677 | Act I | The tower book (OperateFn 6) puts the object in mode 1 and sends message ; … | `0x00595160` | ? | ? | ? | 1 |
| 117 | 696 | Act I | b13, b1 — e8 Andariel: the killer (b0, b1 clear); then every … | `fn:sub_00596210_A1Q6_SetKilled@0x00596210` | ? | ? | ? | 1 |
| 118 | 697 | Act I | b14 — set | `fn:sub_005963E0_A1Q6_FailOthers@0x005963E0` | ? | ? | ? | 1 |
| 119 | 699 | Act I | G b13 — the same message when b13 is set | `fn:sub_00595C60_A1Q6_NpcMessage@0x00595C60` | ? | ? | ? | 1 |
| 120 | 700 | Act I | b2, b3, b4 — set | `fn:sub_00595BD0_A1Q6_StepBits@0x00595BD0` | ? | ? | ? | 1 |
| 121 | 702 | Act I | After the death a timer (period 1) gives each player in level 37 a class-59 … | – | ? | ? | ? | 1 |
| 122 | 712 | Act I | … , run once for each of quest objects 25 and 30: for the draws ; | `0x00596A90` | ? | ? | ? | 1 |
| 123 | 724 | Act I | Which branch a run takes (the conditions above) does not change the draw count. | `0x00596A90` | ? | ? | ? | 1 |
| 124 | 731 | Act I | No record bit is written (its + = 42 is never passed to a setter). … | – | ? | ? | ? | 1 |
| 125 | 748 | Act II | G b13 — the same message; first join of a player with … | `fn:sub_00598640_A2Q0_NpcMessage@0x00598640` | ? | ? | ? | 1 |
| 126 | 750 | Act II | G w8 b13 is read by Jerhyn's placement (word 12). NPC 244's e0 reacts to … | – | ? | ? | ? | 1 |
| 127 | 768 | Act II | b2, b3, b4 — per player with b0, b1 clear, by log state … | `0x005989E0` | ? | ? | ? | 1 |
| 128 | 769 | Act II | b13, b1, b5 — e8 Radament: near credit, b0, b1 clear; party members … | `fn:sub_00598E20_A2Q1_NearCredit@0x00598E20` | ? | ? | ? | 1 |
| 129 | 770 | Act II | b14 — e8: every other player with b0, b1 clear | `0x00598DC0` | ? | ? | ? | 1 |
| 130 | 772 | Act II | b0, b1, b15, b5 — e13: the first joiner has b0 and b5 and … | `fn:sub_00599230_A2Q1_FirstJoin@0x00599230` | ? | ? | ? | 1 |
| 131 | 774 | Act II | G b13 — Radament's death; message while the quest is off; first … | `fn:sub_00599020_A2Q1_RadamentDeath@0x00599020` | ? | ? | ? | 1 |
| 132 | 776 | Act II | So a creator who saved with the Book unread loses the quest at his next … | – | ? | ? | ? | 1 |
| 133 | 793 | Act II | b3 — e11 NPC 244 (cain2) messages ( removes tr1 ) | `fn:sub_005997F0_A2Q2_NpcMessage@0x005997F0` | ? | ? | ? | 1 |
| 134 | 794 | Act II | b4, b5, b6 — e11 messages (SetState(10, msg − )); sets all three | `fn:sub_005997F0_A2Q2_NpcMessage@0x005997F0` | ? | ? | ? | 1 |
| 135 | 795 | Act II | b10; b1 clear — set / clear | `fn:sub_005997F0_A2Q2_NpcMessage@0x005997F0` | ? | ? | ? | 1 |
| 136 | 796 | Act II | b4 / b5 / b6 — e5: vip / msf / box dropped on the … | `fn:sub_00599B30_A2Q2_ItemToGround@0x00599B30` | ? | ? | ? | 1 |
| 137 | 797 | Act II | b11 — the cube makes hst | `fn:sub_0059E5C0_QuestStaffMade@0x0059E5C0` | ? | ? | ? | 1 |
| 138 | 798 | Act II | b0, b13 — the staff placed in the orifice: the placer | `fn:sub_0059DD80_A2Q6_StaffPlaced@0x0059DD80` | ? | ? | ? | 1 |
| 139 | 799 | Act II | b0, b13 — party members in Act II with b0 clear; removes … | `fn:sub_0059DBD0_A2Q6_StaffPartyCredit@0x0059DBD0` | ? | ? | ? | 1 |
| 140 | 800 | Act II | b0, b13 — NpcActTravel, NPC 210, the first crossing (w15 b0 clear) … | `fn:sub_005467E0_NpcActTravel@0x005467E0` | ? | ? | ? | 1 |
| 141 | 801 | Act II | b9 — word 14's e13 and e14 (every join); no constant … | `fn:sub_0059D4F0_A2Q6_FirstJoin@0x0059D4F0` | ? | ? | ? | 1 |
| 142 | 803 | Act II | The three quest chests (OperateFn 39–41, objects 354–356) take one quest-seed step each for their … | – | ? | ? | ? | 1 |
| 143 | 821 | Act II | b3, b4 — the same pass at quest state = 2, = … | `0x0059A4F0` | ? | ? | ? | 1 |
| 144 | 822 | Act II | b1, b13; b14 clear — altar operate (OperateFn 24, object 149), the operator with … | `fn:sub_0059A7E0_A2Q3_ViperChest@0x0059A7E0` | ? | ? | ? | 1 |
| 145 | 823 | Act II | b13, b1 — the same: every player in the altar's level with … | `fn:sub_0059A680_A2Q3_LevelCredit@0x0059A680` | ? | ? | ? | 1 |
| 146 | 824 | Act II | b14 — other players with b0, b1 clear | `0x00599FE0` | ? | ? | ? | 1 |
| 147 | 825 | Act II | b0; b1 clear — e11 report (messages , any NPC) with b1 set | `fn:sub_0059EBE0_A2Q3_NpcMessage@0x0059EBE0` | ? | ? | ? | 1 |
| 148 | 826 | Act II | G b13 — altar; first join with b0 or b1; report | `fn:sub_0059A5D0_A2Q3_FirstJoin@0x0059A5D0` | ? | ? | ? | 1 |
| 149 | 847 | Act II | The level-45 entry takes the same branch (not logged), and the b3/b4 branches (states 2, … | – | ? | ? | ? | 1 |
| 150 | 850 | Act II | The altar refuses (unit event) a player who already has b1 or b0 and (w10 … | – | ? | ? | ? | 1 |
| 151 | 870 | Act II | b7 — e11 NPC 331 message | `fn:sub_0059AF50_A2Q4_NpcMessage@0x0059AF50` | ? | ? | ? | 1 |
| 152 | 872 | Act II | b2–b5 — per player with b0, b1 clear, by quest state | `0x0059ADB0` | ? | ? | ? | 1 |
| 153 | 873 | Act II | b13, b1, b0, b8, b7; steps clear — the journal operate (OperateFn 42, object 357): every player … | `fn:sub_0059B970_A2Q4_JournalOperate@0x0059B970` | ? | ? | ? | 1 |
| 154 | 874 | Act II | b14 — the journal: every other player with b0, b1 clear | `fn:sub_0059B970_A2Q4_JournalOperate@0x0059B970` | ? | ? | ? | 1 |
| 155 | 875 | Act II | b1 — e11 journal pages, messages | `fn:sub_0059AF50_A2Q4_NpcMessage@0x0059AF50` | ? | ? | ? | 1 |
| 156 | 876 | Act II | G b13 — the Canyon portal made; first joiner with b0 or … | `fn:sub_0059B530_A2Q4_FirstJoin@0x0059B530` | ? | ? | ? | 1 |
| 157 | 879 | Act II | W12. NpcTalk331 — e0 for NPC 331: for the open branch ; | `fn:sub_0059B1C0_A2Q4_NpcTalk@0x0059B1C0` | ? | ? | ? | 1 |
| 158 | 886 | Act II | b0 and b1 are set together at the journal, so the quest completes on reading; … | – | ? | ? | ? | 1 |
| 159 | 889 | Act II | No word-12 bit gates level 74's waypoint or the Arcane portal 298, and the palace … | – | ? | ? | ? | 1 |
| 160 | 907 | Act II | b13, b1 — e8 the Summoner: near credit, b0, b1 clear; party | `fn:sub_0059BE70_A2Q5_NearCredit@0x0059BE70` | ? | ? | ? | 1 |
| 161 | 908 | Act II | b14 — e8: other players | `fn:sub_0059C150_A2Q5_SummonerDeath@0x0059C150` | ? | ? | ? | 1 |
| 162 | 909 | Act II | b2 — per player at the state broadcast of the Summoner … | `fn:sub_0059C330_A2Q5_BossSeen@0x0059C330` | ? | ? | ? | 1 |
| 163 | 910 | Act II | b0; b1 clear — e11 report with b1 set | `fn:sub_0059BD70_A2Q5_NpcMessage@0x0059BD70` | ? | ? | ? | 1 |
| 164 | 911 | Act II | G b13 — the report when b13 is set | `fn:sub_0059BD70_A2Q5_NpcMessage@0x0059BD70` | ? | ? | ? | 1 |
| 165 | 913 | Act II | The death registers timer (period 3, two runs). No draw. | `0x0059BFD0` | ? | ? | ? | 1 |
| 166 | 930 | Act II | b2 — e3 entering the true tomb T = act+, or … | `fn:sub_0059C6C0_A2Q6_CanyonCredit@0x0059C6C0` | ? | ? | ? | 1 |
| 167 | 931 | Act II | b5 — e8 Duriel: the killer, party in Act II, players … | `fn:sub_0059D050_A2Q6_DurielDeath@0x0059D050` | ? | ? | ? | 1 |
| 168 | 932 | Act II | b13, b3 — e11 NPC 251 (tyrael1) message , once: the portal … | `fn:sub_0059C810_A2Q6_LairCredit@0x0059C810` | ? | ? | ? | 1 |
| 169 | 933 | Act II | b14 — the same: others with b0, b3, b4 clear | `fn:sub_0059CB20_A2Q6_NpcMessage@0x0059CB20` | ? | ? | ? | 1 |
| 170 | 936 | Act II | — — the same message with w10 b0 set removes hst … | `fn:sub_0059CB20_A2Q6_NpcMessage@0x0059CB20` | ? | ? | ? | 1 |
| 171 | 937 | Act II | b6–b11 — e11 messages , , , , , ("talked to … | `fn:sub_0059CB20_A2Q6_NpcMessage@0x0059CB20` | ? | ? | ? | 1 |
| 172 | 938 | Act II | G b13 — e11 NPC 210 with b13 | `fn:sub_0059CB20_A2Q6_NpcMessage@0x0059CB20` | ? | ? | ? | 1 |
| 173 | 940 | Act II | Tyrael's portal is class 59 to level 40, opened at the player (PortalObjectCreate(room, x, y, … | – | ? | ? | ? | 1 |
| 174 | 943 | Act II | Placing the staff registers timer with period (Missiles[338]+ − 75) ÷ 20 (period 1 from … | `0x0059D870` | ? | ? | ? | 1 |
| 175 | 947 | Act II | Word 14's code reads act + as the true tomb (e3, the tomb message to … | – | ? | ? | ? | 1 |
| 176 | 962 | Act II | b13 — e11 NPC 377 (act2guard4) messages | `fn:sub_0059E0E0_A2Q7_NpcMessage@0x0059E0E0` | ? | ? | ? | 1 |
| 177 | 963 | Act II | b0 — e11 NPC 377, other messages | `fn:sub_0059E0E0_A2Q7_NpcMessage@0x0059E0E0` | ? | ? | ? | 1 |
| 178 | 966 | Act II | W30. NpcTalk377 — e0, one draw per talk: | `fn:sub_0059E140_A2Q7_NpcTalk@0x0059E140` | ? | ? | ? | 1 |
| 179 | 973 | Act II | No stock data places NPC 377: no DS1 that a LvlPrest row names holds it … | – | ? | ? | ? | 1 |
| 180 | 981 | Act II | b0 — e11 NPC 378 (act2guard5) message | `fn:sub_0059E3C0_A2Q8_NpcMessage@0x0059E3C0` | ? | ? | ? | 1 |
| 181 | 989 | Act II | The message is offered while quest object 13 is active below state 2, G w11 … | – | ? | ? | ? | 1 |
| 182 | 994 | Act II | As quest object 37: per-NPC introduction flags only, no record bit, no draw. | `fn:sub_005984C0_A2Intro_NpcTalk@0x005984C0` | ? | ? | ? | 1 |
| 183 | 1009 | Act III | b0 — e11 NPC 253 message | `fn:sub_005B6ED0_A3Q0_NpcMessage@0x005B6ED0` | ? | ? | ? | 1 |
| 184 | 1010 | Act III | G b13 — the same messages; first joiner with b0 | `fn:sub_005B6FD0_A3Q0_FirstJoin@0x005B6FD0` | ? | ? | ? | 1 |
| 185 | 1012 | Act III | Creation reader. Two object InitFns spawn Hratli once per game at the object (SpawnAtPos(x, y, … | – | ? | ? | ? | 1 |
| 186 | 1031 | Act III | b2 — e3 leaving town 75 in state 2 or 3, … | `fn:sub_005B73A0_A3Q1_SetBit2@0x005B73A0` | ? | ? | ? | 1 |
| 187 | 1032 | Act III | b13, b0, b1 — e11 NPC 254 (alkor) message with bbb held (removed): … | `fn:sub_005B74E0_A3Q1_SetDone@0x005B74E0` | ? | ? | ? | 1 |
| 188 | 1033 | Act III | b1 — right after: each player with b1 gets UnitAddStat(player, 4, … | `fn:sub_005B7580_A3Q1_StatReward@0x005B7580` | ? | ? | ? | 1 |
| 189 | 1034 | Act III | b14 — the same pass: each player still with b0, b1 … | `fn:sub_005B75D0_A3Q1_SetMissed@0x005B75D0` | ? | ? | ? | 1 |
| 190 | 1035 | Act III | G b13 — the reporter has b13; first joiner with b0 | `fn:sub_005B7740_A3Q1_NpcMessage@0x005B7740` | ? | ? | ? | 1 |
| 191 | 1037 | Act III | The tome object (193) refuses a player with b0 (items/quest-drops § E). No | – | ? | ? | ? | 1 |
| 192 | 1052 | Act III | b2 — e11 NPC 245 (cain3) message | `fn:sub_005B8060_A3Q2_NpcMessage@0x005B8060` | ? | ? | ? | 1 |
| 193 | 1053 | Act III | b6 / b3 / b4 / b5 / b7 — e11 Cain messages | `fn:sub_005B8060_A3Q2_NpcMessage@0x005B8060` | ? | ? | ? | 1 |
| 194 | 1055 | Act III | b0, b13 — the same hit: party members in Act III (a … | `fn:sub_005BB850_A3Q5_OrbPartyPass@0x005BB850` | ? | ? | ? | 1 |
| 195 | 1071 | Act III | An operate without qf2 counts nothing; it was not reached on the server (the client … | – | ? | ? | ? | 1 |
| 196 | 1073 | Act III | The five items qey qhr qbr qf1 qf2 are removed for each party member on … | `0x005678A0` | ? | ? | ? | 1 |
| 197 | 1093 | Act III | b2–b5 — per player: b5 holding g33 ; b4 (and b2 … | `fn:sub_005B8B20_A3Q3_SetProgressBits@0x005B8B20` | ? | ? | ? | 1 |
| 198 | 1094 | Act III | b6 — e11 NPC 255 (ormus) message with g33 held (removed), … | `fn:sub_005B9240_A3Q3_NpcMessage@0x005B9240` | ? | ? | ? | 1 |
| 199 | 1095 | Act III | b14 — the same message: every player with b0, b6, b7, … | `fn:sub_005B9130_A3Q3_SetMissed@0x005B9130` | ? | ? | ? | 1 |
| 200 | 1097 | Act III | b13, b0 — after b8 when b7 is already set | `fn:sub_005B9240_A3Q3_NpcMessage@0x005B9240` | ? | ? | ? | 1 |
| 201 | 1099 | Act III | b7 — the same message with b8 clear | `fn:sub_005B9240_A3Q3_NpcMessage@0x005B9240` | ? | ? | ? | 1 |
| 202 | 1100 | Act III | b0 — e13: the first joiner has b6, b7, b8 and … | `fn:sub_005B9700_A3Q3_FirstJoin@0x005B9700` | ? | ? | ? | 1 |
| 203 | 1101 | Act III | b9 — e4 on g33 , once per player | `fn:sub_005B9520_A3Q3_ItemEvent@0x005B9520` | ? | ? | ? | 1 |
| 204 | 1102 | Act III | G b13 — message , quest active | `fn:sub_005B9240_A3Q3_NpcMessage@0x005B9240` | ? | ? | ? | 1 |
| 205 | 1104 | Act III | The Gidbinn altar (OperateFn 31, object 252) with b0, b7, b8 clear goes to mode … | – | ? | ? | ? | 1 |
| 206 | 1121 | Act III | b2 — e11 Cain message (and party) | `fn:sub_005BA320_A3Q4_NpcMessage@0x005BA320` | ? | ? | ? | 1 |
| 207 | 1122 | Act III | b4 — e11 Cain message (and party) | `fn:sub_005BA320_A3Q4_NpcMessage@0x005BA320` | ? | ? | ? | 1 |
| 208 | 1123 | Act III | b1 — e11 NPC 254 message with g34 held (removed), b0, … | `fn:sub_005BA320_A3Q4_NpcMessage@0x005BA320` | ? | ? | ? | 1 |
| 209 | 1125 | Act III | b6 — e4 on j34 , once per player | `fn:sub_005BA6A0_A3Q4_ItemEvent@0x005BA6A0` | ? | ? | ? | 1 |
| 210 | 1126 | Act III | G b13 — after message when the reporter has b13 | `fn:sub_005BA320_A3Q4_NpcMessage@0x005BA320` | ? | ? | ? | 1 |
| 211 | 1128 | Act III | NPC 264's (meshif2) message with j34 held turns it into g34 (no bit). The figurine … | – | ? | ? | ? | 1 |
| 212 | 1146 | Act III | b2 / b3 — per player at quest state 2–3; b3 when the … | `fn:sub_005BADC0_A3Q5_SetProgressBits@0x005BADC0` | ? | ? | ? | 1 |
| 213 | 1147 | Act III | b4 or b0, and b13 — the last council member's death: every Act III player … | `fn:sub_005BAE20_A3Q5_CouncilDoneNear@0x005BAE20` | ? | ? | ? | 1 |
| 214 | 1148 | Act III | b4, b13 — party members in Act III | `fn:sub_005BB640_A3Q5_PartySetBit4@0x005BB640` | ? | ? | ? | 1 |
| 215 | 1149 | Act III | b14 — players with b0 and b4 clear | `fn:sub_005BB710_A3Q5_SetMissed@0x005BB710` | ? | ? | ? | 1 |
| 216 | 1150 | Act III | b0; b4 clear — e11 Cain message with b4 set (the five Khalim … | `fn:sub_005BB210_A3Q5_NpcMessage@0x005BB210` | ? | ? | ? | 1 |
| 217 | 1151 | Act III | b0 — the orb's completing operate (operator, party) when b4 is … | `fn:sub_005BB980_A3Q5_CompellingOrbOperate@0x005BB980` | ? | ? | ? | 1 |
| 218 | 1152 | Act III | G b13 — Cain message (reporter has b13), first join, the last … | `fn:sub_005BBC00_A3Q5_CouncilDeath@0x005BBC00` | ? | ? | ? | 1 |
| 219 | 1154 | Act III | Up to six council members (levels below 108) are recorded by the council hook; on … | – | ? | ? | ? | 1 |
| 220 | 1172 | Act III | b2–b9 — every player at the state pass: state 2 → … | `fn:sub_005BC020_A3Q6_SetProgressBits@0x005BC020` | ? | ? | ? | 1 |
| 221 | 1173 | Act III | b13, b0, b11 — e8 Mephisto: the killer if b0 clear; every player … | `fn:sub_005BC8B0_A3Q6_MephistoDeath@0x005BC8B0` | ? | ? | ? | 1 |
| 222 | 1174 | Act III | b14 — players with b0 and b11 clear | `fn:sub_005BC810_A3Q6_SetMissed@0x005BC810` | ? | ? | ? | 1 |
| 223 | 1175 | Act III | b11 — e11 any NPC message (the kill reported) | `fn:sub_005BC5A0_A3Q6_NpcMessage@0x005BC5A0` | ? | ? | ? | 1 |
| 224 | 1176 | Act III | G b13 — the death (always); first joiner with w22 b0, b11 … | `fn:sub_005BCC80_A3Q6_FirstJoin@0x005BCC80` | ? | ? | ? | 1 |
| 225 | 1178 | Act III | The Durance portal reads w22 b13 or b0 (quests/travel § F); | – | ? | ? | ? | 1 |
| 226 | 1182 | Act III | Creation reader. InitFn 52 spawns NPC 297 at the object while G w22 b13 is … | – | ? | ? | ? | 1 |
| 227 | 1197 | Act III | G b13 — e13: the first joiner has b0 (and then no … | `fn:sub_005BD2C0_A3Q7_FirstJoin@0x005BD2C0` | ? | ? | ? | 1 |
| 228 | 1217 | Act III | The 7-try branch (low & 1 = 1) was not reached. | `fn:sub_005BD390_A3Q7_AfterglowTimer@0x005BD390` | ? | ? | ? | 1 |
| 229 | 1218 | Act III | Word 32 has one write through the record functions: b0 at (SetSeen). Beyond the join's … | `0x005BD2AB` | ? | ? | ? | 1 |
| 230 | 1220 | Act III | The init writes + = 16 although the code uses word 32; only the quest … | – | ? | ? | ? | 1 |
| 231 | 1226 | Act III | Per-NPC introduction flags only (player data + + 4·difficulty), no record bit, no draw. | – | ? | ? | ? | 1 |
| 232 | 1257 | Act IV | b1, b13; steps clear — e8 the hooked monster: the killer, near credit, party … | `fn:sub_005B4020_A4Q1_IzualDeath@0x005B4020` | ? | ? | ? | 1 |
| 233 | 1258 | Act IV | b14 — the rest of the game | `fn:sub_005B4020_A4Q1_IzualDeath@0x005B4020` | ? | ? | ? | 1 |
| 234 | 1259 | Act IV | b2, b3, b4 — log state 2 → b2; 3 → b3 or … | `fn:sub_005B3940_A4Q1_StepBits@0x005B3940` | ? | ? | ? | 1 |
| 235 | 1260 | Act IV | b5 — e11 NPC 406 message | `fn:sub_005B39A0_A4Q1_NpcMessage@0x005B39A0` | ? | ? | ? | 1 |
| 236 | 1262 | Act IV | G b13 — the same message when the player also has b13 | `fn:sub_005B39A0_A4Q1_NpcMessage@0x005B39A0` | ? | ? | ? | 1 |
| 237 | 1264 | Act IV | The reward also adds 2 to stat 5 (UnitAddStat(p, 5, 2), ). The death arms … | `0x005B3B1F` | ? | ? | ? | 1 |
| 238 | 1281 | Act IV | b13, b0; steps clear — e8 Diablo (class 243): near credit (Diablo's death room), … | `fn:sub_005B4D20_A4Q2_Credit@0x005B4D20` | ? | ? | ? | 1 |
| 239 | 1282 | Act IV | b6, b7 — the same, classic games only (game+ = 0) | `fn:sub_005B4D20_A4Q2_Credit@0x005B4D20` | ? | ? | ? | 1 |
| 240 | 1283 | Act IV | b14 — set | `fn:sub_005B52E0_A4Q2_DiabloDeath@0x005B52E0` | ? | ? | ? | 1 |
| 241 | 1284 | Act IV | b2, b3, b4 — log state 2 / 3 | `fn:sub_005B4E40_A4Q2_StepBits@0x005B4E40` | ? | ? | ? | 1 |
| 242 | 1285 | Act IV | b7 / b6 — e11 NPC 367 message / NPC 246 message | `fn:sub_005B4670_A4Q2_NpcMessage@0x005B4670` | ? | ? | ? | 1 |
| 243 | 1286 | Act IV | b9 — ( x-talk4, h-talk4); the classic half | `0x005B4702` | ? | ? | ? | 1 |
| 244 | 1288 | Act IV | b9 — e13 and e14 in expansion: b9 set and w28 … | `fn:sub_005B5080_A4Q2_FirstJoin@0x005B5080` | ? | ? | ? | 1 |
| 245 | 1291 | Act IV | … DiabloSummon test , called by a seal operate, a seal boss's death and InitFn 55: | `fn:sub_005B5230_A4Q2_DiabloSummon@0x005B5230` | ? | ? | ? | 1 |
| 246 | 1296 | Act IV | W26b. SealOperate (OperateFn 52; 54–56 first store a boss point and create object 131): | `fn:sub_005B5630_A4Q2_SealOperate@0x005B5630` | ? | ? | ? | 1 |
| 247 | 1300 | Act IV | The Chaos Sanctuary gate (monsters/spawn): once the fifth seal is open and the three | – | ? | ? | ? | 1 |
| 248 | 1303 | Act IV | The end timer reads real time. Diablo's death re-arms the timer in end mode with … | – | ? | ? | ? | 1 |
| 249 | 1307 | Act IV | Classic lock-out: after Diablo dies in a classic game, the cube button and the trade … | – | ? | ? | ? | 1 |
| 250 | 1331 | Act IV | b13, b1; steps clear — the third strike: the striker, and every player in … | `fn:sub_005B5C10_A4Q3_ForgeOperate@0x005B5C10` | ? | ? | ? | 1 |
| 251 | 1332 | Act IV | b14 — set | `fn:sub_005B5B00_A4Q3_ForgeCredit@0x005B5B00` | ? | ? | ? | 1 |
| 252 | 1333 | Act IV | b2 / b5 / b3 — log state 2 → b5 with the soulstone given, … | `fn:sub_005B59C0_A4Q3_StepBits@0x005B59C0` | ? | ? | ? | 1 |
| 253 | 1336 | Act IV | The forge, its strikes and its draws are items/quest-drops § D. | – | ? | ? | ? | 1 |
| 254 | 1341 | Act IV | A dialogue selector for class 408 (reading w27 and w26); no quest script writes word … | – | ? | ? | ? | 1 |
| 255 | 1361 | Act V | b1, b13 — e8 superunique 42: near credit (b0 clear); party members … | `fn:sub_00587100_A5Q1_NearCredit@0x00587100` | ? | ? | ? | 1 |
| 256 | 1362 | Act V | b14 — set | `fn:sub_00587330_A5Q1_ShenkDeath@0x00587330` | ? | ? | ? | 1 |
| 257 | 1363 | Act V | G b13 — set | `fn:sub_00587330_A5Q1_ShenkDeath@0x00587330` | ? | ? | ? | 1 |
| 258 | 1364 | Act V | b2, b3, b4 — set | `fn:sub_00586DE0_A5Q1_StepBitsByState@0x00586DE0` | ? | ? | ? | 1 |
| 259 | 1366 | Act V | b0; b1 clear — the socket service done (items/quest-drops § F) | `fn:sub_005877C0_A5Q1_SocketDone@0x005877C0` | ? | ? | ? | 1 |
| 260 | 1368 | Act V | Larzuk is spawned once by object InitFn 70/71 (SpawnAtPos(x, y, 511, 1, 5, 0), oracle). … | – | ? | ? | ? | 1 |
| 261 | 1385 | Act V | b4 — a cage freed with the rescue not complete (prisoner … | `fn:sub_005888D0_A5Q2_CageFreed@0x005888D0` | ? | ? | ? | 1 |
| 262 | 1386 | Act V | b4 — every join (e13, e14) | `fn:sub_00588040_A5Q2_MonsterDeath@0x00588040` | ? | ? | ? | 1 |
| 263 | 1387 | Act V | b13, b1 — rescue complete: spawned = killed + rescued, all 3 … | `fn:sub_00587E60_A5Q2_PartyCredit@0x00587E60` | ? | ? | ? | 1 |
| 264 | 1388 | Act V | b5 / b6 / b7 — the same: rescued 15 → b5, 14 → b6, … | `fn:sub_00587E60_A5Q2_PartyCredit@0x00587E60` | ? | ? | ? | 1 |
| 265 | 1389 | Act V | b14 — rescue complete with fewer than 12 rescued, or more … | `fn:sub_00587F60_A5Q2_FailBit@0x00587F60` | ? | ? | ? | 1 |
| 266 | 1390 | Act V | b0; b1, steps clear — e11 NPC 515 message with b1 set, after at … | `fn:sub_00587B00_A5Q2_NpcMessage@0x00587B00` | ? | ? | ? | 1 |
| 267 | 1391 | Act V | b2, b3 — set | `fn:sub_005879D0_A5Q2_StepBits@0x005879D0` | ? | ? | ? | 1 |
| 268 | 1393 | Act V | Each cage (InitFn 62, object 473) spawns its 5 prisoners with up to 25 SpawnAtPos … | – | ? | ? | ? | 1 |
| 269 | 1412 | Act V | b13, b1 — OperateFn 67 on object 558 by a player with … | `fn:sub_0058ABC0_A5Q3_FrozenAnyaOperate@0x0058ABC0` | ? | ? | ? | 1 |
| 270 | 1414 | Act V | b14 — the rest of the game at the thaw; entering … | `fn:sub_00589D80_A5Q3_LevelChange@0x00589D80` | ? | ? | ? | 1 |
| 271 | 1416 | Act V | b2 — set | `fn:sub_00588EB0_A5Q3_StepBits@0x00588EB0` | ? | ? | ? | 1 |
| 272 | 1417 | Act V | b3 — e3 entering 114, or the old-level-109 branch (not reached) | `fn:sub_00589D80_A5Q3_LevelChange@0x00589D80` | ? | ? | ? | 1 |
| 273 | 1418 | Act V | b8 — e11 NPC 513 message with b1 set, b0 clear: … | `fn:sub_00589580_A5Q3_NpcMessage@0x00589580` | ? | ? | ? | 1 |
| 274 | 1421 | Act V | b0; b1 clear — the NPC 513 talk coming second (b9 already set) | `fn:sub_00589580_A5Q3_NpcMessage@0x00589580` | ? | ? | ? | 1 |
| 275 | 1425 | Act V | … — e11 NPC 512 message : for the clvl branch of the table choice ; | `fn:sub_00589580_A5Q3_NpcMessage@0x00589580` | ? | ? | ? | 1 |
| 276 | 1435 | Act V | The scroll's bonus. counts the difficulty records (Normal, Nightmare, Hell) whose word 37 has b7 | `0x0058A0A0` | ? | ? | ? | 1 |
| 277 | 1438 | Act V | Creation reader. InitFn 69 (object 462) spawns Nihlathak's superunique only while the quest's private | – | ? | ? | ? | 1 |
| 278 | 1441 | Act V | A later joiner with w37 b0, b1, b6 clear while quest 34 is active and … | – | ? | ? | ? | 1 |
| 279 | 1458 | Act V | b1, b13 — e8 Nihlathak (superunique 60): near credit with w37 b0 … | `fn:sub_0058B4A0_A5Q4_NearCredit@0x0058B4A0` | ? | ? | ? | 1 |
| 280 | 1459 | Act V | G b13 — the same death | `fn:sub_0058B7A0_A5Q4_NihlathakDeath@0x0058B7A0` | ? | ? | ? | 1 |
| 281 | 1460 | Act V | b14 — the rest at the kill; a joiner as in … | `fn:sub_0058B7A0_A5Q4_NihlathakDeath@0x0058B7A0` | ? | ? | ? | 1 |
| 282 | 1461 | Act V | b2, b3 — set | `fn:sub_0058AEA0_A5Q4_StepBits@0x0058AEA0` | ? | ? | ? | 1 |
| 283 | 1462 | Act V | b4 — e11 NPC 512 message | `fn:sub_0058B1C0_A5Q4_NpcMessage@0x0058B1C0` | ? | ? | ? | 1 |
| 284 | 1463 | Act V | b0; b1 clear — the personalise service done | `fn:sub_0058BC00_A5Q4_PersonalizeDone@0x0058BC00` | ? | ? | ? | 1 |
| 285 | 1465 | Act V | The red portal to level 121: PortalObjectCreate(room, x + 10, y + 5, 121, 0, … | – | ? | ? | ? | 1 |
| 286 | 1484 | Act V | b0, b13 — e8 the third Ancient (540–542): the killer, each player … | `fn:sub_0058C9A0_A5Q5_AncientDeath@0x0058C9A0` | ? | ? | ? | 1 |
| 287 | 1485 | Act V | b14 — set | `fn:sub_0058C9A0_A5Q5_AncientDeath@0x0058C9A0` | ? | ? | ? | 1 |
| 288 | 1486 | Act V | b2 / b3 — log state 2 / 3, players with clvl ≥ … | `fn:sub_0058C210_A5Q5_StepBitsByLevel@0x0058C210` | ? | ? | ? | 1 |
| 289 | 1487 | Act V | b4 — e11 message (OperateFn 69, object 561, with b0 set … | `fn:sub_0058C290_A5Q5_NpcMessage@0x0058C290` | ? | ? | ? | 1 |
| 290 | 1488 | Act V | b5–b9 — e11 from NPC 511 → b5, 520 → b6, … | `fn:sub_0058C290_A5Q5_NpcMessage@0x0058C290` | ? | ? | ? | 1 |
| 291 | 1493 | Act V | Experience in Nightmare and Hell: 20 000 000 and 40 000 000, under the same … | – | ? | ? | ? | 1 |
| 292 | 1495 | Act V | Arming and resets. The altar (OperateFn 65) with no town portal on 120 and all … | – | ? | ? | ? | 1 |
| 293 | 1505 | Act V | The Worldstone Keep door (OperateFn 66) refuses a player with b0 and b1 clear, and … | – | ? | ? | ? | 1 |
| 294 | 1522 | Act V | b13, b0 — e8 Baal: each player on level 132 with b0, … | `fn:sub_0058DD30_A5Q6_Credit@0x0058DD30` | ? | ? | ? | 1 |
| 295 | 1523 | Act V | b14 — set | `fn:sub_0058DF20_A5Q6_BaalDeath@0x0058DF20` | ? | ? | ? | 1 |
| 296 | 1524 | Act V | b2 / b3 — log state 2 / 3, players in Act V | `fn:sub_0058D8B0_A5Q6_StepBitsByState@0x0058D8B0` | ? | ? | ? | 1 |
| 297 | 1527 | Act V | b7, b5, b8 — e11 messages , , by the same table | `fn:sub_0058D940_A5Q6_NpcMessage@0x0058D940` | ? | ? | ? | 1 |
| 298 | 1528 | Act V | b10 — the last portal (object 565) used by a player … | `fn:sub_0058E740_A5Q6_LastPortalOperate@0x0058E740` | ? | ? | ? | 1 |
| 299 | 1530 | Act V | Baal's death also calls MissileCreateAt(0, 1, 625, x, y) (missile baalfx control, W4c); its do-function … | – | ? | ? | ? | 1 |
| 300 | 1535 | Act V | W40. ZooInit — InitFn 79 (object 567), once per game (private +): | `fn:sub_0058E830_A5Q6_ZooInit@0x0058E830` | ? | ? | ? | 1 |
| 301 | 1543 | Act V | Every Baal credit, and the first join of a player with b0 or b15, raises … | – | ? | ? | ? | 1 |
| 302 | 1546 | Act V | The Zoo does not run on stock data: no DS1 places object 567 (2 274 … | – | ? | ? | ? | 1 |
| 303 | 1550 | Act V | The Worldstone Chamber portal (objects 563, 569) moves a player from 131 to 132 only … | – | ? | ? | ? | 1 |
| 304 | 1553 | Act V | The join of a player with w40 b0 sets b10 at the first-join callback; the … | – | ? | ? | ? | 1 |
| 305 | 1559 | Act V | Per-NPC introduction flags for NPCs 512–520 only, no record bit; messages also move quest 31 … | – | ? | ? | ? | 1 |
| 306 | 1566 | Warp and portal gates | warp into 73 — the object is active with that byte 0 | `0x0059DB20` | ? | ? | ? | 1 |
| 307 | 1567 | Warp and portal gates | warp into 100 — the orb is whole and the player is not … | `fn:sub_005BBFA0_A3Q5_DuranceWarpGate@0x005BBFA0` | ? | ? | ? | 1 |
| 308 | 1568 | Warp and portal gates | warp into 118 or 128 from 120 — quest 35 is active and not done in this … | `fn:sub_0058D090_A5Q5_SummitWarpBlocked@0x0058D090` | ? | ? | ? | 1 |
| 309 | 1569 | Warp and portal gates | warp into 132 — Baal has not opened the chamber | `fn:sub_0058E640_A5Q6_ChamberWarpBlocked@0x0058E640` | ? | ? | ? | 1 |
| 310 | 1570 | Warp and portal gates | another player's town portal — the user's word bit 0 is clear | `fn:OBJOP_Portal@0x00584870` | ? | ? | ? | 1 |
| 311 | 1571 | Warp and portal gates | Durance portal — w22 b13, b0 | `fn:sub_00584750_DurancePortalOperate@0x00584750` | ? | ? | ? | 1 |
| 312 | 1572 | Warp and portal gates | NPC act travel — w6, w14, w26 bit 0 | `fn:NPC_MenuAction@0x00579D60` | ? | ? | ? | 1 |
| 313 | 1575 | Warp and portal gates | The orb-broken byte is set game-wide by the orb's completing operate or by a first … | – | ? | ? | ? | 1 |
| 314 | 1577 | Warp and portal gates | The waypoint menu and waypoint travel read no quest word on the server; level 74's … | – | ? | ? | ? | 1 |
| 315 | 1586 | Creation-path readers | items/quest-drops — the killer's TCQuestId word bits 15, 1 and TCQuestCP, … | `fn:MONSTER_DropItems@0x005A6600` | ? | ? | ? | 1 |
| 316 | 1587 | Creation-path readers | objects — G w16 b13, G w22 b13, quest private state | `data:g_ObjInitFns@0x00731BC0` | ? | ? | ? | 1 |
| 317 | 1588 | Creation-path readers | monsters/spawn — quest 23's private + (word 26) | `fn:sub_005B5210_DiabloQuestFlag@0x005B5210` | ? | ? | ? | 1 |
| 318 | 1589 | Creation-path readers | monsters/special — the hook lists (§ B) | `fn:QUESTS_HookMonster@0x005436B0` | ? | ? | ? | 1 |
| 319 | 1590 | Creation-path readers | rng/seeds — the true tomb: word 14's level-change step, the join's … | `0x0061AEB0` | ? | ? | ? | 1 |
| 320 | 1591 | Creation-path readers | items/cube — w26 b0 (classic) or w40 b0 (expansion), G w4 … | `fn:CUBE_CowPortalOpen@0x00594140` | ? | ? | ? | 1 |
| 321 | 1592 | Creation-path readers | drlg/collision — no quest bit gates level 74 or portal 298 | `fn:sub_0059BA40_A2Q4_ArcanePortalInit@0x0059BA40` | ? | ? | ? | 1 |
| 322 | 1603 | Outputs |  | `fn:QUESTS_GetSeed@0x005438B0` | ? | ? | ? | 1 |
