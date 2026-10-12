# Two-client drop logger (plan 0011): tc-drops.gdb plus, at every monster drop, the player units
# (id, position, level, dead flag), the party list and the source/killer positions (tc-party.py).
# Attach it to the HOST's game (the TCP/IP host runs the server game):
#   python3 -I tools/d2run.py --seed 1 --gdb tools/gdb/tc-party.gdb --steps tools/gdb/two-host.steps \
#       --after 3600 --log workspace/logs/tc-party-1.log
# Check with `python3 -I tools/tc.py replay <log> -v` (PLR/PTY/KILL lines feed its party check).
set pagination off
set debuginfod enabled off
set confirm off
set width 0
set auto-solib-add off
set displaced-stepping off
set print thread-events off
set print inferior-events off
handle all nostop noprint pass
source tools/gdb/tc-party.py
source tools/gdb/tc-drops.gdb
