# Save round-trip logger for the pinned game.exe (plan 0013 Phase 2, run:2026-10-12-d2s-io). Run through tools/d2run.py:
#   python3 -I tools/d2run.py --seed 0 --gdb tools/gdb/d2s-io.gdb --steps tools/gdb/d2s-io-roundtrip.steps \
#       --after 30 --log workspace/logs/d2sio-1.log
# The breakpoints live in d2s-io.py (gdb Python), one "TAG {json}" line per event: the header sources, every
# item serialised (seed, quality, ilvl, flags, version, file offset) and the whole buffer at write; the bytes
# read, the checksum, the map-seed test, the stats and items read, D2S_LoadFinish and the error exit at load;
# game/act seeds, drops and string-table CRCs. Check with
#   python3 -I tools/d2sio.py check <excel-dir> workspace/logs/d2sio-1.log [<saved.d2s> ...]
set pagination off
set debuginfod enabled off
set confirm off
set width 0
set auto-solib-add off
set displaced-stepping off
set print thread-events off
set print inferior-events off
handle all nostop noprint pass
source tools/gdb/d2s-io.py
continue
