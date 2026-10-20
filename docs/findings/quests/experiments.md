# Quests experiments

Runtime records for [quests/0001](0001-progression.md) and [quests/0002](0002-travel.md). Phase 2 of plan 0042 adds them here.

## run:2026-10-17-quests

- **Question:** (plan 0042 Phase 2) Do the quest dispatch, the join, the quest-seed and player-seed draws of
  [quests/0001](0001-progression.md) and the travel events of [quests/0002](0002-travel.md) (waypoints, NPC act
  changes, town portals, warps, placement, the real-time gates, the level-seed step per point type) reproduce a
  scripted run with 0 mismatches, seeds logged at the entry and exit of every event kind?
- **Setup:** the ADR-0003 harness on **slot 1** (display `:8`, expansion) and **slot 2** (display `:9`, classic and
  Nightmare), agent-driven play (no owner play), one client. Saves: Phase 0's (`workspace/runtime/quest-saves-p42/`,
  `tools/quest_saves.py build`; Phase 1's `quest-w9lost` = `QuestBookLost` and `quest-w39summit` = `QuestSummit`
  among them) and one new classic recipe `tools/d2s_recipes/quest-tpc.json` (`QuestPortalC`: `questfreshc` plus a
  20-charge `tbk` at inventory 0,0; built with `tools/d2s.py build workspace/merged/data/global/excel … 
  workspace/runtime/monspawn-chars/cls/smpsor.d2s`, `fa2c8ba3…`, classic status byte). Each slot's empty saves
  directory set aside as tag `p42h`, restored and set aside again before each launch, the save installed with
  `d2run.py --install p42h`.
  - **Logger** `tools/gdb/quest-state.gdb` (`c54d695f…`): `pilot.py` (`1ad48a4c…`), `vendors.py` (`eddbff8c…`, the
    NPC and object lines the driver walks by), plan 0032's `quests.py` (`7f07110b…`: `QI1` the quest seed and game
    record, `QS`/`QC` every quest-bit write) and `questev.py` (new; tags in its header; final `14598086…`). Three
    revisions ran in recorded sessions: A (x-lut, c-tp): dispatch exits at the `ret` (0x00543974, 0x00543A05), the level points in `LPL`, without the portal room-update line and with the portal-create arguments one slot off (unused by the checker; the older-log path of the portal check derives the population draws from the partner's seed); B (nm-lut, x-act): `80e756f` (the room-update line); C (the rest): `db75787` and later (the summit door bracket, `14598086…`).
  - **Checker** `tools/quests.py check` (`475b298b…`, new; rules in its docstring; tests `tools/test_quests.py`,
    7 tests), tables from `workspace/merged/data/global/excel`, `g_QuestDescs` and the point-type groups
    (`0x006EED88`) read from the pinned image.
  - **Driver** `tools/quest_sessions.py` (`7fa04594…`): per session the actions listed below (`talk`: walk to and click
    an NPC with no menu, Escape; `menu`: `d2pilot.py npc NAME --menu-line L`; `tp`: open the book, take the field end,
    come back through the town end; `wp`: `d2pilot.py wpchain`; `explore`/`walk`; `warp`/`clickwarp`: take a warp;
    `objop`; `qlog`: the quest log opened, the act tabs clicked). `d2pilot.py` gained the `warriv2`, `meshif`,
    `meshif2` menu rows.
- **Procedure:** `python3 -I tools/quest_sessions.py run --slot N --run 2026-10-17-quests SESSION…` (each launch
  `d2run.py --slot N --seed S --gdb tools/gdb/quest-state.gdb --steps tools/gdb/enter-<diff>.steps --after 3600
  --install p42h <save>`; `slots.py stop N` after each session; the Xwayland windows kept on `special:d2harness`).
  Check: `python3 -I tools/quests.py check workspace/logs/quests/2026-10-17-quests-*.log`.

  | Session | Seed | Save | Game, difficulty | Actions | Logger |
  |---|---|---|---|---|---|
  | x-lut | 4212 | `QuestBookLost` (`quest-w9lost`, `20713178…`) | expansion Normal | walk, Kaelan (331) ×22, quest log, waypoint 2,3, portals ×10, waypoint chain (to 3,9), portals ×6, chain (Act I), portal | A |
  | c-tp | 4221 | `QuestPortalC` (`fa2c8ba3…`) | classic Normal | talks (Akara, Kashya, Charsi, Gheed, Warriv), quest log, waypoint 1,2, portals ×10 (+7), chains | A |
  | nm-lut | 4222 | `QuestBookLost` | expansion Nightmare | walk, Kaelan ×22, waypoint 2,3, portals ×10, chain, portals ×6 | B |
  | x-act | 4211 | `ActTwoWarriv` (`travel-act2`, `3d172a6f…`) | expansion Normal | Warriv east / west ×11 | B |
  | c-wp | 4224 | `QuestPortalC` | classic Nightmare | waypoint chain (Acts I–IV), portals ×8, chain | C |
  | x-summit0 | 4213 | `QuestSummit` (`quest-w39summit`, `f9dab74b…`) | expansion Normal | waypoint 5,8, explore, warp 118 → 120 (driven by `quest_sessions.py act` after the runner was stopped), the summit door ×37, portals ×3 on 120 | C |
  | x-summit1 | 4214 | `TravelWpFive` (`travel-wp5`, `9a0d88e8…`) | expansion Normal | waypoint 5,8, explore, warp 118 → 120, the summit door ×36 | C |
  | x-orb | 4215 | `ActFourDurance` (`travel-act4`, `5b3cbe8a…`) | expansion Normal | walk; the waypoint walk failed (no orb) | C |
  | x-off | 4216 | `TravelWpOne` (`travel-wp1`, `a6204557…`) | expansion Normal | talks (five NPCs, every quest switched off), quest log | C |
  | x-fresh | 4217 | `QuestFresh` (`9a12da6e…`) | expansion Normal | the same talks with the quests active, quest log | C |
  | x-wpnew | 4219 | `TravelWpOne` | expansion Normal | waypoint 3,1, walk and explore in the Kurast Docks (the Spider Forest waypoint not reached) | C |

- **Observed** (`tools/quests.py check`, 11 logs; full output `workspace/logs/quests/quests-check.txt`,
  `6b2c787f…`; per-kind seed lines trimmed):
  ```
  act travel +0x4C checks 11
  act travel word 7 already set 10
  act travel word 7 set 1
  act travel word checks 11
  callbacks run e0 1030
  callbacks run e11 604
  callbacks run e2 371
  callbacks run e3 6198
  chained pairs de 331 qs 42
  deactivated quest no write 290
  deactivated quest writes (word, bit) [(12, 8)] 44
  deactivated quest writes checks 334
  dispatch order e0 checks 103
  dispatch order e11 checks 64
  dispatch order e2 checks 101
  dispatch order e3 checks 235
  events chact 32
  events chlevel 81
  events de 503
  events door 73
  events join 11
  events lpf 2356
  events npcact 11
  events npcmove 22
  events p48 1
  events p49 61
  events p58 53
  events place 11
  events pocreate 27
  events portal 122
  events spot 154
  events tp 62
  events warp 2
  events wpop 61
  events wptr 61
  forced e0 callbacks of deactivated quests 352
  forced e11 callbacks of deactivated quests 256
  forced e2 callbacks of deactivated quests 242
  forced e3 callbacks of deactivated quests 3781
  free search checks 545
  free search in place 541
  free search moved 4
  free search with a partner footprint (not modelled) 62
  gate p49 checks 61
  gate p49 stamp 0 61
  gate portal checks 122
  gate portal stamp 0 122
  join deactivation checks 176
  join game record bit 15 checks 176
  join game-record marks checks 11
  join other quests switched off by a first-join callback 0
  join quests deactivated 176
  level point pick type 0 checks 22
  level point pick type 11 checks 337
  level point pick type 5 checks 11
  level seed Position type 0 step 1 22
  level seed Position type 11 step 0 3
  level seed Position type 11 step 1 334
  level seed Position type 13 step 0 28
  level seed Position type 5 step 0 11
  level seed chained pairs 343
  level seed plain type 0 step 0 90
  level seed plain type 11 step 0 1868
  level seed type 0 checks 112
  level seed type 11 checks 2205
  level seed type 13 checks 28
  level seed type 5 checks 11
  level seed unchained pairs 1
  packet 0x48 clear checks 1
  packet 0x58 checks 53
  placement chact checks 32
  placement chlevel checks 81
  placement place checks 11
  portal field SetMode(1) checks 62
  portal field seed checks 62
  portal partner SetMode(2) checks 62
  portal partner seed checks 62
  summit door refused (quest 35 +0x09 0, done 0) 36
  summit door refused (quest 35 +0x09 1, done 0) 37
  summit door refused checks 73
  town portal gs at exit checks 62
  town portal object draws 0 62
  town portal: gs draws of the town room's population (oracle) 41
  town portal: opens with population draws 9
  town portals opened 62
  warps 2
  waypoint mode kept checks 61
  waypoint object seed checks 61
  waypoint record bit checks 61
  SUMMARY mismatches=0 checks=16199 logs=11
  ```
- **Seed invariance per event kind** (gs, qs, ps at the entry and the exit; "unchanged" lines of the check): ≥ 20 events with all three unchanged: waypoint operate 61, waypoint travel and packet 0x49 61 each, portal use 122, summit door 73, packet 0x58 53, NPC move 22, `PlayerChangeLevel` 81, `PlayerChangeAct` 32, `ActLevelSpot` 154, `LevelPointFind` 2 356 (the level's own seed checked apart), dispatches 459 of 503 (the other 44 are the Kaelan talks, one predicted quest-seed step each). Under 20 (named): `NpcActTravel` 11, packet 0x48 1, warps 2. Not logged in a recorded session: packet 0x41, the Durance, Arcane and lair portals. The town portal open: gs two steps plus the town room's population draws (oracle), qs and ps unchanged, 62 of 62.
- **The saves load** (`python3 -I tools/quest_sessions.py load --slot 2`, `tools/gdb/quest-load.steps`, Normal, Save
  and Exit; written-back saves under `workspace/logs/quests/loads/`): 18 of 18 built saves loaded and were written back (`workspace/logs/quests/loads/loads.txt`, `d35aa25b…`). The act bytes come back `[act, 0, 0]` (d2s.md's rule). Quest words: word 40 bit 10 set by the join in the eight loaded saves with word 40 done (`TravelWpOne`–`Five`, `TravelWpNone`, `QuestBookLost`, `QuestBookHeld`) (`QS` at `0x0058E4D0` in the logged joins); `QuestBookLost` (word 9 bits 0 and 5, no `ass`) comes back with word 9 = 0, `QuestBookHeld` (the same with `ass`) keeps it: the word-9 first-join check both ways; `TravelWpNone` comes back with waypoint 0 set in all three difficulties. No other quest or waypoint difference. The written-back saves are kept beside it (hashes in the file); the 18 load logs, the 18 written-back saves and `loads.txt` are hashed in `workspace/logs/quests/loads/loads-manifest.sha256` (`017a6997…`, added at the review); none is pinned in `tools/test_d2s.py` (backlog, archivist).
- **Raw logs:** `workspace/logs/quests/2026-10-17-quests-*.log`, sha256 in
  `workspace/logs/quests/quests-manifest.sha256` (`dc1fc94f…`, 11 logs): c-tp `9822cc89`, c-wp `0c681ef0`, nm-lut `39ecb868`, x-act `0c26bc8f`, x-fresh `6e1f33c8`, x-lut `7a0fff8a`, x-off `80f0bbe4`, x-orb `eac35191`, x-summit0 `a2aec0e0`, x-summit1 `f05eb95a`, x-wpnew `75da006c`; driver transcripts are
  not kept (the scratch output of the runner).
- **Development logs** (not part of the record, kept): `workspace/logs/quests/dev-*.log` (20: `smoke1`, `act1`, `dev-act`, `x-lut-a`/`b`, `c-tp-a`/`b`, `nm-lut-a`, `h-lut-a`–`d`, `h-wp5-a`, `x-summit0-a`–`e`, `x-summit1-a`, `x-act3-a`). Hashed in `workspace/logs/quests/dev-manifest.sha256` (`fc16bedc…`, added at the review); the review ran `tools/quests.py check` over each: 0 mismatches over 4 677 checks, which raises nothing (they stay outside the record). Causes: the dispatch exit read before the `ret`
  (no `de` exits), the portal-create argument offsets, a level-point lookup without the points; aborted sessions
  (the waypoint walk failed, the wrong warp row, a runner killed with its own `pgrep` pattern).
- **Deviations:** Hell: five launches (`h-lut` ×4, `h-wp5`) could not reach the town waypoint by the scripted walk (no waypoint object logged in Lut Gholein; in the Rogue Encampment the walker left the town), so no recorded session is in Hell. The Meshif act-change loop (`x-act3`) did not find Meshif in Lut Gholein in 61 s. Several sessions were relaunched after a driver fix (the field-waypoint walk after portal cycles, the LvlWarp row numbering of the WRP lines: 118 → 120 is row 76, the door is the way back); the aborted launches are the development logs above. x-summit0's last four actions ran through `quest_sessions.py act` on the live session after its runner was stopped (the warp click). One background helper killed its own runner through a `pgrep -f` pattern that matched its command line (the slot-2 runner); the slot was stopped and relaunched, the partial log kept as `dev-nm-lut-a`.
- **Not reached / out of scope:** see the plan log entry and the two findings' Phase 2 sections (shortfalls named per question); the two-player cases (the portal party and `QuestFlag` gates, party credit, a non-zero gate stamp) are plan 0044's and out of scope here.
- **Conclusion:** raises and corrections in [quests/0001 § 15](0001-progression.md#15-phase-2-run2026-10-17-quests)
  and [quests/0002 § 12](0002-travel.md#12-phase-2-run2026-10-17-quests).

## run:2026-10-18-quests2

- **Question:** (plan 0042 Phase 2 part 2, the completion pass) Do the NPC-talk quest steps of
  [quests/0001](0001-progression.md) § 7–§ 10 (each bit write at its call site, from a save set just before the step),
  the saved quest words after *Save and Exit*, the Compelling Orb, the Durance gate, NPC 266, the Tristram portal, a
  new character's join, and the travel events of [quests/0002](0002-travel.md) (warps, waypoint activations and
  travels, NPC act changes, packet 0x48 per travel word, death and resurrection) reproduce with 0 mismatches under
  the part 1 checker, extended, which re-checks part 1's 11 logs unchanged?
- **Setup:** the ADR-0003 harness on **slot 2** only (display `:9`, `workspace/wineprefix-2`; slot 1 was another
  lane's), agent-driven play (no owner play), one client, one game at a time. The slot's empty saves directory set
  aside as tag `p42q`, restored and set aside again before each launch (`quest_sessions.py run`), the session's save
  installed with `d2run.py --install p42q`; the installed save is copied beside the log as `<log>.in.d2s` and the save
  the game writes at *Save and Exit* as `<log>.out.d2s`.
  - **Saves** (new recipes, built with `tools/d2s.py build workspace/merged/data/global/excel <recipe>
    <base> workspace/runtime/quest-saves-p42q/<Name>/<Name>.d2s`; expansion base
    `workspace/samples/d2s-owner/smpsor-l50.d2s`, classic base `workspace/runtime/monspawn-chars/cls/smpsor.d2s`):
    `quest-talk1`..`5` (`QuestTalkOne`..`Five`: every quest done but the step's words, set the same in all three
    difficulties, start act I..V: word 0, 8, 16, 24 clear; words 1, 2, 4, 6, 9, 20, 25, 27, 35 bit 1 only; word 14
    bit 3; word 19 bit 6; word 21 bit 4), `quest-talk1c`..`4c` (the classic `QuestTalkOneC`..`FourC`, the same words,
    classic status byte), `quest-orbwill` (`QuestOrbWill`: `travel-act4` with `qf2` wielded and no `qf1`),
    `quest-death` (`QuestDeath`: 24 life, no belt). Phase 0's `TravelWpOne`, `TravelWpTwo`, `TravelWpFive`,
    `QuestSummit`, `ActThreeMeshif`, `ActFourDurance`, `ActFiveTyrael` as built by `tools/quest_saves.py build`.
  - **Logger** `tools/gdb/quest-state.gdb` as in part 1, with `questev.py` revision D (this run): `QK`, every
    `QUESTRECORD_ClearSteps` call (`0x0065C3E0`, which clears bits 2–11 with `BITFIELD_Clear` and so writes no `QC`
    line), and the `NPCQ` driver line extended to the town NPCs of the talk steps. Part 1's lines are unchanged.
  - **Checker** `tools/quests.py check`, extended (rules in its docstring): the talk steps (`TALK_STEPS`: per word, NPC
    class, message, condition on the word before, the writes with their call sites), the switched-off reward handlers
    (`deactivated_writes`), the saved words (`save_check`: the loader rule, then every logged write to the player's
    record, word by word for all three difficulties), the Compelling Orb, the Durance gate, NPC 266's player-seed steps,
    the Tristram portal; tests `tools/test_quests.py`.
  - **Driver** `tools/quest_sessions.py` (part 2 actions: `towp2`, `pingpong`, `warp1` with the LvlWarp select box,
    `goto`, `tonpc`, `activate`, `approach`, `die`, `saveexit`; `talk` without a stray Escape), `tools/d2pilot.py`
    (Tyrael's menu row), `tools/gdb/quest-newchar.steps`.
- **Procedure:** `python3 -I tools/quest_sessions.py run --slot 2 --tag p42q --run 2026-10-18-quests2 SESSION…`
  (sessions defined at the end of the file), then `systemd-run --user --scope -p MemoryMax=4G python3 -I
  tools/quests.py check workspace/logs/quests/2026-10-17-quests-*.log workspace/logs/quests/2026-10-18-quests2-*.log`.

  | Session | Seed | Save | Game, difficulty | Actions (what happened) |
  |---|---|---|---|---|
  | x-warps | 4311 | `TravelWpTwo` | expansion Normal | waypoint to Lut Gholein, 100 warps through LvlWarp rows 20/21 (town ↔ sewer dock), 14-hop waypoint chain, Save and Exit |
  | x-talk1 | 4321 | `QuestTalkOne` | expansion Normal | Akara ×3, Kashya ×2, Warriv ×3, waypoint chain (6 travels), Save and Exit |
  | x-orbno | 4312 | `ActFourDurance` | expansion Normal | waypoint to Travincal, warp row 64 (no click taken), the orb (no operate reached the server), Save and Exit |
  | x-orb | 4313 | `QuestOrbWill` | expansion Normal | the orb ×2 counted, warp 83 → 100 and back up, Save and Exit |
  | x-navi | 45 | `TravelWpTwo` | expansion Normal | out of the camp to the Blood Moor's border preset, Flavie (266) ×23, Save and Exit |
  | x-summit2 | 4314 | `QuestSummit` | expansion Normal | Ancients' Way, warp 118 → 120, clicks at rows 82/83 (the door answered, 9 refusals), Save and Exit |
  | x-summit3 | 4315 | `TravelWpFive` | expansion Normal | the same (6 door refusals), Save and Exit |
  | x-meshif | 4316 | `ActThreeMeshif` | expansion Normal | Meshif east (word 15 set, packet 0x48); Meshif west not taken; stopped by hand (no Save and Exit) |
  | h-talk1 | 4331 | `QuestTalkOne` | expansion **Hell** | the Act I talks, waypoint chain, Save and Exit |
  | c-talk1 | 4351 | `QuestTalkOneC` | **classic** Normal | the Act I talks, waypoint chain, Save and Exit |
  | x-talk3 | 4323 | `QuestTalkThree` | expansion Normal | Hratli, Ormus; Asheara not found; stopped by hand |
  | x-tristram | 4372 | `TravelWpOne` | expansion Normal | Stony Field explored 240 s, the cairn stones not reached, Save and Exit |
  | x-newchar | 4371 | none (menu) | expansion Normal | a new Sorceress through the menu, Save and Exit |
  | x-talk3b | 4326 | `QuestTalkThree` | expansion Normal | Alkor, Cain (0x1CA); stopped by hand |
  | x-talk4 | 4324 | `QuestTalkFour` | expansion Normal | Tyrael, Cain, Save and Exit |
  | x-talk2 | 4322 | `QuestTalkTwo` | expansion Normal | Jerhyn, Atma, Meshif, Save and Exit |
  | h-talk3 | 4333 | `QuestTalkThree` | expansion **Hell** | Hratli, Ormus, Asheara, Alkor, Cain; the game exited during a machine suspend and the driver hung (below) |
  | x-wpact3 | 4361 | `TravelWpOne` | expansion Normal | Kurast Docks → Spider Forest → Great Marsh, 14 min, no activation, Save and Exit |
  | h-talk4 | 4334 | `QuestTalkFour` | expansion **Hell** | Tyrael, Cain, Save and Exit (supervised driver) |
  | c-talk4 | 4354 | `QuestTalkFourC` | **classic** Normal | Tyrael, Cain, Save and Exit (supervised) |
  | x-talk5 | 4325 | `QuestTalkFive` | expansion Normal | Larzuk ×2, Save and Exit (supervised) |

- **Observed** (`tools/quests.py check` over the 21 logs; full output `workspace/logs/quests/quests2-check.txt`,
  `edd07c40…`; per-kind seed lines and level-point lines trimmed):
  ```
  Durance warp gate checks                                               1
  NPC 266 talk: e0 handler 0x00596A90 runs 2                             23
  chained pairs de 266 ps                                                22
  de gs: a unit created by a talk step (oracle)                          13
  deactivated quest no write                                             426
  deactivated quest writes checks                                        453
  events chact                                                           13
  events chlevel                                                         47
  events de                                                              476
  events door                                                            15
  events due                                                             5
  events join                                                            22
  events lpf                                                             3942
  events npcact                                                          1
  events npcmove                                                         1
  events orb                                                             2
  events p48                                                             1
  events p49                                                             47
  events place                                                           21
  events pocreate                                                        82
  events spot                                                            68
  events warp                                                            104
  events warpgate                                                        1
  events wpop                                                            47
  events wptr                                                            47
  free search checks                                                     323
  free search moved                                                      54
  gate p49 checks                                                        47
  join quests deactivated                                                464
  level seed chained pairs                                               106
  loaded words (join record) checks                                      16
  orb counter checks                                                     2
  orb gs: the completing hit (oracle)                                    1
  orb hit counted (weapon ['qf2 '], mode 0)                              2
  orb mode after the second hit checks                                   1
  orb operates                                                           2
  orb writes checks                                                      2
  saved word checks                                                      2304
  saved words: player-record writes applied                              115
  saved words: sessions compared                                         16
  saved words: words changed in the game's difficulty                    46
  stub character: double join                                            1
  stub join, first call checks                                           1
  stub join, second call checks                                          1
  talk step w0 npc 155 msg 0x0 fires                                     3
  talk step w1 npc 148 msg 0x4c fires                                    3
  talk step w14 npc 201 msg 0x1ba fires                                  1
  talk step w14 npc 210 msg 0x1c2 fires                                  1
  talk step w16 npc 253 msg 0x1d2 fires                                  2
  talk step w19 npc 252 msg 0x24d fires                                  1
  talk step w19 npc 255 msg 0x251 fires                                  2
  talk step w2 npc 150 msg 0x5c fires                                    3
  talk step w20 npc 254 msg 0x21a fires                                  2
  talk step w24 npc 367 msg 0x298 fires                                  3
  talk step w25 npc 367 msg 0x2a4 fires                                  3
  talk step w26 npc 246 msg 0x4e21 fires                                 2
  talk step w26 npc 367 msg 0x4e20 fires                                 2
  talk step w27 npc 246 msg 0x2a8 fires                                  3
  talk step w35 npc 511 msg 0x4e7a fires                                 1
  talk step w4 npc 148 msg 0x76 fires                                    3
  talk step w40 npc 511 msg 0x4ed2 fires                                 1
  talk step w6 npc 155 msg 0xb7 fires                                    3
  talk step w8 npc 201 msg 0xfd fires                                    1
  talk step w9 npc 176 msg 0x14e fires                                   1
  warps                                                                  104
  SUMMARY mismatches=0 checks=23348 logs=21
  ```
- **Part 1 re-checked:** the 11 part 1 logs match their manifest (`sha256sum -c quests-manifest.sha256`: 11 OK) and
  give `SUMMARY mismatches=0 checks=16204 logs=11` under the final checker (`quests2-recheck-part1.txt`, `3a8209f8…`);
  the 5 checks beyond part 1's 16 199 are the new talk-step rule on the Warriv and Jerhyn introductions those logs hold.
- **Raw logs and kept files:** `workspace/logs/quests/2026-10-18-quests2-*.log` (21), the installed saves
  (`*.in.d2s`, 20) and written saves (`*.out.d2s`, 17), `quests2-check.txt`, `quests2-recheck-part1.txt` and
  `2026-10-18-quests2-npcplace.txt`, sha256 in `workspace/logs/quests/quests2-manifest.sha256` (61 lines,
  `29693c4b…`). Driver transcripts (`workspace/scratch-p42q/q*.out`) are not kept as evidence.
- **Development logs** (not part of the record, kept): `workspace/logs/quests/dev-p42q-*.log` (11: `harem-a`,
  `sewer-a`, `sewer-b`, `x-talk1-a`, `x-talk1-b`, `x-orbno-a`, `x-orb-a`, `x-summit2-a`, `x-tyrael-a`, `x-death-a`,
  `h-talk4-a`) with their installed saves, hashed in `dev-p42q-manifest.sha256` (20 lines, `af3aefd0…`); the final
  checker gives 0 mismatches over 2 480 checks on them, which raises nothing. Causes: the driver's walking and clicking
  being fixed (warp select boxes, the town waypoint walk, stale NPC positions, a stray Escape that reached SAVE AND
  EXIT in `x-talk1-b`), the orb preset goal, a wrong Tyrael menu, a false death reading, a run restarted with the
  supervised driver.
- **Deviations:** one slot only (slot 2; slot 1 was freed by plan 0043 late in the run and not taken). During
  h-talk3 the owner's machine suspended for about nine hours; the game exited, the driver kept clicking into the gone
  window and the main session killed it at 07:23; h-talk3 has no written save. Afterwards `quest_sessions.py run`
  supervises each session in its own process group (watchdogs on a quiet log, gdb's exit line and a time limit; waits
  on `d2run.py`; bounded slot and save calls) and was run under `timeout`; h-talk4, c-talk4 and x-talk5 ran that way.
  Sessions stopped by hand (x-meshif, x-talk3, x-talk3b) are recorded without a written save. x-wpact3's session line
  shows no saveexit message but its written save is kept.
- **Not reached / out of scope:** the two findings' part 2 sections name the shortfalls; two-client cases stay plan
  0044's.
- **Conclusion:** raises and corrections in [quests/0001 § 16](0001-progression.md#16-phase-2-part-2-run2026-10-18-quests2)
  and [quests/0002 § 13](0002-travel.md#13-phase-2-part-2-run2026-10-18-quests2).

## run:2026-10-19-quests3

- **Question:** (plan 0042 Phase 2 part 3, the last reproduction pass) Do the quest-seed draws a waypoint hop, a town
  talk or an item use reaches (word 11's eclipse arm and its timer, the cairn order by the decoded scroll, the Dark
  Wanderer timer, Anya's reward), the quest timers, the level-entry and item-use quest steps so reached, the town portal
  refused in a town, Meshif's westward travel (the type-5 point), Tyrael's Act IV → V travel (word 28, packet 0x48), a
  death and resurrection (packet 0x41) and waypoint activations from mode 0 reproduce with 0 mismatches under the part 2
  checker, extended, which re-checks the 32 logs of parts 1 and 2 unchanged?
- **Setup:** the ADR-0003 harness on **slot 2** only (display `:9`, `workspace/wineprefix-2`; slot 1 was plan 0043's
  P2b lane), agent-driven play, one client, one game at a time. The slot's empty saves directory set aside as tag
  `p42r`, restored and set aside again around each launch (`quest_sessions.py run`); the installed save is kept beside
  the log as `<log>.in.d2s`, the save written at *Save and Exit* as `<log>.out.d2s`.
  - **Saves** (new recipes, built with `tools/d2s.py build workspace/merged/data/global/excel <recipe>
    workspace/samples/d2s-owner/smpsor-l50.d2s workspace/runtime/quest-saves-p42r/<Name>/<Name>.d2s`):
    `quest-p3entry` (`QuestEntry`: Act I start, every quest done but words 4, 11, 12 and 37, all clear; every waypoint;
    a tome at inventory 0,0 and the decoded scroll `bkd ` at 1,0), `quest-p3anya` (`QuestAnya`: Act V start, word 37 =
    b1, b8, b15; a tome and `tr2 ` at 1,0), `quest-p3meshif` (`QuestMeshifW`: Act III start, every quest done),
    `quest-p3wpact` (`QuestWpAct`: Act I start, the five towns' waypoints only, a tome). Part 2's `QuestDeath` and Phase
    0's `ActFiveTyrael`, part 1's `QuestBookHeld` as built.
  - **Logger** `tools/gdb/quest-state.gdb` with `questev.py` **revision E**: `TMA` (0x00543F10, timer add), `TMR`/`TMX`
    (0x00543E85/0x00543E87, a timer about to run and its result), `CRN0`/`CRN` (0x00593CD5/0x00593CE6, the cairn order
    fill on the `bkd ` use), `DWS`/`DWF` (0x005BD40F/0x005BD458, the Dark Wanderer timer's step and each free-spot try),
    `ANL`/`ANY` (0x005898D0/0x0058993C, Anya's reward: clvl, table, count, draw, code), and the quest state byte
    `+0x0C` as a seventh element of every quest-object list; revision D's lines unchanged.
  - **Checker** `tools/quests.py check`, extended (docstring "part 3"): timers, the eclipse arm, the cairn order, the
    Dark Wanderer, Anya's reward (a `TALK_STEPS` row and the table/draw check), the `tr2 `/`ass ` uses, the Harrogath
    portal's word 28, the level-entry steps of words 12 and 37, "Cain lost" on arrival in 40, the town-portal refusal in
    a town; `tools/test_quests.py` 19 tests (part 2's rules: talk steps, saved words, NPC 266's handler runs, word 40's
    map; part 3's rules). `tools/quests.py objplace` (DS1 placements of object classes).
  - **Driver** `tools/quest_sessions.py` (part 3 actions `use`, `tpuse`, `clickobj`; `die` standing next to the nearest
    monster; the part 3 session block), `tools/d2pilot.py` (Meshif's Act III menu without *trade*, the `tyraelgo`
    row, the waypoint walk's stop at 5 sub-tiles, a screenshot of the menu as clicked).
- **Procedure:** `timeout 4000 python3 -I tools/quest_sessions.py run --slot 2 --tag p42r --run 2026-10-19-quests3 SESSION…`
  (sessions in the part 3 block of the file; each supervised by the part 2 watchdog), then `systemd-run --user --scope -p
  MemoryMax=4G python3 -I tools/quests.py check workspace/logs/quests/2026-10-19-quests3-*.log`, and the same checker over
  the 32 logs of parts 1 and 2.

  | Session | Seed | Save | Game, difficulty | Actions (what happened) |
  |---|---|---|---|---|
  | x-entry | 4401 | `QuestEntry` | expansion Normal | tome refused in the camp; `bkd ` used twice (the order drawn once); Lut Gholein ("Cain lost"); the palace (level 50); Lost City (the eclipse armed, period 15, the timer ran) and back via Far Oasis (no second arm); Kurast Docks and the Dark Wanderer (8 tries); Arreat Plateau, Crystalline Passage (word 37 b3), Glacial Trail (the driver's `5,5`, meant for Halls of Pain); Save and Exit. The driver was restarted by hand twice inside the game (a warp-click loop in the harem, a waypoint walk in level 76) with `quest_sessions.py act`, and the written save copied beside the log by hand |
  | x-anya | 4411 | `QuestAnya` | expansion Normal | Anya's reward (`ob4 `), a second talk (nothing), the `tr2 ` use (word 37 b7), tome refused in Harrogath, Save and Exit |
  | h-anya | 4412 | `QuestAnya` | expansion **Hell** | Anya's reward (Hell table), tome refused, Save and Exit (the `tr2 ` is a Normal quest item: no use) |
  | nm-anya | 4413 | `QuestAnya` | expansion **Nightmare** | Anya's reward (Nightmare table), tome refused, Save and Exit |
  | x-meshifw | 4421 | `QuestMeshifW` | expansion Normal | Meshif greeted, then six trips west (type 5 into 40) and six east, Save and Exit |
  | h-death3 | 4442 | `QuestDeath` | expansion **Hell** | waypoint to the Cold Plains, three deaths next to monsters, Escape each time (packet 0x41), Save and Exit |
  | x-tyrael3 | 4431 | `ActFiveTyrael` | expansion Normal | Tyrael talked to, five trips through the red portal (object 566) to Harrogath and back by waypoint, Save and Exit |
  | x-entry2 | 4402 | `QuestEntry` | expansion Normal | as x-entry (eclipse period 16), with Halls of Pain (word 37 b14) and the palace last; the final warp-click loop stopped by hand, Save and Exit by `quest_sessions.py act`, the written save copied by hand |
  | x-book | 4451 | `QuestBookHeld` | expansion Normal | the `ass ` right-clicked: no write logged; Save and Exit |
  | h-entry | 4403 | `QuestEntry` | expansion **Hell** | as x-entry2 without the palace (eclipse period 16, Dark Wanderer, word 37's 113 and 123 steps); the driver stuck at the Kurast Docks barricade, the rest finished by `quest_sessions.py act` in the same game, the written save copied by hand |
  | x-wpact1-0 | 4322 | `QuestWpAct` | expansion Normal | out of the Rogue Encampment, exploration of the Blood Moor towards the Cold Plains (4 min): no waypoint reached, Save and Exit |
  | x-wpactr-0 | 4322 | `QuestWpAct` | expansion Normal | straight Teleport hops towards the Cold Plains waypoint's known place: stopped at a river in the Blood Moor; stopped by hand (no written save) |
  | x-wpact3r-0 | 4361 | `TravelWpOne` | expansion Normal | Kurast Docks, the Dark Wanderer (8 tries), towards the Spider Forest waypoint (logged in mode 0): stuck in a jungle pocket; Save and Exit by `quest_sessions.py act`, the written save copied by hand |
- **Observed:** (`tools/quests.py check` over the 13 logs; full output `workspace/logs/quests/quests3-check.txt`,
  `7cde7b36…`; the part 3 lines and the event totals, per-kind seed and level-point lines trimmed):
  ```
  Anya reward draw checks                                                3
  Anya reward ob4                                                        1
  Anya reward ob7                                                        1
  Anya reward obd                                                        1
  Anya reward table checks                                               3
  Cain lost on arrival in 40 checks                                      10
  Cain lost on arrival in 40 none                                        7
  Cain lost on arrival in 40 writes                                      3
  Dark Wanderer object tries checks                                      4
  Dark Wanderer objects created 8 of 8 tries                             4
  Dark Wanderer quest-seed step checks                                   4
  Harrogath portal word 28 checks                                        2
  ass use word 9 b5 checks                                               1
  cairn order checks                                                     3
  cairn order kept checks                                                3
  cairn order quest-seed steps                                           28
  deactivated quest no write                                             102
  deactivated quest writes (word, bit) [(26, 9)]                         1
  deactivated quest writes (word, bit) [(37, 9), (37, 1), (37, 0), (37, 10)] 3
  deactivated quest writes (word, bit) [(40, 6)]                         1
  deactivated quest writes (word, bit) [(40, 9)]                         3
  deactivated quest writes checks                                        110
  eclipse arm off (state 1, +0x09 1, armed False, ran True)              3
  eclipse armed (level 44)                                               3
  eclipse timer period checks                                            3
  eclipse timer: word 11 writes [(2, '0059a542')]                        3
  entry step w12 40 -> 50 [7, 8]                                         2
  entry step w12 checks                                                  2
  entry step w37 112 -> 113 [3]                                          3
  entry step w37 113 -> 123 [14]                                         2
  entry step w37 checks                                                  5
  events chact                                                           33
  events chlevel                                                         54
  events de                                                              110
  events due                                                             7
  events join                                                            13
  events lpf                                                             457
  events npcact                                                          6
  events npcmove                                                         17
  events p41                                                             3
  events p48                                                             1
  events p49                                                             37
  events place                                                           13
  events spot                                                            67
  events tp                                                              6
  events warp                                                            3
  events wpop                                                            37
  events wptr                                                            37
  join quests deactivated                                                320
  level seed Position type 5 step 0                                      5
  level seed Position type 5 step 1                                      6
  level seed chained pairs                                               10
  saved word checks                                                      1728
  saved words: player-record writes applied                              77
  saved words: sessions compared                                         12
  saved words: words changed in the game's difficulty                    33
  talk step w37 checks                                                   3
  talk step w37 npc 512 msg 0x4ea8 fires                                 3
  talk step w40 checks                                                   4
  talk step w40 npc 512 msg 0x4ed0 fires                                 3
  talk step w40 npc 513 msg 0x4ed3 fires                                 1
  timer due checks                                                       7
  timer pass frame checks                                                7
  timer qs checks                                                        3
  timer runs 0059ed80 r1                                                 3
  timer runs 005bd390 r1                                                 4
  timers added 0059ed80                                                  3
  timers added 005bd390                                                  4
  town portal in a town refused checks                                   6
  town portal refused (lid 1)                                            3
  town portal refused (lid 109)                                          3
  tr2 use word 37 b7 checks                                              1
  SUMMARY mismatches=0 checks=6167 logs=13
  ```
- **Parts 1 and 2 re-checked:** the 32 logs under the final checker give `SUMMARY mismatches=0 checks=39568 logs=32`
  (`quests3-recheck-p12.txt`, `3f2b7de7…`); the 16 checks beyond part 2's 39 552 are the "Cain lost" rule on the
  arrivals in 40 those logs hold (1 with writes: part 1's c-wp, classic Nightmare, `QuestPortalC`, word 4 = 0; 15 with
  none).
- **Raw logs and kept files:** `workspace/logs/quests/2026-10-19-quests3-*.log` (13), the installed saves (`*.in.d2s`,
  13) and written saves (`*.out.d2s`, 12; x-wpactr-0 has none), `quests3-check.txt`, `quests3-recheck-p12.txt`,
  `2026-10-19-quests3-objplace.txt` (`tools/quests.py objplace 567 368`), `2026-10-19-quests3-zoo-imm.txt` (the
  `0x237` immediates of the image) and `2026-10-19-quests3-wpmodes.txt` (`tools/quests.py wpmodes` over the 45 part
  1–3 logs), sha256 in `workspace/logs/quests/quests3-manifest.sha256` (43 lines, `1975e350…`; `sha256sum -c` from
  `workspace/logs/quests/`). Driver transcripts (`workspace/scratch-p42r/s-*.out`) are not kept as evidence.
- **Development logs** (not part of the record, kept): `workspace/logs/quests/dev-p42r-*.log` (12: `x-entry-a`,
  `x-anya-a`, `dev-meshif`, `x-meshifw-a`, `dev-tyrael`, `x-tyrael3-a`, `-b`, `-c`, `x-death3-a`, `-b`, `h-death3-a`,
  `x-wpact3r-a`) with their installed saves and the two menu screenshots (`dev-p42r-meshif-menu.png`,
  `dev-p42r-tyrael-menu.png`), hashed in `dev-p42r-manifest.sha256` (26 lines, `38d3aaa5…`); the final checker gives
  0 mismatches over 2 498 checks on them, which raises nothing. Causes: the scroll panel left open (x-entry-a), a
  walking click that opened the waypoint menu (x-anya-a, x-tyrael3-b), Meshif's menu line (no *trade*), Tyrael's
  menu (no travel line: the probes), the waypoint walk stopping at 4 sub-tiles (x-tyrael3-c), deaths not reached in
  Normal and a long hop loop while dead (x-death3-a, -b, h-death3-a), the town waypoint taken for the target
  (x-wpact3r-a).
- **Deviations:** one slot (slot 2). Three sessions (x-entry, x-entry2, h-entry) and x-wpact3r-0 were finished by
  hand-run `quest_sessions.py act` commands in the same game after the driver looped (a warp-click loop in the harem,
  a waypoint walk in level 76, the Kurast Docks barricade, a jungle pocket); their logs are continuous and their
  written saves were copied beside the logs by hand (the `act` driver does not know the save's name). x-wpactr-0 was
  stopped by hand. The driver supervises each session (part 2's watchdog), run under `timeout`.
- **Not reached / out of scope:** the two findings' part 3 sections name the shortfalls (final for this plan);
  two-client cases stay plan 0044's.
- **Review re-run** (architect, `lane/p42r` review, 2026-10-20, at `8ce7e28`): both manifests pass `sha256sum -c` from
  `workspace/logs/quests/` (43 and 26 OK); `tools/quests.py check` (sha256 `b6dfb1a3…`; logger `tools/gdb/questev.py`
  revision E, `f177f890…`) over the 13 logs and over the 32 part 1 and 2 logs gives output byte-identical to
  `quests3-check.txt` and `quests3-recheck-p12.txt`; over the 12 development logs 0 over 2 498;
  `tools/test_quests.py` 19 tests OK.
- **Conclusion:** raises, corrections and shortfalls in
  [quests/0001 § 17](0001-progression.md#17-phase-2-part-3-run2026-10-19-quests3) and
  [quests/0002 § 14](0002-travel.md#14-phase-2-part-3-run2026-10-19-quests3).
