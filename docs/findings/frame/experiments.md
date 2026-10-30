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
