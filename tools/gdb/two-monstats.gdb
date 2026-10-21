# Two-client monster logger (plan 0044 Phase 2, cases MP20 and MP22): tools/gdb/mon-stats.gdb's files (the generator,
# room-k, room-population, collision, special-monster and stat tags, PLR for the pilot) plus tools/gdb/two-players.py
# (PLRS for the joiner's driver). Attach it to the HOST (it runs the server game, ADR-0008).
#   MONSPAWN_WATCH= python3 -I tools/d2run.py --slot 1 --seed N --gdb tools/gdb/two-monstats.gdb \
#       --steps tools/gdb/two-host-normal.steps --after 3000 --install TAG HOST.d2s --log workspace/logs/<run>-host.log
# Check with
#   python3 -I tools/monstats.py check <log>
#   python3 -I tools/monspawn.py check <log>
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
source tools/gdb/mon-special.py
source tools/gdb/mon-stats.py
# plan 0038 batch H4b: new tags only (tools/gdb/mon-extra.py header); H4B_WATCH arms its watchpoints, H4B_TICK=0
# turns its every-room tick lines off
source tools/gdb/mon-extra.py
continue
