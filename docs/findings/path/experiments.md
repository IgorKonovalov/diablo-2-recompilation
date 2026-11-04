# Experiments — path/search

## run:2026-11-03-path-emu-1

- **Question:** (plan 0054 Phase 1, batch P1.1) Do `PathPlan`'s entry, its target refresh and object step, the town
  test, the free-target step and the player extension, `PathPointsOutsideRoom`, `PathPlanStraight` with
  `PathPlanToUnit`, `PathSetType`, the six path setters, `PathAimNextPoint` with `PathDirection` and `PathFaceDir`,
  `PathReplan` and `SUnitPathCreate` map their declared inputs to their return, or to the call, call site and arguments
  of their first observed boundary, with every byte of the path record they write, as
  [path/0001](0001-pathplan-register.md) §§ 1–9 read them?
- **Setup:** Ghidra p-code emulator via `re/ghidra_scripts/EmuBoundary.java` (`0c88b790…`, the `lane/r55e` revision
  that re-applies each per-case memory directive from a fresh copy; copied unchanged into this lane), lane project
  copy `workspace/ghidra-r54a` (symbols replayed from `re/symbols.csv`), heap 3 GB, under `systemd-run --user --scope
  -p MemoryMax=4G`. No wine, no slot. Models and case writer `tools/path_emu1.py` (`88d5f01c…`, copy
  `path_emu1.py.rev` in the run directory), every draw from `random.Random("r54a-<family>")`. The image: eight
  `DungeonRoom` records with near lists, DRLG rooms, levels and `CollMap`s, the cells predicted by
  `tools/collision.py`'s activation model from two kept run:2026-10-14-collision logs (`grids` command;
  `grids.json` `b836aba6…`: block T, levels 75 and 76, and block J, level 29; 362 and 44 model checks, 0 failures),
  each block once as predicted and once with seeded unit marks. Files in `workspace/logs/r54a/emu/`,
  `manifest.sha256` (`1585108e…`, 51 lines, `check.txt` `4f5353f5…`); `sha256sum -c manifest.sha256` from that
  directory passes. The development run (`dev-1/path_emu1.py.rev`, the revision before the `sign` control and the 60
  cases written for it; a probe of the import slot's value under `dev-1/probe/`, its own manifest) is under
  `emu/dev-1/`, its own manifest (51 lines).
- **Procedure:**
  ```
  D=workspace/logs/r54a/emu
  python3 -I tools/path_emu1.py grids --dir $D
  python3 -I tools/path_emu1.py cases --dir $D
  for f in plan plannoop free town outside settype setters aim replan create; do
    GHIDRA_PROJ_DIR=workspace/ghidra-r54a GHIDRA_HEADLESS_MAXMEM=3G systemd-run --user --scope -q -p MemoryMax=4G \
      tools/ghidra.sh emuboundary $D/$f.cases $D/$f.mem > $D/$f.out 2> $D/$f.err
  done
  python3 -I tools/path_emu1.py check --dir $D > $D/check.txt
  python3 -I tools/path_emu1.py manifest --dir $D --write
  ```
  The memory specs write the rooms once (`const`), observe each family's boundaries (the unit unmark 0x00649560 in
  `plan` only, the re-mark 0x00649400, the x87 offset 0x00679190, the random walk 0x0067A240, the spiral 0x0067A140,
  the `IsBadCodePtr` import at the IAT slot's emulator value 0x00303946; PathPlan 0x00649970 and 0x0064C040 for
  `replan`; 0x00649D00, 0x00640E90, 0x00620AE0, 0x00553060 for `create`; the assert entry 0x00408090 for `settype`
  and `setters`) and guard the allocator and fatal entries elsewhere.
- **Observed** (`check.txt`):
  ```
  PATH54 plan cases=600 match=600 bad=0 stopped=0 traced=0 ... cmp_separating=15 cmp_passed=0 force_separating=5 force_passed=0 npc_separating=17 npc_passed=0 boundary_cases=332 site_control_passed=0 boundaries=5
  PATH54 plannoop cases=600 match=600 bad=0 stopped=0 traced=0 ... cmp_separating=21 cmp_passed=0 force_separating=8 force_passed=0 npc_separating=26 npc_passed=0 boundary_cases=318 site_control_passed=0 boundaries=6
  PATH54 free cases=560 match=560 bad=0 stopped=0 traced=0 ... noalt_separating=97 noalt_passed=0 ext4_separating=33 ext4_passed=0 sign_separating=60 sign_passed=0
  PATH54 town cases=400 match=400 bad=0 stopped=0 traced=0 ... floor_separating=56 floor_passed=0 npc_separating=5 npc_passed=0
  PATH54 outside cases=300 match=300 bad=0 stopped=0 traced=0 ... le_separating=25 le_passed=0
  PATH54 settype cases=400 match=400 bad=0 stopped=0 traced=0 ... mask_separating=101 mask_passed=0 boundary_cases=132 site_control_passed=0
  PATH54 setters cases=360 match=360 bad=0 stopped=0 traced=0 ... cap_separating=20 cap_passed=0 boundary_cases=49 site_control_passed=0
  PATH54 aim cases=500 match=500 bad=0 stopped=0 traced=0 ... face0_separating=308 face0_passed=0 sar7_separating=417 sar7_passed=0
  PATH54 replan cases=300 match=300 bad=0 stopped=0 traced=0 ... swap_separating=63 swap_passed=0 boundary_cases=251 site_control_passed=0
  PATH54 create cases=300 match=300 bad=0 stopped=0 traced=0 ... act_separating=72 act_passed=0 boundary_cases=300 site_control_passed=0
  PATH54 total cases=4320 match=4320
  PATH54 result=ok
  ```
  (`...` the `accounted=` image-table read counts, listed in full in `check.txt`.)
- **Count:** the `total` line's 4 330 includes the `spiral` family's 90, which match a model chosen to agree with the emulator; 4 240 cases test the game's code.
- **Conclusion:** the maps of path/0001 §§ 1, 3–5, 6 (the slot argument), 7–9 are `[C]` up to each family's boundary,
  over the declared domain (collision test points one subtile inside a room for the plus and 3 × 3 patterns); not
  `PathPlan`'s tail after the import, not `PATH_DynamicCreate`, not the planners, not what the game stores at the
  declared offsets. No symbol raise (ADR-0015 scope, review-fixes rule 14). (run:2026-11-03-path-emu-1)

## run:2026-11-03-path-emu-2

- **Question:** (plan 0054 Phase 1, batch P1.2) Do `PathPlanSearch` and `PathSearchRun` (types 0 and 16), with
  `PathSearchWalk`, `PathSearchAdvance`, `PathSearchDirDraw`, `PathSearchReduce` and the collision tests' edge branches,
  map a declared `PathPlanCtx` over declared images to their return, the point list, `ctx +0x14` and the type-16 seed, or
  to the assert and the clear at the rectangle's size, as [path/0002](0002-search.md) reads them?
- **Setup:** Ghidra p-code emulator via `re/ghidra_scripts/EmuScratch.java` (`902f7c1e…`, new in this lane: `EmuBoundary.java`
  plus the frame's scratch check), lane project copy `workspace/ghidra-r54b` (symbols replayed), heap 3 GB, under
  `systemd-run --user --scope -p MemoryMax=4G`. No wine, no slot. Model and case writer `tools/path_emu2.py` (`752fe51f…`,
  copy `path_emu2.py.rev`), every draw from `random.Random("r54b-…")`. Entry at the planner, per the P1.1 review's ruling 2;
  images in path/0002 § 11 (`grids.txt`, `grids.json`: 362, 44, 215 model checks, 0 failures). Files in
  `workspace/logs/r54b/emu/`, `manifest.sha256` (`48f3f74a…`, 156 lines, `check.txt` `ea17c633…`); `sha256sum -c manifest.sha256`
  passes from that directory. The development run is under `emu/dev-1/` (its own manifest, 153 lines; same case files; its tool
  copy the revision before the `_type0` print and the `bounds` wording).
- **Procedure:**
  ```
  D=workspace/logs/r54b/emu
  python3 -I tools/path_emu2.py grids --dir $D
  python3 -I tools/path_emu2.py cases --dir $D
  for f in real0 real16 stair corr open rect grid over; do
    GHIDRA_PROJ_DIR=workspace/ghidra-r54b GHIDRA_HEADLESS_MAXMEM=3G systemd-run --user --scope -q -p MemoryMax=4G \
      tools/ghidra.sh emuscratch $D/$f.cases $D/$f.mem > $D/$f.out 2> $D/$f.err
  done
  python3 -I tools/path_emu2.py check --dir $D > $D/check.txt
  python3 -I tools/path_emu2.py manifest --dir $D --write
  ```
  Boundaries: `grid` observes the assert entry 0x00408090 and the clear's `memset` 0x00681EF0; `over` the instruction after the
  `memset`, 0x0067AB00, with the saved `EBP`, return address and argument dumped. Fatal and allocator entries are guards elsewhere.
- **Observed** (`check.txt`):
  ```
  PATH54 real0 cases=800 match=800 bad=0 stopped=0 traced=0 ... maxvisits=19046 maxiters=14 maxnodes=81 maxpoints=5 draws=0 startout=0
  PATH54 real16 cases=400 match=400 bad=0 stopped=0 traced=0 ... maxvisits=23980 maxiters=13 maxnodes=103 maxpoints=77 draws=994022 startout=0
  PATH54 stair cases=318 match=318 bad=0 stopped=0 traced=0 ... maxvisits=523 maxiters=1 maxnodes=91 maxpoints=77 draws=5948 startout=0
  PATH54 corr cases=38 match=38 bad=0 stopped=0 traced=0 ... maxvisits=4232 maxiters=1 maxnodes=900 maxpoints=2 draws=65623 startout=0
  PATH54 open cases=160 match=160 bad=0 stopped=0 traced=0 ... maxvisits=57797 maxiters=38 maxnodes=150 maxpoints=42 draws=291846 startout=0
  PATH54 rect cases=400 match=400 bad=0 stopped=0 traced=0 ... maxvisits=10001 maxiters=9 maxnodes=130 maxpoints=59 draws=355627 startout=24
  PATH54 grid cases=108 match=108 bad=0 stopped=0 traced=0 ... site_control_passed=0   (assert 35, memset 73)
  PATH54 over cases=12 match=12 bad=0 stopped=0 traced=0 ... site_control_passed=0
  PATH54 total cases=2236 match=2236
  PATH54 result=ok
  ```
  (`...` the image-table reads and the two accounted scratch reads, and every control's separating, type-0 and passed counts, in
  full in `check.txt`; every control passes 0 of the cases it separates and separates at least one.)
  Distinct outcomes per family are the `OUTCOMES` lines: `real0` 8 end tags (431 exhausted, 72 past the tries, 81 of one point, 216 routes), `real16` 7, `stair` 4, `corr` 3, `open` 5, `rect` 8; each case also compares its own point list.
- **Count:** the `total` line's 4 330 includes the `spiral` family's 90, which match a model chosen to agree with the emulator; 4 240 cases test the game's code.
- **Conclusion:** the maps of path/0002 §§ 2–7 and the limits of § 9 are `[C]` to the planner's return (`grid`, `over`: to their boundaries) over the declared
  images; not what the game stores in a context, not `PathPlan`'s tail, not any other planner. No symbol raise (ADR-0015 scope,
  review-fixes rule 14). (run:2026-11-03-path-emu-2)

## run:2026-11-03-path-emu-3

- **Question:** (plan 0054 Phase 1, batches P1.3a and P1.3b) Do the short planners, `PathPlanType1`, `PathPlanType15`, the random walk, the client slots 3, 11, 12 and the two missile callbacks map a declared context or path over declared images to their return and the whole path record, as [path/0003](0003-short-planners.md) reads them, and does the scratch check catch an unaccounted read?
- **Setup:** Ghidra p-code emulator via `re/ghidra_scripts/EmuScratch.java` (`f359776b…`, with the `UX` line of the P1.2 check), lane project copy `workspace/ghidra-r54c`, heap 3 GB, under `systemd-run --user --scope -p MemoryMax=4G`; started 2026-11-03 23:50, ended 2026-11-04 00:00. No wine, no slot. Model and case writer `tools/path_emu3.py` (`3e18f991…`, copy `path_emu3.py.rev`; the revision differs from the one that ran only in `bounds`, and re-running `check` gives the same `check.txt`; the Tier B check then changed `check_probe`'s return so the third probe line counts, and `check.txt` is again byte-identical, `b629fe5b…`), every draw from `random.Random("r54c-…")`. Images in path/0003 § 13. Files in `workspace/logs/r54c/emu/`, `manifest.sha256` (`04850d1f…`, 201 lines; `check.txt` `b629fe5b…`); `sha256sum -c manifest.sha256` passes from that directory. Development runs under `emu/dev-1/`, `dev-2/`, `dev-3/`, each with its own manifest (161, 196, 183 lines); no claim cites them; path/0003 *Dead ends* says what moved.
- **Procedure:**
  ```
  D=workspace/logs/r54c/emu
  python3 -I tools/path_emu3.py grids --dir $D > $D/grids.txt
  python3 -I tools/path_emu3.py cases --dir $D > $D/cases.txt
  for f in probe greedy g98 gbound near knock onept t1real t1syn t1stair t15real t15syn t15stair rwalk spiral spiralobs h1 h1obs client; do
    GHIDRA_PROJ_DIR=workspace/ghidra-r54c GHIDRA_HEADLESS_MAXMEM=3G systemd-run --user --scope -q -p MemoryMax=4G \
      tools/ghidra.sh emuscratch $D/$f.cases $D/$f.mem > $D/$f.out 2> $D/$f.err
  done
  python3 -I tools/path_emu3.py check --dir $D > $D/check.txt
  ```
  Boundaries: every family observes the assert entry 0x00408090; `spiralobs` also 0x0040B330; `h1obs` also 0x00649970. Fatal and allocator entries are guards.
- **Observed** (`check.txt`; `...` the table reads and the controls, in full in the file):
  ```
  PROBE read: a planner entered with ECX below the stack's written bytes: U lines=2 unaccounted=2 first=pc=00679f78 size=4 unwritten=4 case_fails=yes
  PROBE overflow: memcpy over unwritten stack: U lines=200 overflow marker UX=312 case_fails=yes
  PROBE tightened: the same pc with another size or count is not accounted: yes
  PATH54C greedy cases=600 match=600 bad=0 stopped=0 traced=0 distinct=364 ... maxret=36
  PATH54C g98 cases=300 match=300 bad=0 stopped=0 traced=0 distinct=180 ... maxret=76
  PATH54C gbound cases=30 match=30 bad=0 stopped=0 traced=0 distinct=29 ... maxret=78
  PATH54C near cases=480 match=480 bad=0 stopped=0 traced=0 distinct=296 ... maxret=20 maxnodes=200 maxstack=5
  PATH54C knock cases=300 match=300 bad=0 stopped=0 traced=0 distinct=159 ... maxret=1
  PATH54C onept cases=200 match=200 bad=0 stopped=0 traced=0 distinct=65 ... maxret=1
  PATH54C t1real cases=400 match=400 bad=0 stopped=0 traced=0 distinct=223 ... maxret=11 maxnodes=200 maxstack=23
  PATH54C t1syn cases=240 match=240 bad=0 stopped=0 traced=0 distinct=240 ... maxret=24 maxnodes=200 maxstack=23
  PATH54C t1stair cases=40 match=40 bad=0 stopped=0 traced=0 distinct=26 ... maxret=77 maxnodes=200
  PATH54C t15real cases=400 match=400 bad=0 stopped=0 traced=0 distinct=178 ... maxret=40 maxn=51 maxline=70
  PATH54C t15syn cases=300 match=300 bad=0 stopped=0 traced=0 distinct=236 ... maxret=56 maxn=72 maxline=73
  PATH54C t15stair cases=40 match=40 bad=0 stopped=0 traced=0 distinct=34 ... maxret=12 maxn=69 maxline=57
  PATH54C rwalk cases=300 match=300 bad=0 stopped=0 traced=0 distinct=300 ... maxret=39 draws=5092
  PATH54C spiral cases=90 match=90 bad=0 stopped=0 traced=0 distinct=90 ... maxret=77 maxiters=95   (against the model that ROUNDS: path/0003 § 9; counted in the total, no evidence about the game)
  PATH54C spiralobs cases=30 match=30 bad=0 stopped=0 traced=0
  PATH54C h1 cases=300 match=300 bad=0 stopped=0 traced=0 distinct=300 ... maxret=39 draws=8192
  PATH54C h1obs cases=100 match=100 bad=0 stopped=0 traced=0
  PATH54C client cases=180 match=180 bad=0 stopped=0 traced=0 distinct=138 ... maxret=14
  PATH54C total cases=4330 match=4330
  PATH54C result=ok
  ```
  What each control separates is in path/0003 §§ 1–10; every one passes 0 of the cases it separates and separates at least one. Distinct outcomes per family are `distinct=` (return and point list) and the `OUTCOMES` lines.
- **Also kept**, `workspace/logs/r54c/manifest.sha256` (`9b81743a…`, 11 lines; it passes from that directory): `p3-h1log.txt` (the 45 logs of run:2026-10-25-skills, run:2026-10-27-skills and run:2026-10-30-skills-catalogue, 654 creations, 0 mismatches), `p3-stock.txt`, `p3-bounds.txt`, `p3-scan3c.txt`, `p3-rngcg.txt`, the disassembly and the decompile.
- **Count:** the `total` line's 4 330 includes the `spiral` family's 90, which match a model chosen to agree with the emulator; 4 240 cases test the game's code.
- **Conclusion:** the maps of path/0003 §§ 1–8 and 10 are `[C]` to each planner's return over the declared images; `spiralobs`, `h1obs` and the assert cases to their boundaries. Not what the game stores in a context, not `PathPlan`'s tail, not x87. The spiral stays `[I]`: the emulator's `FISTP` ignores the rounding field the code sets. H1's draws are also `[C]` from the game's logs. (run:2026-11-03-path-emu-3)

## run:2026-11-04-path

- **Question:** (plan 0054 Phase 2, `lane/p54`) Does `PathPlan` on the server, called by the game for its own units, return what the models of
  [path/0001](0001-pathplan-register.md) § 1, [path/0002](0002-search.md) and [path/0003](0003-short-planners.md) give from what the log holds:
  the return, the points the request leaves in the path record, and the exit seed of the unit?
- **Setup:** slot 1 (display `:8`, `workspace/wineprefix-1`), fresh game process per case (`tools/path_sessions.py`, harness-play.md § Fresh
  process), the logger `tools/gdb/path.gdb` (`pilot.py` + `path.py`), driven by `tools/d2pilot.py`, checked by `tools/path.py check`.
  Tool revisions: the 20 sessions of seeds 5401–5414 and 5501–5506 ran the logger **rev 3** (commit `a501a7fa`; the committed
  `tools/gdb/path.py` then); the last session, seed 5601 (`k4-dru-stony`), ran **rev 4** (commit `178106ec`: items in the unit list, which logged none, and the
  watchpoint control). `tools/path.py` is the revision of `178106ec`; its hashes are in `2026-11-04-path-tools.sha256`. Seeds 5401…, 5501…,
  5601 are the game's `-seed`; the characters are in `tools/d2s_recipes/` (`path-bar.json` on `smpbar`: Crushflange, Whirlwind, Leap, Leap Attack;
  `path-pal.json` on `smppal`: Blessed Hammer, Charge) and the saves of `tools/ai_sessions.py` / `tools/skills_sessions.py` (`CombatSor`, `AiNec`,
  `SkillsDru`). Environment per case: `PATH_SPIRAL_PROBE` (the spiral's probe, path/0004 § 6) on `k-pal-stony` (6) and `k-pal-jail` (4);
  `PATH_CHAIN` (seed watchpoints) on `k-dru-stony`, `k-dru-oasis`, `k4-dru-stony` (60 each); `PATH_CHAIN_CTL` (40) and `PATH_ITEMS` on `k4-dru-stony` only. Caps per game: 250 plans that
  reach a planner per path type, 40 refusals per type, 3 500 plans, 120 units per plan, radius 80 subtiles from the first player.
- **Cases** (21 kept, all `kept` by the runner: the character left its starting level where a waypoint was clicked; plans = `PLN` lines;
  level = the level id of the unit's room, `PLN.ar`; `workspace/logs/path/2026-11-04-path-s1-<seed>-<case>.log`):

  | case | seed | level (act) | plans | case | seed | level (act) | plans |
  |---|---:|---|---:|---|---:|---|---:|
  | k-town-bar | 5401 | 103 Pandemonium Fortress (4, town) | 251 | k-sor-oasis | 5410 | 43 Far Oasis (2) | 649 |
  | k-bar-stony | 5402 | 4 Stony Field (1) | 904 | k-sor-flayer | 5411 | 78 Flayer Jungle (3) | 854 |
  | k-bar-jail | 5403 | 29 Jail 1 (1, maze) | 106 | k-sor-river | 5412 | 107 River of Flame (4) | 735 |
  | k-bar-halls | 5404 | 57 Halls of the Dead 2 (2, maze) | 584 | k-sor-glacial | 5413 | 115 Glacial Trail (5) | 624 |
  | k-pal-stony | 5405 | 4 | 582 | k-necro | 5414 | 29 Jail 1 | 663 |
  | k-pal-jail | 5406 | 29 | 372 | k-sor-oasis-2 | 5501 | 43 | 1 420 |
  | k-dru-stony | 5407 | 4 | 465 | k-sor-river-2 | 5502 | 107 | 1 123 |
  | k-dru-oasis | 5408 | 43 | 808 | k-pal-stony-2 / -jail-2 / -stony-3 | 5503–5506 | 4, 29, 4 | 482, 250, 270 |
  | k-sor-jail | 5409 | 29 | 619 | k-sor-oasis-3 | 5505 | 43 | 1 143 |
  | k4-dru-stony | 5601 | 4 | 989 | | | | |

  (the town is Act IV's: the characters start there; a town case is `k-town-bar` and the first seconds of every case.) 21 logs, 60.0 MB,
  13 893 plans; `k-sor-oasis-2`, `-3`, `k-sor-river-2` and `k-pal-stony-2`, `-3`, `k-pal-jail-2` are repeats of a stage with another seed (the first batch left types 2 and 14 short); `k4-dru-stony` repeats `k-dru-stony` under the rev-4 logger.
- **Observed** (`2026-11-04-path-check.txt`, `sha256` prefix `8f6951c3`; the outcome mix and the controls in full in that file):
  ```
  PATH check logs=21 games=21 plans=13893 reached-a-planner=13265 matched=13893 mismatched=0 unmodelled=0
  type  plans   refused  match  maxret  draws   callers
     2    162         1    162       6      0   mode machine=162
     4   2740         0   2740       1      0   missile=2740
     5    696         0    696       5      0   mode machine=591,movement=105
     6    655         0    655       5      0   mode machine=553,movement=102
     7   2894       169   2894      21      0   mode machine=1462,player=1432
     8    282         0    282       1      0   mode machine=282
     9     54         0     54       1      0   player=54
    10    698         0    698      39    698   missile=698
    13   4078       227   4078      20      0   mode machine=3477,movement=601
    14     54         0     54      77      0   skill=54
    15   1580       231   1580      19      0   mode machine=1552,movement=28
  RESULT OK: 0 mismatches over 13893 reproduced plans; 0 unmodelled; controls passing a separated plan: 0; controls separating nothing: 6
  ```
- **Conclusion:** see path/0004 §§ 1–8. **Boundary of the 0 mismatches:** a plan is compared on its return (`EAX` of `PathPlan`), the first
  `EAX` point words of the path record after the call and the exit seed of the unit; nothing else of the record. It is a statement about the 11
  types listed (2, 4, 5, 6, 7, 8, 9, 10, 13, 14, 15), the planners they call (greedy, greedy-near with its type-1 switch, knockback, one point, type 15, the random
  walk, the spiral, the straight type 4), on the grids of rooms the logger dumped live at the planner call, and on server units within 80
  subtiles of the first player. **Not covered:** type 0 and the search (no logged plan), type 1 as a request (0 plans), types 3, 11, 12, 16 (no
  server plan), 628 refused requests (their return 0 and unchanged seed are compared; their reason only where the record gives it: 226 target = start, 191 window,
  211 'rooms, town or free step', which need the grid before the unmark), the tail of `PathPlan` beyond the refusal test (modelled `[I]`), the unit marks and doors as a cause of a
  refusal (the live cells already contain them).
  **Short:** type 1 (floor 100: 0 plans); the chained draws of § 5 (floor 50 type-10 plans: 70 watched, 68 of class 458, none drawn again before release; classes 195 and 225 one each). Not
  a floor: the first 10 plans' tie is **not exact** (path/0004 § 7). (run:2026-11-04-path)
- **Deviation (review, 2026-11-04): ADR-0003.** `k-pal-stony` and `k-pal-jail` ran the probe, a breakpoint that writes the start's fraction word. From each first write on, the plans (532 and 310, 842) are not stock, and the truncation they show is `[I]`. **Stock counts:** 13 051 plans, 12 427 reached, 624 refused; per type 2 162, 4 2 658, 5 649, 6 604, 7 2 753, 8 282, 9 54, 10 698, 13 3 709, 14 27, 15 1 455. `PATH_SPIRAL_PROBE` is not to be set again.
- **Review output:** `workspace/logs/path/review-p54/review.txt` (`sha256` prefix `93f9098e`, `manifest.sha256` passes from that directory), from `tools/path_review.py` (no game): the stock counts, the natural spiral lists, the control's cap and window, controls per type, type 1's controls on the switch, the model on an empty grid and on the tie's grid, the first plans' bits, the seed watchpoints in full, the corpses. The kept check was rerun at the review: same hash. (run:2026-11-04-path)

## 2026-11-04 `lane/p54b`: no game; logger rev 5 not run

- **No session ran.** `tools/path_review.py` retired into `tools/path.py check` (the review's revision at commit `e990dea0`). The check's rerun on the kept logs of run:2026-11-04-path: `workspace/logs/p54b/check.txt` (`d8211db0`, `manifest.sha256` passes from that directory, `PATH_DEV` the 13 development logs dev2..dev5). Same `RESULT` as the kept check. `audit: n/a, no check of a new run.`
- **Logger rev 5** (`tools/gdb/path.py`, [path/0005](0005-grid-rules.md) § Logger rev 5): read-only, tested on a fake `gdb`; first run is the next kept batch's.
- **Review of `lane/p54b`, no session.** `tools/path.py check` at the lane's tip reproduced `check.txt` (`d8211db0`). After the review's C3 and T1 corrections, `workspace/logs/p54b/check-review.txt` (`48603989`) differs from it in 8 lines, the cell counts and exact rooms of the two code passes; same wrong plans, same `RESULT`. `tools/corpse_copy.py` over run:2026-10-14-collision's seven logs: `corpse-copy.txt` (`db62d6cb`). `tools/collision.py`, unchanged, rerun on those logs: 20 537 collision checks, 0 mismatches. Both outputs in `manifest.sha256`. `audit: n/a, no check of a new run.`

## run:2026-11-04-path-2

The hold-out batch, `lane/p54c` (plan 0054 Phase 2, the kept batch of the `lane/p54b` review's order (a) to (h)).

- **Question:** do the rules of [path/0005](0005-grid-rules.md), fitted on run:2026-11-04-path, predict the live grid on logs taken after they were frozen; do rev 5's lines (`SPX`, `T1S`, `L1M`/`L1U`, `COR`, counted `BRK`, `HasCollision`, unit cap 400) answer their questions? Results: [path/0006](0006-holdout.md).
- **Setup:** slot 1 (display `:8`, `workspace/wineprefix-1`), a fresh game process per case (`tools/path_sessions.py` on `tools/harness_runner.py`), logger rev 5 (`tools/gdb/path.gdb`, `path.py` `d0a5f379d3a2`, read-only: the source holds no `write_memory`), driver `tools/d2pilot.py` (`899818c6282c`), tool commit `a7511120` (`path_sessions.py` `fbea4903ed5a`, which names the cases below), characters `PathBar`, `PathPal` (recipes `path-bar.json`, `path-pal.json`), `CombatSor`, `AiNec` (built by `path_sessions.py build`). `tools/path.py` `e2844c166519` before and after both runs. Saves set aside as `p54c` and restored. Seeds 6001–6026 (6018 development). Caps per game as in run:2026-11-04-path, unit cap 400, `PATH_CHAIN` 200 on the Nova cases of `CombatSor` (`k5-sor-oasis`, `-oasis-2`, `-flayer`, `-cotd`, `-river`, `-river-2`, `-glacial`). Tool hashes: `workspace/logs/path/2026-11-04-path-2-tools.sha256`.
- **Development launch first** (`dev-bar`, seed 6901, `dev-2026-11-04-path-2-s1-6901-dev-bar.log`): rev 5 armed, 0 `LOGERR`, `COR` at 0x004B05E3, 0x004B0A05 and 0x005A65D9, `L1M` at the three reached sites and `L1U`. Development logs (`dev/`, `dev/manifest-path-2-dev.sha256`): that log; `k5-hop-act` (6911) and `k5-hop-in` (6912, 6921), whose `wpchain` hops failed (path/0006 § Hop stages); `k5-bar-cotd-2` (6018), moved there after the batch: it reached level 107 instead of 106 and the pilot ended after 20 s with 24 plans, no stage.
- **Cases** (25 kept; level of the last `PLR`; plans = `PLN`; `workspace/logs/path/2026-11-04-path-2-s1-<seed>-<case>.log`, `manifest-path-2.sha256` passes from that directory):

  | case | seed | level | plans | case | seed | level | plans |
  |---|---:|---|---:|---|---:|---|---:|
  | k5-bar-cotd | 6001 | 106 (4) | 1 269 | k5-pal-river | 6013 | 107 (4) | 1 462 |
  | k5-bar-stony | 6002 | 4 (1) | 1 105 | k5-sor-cotd | 6014 | 106 | 946 |
  | k5-pal-stony | 6003 | 4 | 613 | k5-bar-stony-2 | 6015 | 4 | 829 |
  | k5-sor-oasis | 6004 | 43 (2) | 964 | k5-pal-stony-2 | 6016 | 4 | 707 |
  | k5-bar-river | 6005 | 107 | 1 312 | k5-sor-oasis-2 | 6017 | 43 | 903 |
  | k5-pal-cotd | 6006 | 106 | 852 | k5-pal-cotd-2 | 6019 | 106 | 964 |
  | k5-sor-river | 6007 | 107 | 1 142 | k5-sor-river-2 | 6020 | 107 | 1 114 |
  | k5-bar-jail | 6008 | 29 (1) | 229 | k5-bar-river-2 | 6021 | 107 | 1 464 |
  | k5-necro | 6009 | 29 | 474 | k5-pal-jail-2 | 6022 | **4** | 134 |
  | k5-pal-jail | 6010 | 29 | 169 | k5-sor-jail | 6023 | 29 | 442 |
  | k5-sor-flayer | 6011 | 78 (3) | 459 | k5-pal-halls | 6024 | 57 (2) | 910 |
  | k5-bar-halls | 6012 | 57 | 962 | k5-sor-glacial | 6025 | 115 (5) | 933 |
  | | | | | k5-town-a1 | 6026 | 1 (1, town) | 313 |

  (`k5-pal-jail-2` arrived in Stony Field (4), not Jail Level 1: the waypoint row clicked reached another level, so it is a Stony Field session; `k5-sor-flayer` ended after 60 s of its 200 s Nova stage; both kept as stages of the level they reached. The stage of each case was checked from the last `PLR` level and the plan count before counting it.) 25 logs, 20 671 plans.
- **Observed** (`2026-11-04-path-2-check.txt`, `d93dad5e`): `RESULT OK: 0 mismatches over 20 671 reproduced plans; 0 unmodelled; controls passing a separated plan: 0; controls separating nothing: 7`. Per type (plans): 2 476, 4 3 713, 5 628, 6 664, 7 4 589, 8 1 303, 9 346, 10 248, 13 4 872, 14 233, 15 3 599. Grid (`2026-11-04-path-2-grid.txt`, `56e8a1fb`): wrong plans of 15 663 under frozen own marks 472, corpse reading 472, O1+C1..C3+T1 72, with W1 62, with W1 and L1 **11**, all `0x1000`.
- **Conclusion:** [path/0006](0006-holdout.md). **Boundary of the 0 mismatches:** the planners given the game's live grids at the call, 11 types (2, 4, 5, 6, 7, 8, 9, 10, 13, 14, 15) on server units near the first player; not the predicted grid (11 wrong plans), not type 0, 1, 3, 11, 12, 16.
- **Short:** W1 floors (7 of 16 act changes and 3 of 9 in-act arrivals seen), `deadCol` 1 on the client and class 273, class 195 and 225 watched seeds (3 and 22 of 50), Jump, `T1S` 0 of 7, the type-1 stages, town-follow. `audit: n/a, Tier A.`
- **Review of `lane/p54c`, no session.** `tools/path.py check` and `grid` at the lane's tip reproduced `d93dad5e` and `56e8a1fb` byte for byte. `tools/path_holdout_review.py` (no rule added): `workspace/logs/path/review-p54c/ablate.txt` (`20354891a8b4`), each of O1, T1, C1..C3 off in the `code` pass, 204, 107, 89 against 72; `eleven.txt` (`c8f36656166b`), the 11 plans' lines. `manifest.sha256` passes from that directory. `audit: n/a, no check of a new run.`
