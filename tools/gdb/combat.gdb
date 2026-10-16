# Combat logger (plan 0037 Phase 2): tools/gdb/pilot.py (the lines tools/d2pilot.py steers by) and
# tools/gdb/combat.py (the attack events of docs/findings/combat/0001-formulas.md). Run through tools/d2run.py, e.g.
#   python3 -I tools/d2run.py --slot 3 --seed 3701 --gdb tools/gdb/combat.gdb --steps tools/gdb/enter-normal.steps \
#       --after 1800 --install c37 CombatSor.d2s --log workspace/logs/combat-s3-3701-normal.log
# then drive the character with tools/combat_sessions.py. Check with
#   python3 -I tools/combat.py check workspace/logs/combat-*.log
# Per-kind caps per session (env COMBAT_CAP_PA, _MA, _HA, _MAS, _MD, _PM override): player attack 800, monster
# attack 500, hireling attack 300, MonAttackStats 300, missile defence 300, player missile 300.
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
source tools/gdb/combat.py
continue
