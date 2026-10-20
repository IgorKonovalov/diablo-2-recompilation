# Plan 0038 batch H2b logger (run:2026-10-20-sweep-items-chain): the items-chain set (tools/gdb/items-chain.gdb:
# pilot.py, uniques.py, affixes.py, props.py, then the drop lines of tc-drops.gdb), tools/gdb/cube.py (the transmute
# lines of tools/gdb/cube.gdb; its SLOT/ROLL/WR lines fire only inside a cube mod, so drops get props.py's only), and
# tools/gdb/h2b.py (the game, unit and item seeds around ItemCreate and ItemCreateByQuality, the ITEMS_SetSockets
# clamps, the magic and rare builders' failure points). tc-drops.gdb is sourced last: it ends with `continue`.
# Run through tools/h2b_sessions.py (tools/d2run.py), e.g.
#   python3 -I tools/d2run.py --slot 2 --seed 3901 --gdb tools/gdb/items-h2b.gdb --steps tools/gdb/enter-normal.steps \
#       --after 1500 --install h2b UniqClassic.d2s --log workspace/logs/h2b/items-chain-s2-3901-classic.log
# Check with python3 -I tools/sweep_h2b.py logs <logs> and python3 -I tools/items_chain.py both <logs>.
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
source tools/gdb/uniques.py
source tools/gdb/affixes.py
source tools/gdb/props.py
source tools/gdb/cube.py
source tools/gdb/h2b.py
source tools/gdb/tc-drops.gdb
