# Two-client combat logger (plan 0044 Phase 2, cases MP23 and MP24): tools/gdb/combat.gdb plus tools/gdb/two-players.py
# (PLRS for the joiner's driver; the hostility declaration and the two travel gates, HD0..GPP). Attach it to the HOST.
#   python3 -I tools/d2run.py --slot 1 --seed N --gdb tools/gdb/two-combat.gdb --steps tools/gdb/two-host-normal.steps \
#       --after 3000 --install TAG MpPvpHost.d2s --log workspace/logs/<run>-host.log
# Check with
#   python3 -I tools/combat.py check <log>     (every attack event, players on both sides)
#   python3 -I tools/mp_check.py gates <log>   (MP24: the declaration, the waypoint and portal gates)
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
source tools/gdb/combat.py
continue
