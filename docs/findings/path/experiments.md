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
- **Conclusion:** the maps of path/0002 §§ 2–7 and the limits of § 9 are `[C]` to the planner's return (`grid`, `over`: to their boundaries) over the declared
  images; not what the game stores in a context, not `PathPlan`'s tail, not any other planner. No symbol raise (ADR-0015 scope,
  review-fixes rule 14). (run:2026-11-03-path-emu-2)
