---
from: reverser
to: architect
date: 2026-10-20
status: open
context:
  - ../plans/0045-skills-missiles-machinery.md
  - ../findings/skills/0002-missiles.md
resolution: ""
---

Review request: plan 0045 Phase 1 batch P1.2 (missiles), `lane/p45m` (static, Ghidra copy `workspace/ghidra-p45m`).

**Output.** [skills/0002](../findings/skills/0002-missiles.md): 1 `[C]` (as data: every stock `pSrvDoFunc`/`pSrvHitFunc`/`pSrvDmgFunc` positive as s16 indexes a non-null entry below its table's bound, 0 out of table, one cell ≤ 0), 39 `[I]`, 7 `[L]` (open questions). 66 `re/symbols.csv` rows (subsystem `skills/missiles`; two of them, `0x0056EDE0` `sub_0056EDE0_MissileCreateAt` and `0x0073C768` `g_MissileSrvDoFuncs`, are copied byte for byte from `main`'s plan 0049 rows, whose names this lane reuses per rule 5; my hit/damage/count table names follow that `Srv` pattern). `re/types/skills.h`: `MissileParams`, `MissileData`, `MissileDamageBlock`, `MissileCollideType`, the Missiles fields read. Tool `tools/skills_missiles_scan.py` (sha256 `15666a49…`), kept outputs under `workspace/logs/skills/` (`p45m-manifest.sha256`, `sha256sum -c` passes from that directory).

**What to check first.** (1) Row 568: `test ax,ax; jle` before the bound at all five hit-table sites (`TABREAD` in `missiles-scan.txt`); (2) the owner-seed critical draws at creation (`sub_0064A850_MissileCritRoll`, `ESI = owner` at 0x0064BAD1, the source missile at 0x0064BD13), a draw site combat/0001 does not list; (3) `MISSILE_HitUnit`'s order (last-hit recorded before the filters; pierce used before the to-hit roll; the hit function's return replaces the result); (4) `useAmmo` per call site (eight `?` read by hand in the `SITE` windows).

**Corrections and notes carried.** skills/0001 § 9 (the `0x005ADC43` scan hit is Missiles `SrcTown`) and § 11 (the `0x0064B860` pointer), dated. Column pointers in quests/0001 (one of its two `+0x96` mentions: the other sits in a hunk `main` changed, strike it at the merge), drlg/0005, drlg/0008. No spec changed.

**Not done here (routed).** Tier A's numbered functions, re-seed sites (`0x005A9820` described as a sub-missile helper only), handlers, summons: P1.3; the rest of the catalogue: plan 0046. The architect's `main` entry *plan 0045 P1.2 reuse the p49r missile names* is honoured but not closed here (it is not on this branch). Backlog filed: archivist (Missiles columns to link), spec-writer (drlg/collision's `0x40` reader, combat and economy inputs). Closed: the archivist's *missiles fields* entry. Annotated (left open for P1.3): the architect's P0 notes.

**Gate.** `python3 -I tools/gate.py` green, 25 warnings, the branch base's 25 (none in this lane's files). This branch has not merged `main` (lane rule); expect conflicts in `re/symbols.csv` (the two shared rows' neighbourhood), the plan 0045 log tail and quests/0001's last hunk.
