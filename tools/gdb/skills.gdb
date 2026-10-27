# Skills and missiles logger (plan 0045 Phase 2): tools/gdb/pilot.py (the lines tools/d2pilot.py steers by) and
# tools/gdb/skills.py (the skill, missile, handler and summon events of docs/findings/skills/0001-0003). Run through
# tools/d2run.py, e.g.
#   python3 -I tools/d2run.py --slot 2 --seed 4501 --gdb tools/gdb/skills.gdb --steps tools/gdb/enter-normal.steps \
#       --after 1800 --install p45h SkillsSor.d2s --log workspace/logs/skills/<run>-<session>.log
# then drive the character with tools/skills_sessions.py. Check with
#   python3 -I tools/skills.py check workspace/logs/skills/<run>-*.log
# Per-kind caps per session (env SKILLS_CAP_<KIND>): see tools/gdb/skills.py; SKILLS_WIN missiles followed per frame.
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
source tools/gdb/skills.py
continue
