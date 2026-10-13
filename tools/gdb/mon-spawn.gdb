# Room-population logger for the pinned game.exe (plan 0014 Phase 2): the generator tags of drlg-gen.py, the room-k tags
# of drlg-roomk.py (so the active-room seed is predicted from the map seed) and the population tags of mon-spawn.py.
# Run through tools/d2run.py, e.g. an owner-played session:
#   python3 -I tools/d2run.py --seed 12345 --sound --gdb tools/gdb/mon-spawn.gdb --after 3600 \
#       --log workspace/logs/monspawn-12345-normal.log
# MONSPAWN_WATCH=2,8 (default) picks the two level ids whose MonWndr bytes get access watchpoints. Check with
#   python3 -I tools/monspawn.py check workspace/logs/monspawn-*.log
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
source tools/gdb/drlg-roomk.py
source tools/gdb/mon-spawn.py
continue
