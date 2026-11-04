# 0017 — Phase 2, second run (checkpoint): the outcome mix, the negative controls and a resumable model of the AI decision

> **Subsystem:** monsters/ai
> **Question:** can the claim of [ai/0015](0015-phase2-first-run.md) (0 mismatches at each decision's first boundary) be made to separate
> more than the first callee: what does each tier AI's comparison actually separate, does a deliberately wrong map fail on
> the kept logs, and can a decision be compared past its first boundary?
> **Date:** 2026-11-03 to 2026-11-04   **Plan:** 0052 (Phase 2, second lane run `lane/p52b`, two parts)   **Status:** kept batch filed
> (run:2026-11-03-ai-3, run:2026-11-04-ai-3p: 23 kept sessions). Sections 1 to 5 are the first part's checkpoint (development logs); sections 6 to 12
> are the kept batch. **The resumable model's comparison past the first boundary has 112 mismatches on the kept logs (§ 7), so no claim
> past the first boundary is `[C]`;** the `lane/p52b` review classified them: 104 faults of the model, 8 a logger limit, none a reading of the game's code that the logs contradict. P1b-1 (Duriel) is not done.

Harness run run:2026-11-03-ai-2 (`docs/findings/ai/experiments.md`). Names are `re/symbols.csv` names. A decision is the call of
the think function at 0x005B186F (ai/0001 § 1); a boundary is a call of one of the 136 functions of `BND` in
`tools/gdb/ai.py` from the think code (ADR-0021).

## Answer (third part, 2026-11-04, `lane/p52c`, § 13)

- [I] (run:2026-11-04-ai-resume, 0x005B186F) The fixed resume model: 7 444 of 7 539 resumed, 8 mismatches, all row 23, 87 stopped. This supersedes the 112 below.
- [C] (run:2026-11-04-ai-resume, 0x005B186F) Proposed for review, past the first boundary and scoped in § 13: rows 6, 13, 21, 30, 37, 61, 64, 67, 89. Their outcome mix is uneven (§ 13's table), and Skeleton and Wraith are not proposed since they have no call past the first.
- [C] (run:2026-11-04-ai-resume, fn:sub_0056E050_MonOwnerSkillDamage@0x0056E050) H3: 2 218 Raven calls carry the owner pair at the owner's level, separated by 101 first calls at one owner level, 20.

## Answer (kept batch, second part)

- [C] (run:2026-11-03-ai-3, 0x005B186F) **First boundary, kept.** `python3 -I tools/ai.py check --controls` over the 21 case logs of run:2026-11-03-ai-3
  (7 539 decisions, 10 721 AIN events): 6 272 decisions compared (5 269 by the Ghidra-emulation maps, 1 003 by the five hand maps), **0 mismatches**; the
  rest are 1 265 decisions in rows with no model and 2 decisions at the end of a log, where the game exited inside the decision (no boundary, AIB or AIX
  line: counted `unlogged`, § 6). Boundary of the 0: the first callee of the think function, its call site, registers, stack words, the unit seed and the AI
  control words, never a branch inside the think function (the eleven one-outcome rows below). Controls, live on the same logs: the call site shifted by one
  byte fails 6 272 of 6 272; Fallen's mode test inverted fails 814 of 814; the melee flag flipped fails 1 187 of 6 272 and separates none of 23 rows
  (`CONTROLS site=FAILS-AS-REQUIRED fallen=FAILS-AS-REQUIRED melee=FAILS-AS-REQUIRED`). Eleven tier AIs have one predicted first boundary (rows 6, 13, 28,
  29, 30, 35, 37, 61, 64, 67, 89), six have two to five (`MIXSUM`), and Scarab (row 20) has no decision in this batch (`TIER 20`). `check-run-2026-11-03-ai-3.txt`.
- [I] (run:2026-11-03-ai-3, 0x005B186F) **Past the first boundary, kept: not clean.** `tools/ai_resume.py check --controls` over the same logs: 7 539 decisions, 7 135 resumed to their end,
  **112 mismatches**, 292 stopped; 72 183 logged boundary calls matched, 64 689 of them after the first. Of the 112, 96 are in the five melee and curse
  logs (a Barbarian or a Necromancer on the stage), 66 in AI row 23, 25 in row 64 (SkeletonMage), 9 in row 95, 6 in row 79, 4 in row 37 (SkeletonBow), 1 each
  in rows 78 and 32. The lane filed them unexplained; the review classified all 112 (§ 7's dated note): 104 are model faults and 8 a logger limit, so they say nothing against the game's code. This stays `[I]`, and no tier AI's later branches are claimed until the fixed model's kept rerun (plan 0052 log, the review's order). Controls: every known branch reversed mismatches 7 273 of 7 539 (247 still ok, rows 15 and 54 not separated); a seed one step off 7 497 of 7 539.
- [C] (run:2026-11-03-ai-3, `AiCtl+0x00`) **State control.** `AID`/`AIN` carry the AI control's state. In the logged lines of the 21 sessions (27 caps cut lines off, § 8) the state is 0 in 7 347 decisions and
  10 680 events; **state 10 is observed live** in 38 decisions (session `s-necro-curse`, AI row 12, class 57), **state 11** in 98 decisions (`s-necro-curse` 78 on row 12;
  `s-barb-howl` 20 on rows 37 and 64) and 41 AIN events (`s-barb-howl`, row 64), and **state 12** in 56 decisions (`s-barb-howl`, rows 37 and 64). No other state value is logged (§ 8). State 13, the plan's fourth live control, is not in the window: no session staged The Countess, so the Done-when's state item stays open.
- [I] (run:2026-11-04-ai-3p, 0x005F2A00, 0x005FD470, built state) **P1b-2, not met.** With the champion flag (4) written on corpses at the Greater Mummy's search
  callback and the unique flag (8) on others: 4 of 17 champion-flag corpses reached `MonSkillTargetOk` (skill 327) as its second argument, 2 accepted (result 1,
  then the command mode 14 with that corpse as target), 2 refused (result 0); 0 of 16 unique-flag corpses reached it (§ 9). `[C]` as filed; lowered at the review: ADR-0003 says a breakpoint never writes game memory, and no ADR admits this write. It is a forced result, no natural champion was seen, and C40's required case stays open.
- [C] (run:2026-11-03-ai-3, 0x005DD140, 0x005E9DD0, 0x005F7F10, 0x005FD0F0, 0x005F8010, 0x005FC130, 0x005E9750) **G4, for this window only.** Entry breakpoints on the seven helpers: 0 hits in
  the 23 kept launches (21 stock, 2 of them the built-state P1b-2 launches), Normal; the control 0x005B1CF0 hit in all 23 and 0x005A3250 in 2 (§ 10). It says nothing of an Uber session.
- P1b-1 (Duriel) not done: the route's first development attempt did not reach the tomb (§ 11).

## Answer (summary, first part: checkpoint)

- [C] (run:2026-11-03-ai-2, 0x005B186F) `python3 -I tools/ai.py check` prints, per AI row and think address, the distinct
  predicted (function, call site) first boundaries with their counts (`MIX`) and counts the tier AIs with one outcome (`MIXSUM`).
  Over the 31 kept logs of run:2026-11-03-ai (`check-mix-2026-11-03-ai.txt`, in `manifest-run-2026-11-03-ai-2.sha256`) it reproduces
  the architect's recount: ten tier AIs have one predicted first boundary (rows 6 Fallen, 28 Vampire, 29 BatDemon's think,
  30 Fetish, 35 CorruptArcher, 37 SkeletonBow, 61 Hireable, 64 SkeletonMage, 67 NecroPet, 89 Megademon), eight have two to five
  (Skeleton 4, Wraith 3, FallenShaman 2, Scarab 5, Mummy 5, GreaterMummy 3, Andariel 5, BloodLord 5). The 0 mismatches of ai/0015
  stay as filed: first boundary only, 2 016 decisions in rows with no model, 15 not comparable, 17 679 events that end before
  the think call outside it.
- [C] (run:2026-11-03-ai-2) The live negative control `check --controls` runs three wrong maps over the same 31 logs. A predicted
  call site shifted by one byte fails 12 629 of 12 629 compared decisions; the Fallen map with its mode test inverted (a return
  in every mode but 0 and 12) fails 1 393 of 1 393; a flipped melee flag in the model input fails 2 114 of 12 620 and separates
  none of 26 rows, among them the ten one-outcome tier AIs. So the run has a control that fails where the first callee differs,
  and shows that for the ten rows no input the models read separates the first boundary: for them the first-boundary comparison
  checks the callee, its call site, its registers, stack words and the seed, and no branch. (run:2026-11-03-ai-2, `tools/ai.py`
  rev `c0fd95ec`, 18 no-game tests)
- [I] (development launches r4c, `dev-resume-r4c.txt`) `tools/ai_resume.py` runs the think function from its entry as code, over the
  pinned game.exe, and resumes at each logged boundary with the logged result (the AIR lines of logger rev 4: EAX, the unit seed,
  the AI control words, `Unit+0xC4`, the blocks the arguments point at). On 1 313 decisions of four development logs (Act I town
  rows, Jail 1, Catacombs 2–4; rows 4, 6, 12, 13, 28, 32, 34, 37, 54, 61, 63): **0 mismatches**, 1 028 decisions resumed to their
  end, 14 485 logged boundary calls matched, 13 173 of them after the first. Scope in § 3 and § 4: the first boundary and the later
  ones are compared in function, call site, ECX, EDX, the callee's own stack arguments, the unit seed, the control words and
  `+0xC4`, wherever the model knows the word. The negative controls of the model: every known branch reversed fails 1 200 of
  1 313 decisions (the 113 that survive are the town rows 54 and decisions with no known branch before their calls), a seed one
  step off fails 1 312 of 1 313. Becomes `[C]` for the run's kept sessions, which this checkpoint does not have.
- [I] Fallen (row 6) decisions are 217 of those, 5 924 boundary calls, 2 185 of the 5 707 steps past the first offered more than
  one call (an unknown room list decides the loop), all matched: the first row to have its claim past the first boundary.
- [I] What stops a resume, with counts on the development logs (§ 4): a call through a register the model cannot resolve (row 32's
  callback, 18), the logger's cap of 48 boundary calls (rows 4, 13 and 61: 267 decisions, the cap counted the calls a search made
  inside a pending call; the rev 4 logger now skips those, § 3), a return address the model lost (none left after the fixes of § 5).
- [C] (run:2026-11-03-ai-2) The first run's record had no filed note for launch 5202's rule 5 lapse; the record now states it
  (experiments.md, `run:2026-11-03-ai`): two cases of the launch stayed in the town (`a4-cotd`, `a5-crystal`) and four more
  cases ran in the same process after them (`a5-glacial`, `a1-cloister`, `a1-catacombs`, `a3-durance`).

## Leads used

None.

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x005B1740` | `sub_005B1740_MonAiEvent` | the AI event (ai/0015) | C (unchanged) |
| `0x005DDC30` | `sub_005DDC30_MonAiFindHostile` | a boundary whose result the model takes from AIR; its output block word is the distance the later compare reads | I |
| `0x0056E050` | `sub_0056E050_MonOwnerSkillDamage` | the owner pair added to a summon's attack stats (§ 13, H3; raised by `lane/p52c`) | C |
| `0x0056E000` | `sub_0056E000_SkillDamagePair` | the block at the owner's level (§ 13, H3; raised by `lane/p52c`) | C |

No symbol is raised by this checkpoint: the resume model is an execution of the game's code over logged inputs, which confirms
the maps, not the roles the names state (review-fixes 14, ADR-0015 scope).

## Walkthrough

### 1. The outcome mix and the controls

`tools/ai.py check` keeps the first-run comparison unchanged and adds, per decision, the predicted (function, call site) of the
map (for a hand map that returns, `return@-`). `MIX` lines are per (row, think address): an alt or state think of a row is its
own line (BatDemon's alt 0x005F4FD0, 5 decisions, and think 0x005F5040, 110, are each one outcome). `--controls` re-runs the
comparison with `site` (call site + 1), `fallen` (the inverted mode test, `hand_fallen_inverted`) and `melee` (the model input's
melee flag flipped), and exits 1 if `site` fails to fail on every compared decision or `fallen` fails on none. The test
`test_a_control_that_passes_is_reported_wrongly_passed` builds the case a wrong map passes. (run:2026-11-03-ai-2)

### 2. Logger rev 4

`tools/gdb/ai.py` rev 4 logs the result of each boundary call: an `AIR` line (k, b = the AIB's line number, EAX, ECX, EDX, the unit
seed after the call, the AI control words, `+0xC4`, the 8 dwords at each argument that pointed at the stack). The breakpoint sits at the
call's return address, one of the 2 285 sites of `tools/gdb/ai-retsites.txt` (the calls from the five think windows to the 136
boundary functions; `tools/ai_retsites.py` regenerates it from the pinned game.exe by three `objdump` sweeps started at different
offsets and keeps the instruction starts all three agree on; all 418 distinct return addresses of the first run's logged AIB lines
are in it); each is enabled only while its call is pending. The cap is 48 boundary calls per decision (the log line says
`bmax 48`), and a call made inside a pending boundary call is not logged unless `AI_NESTED=1` (rev 3 logged them: 9 429 of the 17 015 AIB lines of development log
`dev-r4c-s2-5204-L4.log` are `GameFindUnit` calls at 0x0058F0FF made inside a search). (development launches r4a–r4c)

### 3. The resumable model

`tools/ai_resume.py`: an x86 interpreter over the instruction text of `objdump -d -M intel` of the pinned game.exe (a window decoded
from each address execution reaches, to the first `ret`, unconditional `jmp` or `int3`), with three-valued data: every word the
logger recorded is known (the unit: type, class, id, mode, seed, +0xC4, the path position; the AI control with its head record; the
MonStats `aip`, Skill, `aidel` bytes and the AI row; the AiCtx; Game +0x6D and +0xA8; the target's type, class, id, mode and
position), every other byte is unknown (None). A branch on an unknown flag forks the state and both live on; a state set is
deduplicated and capped (96 states, 6 000 steps per run, 120 visits of one address per path). The call of a boundary function from the
think windows is offered, not executed (function, call site, ECX, EDX, the callee's own stack words (its `ret N`), the unit seed, the
control words, +0xC4), and the logged call must equal one offered call in every word the model knows; then the model returns the
logged result and resumes. Callees inside the AI windows and the RNG and position getters are executed; any other callee is opaque
(EAX, ECX, EDX and the stack blocks it is passed become unknown, saved words and return addresses are kept). A logged call lying
between another call's AIB and AIR line was made inside that callee and is dropped before matching. When the logged calls are used
up and the logger did not cap the decision, some state must return with no further call. A path the model cannot follow (an
unsupported instruction, an unresolved indirect call, a state limit) makes a non-match inconclusive (`stop`), never a mismatch.
`--controls` runs the model with every known branch reversed and with a seed one LCG step off. 14 no-game tests
(`tools/test_ai_resume.py`) run it on injected instruction streams: the branch on a logged result, a wrong argument or seed, the
fork on an unknown value, a drawn seed, the nesting filter, the wrapped objdump bytes. (run:2026-11-03-ai-2, development launches r4b, r4c)

What this proves, once it has kept sessions: every logged boundary call is one the game's code can make from the logged inputs and the
earlier logged results. It does not show which of several offered calls the code takes when an unknown value decides (the log shows the
one taken; the `ambiguous_steps` count of each `RROW` line says how often that was open), and it assumes that opaque callees leave the
known memory unchanged except through their pointer arguments.

### 4. Development figures

`dev-resume-r4c.txt` (4 logs of launches 5201–5204: a Jail 1 case that stayed in the town, the Jail 1 case, a town case, the Catacombs
case) per row: 4 Bighead 66 of 86 (20 capped), 6 Fallen 217 of 217
resumed (5 924 boundary calls), 12 Goatman 9, 13 FallenShaman 18 of 52 (34 capped), 28 Vampire 2, 32 (town NPC) 237 of 255 (18 stopped:
`call esi`), 34 Andariel 5, 37 SkeletonBow 21 of 21, 54 100 of 100, 61 Hireable 310 of 523 (213 capped), 63 43 of 43. Seeds and sessions
are on the development manifest `manifest-dev-2.sha256`. These rows are not the tier of the plan's Done-when (rows 4, 12, 32, 54 and 63
are outside it); the kept run needs the tier AIs' stages. (run:2026-11-03-ai-2)

### 5. Dead ends and fixes of this checkpoint

- rev 4's first logger cleared its pending returns when a search passed 600 non-think boundary calls (the same limit that stopped the
  boundary breakpoints): FindHostile's own return was lost in every decision with a large search. The limit now disables only the
  boundary breakpoints and re-enables them when the pending call returns.
- A decode taken from a fixed 0x1000 window started inside an instruction; decoding now starts where execution arrives. `objdump` wraps an
  instruction's bytes after seven, and the model read the wrapped line as an instruction; a re-decode of the same bytes lengthened the
  instruction again; a window's last, cut instruction was kept. Each had a decision that failed only after others had run (a mismatch of a
  development log's row 63), fixed and tested.
- A callee's output block was written to the live address instead of the model's own pointer; written whole, it overwrote the frame
  (now only the words the callee changed, never the saved words).
- Waypoint clicks in the Act IV town left the case in the town on the first try in four of seven development launches (r4a ×2, r4c
  ×2; 12 retried clicks in all, `dev-*-s2.status.json.launches.json`): the runner's rerun in a fresh process held; seed 5601 failed
  twice in a row and is not used again.

### 6. The kept batch and the log truncation

Run run:2026-11-03-ai-3 (slot 2, Normal, 1.14d expansion, logger `tools/gdb/ai-g4.gdb` = `ai.py` rev 4 plus `ai-g4.py`, one game process per case, `tools/ai_sessions.py
run --fresh`): 35 launches for 21 kept sessions, the other 14 left the character in the Act IV town (the waypoint list did not open, 14 of 35 first or repeated
tries; a failed try's launch log is kept under `workspace/logs/ai/dev/`, not in the kept manifest) and were rerun. Characters: `CombatSor` (the first run's), `AiNec`, and the
three built for this part: `AiNecC` (Dim Vision F1, Terror F2), `AiBar` (Howl F1, Taunt F2) from `tools/d2s_recipes/ai-nec-curse.json` and `ai-barb.json`; the pilot for them is
`tools/d2pilot.py explore --melee` (`--melee-button 3 --curse-keys F1,F2 --keys-cycle` for the curse cases, the left Attack for the Barbarian's stage cases). Kept sessions:
Jail 1 (`a1-jail`), Stony Field, Black Marsh, Inner Cloister, Catacombs 2 to 4 and Andariel (`a1-catacombs`, `a1-andariel`), `a1-andariel-p8` (`/players 8`), Halls of the Dead 2
(`a2-halls-long`), Far Oasis (`a2-oasis-3`), Arcane Sanctuary, Flayer Jungle, Durance of Hate 2, City of the Damned (`a4-cotd-long`), River of Flame (`a4-river-long`),
Crystalline Passage, `a1-necro`, `s-necro-curse` and the Barbarian's `s-barb-howl`, `s-barb-halls`, `s-barb-flayer`, `s-barb-oasis`. Manifest
`workspace/logs/ai/manifest-run-2026-11-03-ai-3.sha256` (84 lines, passes from `workspace/logs/ai`); the failed tries, development launches and screenshots are in
`manifest-dev-3.sha256` (106 lines).

The checker's first output had **2 mismatches, both truncations**: the last decision of the log of `a1-jail` (row 61, n 5680) and of `a2-oasis-3` (row 5, n 5258) have an AID
line and nothing after it, because the game exited inside the decision. `tools/ai.py` now marks a log's last decision with no AIB and no AIX as truncated and counts it
`unlogged` (a test, `test_a_log_cut_inside_its_last_decision_is_unlogged_not_a_mismatch`, also checks that a missing boundary mid-log is still a mismatch). The resume model counts the same
shape as a stop ("log ends inside the decision (no AIX)": rows 5 and 61, 3 decisions). (run:2026-11-03-ai-3, `tools/ai.py`, `tools/ai_resume.py`)

Per tier AI, first boundary (decisions, compared by map, distinct predicted first boundaries in the kept logs): Skeleton 126 / 126 / 4, Fallen 814 / 814 / 1, Wraith 62 / 62 / 2,
FallenShaman 104 / 104 / 1, Scarab (row 20) 0 / 0 / 0, Mummy 205 / 205 / 5, GreaterMummy 27 / 27 / 2, Vampire 43 / 43 / 1, BatDemon 20 / 20 / 1, Fetish 316 / 316 / 1,
Andariel 9 / 9 / 5, CorruptArcher 22 / 22 / 1, SkeletonBow 86 / 29 / 1 (57 in thinks with no model: 0x005E8140, 0x005E8340), Hireable 2 066 / 2 065 / 1 (1 truncated), SkeletonMage
91 / 72 / 1 (19 in the two other thinks), NecroPet 53 / 53 / 1, Megademon 77 / 77 / 1, BloodLord 22 / 22 / 5. Seventeen of the 18 tier AIs have decisions; Scarab has none, and 6 others (Andariel, BatDemon, CorruptArcher, BloodLord, GreaterMummy, Vampire) have fewer
than 50 here. [2026-11-04, `lane/p52b` review: filed as "all 18", with Swarm's 82 decisions of row 19 (`ai_cat_emu2:swarm`, not a tier AI) under Scarab's name; `TIER 20 Scarab decisions=0`, 0x005B186F.] (The 21 sessions are a variety batch, not the first run's volume: the first run's kept counts stand for the first-boundary floor, 14 645 decisions, rechecked by the review with `tools/ai.py` at this lane's head: 12 614 compared, 0 mismatches.) The new stages
(a melee Barbarian, a curse caster, `/players 8`) did **not** produce a second first-boundary outcome for any of the eleven one-outcome rows: the Barbarian's melee
changes the monster's target and distance, and the first callee of those think functions does not depend on either (the `melee` control separates none of them). That is
a statement about the first callee only (§ 7 has the later calls). (run:2026-11-03-ai-3, 0x005B186F)

### 7. The resumable model on the kept logs

`resume-stdout-2026-11-03-ai-3.txt`, `resume-tier-2026-11-03-ai-3.txt` (decisions, resumed, mismatches, stopped, matched calls, matched calls past the first, steps where an unknown
value decided / all steps; 17 tier AIs and row 19, which the kept tier file labels Scarab; no tool in the record prints that file, so the next lane prints the table from `tools/ai_resume.py`):

| AI row | tier AI | decisions | resumed | mismatches | stopped | matched calls | past the first | ambiguous / steps |
|---|---|---|---|---|---|---|---|---|
| 2 | Skeleton | 126 | 126 | 0 | 0 | 126 | 0 | 0 / 0 |
| 6 | Fallen | 814 | 814 | 0 | 0 | 25 552 | 24 738 | 8 661 / 24 738 |
| 9 | Wraith | 62 | 62 | 0 | 0 | 62 | 0 | 0 / 0 |
| 13 | FallenShaman | 104 | 103 | 0 | 1 | 465 | 361 | 0 / 362 |
| 19 | Swarm (not a tier AI) | 82 | 82 | 0 | 0 | 82 | 0 | 0 / 0 |
| 20 | Scarab | 0 | 0 | 0 | 0 | 0 | 0 | 0 / 0 |
| 21 | Mummy | 205 | 205 | 0 | 0 | 410 | 205 | 0 / 205 |
| 22 | GreaterMummy | 27 | 1 | 0 | 26 | 1 | 0 | 0 / 0 |
| 28 | Vampire | 43 | 43 | 0 | 0 | 172 | 129 | 0 / 129 |
| 29 | BatDemon | 20 | 20 | 0 | 0 | 69 | 49 | 0 / 49 |
| 30 | Fetish | 316 | 316 | 0 | 0 | 1 193 | 877 | 0 / 877 |
| 34 | Andariel | 9 | 9 | 0 | 0 | 10 | 1 | 0 / 1 |
| 35 | CorruptArcher | 22 | 22 | 0 | 0 | 63 | 41 | 0 / 41 |
| 37 | SkeletonBow | 86 | 82 | **4** | 0 | 366 | 280 | 5 / 284 |
| 61 | Hireable | 2 066 | 2 061 | 0 | 5 | 33 099 | 31 034 | 2 095 / 31 037 |
| 64 | SkeletonMage | 91 | 66 | **25** | 0 | 210 | 119 | 12 / 144 |
| 67 | NecroPet | 53 | 53 | 0 | 0 | 502 | 449 | 21 / 449 |
| 89 | Megademon | 77 | 77 | 0 | 0 | 309 | 232 | 0 / 232 |
| 125 | BloodLord | 22 | 22 | 0 | 0 | 22 | 0 | 0 / 0 |

(The "0 mismatches" of a row is a statement about the logged calls the model could resume: every logged boundary call is one the game's code can make from the logged inputs and the earlier logged results,
with the exclusions of the stopped decisions and of the ambiguous steps; it does not say which of several offered calls the code takes when an unknown value decides.) Rows 2, 9, 19 and 125 have `past the first` 0:
their decisions make one boundary call and return, so for them the resume adds only the return after it.

**What stops a resume** (stop reasons, `RSTOP`): the operand `ds:0x744304`, which the model's `parse_op` does not read, in rows 12, 22, 43, 68, 73 (205 decisions; GreaterMummy 26 of
its 27 decisions stop there, at 0x005F2C1D). [2026-11-04, `lane/p52b` review: filed as "a `.data` pointer the logger does not record"; the stop is the operand parser's, and the word read at 0x005F2C25, `g_pDataTables + 0xA80`, is AID's logged `ms2`. With that operand read, the 205 resume with 0 mismatches and GreaterMummy 27 of 27 (`review-p52b/check-fixed.txt`), so no logger change is needed.] Then: a call through `esi` the model cannot resolve (row 32, 80 decisions); a boundary call whose return site is not armed (row 13: 1, row 61: 3); the log ending inside a decision (rows 5, 61: 3).
There is no longer a decision stopped by the logger's cap of 48 calls. **The 112 mismatches** (`RMISMATCH`, all printed in `resume-stdout-2026-11-03-ai-3.txt`): row 23 66 (the logged call is the model's only offered call
at the same address and differs in the unit's flag word `+0xC4` or in the callee and its arguments), row 64 25 (a logged call to 0x005DDF90 or 0x005DE080 against the model's other call, or the unit seed differing), row 95 9, row 79 6 and row 78 1 (the control word `c0`),
row 37 4, row 32 1. 96 of the 112 are in the five melee and curse logs and 6 in `a2-oasis-3`; the model passed the same rows on the development logs (§ 4: 0 of 1 313). The lane filed them unexplained, with three candidate causes; the review's note below settles them. (run:2026-11-03-ai-3, tools/ai_resume.py)

**[2026-11-04, `lane/p52b` review] The 112, classified.** `tools/ai_resume_review.py classify` (`review-p52b/classify.txt`) gives the smallest set of named fixes that clears each kept `RMISMATCH`; each cause was read against objdump of the pinned image. The tags are `[I]`: the cause of a mismatch is a statement about the model, and the fixes are the reviewer's check until the next lane folds them in with tests and reruns.

| Cluster | Rows (decisions) | Class | Cause (the fix's letter in the tool) |
|---|---|---|---|
| A | 64 (25), 95 (9), 37 (4) | model | `init_state` protects `STK_TOP..+8`, which holds the think's own argument slot `[ebp+8]`. These thinks pass that slot as a search's output (`lea eax,[ebp+0x8]`, 0x005F96DB, callee 0x005DDC30), so `apply_result` dropped the logged distance and the think went on with the stale `AiCtx+0x14`: logged 8 → 5 at `a1-necro` n 2148, where the `aip` compares at 0x005F9702 then pick another branch (P). |
| B | 23 (41), 32 (1) | model | `Unit+0xC4` changes inside an opaque callee: 0x005DE4E0 at 0x005F32A0 and its sites (`s-barb-flayer` n 263: 0 → 0x82001 between the 0x00472210 return and the 0x005DE0F0 call), 0x00553380 returning to 0x005E6A20 in row 32 (C). |
| C | 23 (17) | model and logger filter | as B, and the logged 0x00552F60@0x0058F0FF is made inside that command, between its `MSM0` and `MSM1` lines; the call site lies in a logger window, so the line is written with no pending boundary call, and `top_level` keeps it (C, N). |
| D | 79 (5) | model | the opaque 0x00620870 at 0x005FB824 forgets up to 64 bytes from `[ebp-0xC]` up to EBP, which takes the control pointer `[ebp-4]`; the write of `c0` at 0x005FB862 then goes through an unknown pointer (B). |
| E | 79 (1), 78 (1) | model | as D, and `RNG_RandLoHi` 0x004BC500, called at 0x005FB69D on the unit seed when the region's trap-arrow kind is first set, is opaque, so the model misses that one draw (B, E). Once per region, as ai/0005 § 2.17 reads it. |
| F | 23 (8) | logger | the logged decision stops at 0x00620BB0@0x005F33EC, and the code after it must reach 0x005DE190 or 0x00620BB0@0x005F341F. Seven of the 8 have a next decision of the unit, whose `c0` is one less and whose point `c1`, `c2` has moved, so the code ran on through 0x005F343F (the eighth ends its log). The calls were not logged: the cause read is the limit of 600 non-think boundary calls in `on_bnd`, which disables the boundary breakpoints and re-arms them only when a pending return fires, and `sub_0064E7B0_FreeNearFallback` (not a boundary) leaves nothing pending while `COLL_FindFreeNear` 0x0064DEA0 under it calls the boundary function 0x00463740. Of the 104 row 23 decisions in these three logs that reach 0x005F33EC, 96 log on past it. No fix in the tool clears these. |

Why the five logs: A, B, C and D need a target near the unit (the distance crossing an `aip` compare, row 23's near branches, the `|dy| <= 2` test of row 79 at 0x005FB840), which a melee Barbarian and a Necromancer's pets bring and the Sorceress's stages rarely do. `s-necro-curse` has 0, and all 112 decisions have state 0 at their `AID` line: **the curse states are not a cause, and these 112 need no input the logger lacks**. The three causes the lane listed: an unrecorded input is not needed for any of the 112, the opaque callee holds for B, C and E, and the model error holds for A and D. **No finding's reading of the game is contradicted.** With all fixes (P, B, C, N, E, D) over the 21 logs: 7 444 resumed, 8 mismatches (cluster F alone), 87 stopped (row 32's `call esi` 80, a return site not armed 4, a log's end 3), 72 865 calls matched, 65 332 after the first; the controls still fail: reversed branches 7 290 of 7 539 (rows 15 and 54 not separated), a seed one step off 7 529 of 7 539. (`review-p52b/check-fixed.txt`; run:2026-11-03-ai-3, 0x005F96DB, 0x005F32A0, 0x005FB824, 0x005FB69D, 0x005F33EC)

Which branches stay unseen: for the one-outcome rows the first callee is the same in every decision (§ 6); past it, `distinct_logged_prefixes4` (the distinct first four boundary calls) per row is 2 (Fallen, NecroPet, Hireable), 4 (SkeletonBow's main think), 5 (Fetish, SkeletonMage's main think), 7 (BatDemon's think, Megademon), 8 (CorruptArcher) and 9 (Vampire) in the resume output, and the `ambiguous` column says where an unknown value
(distance, target, an unread table) decided between calls the code offers: Fallen 8 661 of its 24 738 later steps, Hireable 2 095, NecroPet 21, SkeletonMage 12. Seen in the first run's logs and not in this batch (first-boundary outcomes, `MIX`): Wraith's third, all five of Scarab's (no decision of row 20 here), FallenShaman's second, GreaterMummy's third; this batch reproduces the five of Mummy, Andariel and BloodLord. The skills-available and target-distance branches behind a one-outcome first callee are seen only through the later calls above.

### 8. The state control

`AiCtl.state` is logged at every AID and AIN line (`st`). Kept window: the 21 sessions of run:2026-11-03-ai-3 (7 539 decisions, 10 721 events). Values seen: 0 everywhere except `s-necro-curse` (Dim Vision and Terror on monsters of Jail 1: **10** in 38 decisions
and **11** in 78 decisions, all on AI row 12, class 57) and `s-barb-howl` (**11** in 20 decisions and 41 AIN events, **12** in 56 decisions; AI rows 37 (class 172) and 64 (class 384); Jail 1, the Barbarian with Howl and Taunt). The logger is therefore shown live to read states
10, 11 and 12 (the setters at `CurseSetAiState` 0x005C34B0 for `auratargetstate` 23, 56 and 27 of ai/0001 give 10, 11, 12, `[I]`). **In the logged lines of this window the states 1 to 9 and 13 to 17 do not occur: 0 of 7 539 decisions and 0 of 10 721 events**, including 2, 3, 8, 9, 14 and 17.
Scope [2026-11-04, `lane/p52b` review, which struck "no skill in the window sets any state other than through the curse casters": no log here records skills, so the run cannot state it]: Normal; the stages of § 6, 34 980 frames summed over the 21 logs' first and last `fr`; 27 `CAP` lines end a row's or the events' logging within their game, so the statement covers logged lines, not every decision played; the word is read only at a decision or an event, so a state set and cleared between them is not seen. The live control is two sessions' worth (10, 11, 12); elsewhere nothing was staged that sets a state, and the same logger read the same word. The absence is `[C]` as that statement about these logs. State 13 (The Countess) has no live control here, as the plan's Done-when requires, and this window says nothing about a stage it did not hold: Amplify Damage, Decrepify, Lower Resist, Attract, a `MonFleeFrom` by a hireling, Nightmare or Hell. That no code sets 2, 3, 8, 9, 14, 17 stays `[I]` (a static reading, ai/0013 § 3), and P3b still does not call them dead. (run:2026-11-03-ai-3, 0x005B186F, 0x005C34B0)

### 9. P1b-2, the Greater Mummy and a champion corpse (built state)

Run run:2026-11-04-ai-3p (slot 2, `AI_P1B2=1`, `tools/gdb/ai-p1b2.py` rev 2, Halls of the Dead 2, two sessions `a2-halls-p12` and `a2-halls-long`; a first launch stayed in the town; a development session first, `dev-2026-11-03-ai-3p`). At the entry of the Greater Mummy's search callback
`sub_005F2A00_AiGreaterMummyCb` (0x005F2A00) every dead candidate (unit mode 12) with no champion or unique flag gets the champion flag 4 (first, third ... met) or the unique flag 8 (second, fourth ...) in the word at `Unit+0x14 -> +0x16`, the word `MonTypeFlag` (0x005A0180) tests: **a built state**, not a natural
champion. Counts (`p1b2-run-2026-11-04-ai-3p.txt`, `tools/ai_p1b2.py`): 17 champion-flag and 16 unique-flag corpses placed; 46 Greater Mummy decisions (AI row 22); `MonSkillTargetOk` (0x005FD470, skill argument 327) was called from them with a **champion** corpse as its second argument 4 times and with a **unique** corpse 0 times. Results: 2 accepted (EAX 1), after which `sub_00620C10_UnitSetPathTargetUnit` 0x00620C10 and the command (`MSM0`
`cmd` mode 14, the Greater Mummy, the corpse, skill field 101) followed; 2 refused (EAX 0, the skill's own test: the reason is not read), after which the code went to the next search. The callback's own filters before the flag test (same side, alignment, undead) are not logged per candidate, so the unique corpses'
absence is shown only in aggregate. Reading: a champion corpse in range becomes the callback's `corpse` and is offered to the skill test, a unique one does not (flag 8, 0x005F2A96): `[I]`. [2026-11-04, `lane/p52b` review: filed `[C]` "for the code as run". `tools/gdb/ai-p1b2.py` writes game memory at a breakpoint; ADR-0003 says a breakpoint "never writes game memory or registers", and ADR-0010 and ADR-0013 admit cells of one table through a loose `.bin`, not a memory write. Even read by analogy, ADR-0013 keeps `[I]` a claim whose code reads the edited value, and this callback tests the written flag. So the run stands as a stated deviation (experiments.md) and backs no `[C]`. The flag test at 0x005F2A96 also applies only while the block's `+0x18` is 0: Radament sets it (ai/0003 § 2.6, 0x005F2C6E), so "a unique one does not" holds for this class 101 and is not a statement about row 22 at large.] C40 stays `contradicted` for champions in the reading of the code only, and its required case is open: no natural champion was seen. The stock route is the `-forced` run of the plan's order, with no write. (run:2026-11-04-ai-3p, fn:sub_005F2A00_AiGreaterMummyCb@0x005F2A00)

### 10. G4, breakpoints on the seven helpers

`tools/gdb/ai-g4.py` rev 1 arms entry breakpoints on 0x005E9DD0, 0x005FD0F0, 0x005F7F10, 0x005DD140, 0x005F8010, 0x005FC130 and 0x005E9750 and on nine controls (the LIVE rows of ai/0016 § 1), in the logger of every kept launch (no extra session).
`tools/ai_g4.py` over the 23 kept launch logs (`g4-run-2026-11-03-ai-3.txt`): **helper hits 0** in 23 of 23; control 0x005B1CF0 (`sub_005B1CF0_MonPostCreateBoss`) hit in 23 of 23 launches (the counts 4 to 128 are floors: a control prints at its 1st, 2nd, 4th, 8th ... hit), 0x005A3250 (`UModQuestCompleteDeath`) in 2; the other seven controls (the Uber and Baal action entries) are not reached by Normal stages and give
no window. [2026-11-04, `lane/p52b` review:] the two live controls show that an entry breakpoint of this logger fires in that process, at monster creation (its last printed line lies 15 % to 99 % of the way through the 23 launch logs; hits after the last power of two print nothing). They do not show that the window reaches anything near the helpers: their seven sibling controls are silent too. So the 0 is adequate for what it says, these seven entries are not entered in these Normal stages. Scope: Normal difficulty stages of the listed cases, 2 of the 23 launches with the P1b-2 write; no Uber event, no edited cell; an unreferenced entry that only an Uber session would reach is not tested by this window, so the static statement (ai/0016 § 1) gains a run window and stays `[I]`.

### 11. P1b-1, Duriel (not done)

Route from the plan 0032 session 3364 log (`quests-s3-3364-duriel-normal.log`, in the old workspace): on map seed 3364 Tal Rasha's real tomb is level 72 (Canyon of the Magi 46, waypoint arrival (12678, 5178), the warp reached near (12794, 5033); in the tomb the orifice object 152 at (22858, 14043) and a portal object 100 at (22845, 14046); the lair 73 arrival (22638, 15693)).
Built: the character `AiDur` (`tools/d2s_recipes/ai-dur.json`: `CombatSor` plus the quest bits of `questfreshvh` and the Horadric Staff at inventory cell 0,0), the case `d-duriel` of `tools/ai_sessions.py` (Canyon waypoint, `objop --goal --stop-on-level` to the warp, the staff to the cursor with `insert`, `objop` on object 152 and 100, then `hunt --mon-cls 211 --radius 1`). The one development attempt
(`dev-2026-11-04-ai-3d`): the first launch (seed 3364) left the character in the town (waypoint), the rerun ran on seed 3365 (the runner adds the launch number to the seed, so the route's own seed was used once, in the failed launch) and the character was left on the Canyon level at (12859, 5281) after the `objop` to the warp, with no tomb entered; stopped by hand. **No decision of row 44 was logged.** It is a case for owner play (§ 12).

### 12. What stays short

[2026-11-04, `lane/p52c`: H3 and the fixed model's rerun are done, § 13.] H1 (the 331 monster gaps with the skills logger beside this one), H3 (Raven's 2 218 `MonAttackStats` calls), the catalogue sample of batches 5, 7, 10, 11, 12, Fetish's and Andariel's chained pairs at `/players 8` (`a1-andariel-p8` kept: 9 Andariel decisions in the 21 sessions' check, 263 decisions of the session), P1b-1, P1b-2's stock case, state 13, the fixed model's kept rerun, the first run's volume (14 645 decisions) not repeated.
Owner play for P1b-1: [2026-11-04, `lane/p52b` review: the first text would have lost the session, since the logger's default `AI_CAP_ROW` of 200 ends row 44's lines below the 300 asked.] The objective, launch and stop rule are in [the owner entry](../../backlog/2026-11-04-architect-human-plan-0052-p1b-1-duriel-melee-owner-play.md).

### 13. Third part, 2026-11-04 (`lane/p52c`): the fixed model, the tier table, H3, logger rev 5

Run run:2026-11-04-ai-resume, no game, over the same 21 rev 4 logs of run:2026-11-03-ai-3. The review's six fixes are in `tools/ai_resume.py` with a no-game test each (`ReviewFixesTest`; reverting any one fix in a scratch copy fails its test), and `tools/ai_resume_review.py` is retired.

- [I] (run:2026-11-04-ai-resume, 0x005F96DB, 0x005F32A0, 0x005FB824, 0x005FB69D, 0x005F2C1D) **The fixed model reproduces the review's classification.** 7 539 decisions: 7 444 resumed, **8 mismatches**, 87 stopped (row 32's `call esi` 80, a return site not armed 4, a log's end 3), 72 865 calls matched, 65 332 after the first; the `RROW` and `RSTOP` lines equal `review-p52b/check-fixed.txt`. Controls: reversed branches 7 290 of 7 539 (rows 15 and 54 not separated), a seed one step off 7 529 of 7 539.
- [I] (run:2026-11-04-ai-resume, 0x005F33EC) **The 8 are row 23, none in the tier:** each ends after boundary 7 with the model offering another call, four in `s-barb-flayer`, three in `s-barb-oasis`, one in `a2-oasis-3`. The logger's 600-call limit stays the cause read (§ 7, cluster F); rev 5's marker lets the next batch tell. Row 23's claim stays `[I]`.

`resume-tier-2026-11-04-p52c.txt`, printed by `tools/ai_resume.py --tier` (row 19 Swarm, row 20 Scarab). `paths`: distinct sequences of logged calls past the first, among resumed decisions; `top`: the commonest path's share; `sites`: distinct (function, call site) past the first; `branches`: known-value branches decided both ways / one way; `amb`: steps where an unknown value decided, of all steps.

| AI row | tier AI | decisions | resumed | mismatches | stopped | past first | amb | paths | top | sites | branches | reversed fails | proposal |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2 | Skeleton | 126 | 126 | 0 | 0 | 0 | 0/0 | 1 | 126/126 | 0 | 4/0 | 110/126 | weak: no call past the first |
| 6 | Fallen | 814 | 814 | 0 | 0 | 24 738 | 8 661/24 738 | 88 | 102/814 | 22 | 22/21 | 814/814 | `[C]` |
| 9 | Wraith | 62 | 62 | 0 | 0 | 0 | 0/0 | 1 | 62/62 | 0 | 1/1 | 56/62 | weak: no call past the first |
| 13 | FallenShaman | 104 | 103 | 0 | 1 | 361 | 0/362 | 10 | 39/103 | 8 | 10/5 | 104/104 | `[C]` |
| 19 | Swarm (not tier) | 82 | 82 | 0 | 0 | 0 | 0/0 | 1 | 82/82 | 0 | 3/0 | 81/82 | not tier |
| 20 | Scarab | 0 | 0 | 0 | 0 | 0 | 0/0 | 0 | 0 | 0 | 0/0 | - | short |
| 21 | Mummy | 205 | 205 | 0 | 0 | 205 | 0/205 | 5 | 76/205 | 5 | 4/2 | 205/205 | `[C]` |
| 22 | GreaterMummy | 27 | 27 | 0 | 0 | 48 | 0/48 | 7 | 14/27 | 7 | 6/9 | 27/27 | short |
| 28 | Vampire | 43 | 43 | 0 | 0 | 129 | 0/129 | 9 | 12/43 | 11 | 11/12 | 43/43 | short |
| 29 | BatDemon | 20 | 20 | 0 | 0 | 49 | 0/49 | 7 | 4/20 | 12 | 6/11 | 17/20 | short |
| 30 | Fetish | 316 | 316 | 0 | 0 | 877 | 0/877 | 5 | 243/316 | 8 | 7/8 | 316/316 | `[C]` |
| 34 | Andariel | 9 | 9 | 0 | 0 | 1 | 0/1 | 2 | 8/9 | 1 | 4/6 | 9/9 | short |
| 35 | CorruptArcher | 22 | 22 | 0 | 0 | 41 | 0/41 | 8 | 5/22 | 11 | 9/8 | 22/22 | short |
| 37 | SkeletonBow | 86 | 86 | 0 | 0 | 284 | 5/284 | 10 | 47/86 | 19 | 8/13 | 86/86 | `[C]` |
| 61 | Hireable | 2 066 | 2 061 | 0 | 5 | 31 034 | 2 095/31 037 | 14 | 699/2 061 | 31 | 12/24 | 2 065/2 066 | `[C]` |
| 64 | SkeletonMage | 91 | 91 | 0 | 0 | 148 | 12/148 | 11 | 34/91 | 24 | 13/15 | 91/91 | `[C]` |
| 67 | NecroPet | 53 | 53 | 0 | 0 | 449 | 21/449 | 7 | 17/53 | 16 | 11/8 | 53/53 | `[C]` |
| 89 | Megademon | 77 | 77 | 0 | 0 | 232 | 0/232 | 7 | 43/77 | 9 | 7/12 | 77/77 | `[C]` |
| 125 | BloodLord | 22 | 22 | 0 | 0 | 0 | 0/0 | 1 | 22/22 | 0 | 4/0 | 22/22 | short |

- [C] (run:2026-11-04-ai-resume, 0x005B186F) **Proposed for review: past the first boundary, rows 6, 13, 21, 30, 37, 61, 64, 67, 89, for these 21 rev 4 logs.** Each has 0 mismatches and at least 50 resumed decisions, and more than one path past the first boundary. The statement: every logged top-level boundary call of a resumed decision equals, in every word the model knows, a call the row's code can make from the logged inputs and the earlier logged results, and the decision can then return with no further call. It does not say which offered call the code takes when an unknown value decides: Fallen 8 661 of its 24 738 later steps, Hireable 2 095, NecroPet 21, SkeletonMage 12, SkeletonBow 5. The stopped decisions are outside it (FallenShaman 1, Hireable 5). It assumes that an opaque callee changes no known memory but `Unit+0xC4` and its pointer arguments.
- [I] (run:2026-11-04-ai-resume, 0x005B186F) **What each proposed row separates is uneven.** Fetish is the weakest: 243 of 316 decisions take one path. Mummy has one call past the first in every decision, so its 5 paths are 5 single callees. Fallen has 88 paths over 22 call sites, Hireable 14 over 31. Reversing every known branch fails all or all but one of each proposed row's decisions, but that control reverses every branch at once: it does not show that each `branches` entry alone would fail. Branches decided one way have only that way compared.
- [I] (run:2026-11-04-ai-resume, 0x005B186F) **Not proposed.** Skeleton and Wraith pass the floor with no call past the first: they add only the return after one call, so they stay at the first boundary. Short of 50: Scarab 0, Andariel 9, BatDemon 20, CorruptArcher 22, BloodLord 22, GreaterMummy 27, Vampire 43. BloodLord also has no call past the first.

**H3.** `tools/ai_h3.py`, output `h3-2026-11-04-p52c.txt`, over `2026-10-25-skills-dru-1.log` and `-dru-2.log`: 2 320 calls of class 419, 2 218 with a stat list and 102 without.

- [C] (run:2026-11-04-ai-resume, fn:sub_005A4F50_MonAttackStats@0x005A4F50, fn:sub_0056E050_MonOwnerSkillDamage@0x0056E050, fn:sub_0056E000_SkillDamagePair@0x0056E000) **The 2 218 Raven calls carry the pair at the owner's level, for one owner level.** With the caster's logged Raven level 20 (`SST0`, 207 casts; the recipe's 20) and the Skills row 221 cells, the block is (21, 23, 385). The Raven's own MonLvl terms are 0 in these modes, so stats 21 and 22 are the block alone. Of 101 units' first calls with a list, 101 match: no 21 or 22 before, afterwards 21 = 21, 22 = 23, and 19 raised by exactly 385 from the 1 123 the other lists hold. The other 2 117 calls leave the full stats unchanged. The seed does not step in any of the 2 320 calls. What separates is the 101 first calls: level 19, level 21, the summon's level 104, level 0 and no pair each fail all 101. The later 2 117 show only that the write repeats, and all calls have the same owner level, so the band terms (all 1 in this row), the clamp in `SkillLevelClamped` and the Kick, SrcDam, DmgSymPerCalc and ToHitCalc branches are not separated and stay `[I]` (ai/0006 § H3). The modes (0, 1, 2, 4) do not separate: their columns give 0 here. `SKILLS_GetPhysMin`, `GetPhysMax` and `GetToHit` are checked only at this one row and level, so they stay `I`.

**Catalogue sample, what the logs hold.** Batch rows in the case logs of run:2026-11-03-ai and run:2026-11-03-ai-3 (`tools/ai.py counts`, `catalogue-rows-2026-11-04-p52c.txt`): batch 5 only row 67 and batch 7 only row 34, both tier rows; batch 11 none; batch 10 only row 130, 85 decisions in the first run's rev 3 logs, which have no `AIR` lines. Batch 12: rows 32, 54, 99, 100.

- [I] (run:2026-11-04-ai-resume, 0x005E7130, 0x005E73A0, 0x005E9F10, 0x005E7F50) **Batch 12 is compared by the code model only.** Row 54 125 decisions, row 99 25, row 32 199 of 279 resumed (80 stopped at `call esi`), all 0 mismatches. But rows 54 and 99 have no call past the first, and row 54 is one of the two rows the reversed-branch control does not separate, so these say little. Row 100 has 4 decisions, under the floor.
- **No first-boundary maps were added.** `tools/ai.py`'s `MODS` lacks `ai_cat_emu10`, `11` and `12`, and adding them needs their `CTRL` and `HAS_BLOCK` entries and the inputs `inputs()` does not yet build. Row 32 has `hp` 0 in the three decisions read (`a1-jail`), and for such a decision `ai_cat_emu12`'s first boundary is `PARAMSPUSH` at 0x0058EFDD, a site the logger does not log. This rotated to the next lane. Batches 5, 7 and 11 need stages the kept logs do not have, and the catalogue sample stays short.

**Logger rev 5** (`tools/gdb/ai.py`, no game, so not yet run): no `AIB` between a decision's `MSM0` and `MSM1`, and an `AIL` line at the 600-call limit (`k`, `fn`, `ra`, `out`, `pend`). `tools/ai.py` parses it and `tools/ai_resume.py` stops a decision whose `AIL` has `pend` 0, where nothing re-arms the breakpoints. The tests read the source for the order of the breakpoints and test the stop, so the first rev 5 session is the logger's real check.

### 14. Resume note (2026-11-04, `lane/p52c`, rotated at about 250k tokens)

Left, in order. **No game:** (a) first-boundary maps for rows 130, 54, 99, 100 and the state thinks 0x005E8020, 0x005E8140, 0x005E8340 (§ 13); (b) the waypoint entry: the seed held on a rerun with a no-game test, then the cause of the failed click; it needs a game, and its Done-when needs a kept batch; (c) the stage-check entry in `tools/harness_runner.py`. Neither backlog entry was started. **For the kept batch's lane, on rev 5:** Scarab 50 (0 now, the first run's stage), Andariel 41 more, BatDemon 30, CorruptArcher 28, BloodLord 28, GreaterMummy 23, Vampire 7; The Countess beside a curse case (`s-necro-curse`) for state 13; Fetish and Andariel at `/players 8` for the chained pairs; H1 with the skills logger beside this one. Count `AIL` lines in row 23 to settle cluster F. Steps 5 and 6 of the review's order (P1b-2 forced, P1b-1 owner play) are not this lane's.

## Data touched

tbl:MonStats.txt:AI, tbl:MonStats.txt:aip1 … aip8, tbl:MonStats.txt:Skill1, tbl:MonStats.txt:SkillDamage, tbl:Skills.txt:MinDam, tbl:Skills.txt:MaxDam, tbl:Skills.txt:ToHit, tbl:Skills.txt:LevToHit; struct:AiCtl+0x14, struct:AiCtl+0x18, struct:AiCtl+0x1C,
struct:AiCtx+0x00.

## Open questions

- The 8 row 23 decisions of § 7's cluster F: is the 600-call limit the cause? Logger rev 5 marks the limit, so the next batch can tell.
- P1b-1 (Duriel), H1, the catalogue sample: see §§ 12 to 14.
- `[L]` Why the waypoint list does not open on the first try in 14 of 35 launches (§ 6): not investigated.
