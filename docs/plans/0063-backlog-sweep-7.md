# 0063 — Backlog sweep 7: the slot-free entries left after plans 0052 to 0060

> **Status:** approved (2026-11-10, by the owner; not started: the owner starts it)
> **Created:** 2026-11-10
> **Owner skill(s):** archivist, reverser, spec-writer
> **Related ADRs:** 0018-backlog-one-file-per-entry, 0019-backlog-closed-entries-archive, 0023-review-tiers-and-gate-first-fixes, 0024-lane-check-touched-documents-and-routing, 0027-archivist-reader-lanes-tier-a, 0031-constants-of-the-code-image

## TL;DR

**Question:** which open backlog entries can be closed with no harness slot and no game, and what do they change in
the specs? Ten entries can (triage 2026-11-10). When this plan is done, each of them is closed, or annotated with
its static part done and only a live remainder left open. The findings carry the new readings, `re/symbols.csv` names
what they confirm, and the specs carry what the readings and raises change. Gate rule E14 runs as an error. **No
phase needs a slot.** Phases 1, 2a and 2b may run in parallel, which keeps within the memory budget: two static
lanes with Ghidra and one archivist lane without it.

## Context

- **The backlog on 2026-11-10:** 21 open entries after the triage closed four of them (commits `efe2b49d`, `8307f252`:
  the us 21 version-71 piece and plan 0045's P1b cases done, the Diablo owner pair not played, the grid-tie hold-out
  dropped by the owner on 2026-11-04).
- **Why now.** No lane is running. Plans 0052, 0054, 0055 and 0060 closed on 2026-11-04. 0038, 0059 v2 and 0061 are
  approved but held by the owner.
- **What this sweep does not take.** These entries need a game and stay open, unchanged: C2 `spike1`
  (`2026-10-27-architect-reverser-plan-0045-c2-vellev-by-a-blood-moor.md`), P12 missile bit 0
  (`2026-11-04-architect-reverser+spec-writer-0054-p12-missile-own-cell-bit0-vs-floor.md`), plan 0060's three live
  cases (`2026-11-04-reverser-reverser+spec-writer-plan-0060-cross-check-contradictions.md`), the exp-state kill
  (`2026-11-04-architect-reverser-a68-review-exp-state-kill-in-play.md`), the 0044 two-client cases
  (`2026-10-20-architect-reverser-plan-0044-p2-review-agent-stageable-shortfalls.md`) and scol parts 5 and 6
  (`2026-11-04-architect-reverser-scol-review-corpse-remainders.md`). Part 5 lost its carrier when the grid-tie revision
  of `tools/path.py` was dropped. The owner entries stay as the owner left them: `patch_d2.mpq` (parked), the 0044
  owner play, the 0052 Uber forced cases.
- **Gate on 2026-11-10:** fast tier GREEN, 0 errors, 79 warnings; E14 is in `DEMOTED` (`tools/gate.py:120`).

## Phases

### Phase 1 — The act-clock tables
- **Owner skill:** archivist (no slot, no Ghidra)
- **What:** document `g_ActClockTable0..2` (`0x007443F0`, `0x00744438`, `0x00744480`; six rows of three dwords each:
  start, type, colour word) under ADR-0031. Use a rule the survey checks where one exists, else a short listed table
  with the address and the reader (`ActClockTick`, [frame/0001 § 3.1](../findings/frame/0001-tick-and-messages.md#31-actsclockpass-the-act-light-clock)).
- **Entry:** `2026-11-04-spec-writer-archivist-act-clock-tables.md`.
- **Outputs:** the table's home under `docs/formats/` or `docs/tables/` (the lane picks one and says why), with the
  survey or the listed values ADR-0031 allows.
- **Done when:** the three tables are documented with address, row layout and reader. Every value is listed, or
  covered by a rule that the full-tier survey checks. The entry is annotated with the link that Phase 3 gives
  sim/frame G1b. Review: Tier A if the lane writes a statement taken from a finding (ADR-0027), else Tier B.

### Phase 2a — Static readings
- **Owner skill:** reverser (static, Ghidra lane A; no slot)
- **What:** four readings, each written into the finding its entry names, with symbols for what is confirmed.
  1. **h6f** (`2026-10-27-architect-reverser-h6f-review-client-hire-line-and-merc-create.md`): the client function that
     drops the hire line, its quest-word and level reads compared with `HIRE_Hire`'s gates (0x00577115–0x0057717C) in
     every state; and what fills the list at `+0x60` that `sub_005394A0_PlayerPlaceInAct` walks before
     `MERC_Create` at 0x00539637, and when. Give the ruling inputs for hirelings rows 17, 18, 21 and 29.
  2. **0058 party** (`2026-11-03-architect-reverser-plan-0058-p1-party-list-writers-gate-flag.md`, static part): the
     writers of the party list at game `+0x1D2C` (what makes two players one party, and whether nine fit), the caller
     at 0x005408CB, and bit 26 of unit `+0xC4` at its nine writers.
  3. **Act-clock scale** (`2026-11-04-spec-writer-reverser-act-clock-scale.md`): the server's `k` (`+0x28`) and flag
     (`+0x30`) set at act load (`0x0061C240`, `0x0061C180`), so how often 0x53 is sent, and whether the refresh can
     change a usable item and run `AuraSelect`.
  4. **Facing step** (`2026-11-04-spec-writer-reverser-path-facing-step-consumer.md`): the code that applies path
     `+0x66` and steps `+0x64` toward `+0x65`, other writers and readers of the facing, and the two words of
     `PathStep`'s `PathAimNextPoint` call. Start from the entry's leads (0x00648640 and its callers, 0x0064887B,
     0x00648882, 0x006508E6), which are leads only.
- **Outputs:** [hirelings/0001](../findings/hirelings/0001-hirelings.md),
  [player/0002](../findings/player/0002-party.md), [frame/0001](../findings/frame/0001-tick-and-messages.md),
  [path/0001](../findings/path/0001-pathplan-register.md) (or a new path finding), `re/symbols.csv`.
- **Done when:** each reading answers every question its entry asks, at `[I]` or better with anchors, or names the
  step it could not follow and why. Every function it relies on is named in `re/symbols.csv`. Each entry is closed, or
  annotated with its live remainder (the 0058 entry keeps its optional two-client cases). Spec changes are routed to
  Phase 3 in the lane's handoff. Review: Tier B (`reverser-static`).

### Phase 2b — Static model, data and tooling
- **Owner skill:** reverser (static, Ghidra lane B for item 1 only; no slot)
- **What:**
  1. **h5d waypoint mode** (`2026-10-27-architect-reverser-h5d-objects-py-waypoint-mode-after-arrival.md`): read what
     object event 1 does to a waypoint and whether it draws on a unit seed (part a). Model or log the mode change in
     `tools/objects.py` so that `tools/collision.py check` on the kept h5d log reports 0 operate mismatches (part b).
     Route any contradicted quests/travel or objects claim to Phase 3 (part c).
  2. **Inventory live raise** (`2026-11-04-spec-writer-reverser-items-0014-0016-wording-found-in-plan-0060.md`):
     recompute the live separation counts per statement (start offset when the room holds the cell, item bit, walk
     mask, ring order through ring 3) and the per-spot independence tally (90 of 118 searches in six chain spots, 28
     `DropCreateItem` drops at 24 positions). Use the kept `check-*.txt`, the three logs and `tools/inventory_check.py`
     controls. Write them as a finding statement with the second source named, raising what holds.
  3. **Runner stage gate** (`2026-11-03-architect-reverser-plan-0056-p4-stage-check-in-the-library.md`): move the
     stage check from `tools/ai_sessions.py` into `tools/harness_runner.py` as a case gate the runner must supply (a
     stage-check callback, or an explicit no-sharing), with no-game tests, and say so in tooling.md § The runner library.
  4. **E14 rows** (`2026-10-27-archivist-reverser-e14-table-rows-with-an-extra-cell-in.md`): move or drop the fifth
     cell in the six findings rows (items/0002, 0003, 0004 ×2, 0006; rng/0002), so that `tools/gate.py` reports no E14
     with E14 removed from `DEMOTED` (the lane checks this locally; the raise itself is the architect's, at review).
- **Outputs:** [objects/0001](../findings/objects/0001-object-population.md) or
  [quests/0002](../findings/quests/0002-travel.md), `tools/objects.py`, an items finding (0016 or a new one),
  `tools/harness_runner.py` and its tests, `.claude/skills/reverser/references/tooling.md`, the six findings rows.
- **Done when:** the h5d check is clean on the kept log, or the remaining mismatch is named with its cause. The
  inventory statements carry live counts and a named second source, at the tag those support. `batch`/`next_case`
  refuse to switch without a stage gate, and the tests pass. The gate reports 0 E14 with the demotion lifted. All four
  entries are closed. Review: Tier B (`reverser-static`). Item 2 is a raise, so the check reads it as one.

### Phase 3 — Spec updates
- **Owner skill:** spec-writer
- **What:** carry into the specs what Phases 1 to 2b changed, and the two spec-writer remainders already released:
  - **S3b (d)** (`2026-10-16-reverser-spec-writer-plan-0038-s3b-corrections-and-additions.md`): player/creation D1,
    a monster's entry raised also at or above the maximum, the maximum is Skills `maxlvl` (20 when the cell is ≤ 0),
    unreachable at creation on stock data.
  - **H1a (k)** (`2026-10-27-reverser-spec-writer-h1a-save-d2s-player-creation-raises.md`): data/calc L417 raised
    `[C]` for the hovered potions (gate `+0xB4` = 0 at 0x0048638B); rng/seeds L362, the caller 0x00569F4B run-confirmed,
    the other four `[I]`.
  - From Phase 1: sim/frame G1b links the act-clock tables.
  - From Phase 2a/2b, as routed: hirelings, player/party, sim/frame § G and § J, path/overview § H, items/inventory
    § J, and quests/travel or objects if part c routes anything.
- **Outputs:** the specs named above and their wiki pages, where a statement a wiki page restates has changed.
- **Done when:** each routed item is applied or ruled out with a reason. Every *Open questions* entry the readings
  answered is removed or rewritten. The two spec-writer entries are closed. `python3 -I tools/gate.py --full` is
  green. Review: Tier A, and the review closes the plan.

## Open questions

- Whether Phase 2a's h6f reading moves hirelings row 29 to d-2c, or makes it a harness piece. If it is a harness
  piece, it goes to a new backlog entry, not to this plan.
- Whether bit 26 of `+0xC4` (Phase 2a item 2) changes any `[C]` in player/party. The plan 0058 log ruled that both
  `[C]`s stand without it. A contradiction goes to the Phase 3 review.

## Implementation log

_(lanes append dated entries as phases land: what was found, the confidence reached, surprises)_

### 2026-11-10 — Phase 1 (lane/n63a, archivist)

- Done: [docs/tables/ActClockTables.md](../tables/ActClockTables.md) documents `g_ActClockTable0..2` (`0x007443F0`, `0x00744438`, `0x00744480`): contiguous, six rows of three dwords (start, type, colour word), readers, and the 18 rows. Home: `docs/tables/`, beside PathDirTables and PathTypes, the other image-constant docs; `docs/formats/` describes file formats and none is involved. Values read by a `-I` reader from the pinned image (no Ghidra, no slot). ADR-0031: table 2's `start` is the rule `60 * ((p + 5) mod 6)` (survey-checked); the other 48 values have no rule known and are listed (type and colour columns, tables 0 and 1 starts).
- Survey: `tools/actclock_survey.py`, registered in `tools/gate.py` as `actclock`, baseline `tools/gate/baselines/actclock.txt`; it checks the rule and compares the doc's 18 rows with the image. Linked from `docs/tables/README.md`.
- Entry `2026-11-04-spec-writer-archivist-act-clock-tables` annotated, not closed. Handoff to Phase 3: sim/frame G1b links `../../tables/ActClockTables.md`; the colour word's channel order and the meaning of `type` stay `[L]` in the doc (frame/0001 does not settle them).
- Review tier: Tier A (ADR-0027). The doc restates `[I]` statements from frame/0001 § 3.1 (reader roles, the colour blend at 0x0061BCE0, the `type == 2` test).

### 2026-11-10 — Phase 1 review (architect, Tier A, ADR-0027): accept with fixes

- Rules tried (ADR-0031): table 1's `type` column equals table 0's in all six rows, so it is now the rule `T1[p].type = T0[p].type`, survey key `t1_type_rule_mismatches`, baseline updated; 42 values listed, 12 by two rules (doc header, README, entry annotation). Table 2's colour words (`0xF31E00`, rows 1 and 4 `0xF41E00`) are a description by cases and stay listed.
- The readers bullet now states the step's table choice whole: with `f` = 0 both the compare and the new values read table 0; with `f` set the compare reads table 1 in act index 3, table 2 otherwise, and the new values come from table 2 (frame/0001 § 3.1's `[C]` block).
- The colour word's top byte 0 and `type` 0 to 3 are data the survey checks: `[C]`, with "three-byte colour" `[I]` from the 0x0061BCE0 blend.
- The two `[L]` (channel order, `type`'s meaning to the client) moved to a new `## Open questions`: a table doc may carry `[L]` in its body (gate E5 binds specs only), but these are unknowns, not leads.
- Survey and gate registration checked: `actclock` runs in `--full`'s default set (not opt-in), reads the image only at the pinned sha256, and fails on any rule or doc mismatch.
