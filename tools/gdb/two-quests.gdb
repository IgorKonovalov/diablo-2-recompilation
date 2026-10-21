# Two-client quest logger (plan 0044 Phase 2, cases MP12-MP14 and MP26-MP30): tools/gdb/quests.gdb's files plus
# tools/gdb/two-players.py (PLRS for the joiner's driver; PLRK; the travel gates) and tools/gdb/tc-party.py (PLR, PTY,
# KILL at every monster drop). Attach it to the HOST (it runs the server game, ADR-0008).
#   python3 -I tools/d2run.py --slot 1 --seed N --gdb tools/gdb/two-quests.gdb --steps tools/gdb/two-host-normal.steps \
#       --after 3000 --install TAG HOST.d2s --log workspace/logs/<run>-host.log
# Check with
#   python3 -I tools/questdrops.py check <log>
#   python3 -I tools/tc.py replay <log>
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
source tools/gdb/tc-party.py
source tools/gdb/uniques.py
source tools/gdb/affixes.py
source tools/gdb/vendors.py
source tools/gdb/mon-pool.py
source tools/gdb/quests.py
source tools/gdb/tc-drops.gdb
