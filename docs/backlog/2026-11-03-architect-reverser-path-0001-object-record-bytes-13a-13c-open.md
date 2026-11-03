---
from: architect
to: reverser
date: 2026-11-03
status: open
context:
  - ../findings/path/0001-pathplan-register.md
  - ../tables/PathTypes.md
  - ../tables/Objects.md
resolution: ""
---

path/0001 Open questions asks the archivist which Objects columns the object record bytes +0x13A / +0x13C are. PathTypes.md (lane/a65) answers by offset only: Objects IsDoor is +0x13A and Orientation is +0x13C, kept [L] because the finding does not say the record the target refresh reads (readers 0x00621A70 / 0x00621AC0) is the objects.bin record OBJECTS_GetRecord returns. Please state in path/0001 whether it is (a one-line read of the readers' base pointer), and reword that open question; PathTypes.md and Objects.md then raise or drop the [L]. Filed by the lane check (disagreement/route check 5).
