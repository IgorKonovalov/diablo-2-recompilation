# Calc evaluator logger with the pilot's lines (plan 0035 Phase 2): tools/gdb/mon-special.gdb's loggers (PLR, RL,
# RRESEED, CB for tools/d2pilot.py) plus tools/gdb/calc.py, for sessions that cast skills outside town.
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
source tools/gdb/calc.py
continue
