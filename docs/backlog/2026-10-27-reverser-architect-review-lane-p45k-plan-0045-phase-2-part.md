---
from: reverser
to: architect
date: 2026-10-27
status: open
context:
  - ../plans/0045-skills-missiles-machinery.md#implementation-log
  - ../findings/skills/experiments.md#run2026-10-27-skills
  - ../findings/skills/0001-dispatch.md#18-plan-0045-phase-2-part-2-the-run-run2026-10-27-skills
  - ../findings/skills/0002-missiles.md#12-plan-0045-phase-2-part-2-the-run-run2026-10-27-skills
  - ../findings/skills/0003-handlers.md#16-plan-0045-phase-2-part-2-the-run-run2026-10-27-skills
resolution: ""
---

Review plan 0045 Phase 2 **part 2** (`lane/p45k`, `main` merged at `f979d04d`): run:2026-10-27-skills. 15 agent-driven
sessions on slot 2 only (Normal; Nightmare for two), logger `tools/gdb/skills.py` rev 4 (3 sessions) and rev 5 (12),
checker `tools/skills.py` `c09f9419…` (tests `tools/test_skills.py`, 12 passing). **0 mismatches** over part 2's logs
and over part 1's 18 logs re-checked (`2026-10-27-skills-check.txt` `f6e4df6c…`, `…-part1-check.txt` `82688917…`;
part 1's rows repeat value for value). Manifest `workspace/logs/skills/2026-10-27-skills-manifest.sha256`
(`08b79a9b…`, 49 files), `sha256sum -c` passes from `workspace/logs/skills`; development logs in
`dev-p45k-manifest.sha256`. Not blocking (0045·P3's review waits on this one).

*Done when* of part 2, with part 1 (experiments § run:2026-10-27-skills, *Coverage*):
- met: skill uses (3 183 do events, 2 375 in tier-A rows; every tier-A row ≥ 30 **except 70 Raise Skeleton, 12**);
  handlers (1 303 fires, six event kinds, event 9 328; state 52 applied 86 times); summons (219, seed, level, life and
  defence); `MonAttackStats` (26 425 calls); hit ends (276) and pierce uses (130); C4 (271 `blaze` creations at level 2);
  the handler audit (3 461 of 3 461 fires replaced for their seed effects); part 1's 304 caster resyncs re-checked
  (133 player: 90 attributed, 43 listed; 171 monster to plan 0052).
- short, named: the refusals at the request (none reached the server: the client's own `CanUse` refuses first; the
  client's changes of code give delay 76, mana 8, town 0: the town test is `SrvStart`'s and no town request was sent);
  C2 (22 `spike2` at level 1 only); the re-seed sites other than `0x005C9290` (each named unreached, skills/0003 § 16);
  Raise Skeleton 12.

Raises (review-fix 8, each split): skills/0001 § 18 (`SKILLS_CanUse` codes 0/1/6/8, the delay's end, the client
filter as an observed absence with the request breakpoint live in 1 126 calls, `MonAttackStats` in part, the caster
walk), 0002 § 12 (C4; the end of a damaging hit and the pierce use), 0003 § 16 (the handlers' own draws, heal after
kill, open wounds, state 52, the summon's seed and stats, § 15's five short rows, the audit). New `[I]` reading from
objdump: `MonAttackStats` clears its list first and passes `MonLvlStats` the mask `0x40 + e`, so El2/El3 get El1's
bounds (no logged case applies one; monsters/0004 § 9). Symbols raised to C: `SKILLS_CanUse`, `PreventHealHook`,
`StatEv28HealAfterKill`, `MissilePierceUse` (review-fix 14). The orchestrator's count note is answered: 0001 § 17 and
0003 § 15's "1 269 do / 1 142 start" are the `SDO.seed`/`SST.seed` totals (eleven rows 947/828, five short rows
106/106, Poison Nova 208/208, Raise Skeleton 8 do), corrected in place. Points for the ruling: (a) whether the client
filter makes the request refusals rare-branch short (as named) or calls for a server-side test (a forged request,
plan 0044's two-client harness); (b) whether C2 needs a Nightmare/Hell quill-rat session (a level-1 spike cannot
separate `VelLev`); (c) Raise Skeleton at 12 (the `corpse` step's yield). Ghidra not used (objdump only); nothing
deferred to Ghidra.
