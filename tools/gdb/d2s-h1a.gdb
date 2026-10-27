# Plan 0038 batch H1a (run:2026-10-27-sweep-d2s-load): the H1b logger (tools/gdb/d2s-h1b.gdb) plus tools/gdb/d2s-h1a.py (load codes, status, act, quests, waypoints, skills, old stats, item fields); the save round-trip logger of run:2026-10-12-d2s-io
# (tools/gdb/d2s-io.py, unchanged) plus tools/gdb/d2s-h1b.py (section, mercenary-header, hotkey, graphics, LoadFinish,
# item-stat, runeword and bit-13 lines), with tools/gdb/pilot.py for the pilot's PLR/RL/CB lines. Run through
# tools/d2run.py (or tools/h1a_sessions.py); check with python3 -I tools/sweep_h1a.py check.
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
source tools/gdb/d2s-io.py
source tools/gdb/d2s-h1b.py
source tools/gdb/d2s-h1a.py
continue
