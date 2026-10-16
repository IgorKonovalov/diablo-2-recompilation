# Plan 0038 batch H5c logger (run:2026-10-16-sweep-roomk): the collision family as tools/gdb/mon-special.gdb loads it
# (drlg-gen.py, drlg-roomk.py, mon-spawn.py, collision.py, and mon-special.py for the pilot's PLR and MON lines), plus
# the seed-tree breakpoints of tools/gdb/seed-tree-core.gdb (the room activation itself is drlg-roomk.py's JSON
# RRESEED / RACT / AROOM, which tools/rng.py seedtree also reads). Run through tools/d2run.py, e.g.
#   MONSPAWN_WATCH= python3 -I tools/d2run.py --slot 4 --seed 5001 --gdb tools/gdb/sweep-roomk.gdb \
#       --steps tools/gdb/enter-normal.steps --after 3600 --log workspace/logs/sweep-roomk-s1-5001.log
# Check with
#   python3 -I tools/drlg.py gen <logs>; python3 -I tools/collision.py check <logs>; python3 -I tools/rng.py seedtree <logs>
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
source tools/gdb/seed-tree-core.gdb
continue
