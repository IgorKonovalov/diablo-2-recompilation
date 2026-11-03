# 0017 — Phase 2, second run (checkpoint): the outcome mix, the negative controls and a resumable model of the AI decision

> **Subsystem:** monsters/ai
> **Question:** can the claim of [ai/0015](0015-phase2-first-run.md) (0 mismatches at each decision's first boundary) be made to separate
> more than the first callee: what does each tier AI's comparison actually separate, does a deliberately wrong map fail on
> the kept logs, and can a decision be compared past its first boundary?
> **Date:** 2026-11-03   **Plan:** 0052 (Phase 2, second lane run `lane/p52b`)   **Status:** checkpoint. The checker and the
> resumable model are built and tested; **no session of this run is kept**, so no claim of this finding is `[C]` for a game
> run of the run; the live figures are from development launches or from the first run's kept logs (named each time).

Harness run run:2026-11-03-ai-2 (`docs/findings/ai/experiments.md`). Names are `re/symbols.csv` names. A decision is the call of
the think function at 0x005B186F (ai/0001 § 1); a boundary is a call of one of the 136 functions of `BND` in
`tools/gdb/ai.py` from the think code (ADR-0021).

## Answer (summary)

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

## Data touched

tbl:MonStats.txt:AI, tbl:MonStats.txt:aip1 … aip8, tbl:MonStats.txt:Skill1; struct:AiCtl+0x14, struct:AiCtl+0x18, struct:AiCtl+0x1C,
struct:AiCtx+0x00.

## Open questions

The run's required items are open; each is named with its state in the plan's resume note (plan 0052, the dated entry of this lane
run): the kept batch with logger rev 4 and the model on it (past-first-boundary claim per tier AI and the branches of each map that
stay unseen), the staged variety sessions, the state control window (Dim Vision, Terror, Howl, Taunt; recipes
`tools/d2s_recipes/ai-nec-curse.json` and `ai-barb.json` build), P1b-1 (Duriel's lair: the staff in the orifice, the right Tal
Rasha tomb), P1b-2, H1 (the skills logger beside `tools/gdb/ai.gdb`), H3 (Raven), Fetish and Andariel at `/players 8`, the
catalogue sample of batches 5, 7, 10, 11, 12, and the review request.
