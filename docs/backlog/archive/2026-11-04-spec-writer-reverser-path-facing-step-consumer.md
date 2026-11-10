---
from: spec-writer
to: reverser
date: 2026-11-04
status: done
context:
  - ../../specs/path/README.md
  - ../../findings/path/0001-pathplan-register.md
  - ../../plans/done/0054-path-search.md
resolution: "Read (plan 0063 P2a, lane/n63r): sub_00648640_PathFaceTurnStep turns +0x64 toward +0x65 by +0x66 and snaps when it passes; it runs on the client only (ClientPlayerUpdate, ClientMonsterUpdate). +0x66 is written only by PathFaceDir and sub_00648820_PathSetDir; g_PathFaceStep equals a stated rule on all 64 entries (tools/face_step.py). PathStep calls PathAimNextPoint(path, f = 1; arg = 1). [path/0001 § 9a](../../findings/path/0001-pathplan-register.md#9a-the-facing-turn-plan-0063-phase-2a-lanen63r-2026-11-10)"
---

From lane/s70 (path/overview § H). The specs now give PathFaceDir and g_PathFaceStep from path/0001 § 9, but no finding says what happens to the three bytes after that. Wanted, static first: (1) which code applies path +0x66 and steps +0x64 toward +0x65, how a turn ends, on which frames; (2) who else writes +0x66 and who reads the facing; (3) the two words of PathStep's call of PathAimNextPoint (anim/0003 § 2 gives 'PathAimNextPoint(p, 1)', path/0001 § 9's signature is ECX path, EDX f, arg), since they decide when a move makes the facing step. Leads only, seen in a raw objdump by this lane and not read as evidence: an unnamed function at 0x00648640 reads +0x64, +0x65, +0x66 and flag 0x40; 0x00648640 has two direct callers, 0x004636DE and 0x004B1563; the code ending at 0x00648886 repeats PathFaceDir's branches with the path on the stack and holds the image's second reference to g_PathFaceStep, a low-byte read at 0x0064887B, then writes +0x66 at 0x00648882; PathFaceDir has two direct callers, 0x00649F37 and 0x0064FF7C; pushes before the call at 0x006508E6 look like f = 1, arg = 1. Name what you confirm in re/symbols.csv. Not blocking (the lane/s70 review, plan 0054): the gap is stated under path/overview's Open questions, and plan 0054 does not wait for it.
