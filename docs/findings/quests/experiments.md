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
