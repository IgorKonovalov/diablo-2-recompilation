# 0065 — Harness sweep 8: the backlog's live cases in one batch per slot plan

> **Status:** approved (2026-11-10, by the owner, as recommended: Phase 2 runs, paired with plan 0067 Phase 2; not started: the owner starts it)
> **Created:** 2026-11-10
> **Owner skill(s):** reverser, spec-writer
> **Related ADRs:** 0003-runtime-experiments, 0008-two-client-harness, 0010-forced-path-runs, 0013-forced-path-runs-cell-level, 0014-scope-game-simulation, 0023-review-tiers-and-gate-first-fixes, 0028-case-and-process-in-experiment-records, 0030-verdict-lanes-and-wiki-tier-a

## TL;DR

**Question:** the open backlog holds six entries whose remaining work needs the game running. Each one is a handful of
cases that no plan schedules. Can one staging pass and two batches (one single-client, one two-client) settle them
all? When this plan is done, each case has a kept log and a check (0 mismatches or a named contradiction), and the
affected statements are re-tagged in their specs. The six entries are closed, or annotated with what stayed short and
why.

## Context

- **The six entries (backlog on 2026-11-10):**

  | Entry | Cases | Clients |
  |---|---|---|
  | `2026-10-27-architect-reverser-plan-0045-c2-vellev-by-a-blood-moor.md` | C2: a `spike1` creation (`quillrat1`, Blood Moor) under the skills logger; `skills.py check` | 1 |
  | `2026-11-04-architect-reverser+spec-writer-0054-p12-missile-own-cell-bit0-vs-floor.md` | P12: a do-function-1, CollideType-3 missile across a logged bit-0-only cell, and a control on a free cell (**verdict lane, Tier A**) | 1 |
  | `2026-11-04-reverser-reverser+spec-writer-plan-0060-cross-check-contradictions.md` | H3 (`mp1` and four more rows to the hireling with the flag), H2 (two potions of different tiers below the meter's maximum), B8 (a death with a belt holding boxes above 3, with and without inventory room) | 1 |
  | `2026-11-04-architect-reverser-a68-review-exp-state-kill-in-play.md` | a converted monster's kill (Conversion) and a kill of a converted monster, with the exp-mask states and the `0x800` list's owner at `XK0` | 1 |
  | `2026-11-03-architect-reverser-plan-0058-p1-party-list-writers-gate-flag.md` (live part; the static part is plan 0063's) | a partied credited player far from the victim with the other member near; a dead killer with a living member in range; a player killing a player | 2 |
  | `2026-10-20-architect-reverser-plan-0044-p2-review-agent-stageable-shortfalls.md` | MP16, MP18, MP20, MP21, MP25's offensive auras, MP27, MP28 (b) and (c), MP30, MP31, MP32, the open-wounds pair; the shield flag for `combat.py --no-shield` | 2 |

- **Staged already** (plan 0051 Phase 1a/1b): MP18, MP25 offensive, MP30, the open-wounds pair (recipes, pairs,
  loggers, checks); MP31 and MP32 have predictions ([multiplayer/0002](../findings/multiplayer/0002-trade-and-party-gold.md) § 3)
  but no logger lines.
- **Not taken:** the owner-play entries (0044 MP12–MP14 and MP17; the 0052 Uber forced cases). They stay the owner's.
  The scol corpse entry's parts 5 and 6 have no case to run.
- **Runner:** sessions go through `tools/harness_runner.py`. If plan 0063 Phase 2b has landed, its stage gate applies.
  Several cases per process follow ADR-0028 (sharing opt-in, with a stated reason).
- **Slots:** Phase 1 holds one slot, Phase 2 both. Phase 2 needs the port-4000 precondition re-read before its first
  session ([multiplayer/0001 § 5](../findings/multiplayer/0001-cases.md)) and `tools/ufwcheck.sh` around each session.

## Phases

### Phase 0 — Staging
- **Owner skill:** reverser (no slot, no Ghidra unless a logger point needs one read)
- **What:** for every case above, a recipe, a pair or session entry, a logger and a check, each with its prediction
  written before any run. Specifically:
  - logger lines for MP31 and MP32;
  - an `exp`-mask state read at `XK0` in `tools/gdb/player.py`;
  - a logged shield flag on the defender for `combat.py`;
  - the bit-0-only cell pick for P12 (from a kept collision grid), plus its control;
  - the H2 pair of tiers;
  - the B8 belt;
  - a route for C2 that crosses Blood Moor with the skills logger (rev 5).

  Cases whose staging needs more than a logger line (MP16, MP20, MP21, MP27, MP28 (b), (c)) are staged or named as
  shortfalls here, with the reason.
- **Outputs:** `tools/d2s_recipes/`, `tools/mp_saves.py`, `tools/gdb/`, the checks and their no-game tests; a staging
  table in this plan's log.
- **Done when:** every case is staged with a written prediction, or named a shortfall with its reason; `mp_saves.py
  check` and the no-game tests pass; gdb parses and arms each new logger against the pinned image. Review: Tier B.

### Phase 1 — Single-client batch
- **Owner skill:** reverser (harness, slot 1)
- **What:** run C2, H3, H2, B8 and the two exp-state kills as one batch, sharing processes where ADR-0028 allows.
  Run P12 as its own verdict session.
- **Outputs:** run records `run:<date>-sweep8-single` and `run:<date>-sweep8-p12`; addenda in skills/0002, items/0013
  to items/0016 (as each case belongs), player/0002, path/0007.
- **Done when:** each case has a kept log and a check, with 0 mismatches or a named contradiction routed to the spec.
  P12 states which reading holds, either way. The four entries are closed or annotated. Review: Tier B for the batch,
  **Tier A for P12** (ADR-0030).

### Phase 2 — Two-client batch
- **Owner skill:** reverser (harness, slots 1 and 2)
- **What:** after the port-4000 re-read, run the staged two-client cases (0044's list and 0058's three), with
  `mp_check.py` and each case's own check.
- **Outputs:** `run:<date>-sweep8-two-clients`; addenda in multiplayer/0001 § 6 (the raises), multiplayer/0002,
  player/0002, combat and stats findings as each case belongs.
- **Done when:** each staged case has a kept log and a check (0 mismatches or a named contradiction). Each unstaged
  case is named with its reason. Both entries are closed or annotated. Review: Tier B.

### Phase 3 — Re-tag
- **Owner skill:** spec-writer
- **What:** carry the raises and contradictions into the specs:
  - skills/missiles: C2, and D3 for P12;
  - items/use and items/inventory: H2, H3, B8;
  - player/party: the exp-state credit, the 0058 live cases;
  - combat/formulas: open wounds on a player, the shield flag;
  - quests/progression: MP30;
  - items/economy: MP32;
  - the multiplayer-tagged statements of the other specs.

  Remove the *Open questions* entries the runs answered.
- **Outputs:** the specs named, their wiki pages where a restated sentence changed.
- **Done when:** every raise and contradiction of Phases 1 and 2 is applied or ruled out with a reason, and
  `python3 -I tools/gate.py --full` is green. Review: Tier A, and the review closes the plan.

## Open questions

- Whether to run Phase 2 at all, or close the two-client entries as shortfalls. Phase 2 holds both slots for an
  estimated 15–20 sessions, and most of its cases re-tag `[I]` statements no other spec depends on. The architect
  recommends running Phase 2 only if plan 0067 (trade) is approved, so the two-client set-up is paid once for both.
- Whether P12's control needs a forced cell (ADR-0013) if no stock bit-0-only cell lies on a missile path. Ruled at
  Phase 0's review.

## Implementation log

_(lanes append dated entries as phases land: what was found, the confidence reached, surprises)_
