# Plan 0038 batch H1c (run:2026-10-27-sweep-d2s-legacy): the H1a logger (tools/gdb/d2s-h1a.gdb) plus tools/gdb/d2s-h1c.py (the legacy reader's calls: NewCharLegacy, the section readers, ReadMercOldSave, MercExpFromOldSave, MERC_Create, the version-71 list and its inserts, the unique builder's restore branch); the save round-trip logger of run:2026-10-12-d2s-io
# (tools/gdb/d2s-io.py, unchanged) plus tools/gdb/d2s-h1b.py (section, mercenary-header, hotkey, graphics, LoadFinish,
# item-stat, runeword and bit-13 lines), with tools/gdb/pilot.py for the pilot's PLR/RL/CB lines. Run through
# tools/d2run.py (or tools/h1c_sessions.py); check with python3 -I tools/sweep_h1c.py check.
# Ready line (lane/hx): RDY {"logger": ...} once every file below is sourced, before `continue`; the runner keys
# its start wait on it (the TBL lines come only from a load the runner starts).
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
source tools/gdb/d2s-h1c.py
echo RDY {"logger":"d2s-h1c"}\n
continue
