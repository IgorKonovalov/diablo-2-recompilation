# Two-client steering logger (plan 0044): tools/gdb/pilot.py (PLR, RL, RRESEED, CB, MON) plus
# tools/gdb/two-players.py (PLRS: every player unit, its travel-gate tick and hostility stamps, the party list).
# Attach it to the HOST's game (the TCP/IP host runs the server game, ADR-0008); a Phase 2 model logger sources
# tools/gdb/two-players.py beside its own files instead. Steer the joiner with
#   python3 -I tools/d2pilot.py join <host.log> follow --slot <joiner slot> --me join --lead host
# PLR lines alternate between the players' marks in a two-client game; d2pilot's --me reads PLRS instead.
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
continue
