# 0015 — Phase 2, first run: the AI decisions of the 18 tier AIs against their maps, and the event's seeds

> **Subsystem:** monsters/ai
> **Question:** do the first-boundary maps of the tier AIs (ai/0002–0010) hold on live decisions, and what do the AI
> event's seeds, path plans and skill starts do around them?
> **Date:** 2026-11-03   **Plan:** 0052 (Phase 2, first lane run `lane/p52a`)   **Status:** answered for the tier's first boundaries; open for the rest of Phase 2

Harness run run:2026-11-03-ai (`docs/findings/ai/experiments.md`): `tools/gdb/ai.py` logs each AI event of a server
monster near the player, `tools/ai.py check` compares it. Names are `re/symbols.csv` names. A decision is the call of the
think function at 0x005B186F (ai/0001 § 1); its **first boundary** is the first call, from the think code, of a function
the emulation of that think function treats as a boundary (ADR-0021).

## Answer (summary)

- [C] (run:2026-11-03-ai, 0x005B186F) For 13 tier AIs (rows 2, 9, 20, 21, 22, 30, 34, 37, 61, 64, 67, 89, 125, and BatDemon's alt branch of row 29) each live decision's first boundary (function, call site, registers and stack words, unit seed, the AI
  control words, and the block a pointer argument addresses) equals the model of the emulated map: 10 374 decisions,
  0 mismatches. The five unemulated tier AIs (Fallen 6, FallenShaman 13, Vampire 28, BatDemon 29's think, CorruptArcher
  35) match the first-callee maps read from the findings and objdump (`HAND` in `tools/ai.py`, unchanged since the first
  tool commit, before the first kept launch): 2 240 decisions, 0 mismatches. Every tier AI has at least
  50 compared decisions. The 0 excludes 2 016 decisions in rows with no model, 15 Scarab decisions the rev 2 window
  could not compare and the 17 679 events that end before the think call. Ten tier AIs show one predicted first
  boundary in the window (experiments.md, what the comparison separates), so for them the 0 checks that first callee
  and its arguments, not a branch. Claim ends at the first boundary; what the boundary's callee returns and everything after is
  `[I]` (ADR-0021, ADR-0004). (run:2026-11-03-ai, fn:sub_005B1740_MonAiEvent@0x005B1740)
- [C] The think call at 0x005B186F is reached by 14 645 of 32 324 logged events; 17 679 end before it (pre-checks, the
  search, `MonSpcWalk`), and `AiCtl.state` is 0 at all of them. (run:2026-11-03-ai, 0x005B186F, 0x005B1876)
- [C] `PathPlan` leaves the unit seed unchanged on all 9 618 plan calls inside decisions (path types 2, 5, 6, 7, 13, 15
  observed): ai/0001 § 8's reading holds for the types the AI requests. Type 1 was not requested in this run.
  (run:2026-11-03-ai, fn:sub_00649970_PathPlan@0x00649970)
- [C] Every logged point of a decision (entry, think call, boundaries, `MonSetMode`, `PathPlan`, skill start, exit) follows
  the previous one by whole steps of the acting unit's own seed (0 to 7 steps, 0 violations in 14 645 decisions). The
  search's state-146 candidate draw is on another seed and is not logged. (run:2026-11-03-ai)
- [C] `SKILLS_SrvStart` runs inside the AI event: 899 skill starts of the decision's unit between the think call and
  the exit, each entered at the decision's last logged seed advanced 0 to 12 steps (the 0-step case 791 times) and each
  exiting with the event's exit seed. (run:2026-11-03-ai, fn:SKILLS_SrvStart@0x0056F640)
- [C] Decision pairs on one seed (exit seed = the next decision's entry seed, same unit): 12 368, 9 687 of them with
  draws; at least 20 drawing pairs for every tier AI except Fetish (2) and Andariel (5); Fetish draws on 2 of 98
  decisions and BatDemon on none. (run:2026-11-03-ai)
- [C] The commands the AI sites give `MonSetMode` are modes 2 (WL) 6 133, 15 (RN) 1 533, 4 (A1) 712, 5 (A2) 425, 14
  (SQ) 289, 8 (S1) 375, with path type byte 101 for every-frame modes and 100 otherwise. (run:2026-11-03-ai,
  fn:sub_005A7C20_MonSetMode@0x005A7C20)
- [I] State rows 2, 3, 8, 9, 14, 17: nothing set `AiCtl.state` in this window (all events state 0), but the window has no
  control (no state 10–13 event), so the absence is not evidence for "no setter". (experiments.md run:2026-11-03-ai)

## Leads used

None: no community page was read for this run (plan 0052 Phase 1b is ai/0014).

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x005B1740` | `sub_005B1740_MonAiEvent` | the AI event: entry, think call at 0x005B186F, exit at 0x005B1876 | C |
| `0x005EFCF0`, `0x005F02C0`, `0x005F0A20`, `0x005F1440` | `sub_005EFCF0_AiSkeleton`, `sub_005F02C0_AiFallen`, `sub_005F0A20_AiWraith`, `sub_005F1440_AiFallenShaman` | think of rows 2, 6, 9, 13 | C (first boundary) |
| `0x005F2540`, `0x005F2850`, `0x005F2B10`, `0x005F4A70`, `0x005F5040`, `0x005F53E0` | `sub_005F2540_AiScarab`, `…AiMummy`, `…AiGreaterMummy`, `…AiVampire`, `…AiBatDemon`, `…AiFetish` | think of rows 20, 21, 22, 28, 29, 30 | C (first boundary) |
| `0x005F5830`, `0x005F5A20`, `0x005F6070`, `0x005E52D0`, `0x005F96C0`, `0x005E4CF0`, `0x005E0C80`, `0x005E36F0` | `sub_005F5830_AiAndariel`, `…AiCorruptArcher`, `…AiSkeletonBow`, `…AiHireable`, `…AiSkeletonMage`, `…AiNecroPet`, `…AiMegademon`, `…AiBloodLord` | think of rows 34, 35, 37, 61, 64, 67, 89, 125 | C (first boundary) |
| `0x00649970` | `sub_00649970_PathPlan` | path plan, seed unchanged for the AI's types | I (role), seed claim `[C]` |

## Walkthrough

### 1. What is logged and compared

The logger (`tools/gdb/ai.py`, rev 3) breaks at the event entry 0x005B1740 (ECX game, EDX unit), at the think call
0x005B186F and at the event's `ret 8` 0x005B1876; between the last two it arms the boundary addresses (136 functions)
and logs the first eight calls whose return address lies in the think code (0x005B14E0–0x005B1650, 0x005E0000–0x005FFFFF,
and from rev 3 `MonsterOwner`, 0x005DE830 and 0x005DF850), and the entry and exit seeds of `MonSetMode` (0x005A7C20, five
rets), `PathPlan` (0x00649970, six rets) and `SKILLS_SrvStart` (0x0056F640, three rets). The model of a decision is the
emulation family of its think address (`FNS` of `tools/ai_cat_emu*.py`) run on the logged inputs (`tools/ai.py inputs`);
the five hand maps are in `tools/ai.py` (`HAND`): Fallen returns without a call in modes 0 and 12 and otherwise calls
`UNIT_CancelEvents` (0x005F02FD, 2, 0); FallenShaman draws once when in melee (signed `aip3`) and attacks or calls
`MonTypeFlag(U, 8)` (0x005F14E1); Vampire and CorruptArcher call `MonAiFindHostile` (0x005F4AD5, 0x005F5A56); BatDemon
calls `UnitLifePct` (0x005F5070). (fn:sub_005B1740_MonAiEvent@0x005B1740)

### 2. Counts

See experiments.md: 14 645 decisions, 12 614 compared, 0 mismatches at the first boundary, 15 not comparable; per tier AI 55 (BloodLord) to
5 697 (Hireable). The mercenary dominates because it thinks every few frames; the logger's cap of 200 per row per game
limits it. The 17 679 events that end before the think call are logged without inputs (AIN lines).

### 3. Skill starts and chains

A skill start is not a later event: `SKILLS_SrvStart` is called inside the decision, after the command's draws, and its
exit seed is the event's exit seed in all 899 cases (steps from the last logged seed: 0 in 791 cases; the rest 1–4 steps:
Mummy-class rows 1–2, Vampire up to 4, the mercenary 2). So "decision → skill start" is one seed chain per event.
(fn:SKILLS_SrvStart@0x0056F640)

## Data touched

tbl:MonStats.txt:AI, tbl:MonStats.txt:aip1 … aip8, tbl:MonStats.txt:Skill1, tbl:MonStats.txt:Sk1mode; struct:AiCtl+0x00,
struct:AiCtl+0x14, struct:AiCtx+0x14, struct:MonCmd+0x15.

## Dead ends

- rev 1 of the logger read `MonSetMode`'s command from EDX; the command is the second stack word (the function is
  `ret 0xC`), and logged only three of `PathPlan`'s six returns. Both fixed before any kept session.
- The waypoint click in the Act IV town sometimes does not open the list (a non-player character in the way, three
  failed attempts in 34 case runs); the sessions retry and mark a case that stayed in its first level as failed.

## Open questions

- Not covered by the 0 mismatches: everything after the first boundary of each decision (the boundary's result decides
  the rest). A resumable model fed with the logged boundary results would extend the claim; the log carries the first
  eight boundary calls but not their results.
- Fetish and Andariel have fewer than 20 drawing chained pairs (their decisions rarely draw); BatDemon never draws.
- The 15 Scarab decisions of the rev 2 window are not comparable; the 95 of rev 3 are.
- Required cases still open: the H1 oracle replacement (331 gaps; the kept skills logs hold no AI line), H3's Raven calls,
  P1b-1 (Duriel, 300 melee decisions) and P1b-2 (Greater Mummy and a champion corpse), a live control for `AiCtl.state`
  (states 10–13), pilots for P1 batches 5, 7, 10, 11, 12 outside the tier.
