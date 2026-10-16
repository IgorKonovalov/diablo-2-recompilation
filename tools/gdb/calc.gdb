# Calc evaluator logger (plan 0035 Phase 2): tools/gdb/calc.py (CALC_Eval entry and returns, every variable read and
# function call with its value). Run through tools/d2run.py, e.g.
#   python3 -I tools/d2run.py --slot 3 --seed 3501 --gdb tools/gdb/calc.gdb --steps tools/gdb/enter-normal.steps \
#       --after 600 --install h35p2 workspace/scratch-h35p2/CalcSor.d2s --log workspace/logs/calc-s3-sor.log
# then open the skill tree and hover the skills (tools/calc_sessions.py), and check with
#   python3 -I tools/calc.py check <excel-dir> workspace/logs/calc-*.log
set pagination off
set debuginfod enabled off
set confirm off
set width 0
set auto-solib-add off
set displaced-stepping off
set print thread-events off
set print inferior-events off
handle all nostop noprint pass
source tools/gdb/calc.py
continue
