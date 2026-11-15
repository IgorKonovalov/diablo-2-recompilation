# Two-client party-gold logger (plan 0065 Phase 0, case MP32; multiplayer/0002 § 3): attach to the HOST (it runs the
# server game, ADR-0008). tools/gdb/pilot.py (the lines tools/d2pilot.py steers by), tools/gdb/two-players.py (PLRS
# for the joiner's driver and the checker: party, level id, mode, position) and tools/gdb/two-gold.py (GP0..GPE: the
# pickup, the share, the clips and every gold add). Ready line "TWO-GOLD logger armed".
#   python3 -I tools/d2run.py --slot 1 --seed N --gdb tools/gdb/two-gold.gdb --steps tools/gdb/two-host-normal.steps \
#       --after 3000 --install TAG MpNovaHost.d2s --log workspace/logs/<run>-host.log
# Check with
#   python3 -I tools/mp_check.py gold <log>
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
source tools/gdb/two-players.py
source tools/gdb/two-gold.py
continue
