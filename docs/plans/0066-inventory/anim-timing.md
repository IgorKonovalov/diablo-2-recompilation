# Plan 0066 inventory: anim/timing

- **Spec:** [anim/timing](../../specs/anim/timing.md), read at `main` `b5999f5e`.
- **Front matter `I`:** 134; the *Count* column sums to 134.
- Classes, batches and conventions as in [the inventory README](README.md#conventions).

| # | Line | Section | Claim (excerpt) | Anchor | Class | Route or reason | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | 43 | Entry points | A unit's mode changes — → | `fn:UNIT_SetMode@0x00624690` | ? | ? | ? | 1 |
| 2 | 44 | Entry points | A server player or monster mode starts | `fn:SUNIT_AnimInit@0x005533D0` | ? | ? | ? | 1 |
| 3 | 47 | Entry points | Each game frame, the unit event lists run | `fn:sub_005414D0_GameRunUnitEvents@0x005414D0` | ? | ? | ? | 1 |
| 4 | 50 | Entry points | A player's mode ends | `fn:sub_00581020_PlayerModeEnd@0x00581020` | ? | ? | ? | 1 |
| 5 | 51 | Entry points | A monster's mode command | `fn:sub_005A7C20_MonSetMode@0x005A7C20` | ? | ? | ? | 1 |
| 6 | 52 | Entry points | A hit reaches the defender's mode | `fn:COMBAT_GetHit@0x0057CEE0` | ? | ? | ? | 1 |
| 7 | 54 | Entry points | A player mode request is tested | `fn:sub_0057EDD0_PlrModeLeaveOk@0x0057EDD0` | ? | ? | ? | 1 |
| 8 | 97 | Inputs and oracles | A catalogue function's reschedule (§ E3), its queued kinds … — outputs taken as given (plan 0046's catalogue), not compared | `fn:sub_00553DC0_RescheduleAt@0x00553DC0` | ? | ? | ? | 1 |
| 9 | 104 | Constants | fallback record — 2 048 frames, speed 256, no event byte | `fn:ANIMDATA_Load@0x0066A770` | ? | ? | ? | 1 |
| 10 | 105 | Constants | event-byte scan bound — frames < (144) | `fn:SUNIT_ScheduleModeEvents@0x005539B0` | ? | ? | ? | 1 |
| 11 | 107 | Constants | attack and default factor clamp — the attack's 175 ; the floor 15 | `fn:UNIT_AnimSetRate@0x00623F50` | ? | ? | ? | 1 |
| 12 | 111 | Constants | PlrModeEndPending slack — 5 frames | `fn:sub_0057ED70_PlrModeEndPending@0x0057ED70` | ? | ? | ? | 1 |
| 13 | 128 | A. The two clocks and the event kinds | Two clocks. A player's attack, cast, skill, get-hit, block, death and sequence modes, and a … | – | ? | ? | ? | 1 |
| 14 | 136 | A. The two clocks and the event kinds | A player's walk, run, town walk and knockback run an every-frame event too, which steps … | – | ? | ? | ? | 1 |
| 15 | 141 | A. The two clocks and the event kinds | Event kinds (ADR-0014): mode start (inputs the mode, type, class, transform states, used skill, weapon | – | ? | ? | ? | 1 |
| 16 | 154 | B. The animation record | … ANIMDATA_Find(name) or, when none, the fallback record (2 048 frames, speed 256, no event) ; | – | ? | ? | ? | 1 |
| 17 | 156 | B. The animation record | B2. ANIMDATA_Find(name): | `fn:ANIMDATA_Find@0x0066A8F0` | ? | ? | ? | 1 |
| 18 | 170 | B. The animation record | The Barbarian's dual classes 1js (1hs + 1ht), 1jt (1ht + 1ht) and 1st (1ht … | – | ? | ? | ? | 1 |
| 19 | 174 | B. The animation record | Duplicate names. Of two records with one name (29 names in animdata.d2, 9 with different … | – | ? | ? | ? | 1 |
| 20 | 183 | B. The animation record | The fallback's steps, read from the code: down 5, 7 → 4; 6 → 3; … | – | ? | ? | ? | 1 |
| 21 | 187 | B. The animation record | A record's frames gives + = frames << 8 at every non-sequence start; its speed … | – | ? | ? | ? | 1 |
| 22 | 193 | C. The mode start | C1. UNIT_SetMode(unit, mode) → bool: | `fn:UNIT_SetMode@0x00624690` | ? | ? | ? | 1 |
| 23 | 199 | C. The mode start | C2. UNIT_AnimInit(unit): | `fn:UNIT_AnimInit@0x00624390` | ? | ? | ? | 1 |
| 24 | 219 | C. The mode start | C3. SUNIT_AnimInit(unit): | `fn:SUNIT_AnimInit@0x005533D0` | ? | ? | ? | 1 |
| 25 | 228 | C. The mode start | In UNIT_SetMode, a request for the mode the unit is already in runs no UNIT_AnimInit … | – | ? | ? | ? | 1 |
| 26 | 236 | C. The mode start | one object was logged (7 pairs, each with another draw between). | run:2026-10-27-anim | ? | ? | ? | 1 |
| 27 | 237 | C. The mode start | An object's server frame fields come from the Objects row, never from its animdata.d2 record … | – | ? | ? | ? | 1 |
| 28 | 243 | C. The mode start | The rate no server code reads back for an object, a missile or an item … | – | ? | ? | ? | 1 |
| 29 | 245 | C. The mode start | A scheduled mode starts from + = 0 whatever C2 set; the schedule reads the … | – | ? | ? | ? | 1 |
| 30 | 253 | D. The start frame | the S3/S4 half: its cells are 0 | – | ? | ? | ? | 1 |
| 31 | 263 | D. The start frame | The table's non-zero cells are those two classes' only: 1 for hand to hand, 2 … | – | ? | ? | ? | 1 |
| 32 | 286 | E. The schedule | no logged rate is 0 | – | ? | ? | ? | 1 |
| 33 | 290 | E. The schedule | the bound: no stock record with an event reaches it | – | ? | ? | ? | 1 |
| 34 | 296 | E. The schedule | if t = T: t ← t + 1 ; | – | ? | ? | ? | 1 |
| 35 | 312 | E. The schedule | Part 1's 124 such dispatches (110 kind 0, 14 kind 1), | `fn:UNIT_CancelEvents@0x00540E60` | ? | ? | ? | 1 |
| 36 | 319 | E. The schedule | The event frames, derived from E1's loop: with N = ⌈256 (F − S) / … | – | ? | ? | ? | 1 |
| 37 | 324 | E. The schedule | On stock data a player never reaches the no-event case (the start frames 1 and … | – | ? | ? | ? | 1 |
| 38 | 328 | E. The schedule | Reschedules (catalogue). Three functions cancel kinds 0 and 1 and rebuild the list from an … | – | ? | ? | ? | 1 |
| 39 | 335 | E. The schedule | Callers. The player starts for get-hit, block, the skill modes and death, and MonSetMode for … | – | ? | ? | ? | 1 |
| 40 | 351 | F. The per-frame advance (every-frame monsters) | a start frame ≠ 0: no case | – | ? | ? | ? | 1 |
| 41 | 355 | F. The per-frame advance (every-frame monsters) | F2. UNIT_AnimAtEnd(unit) → bool: | `fn:UNIT_AnimAtEnd@0x006217C0` | ? | ? | ? | 1 |
| 42 | 366 | F. The per-frame advance (every-frame monsters) | The 0 is C3's + ← 0, which MonSetMode reaches whether or not UNIT_SetMode saw … | – | ? | ? | ? | 1 |
| 43 | 368 | F. The per-frame advance (every-frame monsters) | Below a rate of the frame the unit stood on is scanned again, so one … | – | ? | ? | ? | 1 |
| 44 | 374 | F. The per-frame advance (every-frame monsters) | The every-frame monster frame functions call F2 after advancing; the length + stays the start's, … | – | ? | ? | ? | 1 |
| 45 | 380 | G. Sequences | G1. Which sequence record: | `fn:sub_00663310_UnitSeqRecord@0x00663310` | ? | ? | ? | 1 |
| 46 | 387 | G. Sequences | G2. UNIT_SeqInit(unit): | `fn:UNIT_SeqInit@0x00621260` | ? | ? | ? | 1 |
| 47 | 401 | G. Sequences | A sequence frame is 6 bytes (mode, frame, direction, event, after a u16 sequence id); … | – | ? | ? | ? | 1 |
| 48 | 407 | G. Sequences | In two advances the byte was 0 where the rows give 1: read as the … | – | ? | ? | ? | 1 |
| 49 | 410 | G. Sequences | The event of a sequence is the sequence row's, never the animdata.d2 byte of the … | – | ? | ? | ? | 1 |
| 50 | 414 | G. Sequences | A player's sequence (mode 18) is scheduled once from its step + and length + … | – | ? | ? | ? | 1 |
| 51 | 430 | H. The event queue and the frame order | UnitQueueEvent(game, unit, kind, frame, a, b) takes kinds below 15, raises a frame at or … | – | ? | ? | ? | 1 |
| 52 | 436 | H. The event queue and the frame order |  | `fn:sub_005417D0_UnitQueueEvent@0x005417D0` | ? | ? | ? | 1 |
| 53 | 438 | H. The event queue and the frame order | Each game frame runs the missile, player, monster, object and item lists in that order, … | – | ? | ? | ? | 1 |
| 54 | 448 | H. The event queue and the frame order | Dispatch. A player record goes to g_PlayerEventFuncskind: kind 0 runs the mode's frame | – | ? | ? | ? | 1 |
| 55 | 455 | H. The event queue and the frame order | With no mode record or no function in it, the monster handlers call : clear … | `0x005A7B30` | ? | ? | ? | 1 |
| 56 | 486 | I1. Players | 1 NU, 5 TN — PlrModeStartNeutral (5 in a town room) | `fn:sub_0057F020_PlrModeStartNeutral@0x0057F020` | ? | ? | ? | 1 |
| 57 | 487 | I1. Players | 2 WL, 3 RN, 6 TW, 19 KB — neutral on arrival | `fn:sub_0057F090_PlrModeStartMove@0x0057F090` | ? | ? | ? | 1 |
| 58 | 488 | I1. Players | 4 GH, 9 BL — PlrModeStartGetHit, PlrModeStartBlock | `fn:sub_0057FE30_PlrModeStartGetHit@0x0057FE30` | ? | ? | ? | 1 |
| 59 | 489 | I1. Players | 7, 8, 10–16, 18 — PlrModeStartSkillXY / …Unit | `fn:sub_0057FE90_PlrModeStartSkillXY@0x0057FE90` | ? | ? | ? | 1 |
| 60 | 490 | I1. Players | 0 DT — PlayerDeath | `fn:sub_00580EC0_PlayerDeath@0x00580EC0` | ? | ? | ? | 1 |
| 61 | 494 | I1. Players | PlayerModeEnd (kind 1, or a frame function's 2): for modes 7, 8, 11 or a … | – | ? | ? | ? | 1 |
| 62 | 497 | I1. Players | PlrModeStartMove: a run with stamina 0 becomes a walk (reached 81 times in Phase 2 … | – | ? | ? | ? | 1 |
| 63 | 504 | I1. Players | PlrModeStartGetHit and PlrModeStartBlock: SUNIT_SetMode(4 or 9), SUNIT_AnimInit, clear the used | – | ? | ? | ? | 1 |
| 64 | 529 | I2. Monsters | 0 — mode 12, event 13; SplEndDeath | `data:g_MonModeRecords@0x006E2260` | ? | ? | ? | 1 |
| 65 | 530 | I2. Monsters | 1 — NU | `data:g_MonModeRecords@0x006E2260` | ? | ? | ? | 1 |
| 66 | 531 | I2. Monsters | 2, 15 — trails, step; arrival → generic end | `data:g_MonModeRecords@0x006E2260` | ? | ? | ? | 1 |
| 67 | 532 | I2. Monsters | 3, 6 — GH, BL | `data:g_MonModeRecords@0x006E2260` | ? | ? | ? | 1 |
| 68 | 533 | I2. Monsters | 4, 5, 7, 8, 9 — A1, A2, SC, S1, S2 | `data:g_MonModeRecords@0x006E2260` | ? | ? | ? | 1 |
| 69 | 534 | I2. Monsters | 10, 11 — S3: step, advance, at the end mode 11 | `data:g_MonModeRecords@0x006E2260` | ? | ? | ? | 1 |
| 70 | 535 | I2. Monsters | 12 — DD | `data:g_MonModeRecords@0x006E2260` | ? | ? | ? | 1 |
| 71 | 536 | I2. Monsters | 13 — step, advance; at the end MonKnockbackEnd | `data:g_MonModeRecords@0x006E2260` | ? | ? | ? | 1 |
| 72 | 537 | I2. Monsters | 14 — SQ | `data:g_MonModeRecords@0x006E2260` | ? | ? | ? | 1 |
| 73 | 541 | I2. Monsters | MonSetMode(game, cmd, flag): fatal under state 54; for a mode other than 3, the path … | – | ? | ? | ? | 1 |
| 74 | 546 | I2. Monsters | Class overrides (MonStats SplGetModeChart set, all ten classes on stock data): 243, 333 and 705 … | – | ? | ? | ? | 1 |
| 75 | 550 | I2. Monsters | MonAttackFrame. With no used skill, a scheduled mode strikes (MON_MeleeHit, COMBAT_DeliverQueued) on | – | ? | ? | ? | 1 |
| 76 | 554 | I2. Monsters | MonModeEndGeneric (GH, BL, A1–S2, SQ; WL and RN on arrival): a SplEndGeneric base class in … | – | ? | ? | ? | 1 |
| 77 | 561 | I2. Monsters | Its branches: path stop; when MonModeAllowed(3) refuses, the AI event at T + 1; base | run:2026-10-27-anim | ? | ? | ? | 1 |
| 78 | 564 | I2. Monsters | MonModeStartNeutral: SUNIT_SetMode(1); when the next AI event is not later than now, re-queue it at … | – | ? | ? | ? | 1 |
| 79 | 579 | I3. Objects | After a chest's drops OBJOP_Chest sets mode 1 (when Mode1 is set) and queues object … | – | ? | ? | ? | 1 |
| 80 | 617 | J. The rate (UNIT_AnimSetRate) | … ? 100 : 50); q ← max(1, (spd × X) mod 2³² ÷ 100) ; | – | ? | ? | ? | 1 |
| 81 | 623 | J. The rate (UNIT_AnimSetRate) | if no path: return ; + kept; | – | ? | ? | ? | 1 |
| 82 | 624 | J. The rate (UNIT_AnimSetRate) | the floor 25: no case | – | ? | ? | ? | 1 |
| 83 | 632 | J. The rate (UNIT_AnimSetRate) | the floor 15: no case | – | ? | ? | ? | 1 |
| 84 | 637 | J. The rate (UNIT_AnimSetRate) | … ? 0 : min(q, ); + ← (i16) q ; signed test, then the cap; | – | ? | ? | ? | 1 |
| 85 | 642 | J. The rate (UNIT_AnimSetRate) | . For s ≥ 0 the bonus rises from 0 toward | – | ? | ? | ? | 1 |
| 86 | 644 | J. The rate (UNIT_AnimSetRate) | For −k < s < 0 the bonus is negative and unbounded below; s = … | – | ? | ? | ? | 1 |
| 87 | 653 | J. The rate (UNIT_AnimSetRate) | The moving floor 25, the attack floor 15, block's floor 1 and the cap are … | – | ? | ? | ? | 1 |
| 88 | 657 | J. The rate (UNIT_AnimSetRate) | The record is set again at every call, so a mid-mode call can change + … | – | ? | ? | ? | 1 |
| 89 | 660 | J. The rate (UNIT_AnimSetRate) | Which branch a mode takes is the mode-class tables (players; monsters below class 410; from … | – | ? | ? | ? | 1 |
| 90 | 676 | J. The rate (UNIT_AnimSetRate) | from the code: | `0x00624211` | ? | ? | ? | 1 |
| 91 | 684 | J. The rate (UNIT_AnimSetRate) | HumanAttackFrames takes speed 45 when the name has no record, and a zero divisor faults. | – | ? | ? | ? | 1 |
| 92 | 686 | J. The rate (UNIT_AnimSetRate) | Where the terms come from (to the depth the rate needs): stats 67, 68, 69 … | – | ? | ? | ? | 1 |
| 93 | 694 | J. The rate (UNIT_AnimSetRate) | Who recomputes it. 31 call sites, 24 server: the mode starts, equip, auras, curses, chill … | – | ? | ? | ? | 1 |
| 94 | 700 | J. The rate (UNIT_AnimSetRate) | rate call comes after (fire). | `fn:SUNIT_ScheduleModeEvents@0x005539B0` | ? | ? | ? | 1 |
| 95 | 708 | K. Breakpoints (derived) | : tools/anim_rates.py bp checks them against E1's loop and brute | – | ? | ? | ? | 1 |
| 96 | 721 | K. Breakpoints (derived) | (derived from E1 and E2, , all of K1) | `fn:SUNIT_ScheduleModeEvents@0x005539B0` | ? | ? | ? | 1 |
| 97 | 725 | K. Breakpoints (derived) | (derived, , all of K2) | `fn:UNIT_AnimSetRate@0x00623F50` | ? | ? | ? | 1 |
| 98 | 730 | K. Breakpoints (derived) | (derived from J1, , all of K3) | `fn:sub_00621740_AnimRateBonus@0x00621740` | ? | ? | ? | 1 |
| 99 | 736 | K. Breakpoints (derived) | Block's max(1, …) and the moving and knockback branches (which do not divide spd) are … | – | ? | ? | ? | 1 |
| 100 | 739 | K. Breakpoints (derived) | A gain shows only when it lowers ⌈256 (F − S) / r⌉: between two … | – | ? | ? | ? | 1 |
| 101 | 741 | K. Breakpoints (derived) | Illustrations from stock records (p50b-bp.txt, the tool's model, not a run): SOSCHTH (14 frames, speed | – | ? | ? | ? | 1 |
| 102 | 758 | K. Breakpoints (derived) | Recorded short (not a mismatch): three FHR rates of 30 for the Barbarian (it has … | – | ? | ? | ? | 1 |
| 103 | 769 | L. The frame events as gates | PlrModeSkillFrame runs the used skill's do on an event of code 1 or 2 while … | run:2026-10-27-anim | ? | ? | ? | 1 |
| 104 | 775 | L. The frame events as gates | The attack's delivery is on the do frame: a player's normal attack is skill 0's … | – | ? | ? | ? | 1 |
| 105 | 794 | L. The frame events as gates | The client's own rule for when it sends a held request is not read (ADR-0005: … | – | ? | ? | ? | 1 |
| 106 | 798 | L. The frame events as gates | Get-hit and block are never left before T + n: in the run no get-hit … | – | ? | ? | ? | 1 |
| 107 | 805 | M. Hit recovery, the block, the get-hit roll, the mode tests | M1. COMBAT_GetHit(defender, packet; attacker), the timing part: | `fn:COMBAT_GetHit@0x0057CEE0` | ? | ? | ? | 1 |
| 108 | 826 | M. Hit recovery, the block, the get-hit roll, the mode tests | 32 and 64 not separated from 16 | – | ? | ? | ? | 1 |
| 109 | 830 | M. Hit recovery, the block, the get-hit roll, the mode tests | if def is a monster and not MonModeAllowed(def.class, 3): return 1 ; | – | ? | ? | ? | 1 |
| 110 | 836 | M. Hit recovery, the block, the get-hit roll, the mode tests | Stat 95 is written only when the test passes, whether or not | `fn:COMBAT_GetHit@0x0057CEE0` | ? | ? | ? | 1 |
| 111 | 841 | M. Hit recovery, the block, the get-hit roll, the mode tests | Why Blood Raven's knockback commands end in neutral at once | `fn:COMBAT_GetHit@0x0057CEE0` | ? | ? | ? | 1 |
| 112 | 853 | M. Hit recovery, the block, the get-hit roll, the mode tests | The divisors 32 (19 calls) and 64 (4) are met but not shown to separate … | – | ? | ? | ? | 1 |
| 113 | 856 | M. Hit recovery, the block, the get-hit roll, the mode tests | Hit recovery is the get-hit mode's schedule: the GH record at the get-hit rate ⌊spd … | – | ? | ? | ? | 1 |
| 114 | 866 | M. Hit recovery, the block, the get-hit roll, the mode tests | PlrModeLeaveOk(unit, requested) → bool: | `fn:sub_0057EDD0_PlrModeLeaveOk@0x0057EDD0` | ? | ? | ? | 1 |
| 115 | 874 | M. Hit recovery, the block, the get-hit roll, the mode tests | E ; | `fn:sub_0057ED70_PlrModeEndPending@0x0057ED70` | ? | ? | ? | 1 |
| 116 | 875 | M. Hit recovery, the block, the get-hit roll, the mode tests | PlayerModeAllowed(requested, 1, skill) → bool: | `fn:sub_0057EEC0_PlayerModeAllowed@0x0057EEC0` | ? | ? | ? | 1 |
| 117 | 887 | M. Hit recovery, the block, the get-hit roll, the mode tests | PlrModeLeaveOk returned 1 at all 5 633 | `fn:sub_0057ED70_PlrModeEndPending@0x0057ED70` | ? | ? | ? | 1 |
| 118 | 892 | M. Hit recovery, the block, the get-hit roll, the mode tests | So the Concentration draw is read from the | `fn:sub_0057EEC0_PlayerModeAllowed@0x0057EEC0` | ? | ? | ? | 1 |
| 119 | 896 | M. Hit recovery, the block, the get-hit roll, the mode tests | Stun. COMBAT_ApplyStun sets state 21 until frame + length (capped at 250, 13 for a … | – | ? | ? | ? | 1 |
| 120 | 901 | M. Hit recovery, the block, the get-hit roll, the mode tests | The hit class is the packet's +. Melee delivery fills its low nibble when + … | – | ? | ? | ? | 1 |
| 121 | 927 | N. Draws and seeds per event kind | Over the 171 functions under the animation machine's 29 roots (three indirect stat-list callbacks | – | ? | ? | ? | 1 |
| 122 | 930 | N. Draws and seeds per event kind | On a hit, in delivery order: the durability draws (items/economy § H), | – | ? | ? | ? | 1 |
| 123 | 936 | N. Draws and seeds per event kind | N3. The GetHitRoll draws chain on the defender's seed (M2, 102 chained pairs). | run:2026-10-27-anim | ? | ? | ? | 1 |
| 124 | 945 | Outputs | The next mode at each end (§ I), the get-hit, block and knockback commands of … | – | ? | ? | ? | 1 |
| 125 | 953 | Worked example | A Sorceress cast at FCR 20 (SOSCHTH: 14 frames, speed 256, event byte 1 at … | – | ? | ? | ? | 1 |
| 126 | 958 | Worked example | A Paladin get-hit (PAGHHTH: 5 frames, speed 256). FHR 0: X = 50, r = … | – | ? | ? | ? | 1 |
| 127 | 961 | Worked example | An Amazon's one-handed swing (AMA11HS: 16 frames, start frame 2, event at frame 10) at … | – | ? | ? | ? | 1 |
| 128 | 971 | Reimplementation notes | Two rate calls per server start. UNIT_AnimInit calls the rate before it writes the new … | – | ? | ? | ? | 1 |
| 129 | 974 | Reimplementation notes | Unsigned divides. Cast, get-hit, block, attack and default take (spd × X) mod 2³² ÷ … | – | ? | ? | ? | 1 |
| 130 | 977 | Reimplementation notes | The record is the display's. A shapeshifted player takes the form's record, start frame and … | – | ? | ? | ? | 1 |
| 131 | 979 | Reimplementation notes | A monster's frame function result is ignored. An every-frame monster attack or skill mode with … | – | ? | ? | ? | 1 |
| 132 | 981 | Reimplementation notes | An object's opened mode is set without an animation start: no start draw at the … | – | ? | ? | ? | 1 |
| 133 | 983 | Reimplementation notes | A frozen monster loses its scheduled events (dropped and freed), its mode end among them. | – | ? | ? | ? | 1 |
| 134 | 1030 | Open questions | … played in part 3; part 2's record reports no outcome for them). Their statements stay | – | ? | ? | ? | 1 |
