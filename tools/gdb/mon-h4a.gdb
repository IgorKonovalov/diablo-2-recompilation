# Monster logger for plan 0038 batch H4a (monsters-a): tools/gdb/mon-stats.gdb unchanged (every tag of it, mon-extra.py
# included) plus the tags of tools/gdb/mon-h4a.py (SuperUniqueSpawn's tail calls, Radament's draw, the Chaos Sanctuary
# gate). Run from the worktree root (the source lines are relative), e.g.
#   MONSPAWN_WATCH= H4B_WATCH= python3 -I tools/d2run.py --slot 1 --seed 4901 --gdb tools/gdb/mon-h4a.gdb \
#       --steps tools/gdb/enter-nightmare.steps --after 7200 --log workspace/logs/h4a/<session>.log
# Check with
#   python3 -I tools/sweep_h4a.py check <logs>   (and tools/sweep_h4b.py, tools/monstats.py as for mon-stats.gdb)
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
# plan 0038 batch H4b: new tags only (tools/gdb/mon-extra.py header); H4B_WATCH arms its watchpoints, H4B_TICK=0
# turns its every-room tick lines off
source tools/gdb/mon-extra.py
# plan 0038 batch H4a: new tags only (tools/gdb/mon-h4a.py header)
source tools/gdb/mon-h4a.py
continue
