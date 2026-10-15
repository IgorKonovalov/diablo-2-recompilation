# Monster-stats logger for the pinned game.exe (plan 0025 Phase 2): every tag of tools/gdb/mon-special.gdb (the
# generator, room-k, room-population, collision and special-monster tags, and PLR for the pilot) plus the stat tags of
# tools/gdb/mon-stats.py. Run through tools/d2run.py, e.g.
#   MONSPAWN_WATCH= python3 -I tools/d2run.py --slot 3 --seed 2501 --gdb tools/gdb/mon-stats.gdb \
#       --steps tools/gdb/enter-nightmare.steps --after 7200 --log workspace/logs/monstats-s1-2501-nightmare.log
# Check with
#   python3 -I tools/monstats.py check workspace/logs/monstats-*.log
set pagination off
set debuginfod enabled off
set confirm off
set width 0
set auto-solib-add off
set displaced-stepping off
set print thread-events off
set print inferior-events off
handle all nostop noprint pass
source tools/gdb/drlg-gen.py
source tools/gdb/drlg-roomk.py
source tools/gdb/mon-spawn.py
source tools/gdb/collision.py
source tools/gdb/mon-special.py
source tools/gdb/mon-stats.py
continue
