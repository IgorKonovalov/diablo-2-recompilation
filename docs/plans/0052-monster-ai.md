# 0052 — Monster AI: the AI tick, target and skill choice, and the pathing it drives (ADR-0014 phase 5; first draft)

> **Status:** proposed (first draft, held until its gate: approvable at the review of plan 0045's spec, owner 2026-10-25)
> **Created:** 2026-10-25
> **Owner skill(s):** archivist, reverser, spec-writer
> **Related ADRs:** 0003-runtime-experiments, 0004-boundary-oracles-in-reproduction, 0011-harness-slots, 0014-scope-game-simulation, 0015-emulated-reproduction, 0016-pipelined-simulation-phases, 0020-skills-phase-in-two-plans, 0021-observed-boundaries-in-emulation

## TL;DR

**Question:** on each frame a monster (or a hireling, or a summon) is active, what does its AI do: when does it think,
which target does it pick, which mode or skill does it choose, where does it path to, and which draws does it make on
which seed? This is phase (5) of [ADR-0014](../adrs/0014-scope-game-simulation.md), after animation and frame timing
(phase (4), plan [0050](0050-animation-frame-timing.md)). When it is done, `docs/findings/ai/` names the AI dispatch
and the per-AI functions, `tools/ai.py` reproduces AI decisions per event, and `docs/specs/monsters/ai.md` (research-map
row `monsters/ai`; a directory if the spec-writer splits it) is reviewed. It also explains the out-of-scope draws that make ADR-0014 resynchronise most combat and
skill events' entry seeds, and lets the later runs chain more of them.

This is a **first draft**: its scope is set by the owner's answers to the questions in § Scoping questions, and the
architect re-drafts it at its gate.

## Context

- **The gate.** ADR-0020 lets phase (5)'s plan follow plan 0045's reviewed spec (0045·P3, `skills/dispatch` and
  `skills/missiles`); this draft is written ahead of that at the owner's request (2026-10-25), and its approval takes
  effect at that gate. Its harness phase starts only once **phase (4)'s spec (0050·P3) is reviewed** (ADR-0016: a
  phase's harness waits for the previous phase's reviewed spec), since the AI's mode choices are timed by phase (4)'s
  model. Plan 0046 never gates it (ADR-0020); a catalogue function an AI calls and 0046 has not specified is a boundary
  oracle under ADR-0004, named in the spec, as plan 0050 does.
- **Size.** MonStats `AI` names 146 distinct AIs over a table of 148 entries (`g_MonAiTable` `0x0073CA18`,
  `sub_005B15D0_MonAiEntryGet`, [items/0001](../findings/items/0001-tc-resolution.md)); each AI reads its `aip1..8`
  per difficulty and `aidel`/`aidist` ([MonStats](../tables/MonStats.md)). Hirelings have their own AI
  (`MERCAI_PickSkill` `0x005E4D30`, [hirelings](../specs/hirelings/README.md)). This is a catalogue as large as plan
  0046's, plus the shared machinery.
- **Code already named:** `sub_005DDFC0_MonAiSetMode`, `sub_005DEAD0_MonAiUseSkill`, `sub_005DE190_MonAiPathOverride`,
  `sub_005A6260_AiPathOverrideSet`, `sub_005DD220_AiCtlFlagTest`, `sub_005DD250_AiCtlTeleportFlagSet`,
  `sub_005F72D0_AiZakarumPriest`, the inactive save and restore `sub_00541FE0_InactiveMonAiSave` /
  `sub_00541E20_InactiveMonAiRestore` ([drlg/lifecycle](../specs/drlg/lifecycle.md)); the path code plan 0050 reads for
  speed (`PathSetSpeed`, `PathVelocityStep`).
- **Research map row:** `monsters/ai` (Simulation band; ADR-0014's expected name), added with this draft. Wiki owner:
  Phase 4.

## Phases (outline)

### Phase 0 — The AI tables
- **Owner skill:** archivist
- **What:** the AI index: per AI number, the MonStats rows that use it, their `aip1..8` per difficulty, `aidel`,
  `aidist`, the skill columns (`Sk1mode..Sk8mode` and the skills and levels beside them); the not-loaded `Aiparms.txt` read as a lead for the parameter names only;
  `tools/ai_survey.py` (gate survey `ai`) with the batch sizes.
- **Done when:** every AI a stock row uses is listed once with its rows; the survey matches; meanings `[L]` until
  anchored; the gate is green.

### Phase 1 — The AI machinery, then the AI catalogue
- **Owner skill:** reverser (one Ghidra lane, batches as plan 0046's)
- **What:** P1.1 the machinery (the AI tick and its delay, the AI state, target search, `MonAiUseSkill` and
  `MonAiSetMode`, the path request and its kinds, leader and minion following, the draws and their seeds); P1.2 onward,
  the per-AI functions in batches sized from Phase 0's survey (estimate: eight to twelve), each emulated where it
  is a pure decision (ADR-0015, ADR-0021).
- **Done when:** each batch's functions named with addresses, `[I]` or better, draws listed per seed; the boundary
  recommendation for Phase 2 (what the AI takes as oracles: the skill outcome, the animation's frames, the path's
  result if pathing stays out).

### Phase 1b — Community cross-check
- **Owner skill:** reverser (no Ghidra). AI descriptions in the community (boss behaviour guides) are compared blind;
  `contradicted` claims reachable on stock data become Phase 2 cases.

### Phase 2 — Per-event reproduction
- **Owner skill:** reverser (harness; slots per § Scoping questions)
- **What:** `tools/ai.py`, `tools/gdb/ai.gdb`; one event is one AI decision (inputs: the monster, its state, its
  targets in range, the frame; outputs: the mode or skill chosen, the target, the path request; the draws). Chained
  pairs per kind as ADR-0014 requires; the floors are set at the P1.1 review.

### Phase 3 — Spec: monster AI
- **Owner skill:** spec-writer. `docs/specs/monsters/ai.md` or a directory (overview, machinery, per-AI entries); combat, skills and the
  monsters specs updated where AI was an input.

### Phase 4 — Wiki page: monster AI
- **Owner skill:** spec-writer. `docs/wiki/monster-ai.md` over the reviewed spec.

## Scoping questions for the owner

Open until this plan is re-drafted at its gate (owner, 2026-10-25). The owner leans towards pathing as **its own
part** (question 1). Question 6's reading is confirmed (below).

1. **Pathing in or out.** The path search a monster runs (its kinds, its cost, its draws) is large and close to
   collision. Include it in this plan, give it its own plan, or keep it as an oracle (the path request and its result
   logged) with only the speed in plan 0050?
2. **One plan or two.** Split as phase (3) was (ADR-0020): a machinery plan with a named tier of AIs reproduced per
   event, and an AI catalogue plan by static reading and emulation? The split would need its own ADR, amending
   ADR-0014 for phase (5) as ADR-0020 did for phase (3).
3. **Per-frame observation.** AI decisions run every few frames on every active monster. If per-event breakpoints
   with filters and caps cannot keep the logs bounded, ADR-0014 keeps an injected logger in reserve "behind its own
   ADR". Should the architect draft that ADR at the P1.1 review if the boundary recommendation asks for it?
4. **Hirelings and summons.** Mercenary AI and the player's summons' AI: in this plan, or a follow-up?
5. **Harness slots.** One slot (as plan 0050) or both, given that the remaining plan 0038 batches may still run on
   the other?
6. **The gate's reading.** This draft reads ADR-0020 as letting phase (5)'s plan be approved once 0045·P3 is reviewed,
   with its harness phase after 0050·P3 (ADR-0016's harness rule). ADR-0016's one-phase-ahead rule, read alone, would
   hold the plan until 0050·P2 is accepted. **Confirmed (owner, 2026-10-25):** approvable at the review of 0045's
   spec, per ADR-0020.

## Resources and limits

- **Harness:** at most **two harness lanes** at once across all plans, on **slots 1 and 2** (slot 0 is the owner's).
- **Static:** at most **two static lanes** and at most **two headless Ghidra** at once, `-Xmx3G` each; Phase 1 holds
  one Ghidra at a time, batch after batch.
- **Replays:** heavy replays and re-checks of kept logs run under `systemd-run --user --scope -p MemoryMax=4G`.
- **Rotation:** lanes past about 4 h checkpoint, write a resume note and stop; a fresh lane resumes on the same branch.
- **Estimate** (an estimate): larger than plan 0046; set once the scoping questions are answered.

## Open questions

- Which monster uses which skill, and when, is this plan's (plan 0046 open questions; skills/0001 § 13 and
  skills/0003 § 14 take it as an input).
- The town-follow and teleport-target questions of [drlg/lifecycle](../specs/drlg/lifecycle.md) are AI decisions and
  may be answered here.

## Implementation log

_(lanes append dated entries as phases land: what was found, the confidence reached, surprises)_

- **2026-10-25 — First draft (architect, `lane/plans50`).** Status `proposed`, held until 0045·P3 is reviewed;
  scoping questions for the owner listed.
- **2026-10-25 — Owner ruling (via the orchestrator).** The gate's reading confirmed (approvable at 0045·P3's review,
  ADR-0020); status stays `proposed` until then; the scoping questions stay open until the re-draft, with the owner
  leaning towards pathing as its own part; movement speed stays in plan 0050.
