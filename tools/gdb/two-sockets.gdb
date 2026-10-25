# Two-client socket logger (plan 0051 Phase 1a staging for plan 0044's MP18; no session yet): tools/gdb/pilot.py,
# tools/gdb/two-players.py (PLRS for the joiner's driver) and tools/gdb/sockets.py (client packets PKT, SOCK_PacketInsert,
# ITEMS_InsertSocket INSX). Attach it to the HOST (it runs the server game, ADR-0008); the joiner is MpSockJoin
# (tools/mp_saves.py pair MP18). J opens a trade with H, then, the trade window open, tries to put r01 into its cap.
#   python3 -I tools/d2run.py --slot 1 --seed N --gdb tools/gdb/two-sockets.gdb --steps tools/gdb/two-host-normal.steps \
#       --after 3000 --install TAG MpNovaHost.d2s --log workspace/logs/<run>-host.log
# Expected (multiplayer/0001 § 2, MP18): a PKT 0x28 line and then no INSX and no error 3; no PKT 0x28 at all makes MP18
# a shortfall (plan 0044 Phase 1 ruling e). Check with
#   python3 -I tools/sockets.py check <log>
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
source tools/gdb/sockets.py
continue
