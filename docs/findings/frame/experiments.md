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
- **Conclusion:** the five maps are `[C]` in frame/0003 §§ 1.2, 1.4, 2, 4 and 7 for the declared inputs, up to each
  observed boundary. Not covered: `QUESTS_TimerAdd` (allocates), every real timer callback, the release test, the
  saves, the frees, the population calls, the writes after each boundary, and the next-pointer reads before the
  deactivation's and the sweep's tests (no case separates them). No symbol raise (ADR-0015 scope, review-fixes rule 14).
  (run:2026-10-30-frame-emu-3)
