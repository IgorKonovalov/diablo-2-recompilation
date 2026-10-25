# Two-client open-wounds logger (plan 0051 Phase 1a staging for the plan 0044 shortfalls entry's (4), the plan 0047
# case "open wounds on the player"; no session yet): tools/gdb/pilot.py, tools/gdb/two-players.py (PLRS, the
# hostility lines HD0..), tools/gdb/combat.py (attack events with the open-wounds handler, STA, and the windowed
# stat-74 ticks RGN on a logged defender) and tools/gdb/stats.py (the state and life-tick lines). Attach it to the
# HOST: the host is A (MpPvpHost), the joiner B (MpWoundJoin, Ripsaw equipped: open wounds 80); B declares hostility
# and melee-attacks A outside town (tools/mp_saves.py pair "open wounds").
#   python3 -I tools/d2run.py --slot 1 --seed N --gdb tools/gdb/two-wounds.gdb --steps tools/gdb/two-host-normal.steps \
#       --after 3000 --install TAG MpPvpHost.d2s --log workspace/logs/<run>-host.log
# Expected (stats/0002 § 2 and § 6, [I]): state 62 on A for 200 frames per application, A's life tick adding a
# negative stat 74 but never below 1 life, the tick back to normal when the list expires. Check with
#   python3 -I tools/combat.py check <log>
#   python3 -I tools/stats.py check <log>
#   python3 -I tools/mp_check.py gates <log>
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
source tools/gdb/stats.py
continue
