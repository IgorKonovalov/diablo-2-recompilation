# Room-k logger for the pinned game.exe (plan 0008 Phase 2). Run through tools/d2run.py:
#   python3 -I tools/d2run.py --seed 12345 --gdb tools/gdb/drlg-roomk.gdb --steps tools/gdb/enter-sp.steps \
#       --after 15 --log workspace/logs/roomk-12345-town.log
# The breakpoints live in drlg-roomk.py (gdb Python), one JSON line per event; check with
#   python3 -I tools/drlg.py roomk workspace/logs/roomk-*.log
set pagination off
set debuginfod enabled off
set confirm off
set width 0
set auto-solib-add off
set displaced-stepping off
set print thread-events off
set print inferior-events off
handle all nostop noprint pass
source tools/gdb/drlg-roomk.py
continue
