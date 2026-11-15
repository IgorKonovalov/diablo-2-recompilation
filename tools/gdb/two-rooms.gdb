# Two-client room logger (plan 0065 Phase 0, cases MP20 and MP21; multiplayer/0001 § 2): attach to the HOST. The files
# of tools/gdb/two-monstats.gdb's room side (tools/gdb/two-players.py, drlg-gen.py, drlg-roomk.py, mon-spawn.py,
# collision.py: the generator, activation, population and grid lines monspawn.py checks) plus tools/gdb/rooms.py (plan
# 0040's lifecycle logger: CE/CL each client's room enter and leave with the room's +0x78, RP the release pass, FREE,
# CRC the near lists). Ready lines "TWO-PLAYERS logger armed" and the rooms logger's.
# Known tag clash: rooms.py's GP (the game pointer at GAME_InitSeeds) shares its tag with two-players.py's GP (the
# portal gate); this session uses no portal, and tools/mp_check.py gates is not run on it.
#   MONSPAWN_WATCH= python3 -I tools/d2run.py --slot 1 --seed N --gdb tools/gdb/two-rooms.gdb \
#       --steps tools/gdb/two-host-normal.steps --after 3000 --install TAG MpNovaHost.d2s --log workspace/logs/<run>-host.log
# Check with
#   python3 -I tools/mp_check.py rooms <log>      (MP21: +0x78 is the clients' count, a room freed only with none; MP20:
#                                                  which client's enter activated each room)
#   python3 -I tools/monspawn.py check <log>      (MP20: the population of every room, with no player term)
set pagination off
set debuginfod enabled off
set confirm off
set width 0
set auto-solib-add off
set displaced-stepping off
set print thread-events off
set print inferior-events off
handle all nostop noprint pass
source tools/gdb/two-players.py
source tools/gdb/drlg-gen.py
source tools/gdb/drlg-roomk.py
source tools/gdb/mon-spawn.py
source tools/gdb/collision.py
source tools/gdb/rooms.py
continue
