# Unique/set selection logger (plan 0019 Phase 2): tools/gdb/pilot.py (the lines tools/d2pilot.py steers by),
# tools/gdb/uniques.py (ItemCreateByQuality, the builders, the fallbacks) and the drop lines of tools/gdb/tc-drops.gdb
# (TC resolution and the quality roll, sourced last: it ends with `continue`). Run through tools/d2run.py, e.g.
#   python3 -I tools/d2run.py --seed 1901 --gdb tools/gdb/uniques.gdb --steps tools/gdb/enter-hell.steps \
#       --after 7200 --log workspace/logs/uniques-s1-1901-hell.log
# Check with
#   python3 -I tools/uniques.py check workspace/logs/uniques-*.log
#   python3 -I tools/tc.py replay <log> --quality model
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
source tools/gdb/tc-drops.gdb
