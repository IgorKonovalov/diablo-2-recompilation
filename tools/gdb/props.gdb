# Base-stat and property-roll logger (plan 0024 Phase 2): tools/gdb/pilot.py (the lines tools/d2pilot.py steers by),
# tools/gdb/uniques.py (ItemCreateByQuality, the builders, the fallbacks), tools/gdb/props.py (ItemInitStats,
# ItemApplyProps with its slots, rolls and writes, ethereal, sockets, the final stat lists) and the drop lines of
# tools/gdb/tc-drops.gdb (sourced last: it ends with `continue`). Run through tools/d2run.py, e.g.
#   python3 -I tools/d2run.py --slot 1 --seed 5001 --gdb tools/gdb/props.gdb --steps tools/gdb/uniques-hell.steps \
#       --after 900 --log workspace/logs/props-s1-5001-hell.log
# Check with
#   python3 -I tools/props.py check workspace/logs/props-*.log
set pagination off
set debuginfod enabled off
set confirm off
set width 0
set auto-solib-add off
set displaced-stepping off
set print thread-events off
set print inferior-events off
handle all nostop noprint pass
source tools/gdb/pilot.py
source tools/gdb/uniques.py
source tools/gdb/props.py
source tools/gdb/tc-drops.gdb
