# Plan 0016 Phase 2 required case (logicals): the preset-unit logger (drlg-preset.gdb) plus tools/gdb/drlg-preset-wp.py,
# watches that follow the player's region box in Logicals-1, Populate-1 preset rooms. Run through tools/d2run.py as drlg-preset.gdb.
set pagination off
set debuginfod enabled off
set confirm off
set width 0
set auto-solib-add off
set displaced-stepping off
set print thread-events off
set print inferior-events off
set can-use-hw-watchpoints 1
handle all nostop noprint pass
python WP_MODE = "logicals"
source tools/gdb/drlg-gen.py
source tools/gdb/drlg-preset.py
source tools/gdb/drlg-preset-wp.py
continue
