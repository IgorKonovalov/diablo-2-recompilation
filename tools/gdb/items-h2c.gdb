# Plan 0038 batch H2c logger (forced runs run:2026-10-21-throw-forced and run:2026-10-21-tcnamed-props-forced): the
# items-h2b set unchanged (tools/gdb/items-h2b.gdb: pilot.py, uniques.py, affixes.py, props.py, cube.py, h2b.py), then
# tools/gdb/h2c.py (the classic throwable re-pick of TC_ResolveDrops: THR, THF, THL; the entry state and value of the
# func 12, 23 and 24 handlers: E12, E23, E24 and their follow-up lines), then tc-drops.gdb, sourced last: it ends with
# `continue`. Run through tools/h2c_sessions.py (tools/d2run.py with --game-dir <forced copy> --game-args=-direct).
# Check with python3 -I tools/sweep_h2c.py logs <logs>, tools/tc.py replay and tools/items_chain.py both.
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
source tools/gdb/h2c.py
source tools/gdb/tc-drops.gdb
