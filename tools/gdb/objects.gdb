# Object logger (plan 0023 Phase 2): the loggers of tools/gdb/mon-special.gdb (drlg-gen.py, drlg-roomk.py, mon-spawn.py
# with "os" on the RW lines, collision.py, mon-special.py: the lines tools/d2pilot.py steers by and the room-population
# and collision tags tools/monspawn.py checks) plus tools/gdb/objects.py (object region seed and its draws, the populate
# pass, position tests, object creation and InitFns, operate and the chest drop) and the drop lines of
# tools/gdb/tc-drops.gdb (sourced last: it ends with `continue`). MONSPAWN_WATCH must be empty: the object-region
# watchpoint needs a debug register that mon-spawn.py's MonWndr watchpoints would otherwise take. Run through
# tools/d2run.py, e.g.
#   MONSPAWN_WATCH= python3 -I tools/d2run.py --slot 0 --seed 2301 --gdb tools/gdb/objects.gdb --steps tools/gdb/enter-normal.steps \
#       --after 3600 --log workspace/logs/objects-s1-2301-normal.log
# Check with
#   python3 -I tools/objects.py check workspace/logs/objects-*.log
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
source tools/gdb/mon-special.py
source tools/gdb/objects.py
source tools/gdb/tc-drops.gdb
