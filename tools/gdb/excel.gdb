# Data-load logger (plan 0038 batch H3b): tools/gdb/pilot.py (the lines tools/d2pilot.py steers by),
# tools/gdb/strings.py (SIDX / SKEY / SSTAT: string-table lookups) and tools/gdb/excel.py (the X* lines: file layer,
# archives, language byte, string-table load and release, excel load, item-code and TC-name lookups, record dumps).
# Run through tools/d2run.py --early so that gdb is on the game before its startup code, e.g.
#   H3B_DUMP=workspace/logs/h3b/<run>-dump python3 -I tools/d2run.py --slot 2 --early --seed 3101 \
#       --gdb tools/gdb/excel.gdb --steps tools/gdb/enter-normal.steps --after 600 --log workspace/logs/h3b/<run>.log
# Check with python3 -I tools/sweep_h3b.py check <log>...
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
source tools/gdb/strings.py
source tools/gdb/excel.py
continue
