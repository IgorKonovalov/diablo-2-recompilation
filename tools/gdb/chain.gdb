# Seed-to-world logger (plan 0048 Phase 1, for the Phase 2 end-to-end run): the loggers whose lines tools/chain.py
# check composes, in one session.
#   world: tools/gdb/drlg-gen.py, drlg-roomk.py (the DRLG builds, the activations), mon-spawn.py (the room driver RW0..RW4
#          with "os", the population pass P0..PX, MonSpawnTry), collision.py (the activation dumps and the pass-entry
#          grid snapshot), mon-special.py (the special monsters and the presets window's specials; PLR for the pilot),
#          mon-stats.py (MonStatsInit SI0..SIX), objects.py (the object-region seed and its draws, the presets window
#          OPU0..OPUX, the populate pass, object creation, operate and the chest drop);
#   items: tools/gdb/uniques.py, affixes.py, props.py (the item creation IC0..ICX with both line sets, as
#          tools/gdb/items-chain.gdb), and tools/gdb/tc-drops.gdb (TCR..TCEND, sourced last: it ends with `continue`).
# MONSPAWN_WATCH must be empty (objects.py's watchpoint on the object-region seed takes the debug register).
#
# Boundaries and their seed asserts (each logger's own entry and exit lines; tools/chain.py check asserts the model's
# seed at every entry line and compares every exit line):
#   game creation   OGC (game seed after draw 2 = the object-region seed's Init); the monster regions (draw 1) are
#                   not logged: the model's regions from -seed N are compared with every region snapshot (P0, SU0, PM0)
#   level build     LC0 (act base = step(Init(N)).low), LI1 (level seed at LevelInit end), RL (each room's +0x04)
#   activation      RRESEED, AROOM (k and the active-room seed)
#   room driver     RW0 (room seed before the tick), RW1..RW4 (room, object-region and game seeds)
#   presets window  OPU0 / OPUX (room, object-region and game seeds), SU0..SUX, PM0..PMX
#   creation        MU0 / MU (game seed, the unit seed after SUnitCreate), SI0..SIX, OU0 / OUX, OI0 / OIX
#   pass            P0 / PX (room and game seeds, the region snapshot)
#   revisit restore CMR0 / CMRX (plan 0048 Phase 2 run 2, tools/gdb/collision.py): RoomInactiveUnitsRestore called
#                   outside a window (0x0052D142, 0x0052D205); the CM marks of its re-creations are logged inside
#   drop            DROP, TCR / TCEND (the source seed), QIN / QOUT, CPRE / CPOST, OC0 / OCT / OCX
#   item            IC0 / ICJ / ICX (the item seed), APE / APX, STF0 / STF1, ETH0 / ETHX, SOK0 / SOKX
# Not reduced to entry and exit lines: the composition's checkers consume the lines inside each boundary (every draw
# and every position test is compared there), so the full loggers are kept. This file has not been run (plan 0048
# Phase 1 runs no harness); Phase 2's smoke session is its first run, and its log volume is Phase 2's to rule on.
# Run through tools/d2run.py, e.g.
#   MONSPAWN_WATCH= python3 -I tools/d2run.py --slot 1 --seed 4801 --gdb tools/gdb/chain.gdb \
#       --steps tools/gdb/enter-normal.steps --after 3600 --log workspace/logs/chain-s1-4801-normal.log
# Check with
#   python3 -I tools/chain.py check workspace/logs/chain-*.log
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
source tools/gdb/mon-stats.py
source tools/gdb/objects.py
source tools/gdb/uniques.py
source tools/gdb/affixes.py
source tools/gdb/props.py
source tools/gdb/tc-drops.gdb
