# Plan 0038 Phase 2 leftover pieces of S1b, staged by plan 0051 Phase 1a for one H1a session: data-calc 19 (the
# hover marker CH of tools/gdb/calc.py at the client function 0x00486370) and rng-seeds 11 (the caller ra on
# SUNITPRE in tools/gdb/seed-tree-core.gdb), in one logger. The seed-tree lines are plain `TAG k=v`, the calc lines
# `TAG {json}`; each checker skips the other's tags. Run through tools/d2run.py with tools/gdb/s1b-pieces.steps
# (a CalcSor load, the potions hovered and three drunk, Save and Exit, the same character loaded again); check with
#   python3 -I tools/rng.py seedtree <log>          (the "server unit caller" lines)
#   python3 -I tools/calc.py hover <log>            (CH lines, evaluations from 0x00486370)
#   python3 -I tools/calc.py check <excel-dir> <log>
# The room activation lines (RRESEED/RACT/AROOM) of seed-tree.gdb are left out: neither piece needs them.
set pagination off
set debuginfod enabled off
set confirm off
set width 0
set auto-solib-add off
set displaced-stepping off
set print thread-events off
set print inferior-events off
handle all nostop noprint pass
source tools/gdb/seed-tree-core.gdb
source tools/gdb/calc.py
continue
