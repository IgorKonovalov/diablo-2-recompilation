# Collision logger for plan 0038 batch H5d (run:2026-10-25-sweep-collision): tools/gdb/collision.gdb (drlg-gen, drlg-roomk,
# mon-spawn and collision.py, whose H5d lines TCB0/TCB1, IM0/IM1, PN0/PN1, SCT0/SCT1 and LPP0/LPP1 are new) plus
# tools/gdb/mon-special.py and tools/gdb/objects.py, whose PLR/MON and OU0/OUX lines tools/d2pilot.py steers by (wp
# --wp-find). Run with MONSPAWN_WATCH= empty.
# Driven by tools/h5d_sessions.py; checked with tools/collision.py check and tools/sweep_h5d.py logs.
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
source tools/gdb/objects.py
continue
