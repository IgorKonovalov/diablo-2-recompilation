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
