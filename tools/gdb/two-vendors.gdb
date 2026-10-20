# Two-client vendor and hireling logger (plan 0044 Phase 2, cases MP07-MP11 and MP15): tools/gdb/vendors.gdb's files
# (pilot.py, uniques.py, affixes.py, vendors.py), tools/gdb/hirelings.gdb's (mon-pool.py, hirelings.py) and
# tools/gdb/two-players.py (PLRS for the joiner's driver). Attach it to the HOST (it runs the server game, ADR-0008).
#   python3 -I tools/d2run.py --slot 1 --seed N --gdb tools/gdb/two-vendors.gdb --steps tools/gdb/two-host-normal.steps \
#       --after 3000 --install TAG HOST.d2s --log workspace/logs/<run>-host.log
# Check with
#   python3 -I tools/vendors.py check <log>
#   python3 -I tools/hirelings.py check <excel-dir> <log>
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
source tools/gdb/two-players.py
source tools/gdb/uniques.py
source tools/gdb/affixes.py
source tools/gdb/vendors.py
source tools/gdb/mon-pool.py
source tools/gdb/hirelings.py
continue
