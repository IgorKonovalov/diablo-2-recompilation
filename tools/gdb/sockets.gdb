# Socket-insert and runeword logger (plan 0029 Phase 2): tools/gdb/sockets.py (client packets, SOCK_PacketInsert,
# ITEMS_InsertSocket with its tests, the gem/rune transfer, RUNEWORD_Match, RUNEWORD_Apply with its slots, rolls
# and writes, the charge refill). Run through tools/d2run.py, e.g.
#   python3 -I tools/d2run.py --slot 2 --seed 1 --gdb tools/gdb/sockets.gdb --steps tools/gdb/enter-normal.steps \
#       --after 600 --install h29p2 workspace/scratch/SocketA.d2s --log workspace/logs/sockets-s2-a.log
# then drive the inserts with tools/d2pilot.py insert. Check with
#   python3 -I tools/sockets.py check workspace/logs/sockets-*.log
set pagination off
set debuginfod enabled off
set confirm off
set width 0
set auto-solib-add off
set displaced-stepping off
set print thread-events off
set print inferior-events off
handle all nostop noprint pass
source tools/gdb/sockets.py
continue
