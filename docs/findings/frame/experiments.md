# Experiments — sim/frame

## run:2026-10-30-frame-emu

- **Question:** (plan 0055 Phase 1, batch P1.1) Do `ActClockTick`, `UnitMarkUpdated` and `RoomUpdatedClear` map their
  declared inputs to their return and the memory they write as [frame/0001](0001-tick-and-messages.md) §§ 3.1 and 3.3
  say?
- **Setup:** Ghidra p-code emulator via `re/ghidra_scripts/EmuBoundary.java` (`286393aa…`, unchanged), lane project copy
  `workspace/ghidra-r55` (symbols replayed from `re/symbols.csv`), heap 3 GB, under `systemd-run --user --scope -p
  MemoryMax=4G`. No wine, no slot. Models and case writers `tools/frame_emu.py` (`7d2efd93…`), every draw from
  `random.Random("r55-<family>")`; `cases` run twice gives identical files. Files in `workspace/logs/r55/emu/`,
  `manifest.sha256` (`60d57be2…`, 10 lines, `check.txt` `ba9c5c24…`); `sha256sum -c manifest.sha256` from that
  directory passes.
- **Procedure:**
  ```
  D=workspace/logs/r55/emu
  python3 -I tools/frame_emu.py cases
  for f in env mark clear; do
    GHIDRA_PROJ_DIR=workspace/ghidra-r55 GHIDRA_HEADLESS_MAXMEM=3G systemd-run --user --scope -q -p MemoryMax=4G \
      tools/ghidra.sh emuboundary $D/$f.cases $D/$f.mem > $D/$f.out 2> $D/$f.err
  done
  python3 -I tools/frame_emu.py check > $D/check.txt
  python3 -I tools/frame_emu.py manifest --write
  ```
  Each case writes only the fields its function reads: the act's clock pointer and the clock's six fields (`env`;
  20 cases with a null clock), the unit's type, `+0x2C`, `+0xC4`, `+0xE0`, the path's or the direct cell's room, and
  the room's `+0x1C`, `+0x2C`, `+0x34` and the act word (`mark`), and up to seven linked units (`clear`). The three
  clock tables `0x007443F0`–`0x007444C7` are declared case memory without being written: the image's own values are
  read (the xref scan lists only reads of them, frame/0001 § 3.1). The memory specs guard the allocator and fatal
  entries (0x00408090, 0x00408A60, 0x00681E09, 0x0040B4B0, 0x0040B430, 0x0040B480); no case reaches one.
- **Observed** (`check.txt`):
  ```
  FR55 env cases=420 match=420 bad=0 stopped=0 traced=0 neg_separating=12 neg_passed=0 neg=ge
  FR55 mark cases=300 match=300 bad=0 stopped=0 traced=0 neg_separating=102 neg_passed=0
  FR55 clear cases=120 match=120 bad=0 stopped=0 traced=0 neg_separating=105 neg_passed=0
  FR55 env cases=420 match=420 bad=0 stopped=0 traced=0 neg_separating=68 neg_passed=0 neg=flat
  FR55 env advances=197 returns1=284 bucket_moves=260
  FR55 result=ok
  ```
  Negative controls: `env` "ge" (advance on `>=`, 12 cases at the boundary separate it) and "flat" (the act 2 and act 3
  extra steps left out, 68 separate it); `mark` without the `0x2000` test (102 separate it); `clear` keeping the head
  (105 separate it). Every control fails every case it separates. Of the 400 clock cases 197 advance the period, 284
  return 1 and 260 move the bucket.
- **Conclusion:** the three maps are `[C]` in frame/0001 §§ 3.1 and 3.3: the clock step and its return, the mark (bit,
  front push, act word) and the clear, for the declared inputs. Not covered: the callers' loops, the scale and flag
  values the server sets, what the marked units are. No symbol raise (ADR-0015 scope, review-fixes rule 14).
  (run:2026-10-30-frame-emu)

## run:2026-10-30-frame-emu-2

- **Question:** (plan 0055 Phase 1, batch P1.2) Do the event queue's entries (`EventQueueAt`, `EventQueueEveryFrame`
  and their wrappers), `EventFree`, the cancel and free-all functions, the five list runners and `GameRunUnitEvents`
  map their declared inputs to the memory they write as [frame/0002](0002-unit-events-queue.md) §§ 1–2 say?
- **Setup:** Ghidra p-code emulator via `re/ghidra_scripts/EmuBoundary.java` (`286393aa…`, unchanged), lane project
  copy `workspace/ghidra-r55b` (symbols replayed from `re/symbols.csv` at lane start), heap 3 GB. No wine, no slot.
  Models and case writers `tools/frame_queue_emu.py` (`44ff146b…`), every draw from `random.Random("r55b-<family>")`.
  The declared image: the game, the event control (0xA20 bytes), two record blocks (24 and 8 records in use, the
  block headers), eight units of types 0, 1, 1, 2, 3, 3, 4, 1; the memory spec zeroes all of it before each case and
  writes the image's own `g_UnitTypeEventList` once (`const`); each case writes its state's non-zero dwords (a state
  built by the model's own queue calls: an input, not a claim) and dumps every region after the call. Guards: the
  fatal entries and the allocators (0x00408090, 0x00408A60, 0x00681E09, 0x0040B4B0, 0x0040B430, 0x0040B480,
  0x00540BB0); no case reaches one. Observed boundaries (ADR-0021) in `qat`, `run` and `tick`: `UNIT_HasState`
  0x00639DF0 and the five dispatches 0x00581220, 0x005A7F80, 0x00586AD0, 0x005ADCC0, 0x00562DA0. Kept files in
  `workspace/logs/r55b/emu/`, `manifest.sha256` (`b1b00fea…`, 19 lines, `check.txt` `3df20e99…`); `sha256sum -c
  manifest.sha256` from that directory passes.
- **Procedure:**
  ```
  D=workspace/logs/r55b/emu
  python3 -I tools/frame_queue_emu.py cases
  for f in qat qef free cancel run tick; do
    GHIDRA_PROJ_DIR=workspace/ghidra-r55b GHIDRA_HEADLESS_MAXMEM=3G \
      tools/ghidra.sh emuboundary $D/$f.cases $D/$f.mem > $D/$f.out
  done
  python3 -I tools/frame_queue_emu.py check > $D/check.txt
  python3 -I tools/frame_queue_emu.py manifest --write
  ```
  The kept run was made without the memory scope; a rerun of all six families under `systemd-run --user --scope -p
  MemoryMax=4G` into `workspace/logs/r55b/dev/emu-rerun/` gives byte-identical `.cases`, `.mem` and `.out` files
  (`cmp`, 18 files; `dev/manifest-emu-rerun.sha256` `a6a768d0…`, 18 lines, passes from `dev/`).
- **Observed** (`check.txt`):
  ```
  FR55B qat cases=400 match=400 bad=0 boundary=41 traced=0 neg=qat-head neg_separating=241 neg_passed=0
  FR55B qat counts boundary=37 every-frame=14 every-frame-callback-dropped=3 kept=250 negative-kind=14 raised=79 rejected=20 second-block=24 slot-nonempty=241
  FR55B qef cases=150 match=150 bad=0 boundary=0 traced=0 neg=qef-tail neg_separating=36 neg_passed=0
  FR55B qef counts kept=138 rejected=12
  FR55B free cases=300 match=300 bad=0 boundary=0 traced=0 neg=free-noadvance neg_separating=96 neg_passed=0
  FR55B free counts advance=96 at-head=160 at-tail=184 ef=75 no-unit=26 running=62 slot=163
  FR55B cancel cases=150 match=150 bad=0 boundary=0 traced=0 neg=cancel-kindonly neg_separating=3 neg_passed=0
  FR55B cancel counts cancel=60 cancelcb=27 freeall=27 freeall2=36
  FR55B run cases=300 match=300 bad=0 boundary=35 traced=0 neg=run-nextafter neg_separating=96 neg_passed=0
  FR55B run counts boundary=35 list0-mode0=30 ... list4-mode1=30 slot-record-not-due=169
  FR55B tick cases=100 match=100 bad=0 boundary=33 traced=0 neg=tick-playersfirst neg_separating=33 neg_passed=0
  FR55B tick counts boundary=33 complete=67
  FR55B result=ok
  ```
  The `qat` counts are by precedence (refused, every-frame, raised, boundary, kept); `boundary=41` on the first line
  counts every case that ended at `UNIT_HasState`, 4 of them after a raise. Negative controls: `qat` slot insert at the
  head (241 separate it), `qef` append at the tail (36), `free` no advance of the walker's next (96), `cancel` kind only
  (3), `run` the next read after the run (96), `tick` players before missiles (33); each fails every case it separates.
- **Development runs** (not cited): `workspace/logs/r55b/dev/emu1/` (tag `dev1`) and `dev/emu2/` (tag `dev2`, `qat` and
  `run` only), made by two earlier revisions of `tools/frame_queue_emu.py` (the first with fewer crowded slots and
  monster AI cases; not kept), all 0 mismatches; manifests `dev/manifest-emu1.sha256` (`75e1327b…`, 18 lines) and
  `dev/manifest-emu2.sha256` (`53d7a67e…`, 14 lines), both passing from `dev/`.
- **Conclusion:** the queue's insertion, free, cancel and walk maps are `[C]` in frame/0002 §§ 2.1–2.4 for the
  declared inputs, and the pass's walk order in § 1 as far as `tick`'s cases reach (the dispatch first reached names the
  list). Not covered: the dispatches and every event function, the block allocator, `UninterruptibleEnd`, a callback
  that frees another record, a frame counter near 2³¹. No symbol raise (ADR-0015 scope, review-fixes rule 14).
  (run:2026-10-30-frame-emu-2)
- **Review addendum (P1.2 review, 2026-10-30): `cancel`'s controls.** The run's control separates 3 cases. Three more
  wrong readings scored against the kept `cancel.out` (no re-run): `python3 -I tools/frame_queue_controls.py >
  workspace/logs/r55b/review/cancel-controls.txt` (tool `758a1eea…`, output `063b97d8…`, `review/manifest.sha256`
  `ebb50d18…`, 1 line, passes from `review/`):
  ```
  FR55BC cancel neg=cancel-kindonly separating=3 passed=0 by_op=cancel:3
  FR55BC cancel neg=always-a separating=10 passed=0 by_op=cancel:10
  FR55BC cancel neg=cb-zero separating=3 passed=0 by_op=cancelcb:3
  FR55BC cancel neg=reverse separating=5 passed=0 by_op=cancel:5
  FR55BC result=ok
  ```
  "The chain's next is read before the free" separates no case (`EventFree` leaves `+0x24`) and is `[I]` in
  frame/0002 § 2.3. (run:2026-10-30-frame-emu-2)

## run:2026-10-30-frame-emu-3

- **Question:** (plan 0055 Phase 1, batch P1.3) Do `QUESTS_TimersRun`, `RoomsDeactivate`, the 1 500-frame expiry
  sweep (`0x0052D310` with `0x00558B90` and `0x00542AC0`), the kind-6 handlers of players and monsters and
  `NewRoomsUpdate`'s act walk map their declared inputs to the memory they write and the boundary they reach as
  [frame/0003](0003-timers-activation.md) §§ 1, 2, 4 and 7 say?
- **Setup:** Ghidra p-code emulator via `re/ghidra_scripts/EmuBoundary.java` (`286393aa…`, unchanged), lane project
  copy `workspace/ghidra-r55c` (symbols replayed from `re/symbols.csv` at lane start), heap 3 GB, every run under
  `systemd-run --user --scope -p MemoryMax=4G`. No wine, no slot. Models, case writers and checker
  `tools/frame_timers.py` (`1dd75a73…`), every draw from `random.Random("r55c-<family>")`; `cases` run twice gives
  identical files (`cmp`, ten files). The declared image: a game, the quest control and its timers, five acts, rooms,
  units, item data, inactive-record lists and records, a chat record; the memory spec zeroes it before each case in
  0x800-byte directives (see *Development runs*). Guards: the allocator and fatal entries (0x00408090, 0x00408A60,
  0x00681E09, 0x0040B4B0, 0x0040B430); no case reaches one. Observed boundaries (ADR-0021), each asserted with its
  arguments and its call site (the `A` line's return address): the free 0x0040B480 (`timers`, `sweep`),
  `RoomReleaseAllowed` 0x0061A3F0 (`deact`, with `InactiveUnitSaveTest` and `ActiveRoomFree` declared too),
  `UnitGetRoom` 0x00620BB0 (`sweep`), `ChatRecordFree` 0x006611A0 and `UnitQueueEvent` 0x005417D0 (`k6`, with
  `UnitMarkUpdated`), `RoomWandererTick` 0x0054F060 and the five other population entries (`nru`). **Stand-ins**
  (`timers` only, stated): the timer callbacks are game functions whose whole body returns a constant `AL`
  (0x00407DD0 `xor al, al; ret`, 0x004BDAF0 `mov al, 1; ret`), and the `IsBadCodePtr` import slot 0x006CC34C holds, as
  a `const` of the spec, a game function returning `EAX` = 0 that pops one argument (0x004BAD70), in place of the OS
  call (`cbscan.txt` in `workspace/logs/r55c/static/`). Kept files in `workspace/logs/r55c/emu/`, `manifest.sha256`
  (`269cde48…`, 21 lines, `check.txt` `c37bcd4f…`); `sha256sum -c manifest.sha256` from that directory passes.
- **Procedure:**
  ```
  D=workspace/logs/r55c/emu
  python3 -I tools/frame_timers.py cases $D
  for f in timers deact sweep k6 nru; do
    GHIDRA_PROJ_DIR=workspace/ghidra-r55c GHIDRA_HEADLESS_MAXMEM=3G systemd-run --user --scope -q -p MemoryMax=4G \
      tools/ghidra.sh emuboundary $D/$f.cases $D/$f.mem > $D/$f.out 2> $D/$f.err
  done
  python3 -I tools/frame_timers.py check $D > $D/check.txt
  python3 -I tools/frame_timers.py manifest $D --write
  ```
- **Observed** (`check.txt`):
  ```
  FR55C timers cases=300 match=300 bad=0 stopped=0 traced=0
  FR55C timers counts complete=224 removed=76 wrap=33
  FR55C deact cases=300 match=300 bad=0 stopped=0 traced=0
  FR55C deact counts complete=221 released=79
  FR55C sweep cases=300 match=300 bad=0 stopped=0 traced=0
  FR55C sweep counts complete=116 off-period=65 rec=79 unit=40
  FR55C k6 cases=200 match=200 bad=0 stopped=0 traced=0
  FR55C k6 counts monster-free=49 monster-none=10 monster-requeue=41 player-free=48 player-none=14 player-requeue=38
  FR55C nru cases=200 match=200 bad=0 stopped=0 traced=0
  FR55C nru counts complete=112 walked=88
  FR55C result=ok
  ```
  Negative controls, one per half of each claim, scored on the kept outputs (`separating` the cases where the wrong
  reading's prediction differs; `passed` 0 for every one): `timers` tail first 74, `≤` 47, signed 89, no wrap 23,
  re-arm from `due` 176, no unlink 76; `deact` at 10 86, no reset 263, acts reversed 77; `sweep` period 20 34, items `<`
  15, records `≤` 110, acts reversed 73, records before items 10; `k6` `<` 26, signed 24; `nru` tail first 45, flag kept
  101, acts reversed 63. The counts: `removed` the timer cases that end at a free, `wrap` the cases at tick
  `0xFFFFFFFF` with a timer; `released` the cases that reach `RoomReleaseAllowed`; `unit` and `rec` the sweep cases
  ending at an item unit or a freed record, `off-period` those whose frame is no multiple of 1 500.
- **Development runs** (not cited): `workspace/logs/r55c/dev/emu1/` and `dev/emu2/` (memory specs with `bytes`
  directives of up to 0x2000 and of up to 0x1000 bytes: 2 `deact` mismatches in each, both an empty-room case whose dump held the
  previous case's room; `emu1`'s `sweep` check stopped on a packing error of the checker), `dev/emu3/` (0x800-byte
  directives, all five families 0 mismatches, an earlier case generator with fewer wrap and period-20 cases),
  `dev/emu4/` (`timers` and `sweep` only, the kept generator); `dev/zerotest/` (one two-case file against `bytes`
  directives of 0x800, 0xFFF, 0x1000 and 0x1800 bytes: the first two re-zero, the last two do not). Manifests
  `dev/manifest-emu1.sha256` (`69237024…`, 20 lines), `-emu2` (`5043b081…`, 20), `-emu3` (`dfbea989…`, 20), `-emu4`
  (`64960a2f…`, 14), `-zerotest` (`3eeafa22…`, 9), each passing from `dev/`.
- **Imports, ADR-0029 (d)** (added 2026-11-04, `lane/r29`, no re-run): `timers` holds slot `0x006CC34C`
  `KERNEL32!IsBadCodePtr` at the stand-in `0x004BAD70` (`33 C0 C2 04 00`), rule (b); its `[C]` reads "given the import
  returned 0", and that value and the fatal branch at `0x00543EEB` are `[I]`. Not evidenced: what the import does, a
  fault, a wait. `deact`, `sweep`, `k6`, `nru` write no import slot. (0x00543E73, run:2026-11-04-lock-scan)
- **Conclusion:** the five maps are `[C]` in frame/0003 §§ 1.2, 1.4, 2, 4 and 7 for the declared inputs, up to each
  observed boundary. Not covered: `QUESTS_TimerAdd` (allocates), every real timer callback, the release test, the
  saves, the frees, the population calls, the writes after each boundary, and the next-pointer reads before the
  deactivation's and the sweep's tests (no case separates them). No symbol raise (ADR-0015 scope, review-fixes rule 14).
  (run:2026-10-30-frame-emu-3)

## run:2026-11-03-emu-spec-reapply

Static, no game and no slot (plan 0055, `lane/r55e`; backlog 2026-10-30 architect → reverser, from the plan 0055 P1
review). A tool fix and its test, then a re-run of the kept emulations it could have touched.

- **Question:** (1) Why did a per-case memory-spec directive of 0x1000 bytes or more keep the previous case's writes
  (frame/0003 *Dead ends*), and does the fixed `EmuTrace.java`, `EmuBoundary.java` and `EmuCall.java` re-apply every
  per-case directive for every case? (2) Do the six kept emulations whose per-case specs hold such a directive give the
  same output with the fixed scripts?
- **Cause** (Ghidra 12.1.2's own source, `Emulation-src.zip`): `EmulatorHelper.writeMemory` calls
  `MemoryState.setChunk`, which splits the write into pages; `MemoryPageBank.setPage` (inherited by the
  `FilteredMemoryPageOverlay` that `DefaultEmulator` uses) stores `new MemoryPage(val)` when a chunk is a whole page
  *and* its offset in the caller's buffer is 0, and `MemoryPage(byte[])` keeps that array as the page's data, with no
  copy. So for a directive that starts on a 4 KiB boundary and is 0x1000 bytes or more, the first page *is* the spec's
  byte array: the case's `w` writes and the emulated code's stores into that page went into the array, and the next
  case's re-apply wrote them back. A later whole page of the directive has a non-zero buffer offset and is copied, as
  is every partial page. The scripts kept one array per directive for the whole run, so every case after the first was
  exposed.
- **Fix:** each case writes `what.get(i).clone()`, a fresh copy, for every per-case directive (one line in each of the
  three scripts, with a header note). `const` directives are still written once, from their own array, by design.
  Revisions: `EmuTrace.java` `3255db0c…` → `0753a291…`, `EmuBoundary.java` `286393aa…` → `0c88b790…`, `EmuCall.java`
  `d7e4bb10…` → `0cba26de…` (pre-fix hashes at `dda63dfd`). `EmuFastcall.java` and `EmuCalcFunc.java` write only
  8-byte seeds and fresh 4-byte arrays per case and are not affected.
- **Setup:** lane project copy `workspace/ghidra-r55e`, heap 3 GB, each headless run under
  `systemd-run --user --scope -p MemoryMax=4G`, one instance. New tools: `tools/emu_zerotest.py` (`afc4d1b1…`, the
  no-case-dependence test, deterministic, uses `tools/rng.py`'s `rng_range`) and `tools/emu_spec_scan.py`
  (`d013c72b…`, lists every memory spec under a log tree with a per-case directive that starts page-aligned and is
  0x1000 bytes or more). Files in `workspace/logs/r55e/`: `manifest.txt` (`c26d6048…`, the top-level files and the two manifests
  below), `commands.txt`, `tools-revisions.txt`, `scan.txt` (`e3dd2634…`); `zerotest/` with
  `manifest-zerotest.sha256` (`b4ec7155…`, 76 lines, passes from `zerotest/`), `zerotest/check.txt` (`ca2ecb7f…`) and the
  pre-fix control scripts (`control-scripts/`, the `dda63dfd` files with their classes renamed `*Old`); `rerun/` with
  `manifest-rerun.sha256` (`50e90a44…`, 10 lines, passes from `rerun/`) and `rerun/compare.txt` (`33aac500…`). Each
  manifest sits beside its directory and passes with `sha256sum -c ../manifest-<name>.sha256` run inside it.
- **Procedure:** `commands.txt`. The test: a spec of one directive with the 64-bit seed `0x9ABCDEF0:12345678` at
  `+0x78`; three identical cases of `RNG_Range(seed, 0x10000)` (`call 0045c390 <start+0x78> 00010000`), the first with a
  `w` of `05000000` at `+0x100`, each dumping the seed and `+0x100` (EmuCall: three identical `ecx edx` lines). Specs:
  `bytes` of 0x800, 0xFFF, 0x1000, 0x1800 at `0x10300000`, 0x2000 at `0x10300800` (unaligned), `load` of 0x1000 at
  `0x10300000` and 0x46230 at `0x7F800000` (EmuTrace and EmuBoundary); `load` of 0x800, 0x1000, 0x1800 at `0x10300000`,
  0x2000 at `0x10300800` and 0x46230 at `0x7F800000` (EmuCall). One headless run ran the fixed scripts and the controls
  over all of them (`zerotest/run.sh`); `emu_zerotest.py check` scores each output against the model. The re-run:
  `rerun/run.sh`, one headless run, the kept cases and specs read in place (never rewritten), outputs under `rerun/`,
  then `cmp` of each with the kept output.
- **Observed** (`zerotest/check.txt`, `ZT` lines summarised; `pass` = all three cases return the model's `0x0000E948`
  and the model's seed, and the `w` bytes appear in case 1 only):
  ```
  fixed   EmuTrace 7/7 pass, EmuBoundary 7/7 pass, EmuCall 5/5 pass
  control EmuTraceOld, EmuBoundaryOld: pass b800 bFFF b2000u, fail b1000 b1800 l1000 l46230   (eax e948 cefc 2e19)
          EmuCallOld: pass l800 l2000u, fail l1000 l1800 l46230                             (eax e948 cefc 2e19)
  ZT summary outcomes_unexpected=0
  ```
  A failing control returns the model's first draw, then the second and third draws of the same seed: each case
  started from the seed the previous case left. The controls fail exactly the specs whose directive starts on a page
  boundary and is 0x1000 bytes or more; the unaligned 0x2000 directive (first page partial, second page copied) passes
  before the fix too.
  `scan.txt` (`SUMMARY specs=483 affected_specs=18 affected_directives=55`, `workspace/logs/r55e/` itself skipped):
  the six kept runs the entry names, and twelve development specs of `lane/r55c` (`r55c/dev/emu1/`, `dev/emu2/`,
  `dev/zerotest/z0x1000`, `z0x1800`). No spec under `r52*/emu/` (the plan 0052 `ai-cat-emu` runs, 233 `.mem` files) holds a
  directive of 0x1000 bytes or more, per-case or `const`. Every long directive in the tree is page-aligned (no
  `LONG-UNALIGNED` line); the 26 others are `const`.
  `rerun/compare.txt`:
  ```
  sweep-s1e/calcvar.out        5 053 lines  identical (27754eb9…)
  sweep-s1e/eval.out          18 083 lines  identical (c98c70db…)
  sweep-s1f/calcvar2.out       3 010 lines  identical (77d49abf…)
  sweep-s1f/varroll.out        9 000 lines  identical (b322281e…)
  calc-emu/eval/eval.out         236 lines  identical (93337d6b…)   EmuCall 0x0064B7C0
  p51s/emu/calcemu/eval.out      242 lines  identical (85e8e041…)
  ```
- **Conclusion:** `[C]` the three scripts now re-apply every per-case directive for every case, whatever its length
  and alignment, on the test's 19 script-and-spec runs (7 specs under EmuTrace and EmuBoundary each, 5 under EmuCall);
  the pre-fix scripts did not on exactly the 11 runs whose spec is aligned and 0x1000 bytes or more. `[C]` the six kept emulations are byte-identical with the fixed scripts, so no claim resting on them changes
  and no finding note is needed (data/0005, run:2026-10-16-calc-emu; run:2026-10-27-p51s-emu; the S1e and S1f records
  in [data/experiments.md](../data/experiments.md)). `[I]` the two `deact` mismatches of `r55c/dev/emu1/` and
  `dev/emu2/` are this effect (an empty-room case dumping the previous case's room from a page-aligned directive); those
  development runs are not re-run. (fn:RNG_Range@0x0045C390, fn:MISS_EvalCalc@0x0064B7C0, run:2026-11-03-emu-spec-reapply)
## run:2026-11-03-frame-order

- **Question:** (plan 0055 Phase 2a) Does the frame order of [frame/0001](0001-tick-and-messages.md)–[0003](0003-timers-activation.md)
  predict the logged order of every frame of the kept corpus with two or more events, and the seed hand-off of every
  pair of events on one seed in one frame? How many of the resynchronised skill entries of plans 0045 and 0052 does it
  re-chain, and how many cross-type every-frame runs do the kept logs hold? ([frame/0004](0004-order-on-kept-logs.md))
- **Setup:** no game, no wine, no slot, no Ghidra: a replay of kept logs. Input: the 331 frame-stamped, run-attributed
  corpus logs of plan 0055 Phase 0 (`workspace/logs/frame-corpus/frame-corpus-logs.tsv` `12c71c1c…`, each log's sha256
  in it), read by `tools/frame_corpus.py` (`287f3761…`, unchanged) `read_events`; the pinned `game.exe` (`631066c1…`)
  disassembled by `objdump` for the reach; the kept gap lists of run:2026-10-27-skills
  (`workspace/logs/skills/2026-10-27-skills-part1-gaps.txt` `5f43d175…`, `2026-10-27-skills-gaps.txt` `6843be4a…`).
  Tool `tools/frame.py` (`73715f53…`, commit `eb962968`), tests `tools/test_frame.py` (`d3e87689…`, 18 tests). Every
  replay under `systemd-run --user --scope -p MemoryMax=4G`, one at a time. Kept files in `workspace/logs/p55a/`,
  `manifest.sha256` (`11056497…`, 8 lines); `sha256sum -c manifest.sha256` from that directory passes.
- **Procedure:**
  ```
  K=workspace/logs/p55a
  python3 -I tools/test_frame.py > $K/test.txt 2>&1
  python3 -I tools/frame.py kinds > $K/kinds.tsv
  systemd-run --user --scope -q -p MemoryMax=4G python3 -I tools/frame.py reach > $K/reach.txt
  systemd-run --user --scope -q -p MemoryMax=4G python3 -I tools/frame.py check --out $K/check workspace/logs \
      > /dev/null 2> $K/check-progress.txt
  systemd-run --user --scope -q -p MemoryMax=4G python3 -I tools/frame.py rechain --out $K/rechain-gaps.txt \
      workspace/logs workspace/logs/skills/2026-10-27-skills-part1-gaps.txt workspace/logs/skills/2026-10-27-skills-gaps.txt \
      > $K/rechain.txt
  ```
  Exit codes 0 (`check` exits 1 on any order mismatch, nesting conflict, inverted slot pair, oldest-first missile pair
  or reversed hand-off).
- **Observed** (`check/check.txt` `106aa180…`, 471 lines; `check/frame-check-logs.tsv` `17825a3c…`, one row per log;
  `kinds.tsv` `e1f30175…`, 115 kinds; `reach.txt` `e8277d18…`, 89 hooks; `rechain.txt` `40258860…`;
  `rechain-gaps.txt` `7f1c951c…`, 477 gaps; `test.txt` `5b2b5ea9…`, `OK`; `check-progress.txt` `7b9623da…`, 331 logs):
  ```
  logs 331  events 6436250  no unit id 5338066  no seed 5061144  segments 331
  frames2 501689  events in frames2 6176531  frames placed2 192294
  compared 1719463  compared own 267695  separating 14061  mismatch 0  nesting conflicts 0
  controls: monsters-before-players events 17040 frames 5997; slot-before-every-frame 9608 / 7924;
            missiles-after-items 110 / 46; drain-before-the-tick 87 / 87
  slot order: MDS pairs in queue order 4566, PDS 13, inverted 0 (matched MDS 41178 of 51842, PDS 17476 of 19125;
              records cancelled 9812)
  every-frame order: MF0 pairs newest first 24652 in 4710 frames, oldest first 0
  cross-type EF: monster 926 this frame (mis-ef 79, plr-slot 847); player 0 (2 in mon-slot: next frame)
  seed hand-offs: handed 1023086, stepped 42310, reversed 0, off 0
  rechain: part 1 player 43 listed 0 re-chained, monster 171 / 0; part 2 player 103 / 7, monster 160 / 0
  ```
  Per logger (events; compared, of them by own kind; separating): anim 1 762 331; 66 404, 66 404; 13 967. skills
  209 310; 32 583, 29 810; 94. stats 4 275 908; 1 619 807, 171 283; 0. economy 50 189; 486, 122; 0. economy2 9 807;
  183, 76; 0. combat 126 285, two-combat 575, economy-hire 1 223, h6b 622: none compared. Mismatches 0 in each. The
  limits: stats, economy, economy2, economy-hire and h6b carry no unit id on any event, h6b no seed (`check.txt` § per
  logger).
- **Development runs** (not cited): `workspace/logs/p55a/dev/`: `run1-crash.err` (the first full pass stopped on a
  list-valued `w` field of stats' `RNGA`); `run2/` (tool `c8298557…`, uncommitted: 2 277 `MDS` mismatches from `EF`
  lines without a phase, 4 inverted slot pairs from cancels not applied); `run3/` (`cd936f2b…`, uncommitted: both fixed,
  0 mismatches); `run4/` (`a8e183f8…`, commit `6fba3cd1`: 4 "off" hand-offs between the server's and the client's
  player); `run5/` (`b8731d13…`, `8f6d9fa6`: 20 "off" across pointers reused in a frame); `run6/` (`1d930258…`,
  `6ecfb7db`) and `run7/` (`4117be67…`, `a7fb027b`): the kept counts, without the return-address list and the
  separating pairs by rule. `dev/manifest-dev.sha256` (`dabf2b83…`, 39 lines) passes from `dev/`.
- **Conclusion:** frame/0004's `[C]` claims: the pass and walk order with 0 mismatches and the separating pairs and
  controls above; the slot lists oldest queued first and the missiles' every-frame list newest first in the game's own
  runs; the drain's stamp for the skill-request handlers; the seed hand-offs; 926 monster cross-type every-frame queues;
  7 more resyncs re-chained (142 of 281 player gaps, 0 of 331 monster gaps). No symbol raise (no logged return compared;
  review-fixes rule 14). (run:2026-11-03-frame-order)

## run:2026-11-03-frame-order-2

- **Question:** (plan 0055 Phase 2a-ii) With the pointer tables and stored callbacks behind the 74 open hooks declared, how many hooks get a pass, how many frames place two or more events, and does the order still hold? ([frame/0005](0005-dispatchers.md))
- **Setup:** no game, no wine, no slot. Input as run:2026-11-03-frame-order: the 331 corpus logs (`frame-corpus-logs.tsv` `12c71c1c…`) and the pinned `game.exe` (`631066c1…`). Tool `tools/frame.py`: `check` and `check --direct` on `a21171fc…` (commit `966613c8`); `kinds`, `reach` and the tests on `9d6487a6…` (commit `6cb4a3a2`, one anchor string changed, no logic). `tools/test_frame.py` `02d81f8c…`, 23 tests; `tools/frame_corpus.py` `287f3761…`, unchanged. Every replay under `systemd-run --user --scope -p MemoryMax=4G`, one at a time. Kept files in `workspace/logs/r55f/`, `manifest.sha256` (`2109a8b4…`, 24 lines); `sha256sum -c manifest.sha256` from that directory passes.
- **Procedure:**
  ```
  K=workspace/logs/r55f
  python3 -I tools/test_frame.py > $K/test.txt 2>&1
  systemd-run --user --scope -q -p MemoryMax=4G python3 -I tools/frame.py kinds --resolved > $K/kinds.tsv
  systemd-run --user --scope -q -p MemoryMax=4G python3 -I tools/frame.py reach > $K/reach.txt
  systemd-run --user --scope -q -p MemoryMax=4G python3 -I tools/frame.py reach <42 dispatchers> > $K/dispatchers.txt
  systemd-run --user --scope -q -p MemoryMax=4G python3 -I tools/frame.py check --out $K/check workspace/logs \
      > /dev/null 2> $K/check-progress.txt
  systemd-run --user --scope -q -p MemoryMax=4G python3 -I tools/frame.py check --direct --out $K/check-direct \
      workspace/logs > /dev/null 2> $K/check-direct-progress.txt
  ```
  Exit codes 0 for both checks (`check-rc.txt`). `classes.txt` and `pairs.txt` are awk sums over `check/check.txt`. `reads/` holds the Ghidra decompiles read (`dec1.c`–`dec7.c`), `edges.py` with `edges.txt` (the declared edges by class) and `chains-example.py` with `chains-example.txt`.
- **Observed** (`check/check.txt` `f4f4499d…`, 507 lines; `check/frame-check-logs.tsv` `0989184c…`; `check-direct/check.txt` `dd1bf530…`; `kinds.tsv` `c7d1a1e0…`, 115 kinds; `reach.txt` `072d76ca…`, 89 hooks; `dispatchers.txt` `b4249d9b…`; `test.txt` `eb79a834…`, `OK`):
  ```
  hooks 89: reach 16, dispatch 8, universal 65; of the 74 open in Phase 2a: dispatch 8, reach 1, universal 65
  open functions 54 (50 shared by the 65)
  logs 331  events 6436250  segments 331
  frames2 501689  events in frames2 6176531  frames placed2 383349
  compared 3713293  compared own 646824  separating 17254  mismatch 0  nesting conflicts 0
  frames placed2 any 501659  events placed any 6168827  frames2 all placed 494897
  separating without the logged phase 9029; with a hook closed by a declared edge 4436
    (PS0 3820, AD0 568, DR0 90, KBE 1)
  controls: monsters-before-players 42148 / 19242; slot-before-every-frame 9608 / 7924;
            missiles-after-items 8885 / 729; drain-before-the-tick 95 / 95
  ```
  `check --direct` equals run:2026-11-03-frame-order in its totals, controls, separating pairs and later sections; only the new counter lines differ. The slot, every-frame, cross-type and seed sections of `check/check.txt` equal that run's.
- **Development runs** (not cited for a count): `workspace/logs/r55f/dev/`: `run1/` (five logs); `reach-dev1..4` (the declarations growing); `diag-before-entries.txt` (88 of 89 closed, before table entries became function entries); `downward-closure.txt`; `aborted1/` (a full check stopped at about 105 logs when three table bounds proved too long; `ef673711`). `dev/manifest-dev.sha256` (`e72339cd…`, 18 lines) passes from `dev/`.
- **Conclusion:** frame/0005's `[C]` claims: 0 mismatches over 383 349 frames with two or more closed sets, with the separating pairs and controls above; the order of `PathStep` (monsters' half), `UNIT_AnimAdvance` and `RunStaminaDrain` against their logged neighbours, by their pair counts (frame/0005 § 6). Phase 2a's Done-when stays unmet as written: 118 340 frames hold fewer than two closed sets. No symbol raise (no logged return compared; review-fixes rule 14). (run:2026-11-03-frame-order-2)

## run:2026-11-04-frame

- **Question:** (plan 0055 Phase 2b, the pilots) Do the frame windows of the Act I town and of Cold Plains with a pack pass the plan's (a) whole, (b) unmoved and (c) carried tests?
- **Setup:** harness slot 1, one fresh single-player process per scene (`-ns`, map seed 5501), character `tools/d2s_recipes/framenova.json` (Sorceress clvl 80, expansion, normal, Act I start); logger `tools/gdb/frame.gdb` (`tools/gdb/frame.py` rev 1 at commit `8f026bf2`, `a6ecf7cd…`), reader `tools/frame.py window` (`tools/frame_window.py` `4ae96fec…`), runner `tools/frame_sessions.py` (`995db897…`); pilot `tools/d2pilot.py`. Pinned `game.exe` `631066c1…`. Predictions committed before each kept log (`abb7ebb6`, `241adf4a`).
- **Procedure:**
  ```
  python3 -I tools/frame_sessions.py build --saves SAVES
  python3 -I tools/frame_sessions.py run --slot 1 --tag p55 --saves SAVES --run 2026-11-04-frame --launch town
  python3 -I tools/frame_sessions.py run --slot 1 --tag p55 --saves SAVES --run 2026-11-04-frame --pilot-only --launch pack
  python3 -I tools/frame.py window --pilot workspace/logs/frame/2026-11-04-frame-s1-5501-{town,pack}.log
  ```
- **Cases (ADR-0028):** two processes, one case each, position 1, both fresh: `2026-11-04-frame-s1-5501-town` (seed 5501) and `2026-11-04-frame-s1-5501-pack` (seed 5501). No sharing. The raw logs, marks and control files are in the manifest; no piece is cut.
- **Observed:** kept logs, manifest `workspace/logs/frame/manifest-2026-11-04-frame.txt` (`44e1f4e7…`, 13 lines, 12 pass from `workspace/logs/frame/`; `2026-11-04-frame-s1.bg.txt`, the background pilot's text, was appended 17 s after the manifest and now hashes `a3c63fb1…`, listed `584e9b0b…`; no count rests on it; the logs `dfbd4401…` town, `35915470…` pack; the first-check outputs under `first/`). Town: pilot passes (a), (b), (c); 3 windows, 750 frames, 1 543 chained events, 0 mismatches, 0 located. Pack: (a) and (c) pass, (b) fails by the reader's rule at that revision with 8 mismatches in 3 369 chained events (frame/0006 § 2). **What the comparison separates (ADR-0028 item 7):** the town window has 6 `UE0` that moved a unit seed and none that moved the game seed, so it confirms "unchanged"; the pack has 16 and 11 and 3 `RU0`.
- **Development runs** (not cited for a count): `workspace/logs/frame/dev-*` (smoke sessions; `dev-act4-*` is the Act IV town window, which also passed; `dev-2026-11-04-frame-h-*` the pack with `FRAME_TRACE=1`).
- **Conclusion:** the town pilot is passed; the pack pilot's mismatches are attributed by the review, `[I]`, none to the logger, so it is not Q2's trigger (frame/0006 § 6, plan 0055's log); that window does not count towards the floors (no sites logged, and no Fallen or shaman pack). The maze and the batch were not run.
