# Collision-grid logger for the pinned game.exe (plan 0017 Phase 2): the generator and room-k tags (drlg-gen.py,
# drlg-roomk.py), the room-population tags of mon-spawn.py (plan 0014) and the grid tags of collision.py.
# Run through tools/d2run.py, e.g.
#   MONSPAWN_WATCH= python3 -I tools/d2run.py --seed 4242 --gdb tools/gdb/collision.gdb --after 3600 \
#       --log workspace/logs/collision-s1.log
# Check with
#   python3 -I tools/collision.py check workspace/logs/collision-*.log
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
source tools/gdb/collision.py
continue
