# Generator-dispatch logger for the pinned game.exe (plan 0008 Phase 3). Run through tools/d2run.py:
#   python3 -I tools/d2run.py --seed 12345 --gdb tools/gdb/drlg-gen.gdb --steps tools/gdb/drlg-roomk-bloodmoor.steps \
#       --after 10 --log workspace/logs/gen-12345-bloodmoor.log
# The breakpoints live in drlg-gen.py (gdb Python), one JSON line per event; check with
#   python3 -I tools/drlg.py gen workspace/logs/gen-*.log
set pagination off
set debuginfod enabled off
set confirm off
set width 0
set auto-solib-add off
set displaced-stepping off
set print thread-events off
set print inferior-events off
handle all nostop noprint pass
source tools/gdb/drlg-gen.py
continue
