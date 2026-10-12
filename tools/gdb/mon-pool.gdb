# Monster-pool logger for the pinned game.exe (plan 0012 Phase 2). Run through tools/d2run.py:
#   python3 -I tools/d2run.py --seed 1 --gdb tools/gdb/mon-pool.gdb --steps tools/gdb/enter-sp.steps \
#       --after 10 --log workspace/logs/monpool-1-normal.log
# The breakpoints live in mon-pool.py (gdb Python), one JSON line per event; check with
#   python3 -I tools/monpool.py check <excel-dir> workspace/logs/monpool-[1-5]-*.log   (run:2026-10-12-mon-pool; monpool-p2-*.log for -p2)
set pagination off
set debuginfod enabled off
set confirm off
set width 0
set auto-solib-add off
set displaced-stepping off
set print thread-events off
set print inferior-events off
handle all nostop noprint pass
source tools/gdb/mon-pool.py
continue
