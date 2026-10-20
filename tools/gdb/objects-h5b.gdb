# Object logger for plan 0038 batch H5b (run:2026-10-19-h5b-objects): tools/gdb/objects.gdb (with the trap lines
# TF/TFQ/TE0/TT0/TTX that tools/gdb/objects.py gained in this batch) plus tools/gdb/vendors.py, whose OBJS/OBJP/NPC
# lines tools/d2pilot.py objop, wpchain and npc steer by (nothing in them feeds a model; tools/objects.py skips them).
# Run with MONSPAWN_WATCH= empty, as objects.gdb. Driven by tools/h5b_sessions.py.
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
source tools/gdb/vendors.py
source tools/gdb/tc-drops.gdb
