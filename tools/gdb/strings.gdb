# String-table lookup logger (plan 0028 Phase 1): tools/gdb/pilot.py (the lines tools/d2pilot.py steers by) and
# tools/gdb/strings.py (STRTABLE_GetByIndex, STRTABLE_GetByKey and STRTABLE_FindInTable; SIDX / SKEY / SSTAT lines).
# Run through tools/d2run.py, e.g.
#   python3 -I tools/d2run.py --slot 2 --seed 2801 --gdb tools/gdb/strings.gdb --steps tools/gdb/uniques-normal.steps \
#       --after 900 --log workspace/logs/strings-s2-2801-exp.log
# Check with
#   python3 -I tools/tbl.py check workspace/merged/data/local/lng/eng workspace/logs/strings-*.log
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
continue
