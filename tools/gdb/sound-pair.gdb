# Room-population logger for the pinned game.exe (plan 0014 Phase 2): the generator tags of drlg-gen.py, the room-k tags
# of drlg-roomk.py (so the active-room seed is predicted from the map seed) and the population tags of mon-spawn.py.
# Run through tools/d2run.py, e.g. an owner-played session:
#   python3 -I tools/d2run.py --seed 12345 --sound --gdb tools/gdb/mon-spawn.gdb --after 3600 \
#       --log workspace/logs/monspawn-12345-normal.log
# MONSPAWN_WATCH=2,8 (default) picks the two level ids whose MonWndr bytes get access watchpoints. Check with
#   python3 -I tools/monspawn.py check workspace/logs/monspawn-*.log
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
# sound-pair block (archaeology/0003 § 6): the device words once, 2000 client frames in
break *0x00482C20
ignore $bpnum 2000
commands
  silent
  echo SNDWORDS 0x00881768 device\n
  x/wx 0x00881768
  echo SNDWORDS 0x007C545C\n
  x/wx 0x007C545C
  echo SNDWORDS 0x007C8C78\n
  x/wx 0x007C8C78
  echo SNDWORDS clientseed\n
  x/2wx *(int*)0x007A6A70+0x20
  disable $bpnum
  continue
end
continue
