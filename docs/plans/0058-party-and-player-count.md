# 0058 — Party and player count: the experience split, the share radius and every player-count effect, in one page

> **Status:** draft (architect, `lane/plans57`, 2026-10-30), for the owner's approval
> **Created:** 2026-10-30
> **Owner skill(s):** reverser (phase 1), spec-writer (phases 2, 3)
> **Related ADRs:** 0008-two-client-harness, 0015-emulated-reproduction, 0017-scope-quests-travel-economy

## TL;DR

How is a kill's experience split among players, what bounds who shares, and what does the player count change across
the game? **Most of it is already specified**, so this plan is small: the split is
[player/creation § J4](../specs/player/creation.md#j-other-level-and-experience-changes) (`XP_PartyShare`: alive, same
level, distance² ≤ 6400, at most 8; `total = exp + ((n − 1) × exp × 89) ÷ 256`; the f32 quotient and the unrounded
member product; `[C]` for n = 2 by run:2026-10-20-two-clients), the level-difference penalty is § G3 (`[C]`), and the
player-count effects are spread over five specs. When it is done, the split is `[C]` for n = 3 to 8 by emulation, the
hireling's and the minion's credit are stated, and `docs/specs/player/party.md` (row `player/party`) composes every
party and player-count rule with links to the owning sections.

## Context

- **Where the pieces live now:** the split and the radius, player/creation J4 (n = 2 `[C]`; n ≥ 3 the same code,
  unrun); the penalty and the ratio, G3–G4; the death loss and the corpse's 75 %, J3 (`[I]`, unrun); the monster's hit
  points and experience at **+50 % per player beyond the first**, frozen at creation, monsters/stats § C1 (`[C]`);
  NoDrop and the drop count by players, items/tc; the crushing-blow divisor and `MonAttackStats` damage by the
  monster's stat 100, combat/README (`[C]` and `[I]`); the gold pickup's `PartyGoldShare`, items/economy G4 (`[I]`);
  quest credit to the party, quests/progression (e.g. the Ancients' e8 row); the case list,
  [multiplayer/0001](../findings/multiplayer/0001-cases.md) MP16.
- **The gap:** no page states these together; n ≥ 3 is unrun (the two harness slots give two clients, so a third
  player needs slot 0, the owner's); G6's mercenary cap and the minion credit of G0 are `[I]`; J4's record branch counts
  are one off (265 against 264 single inputs, already filed to the reverser).
- **Dependencies:** none open (player/creation, monsters/stats, items/tc, combat, items/economy are reviewed).

## Phases

### Phase 1 — The n ≥ 3 split and the credit edges, from the code and by emulation
- **Owner skill:** reverser (static; one headless Ghidra `-Xmx3G` at most; emulation under ADR-0015; no slot)
- **What:** emulate `XP_PartyShare` (`0x0057E6C0`) and `sub_0057E5A0_PartyXpCollect` (`0x0057E5A0`) over generated
  member sets for n = 1 to 8 (levels, distances at and around 6400, dead and other-level members, a ninth member) and
  check `tools/player.py`'s model against every output; read the mercenary's and the minion's credit (G0, G6) and the
  party definition the collector tests; close the 265/264 branch count entry if it is this code.
- **Outputs:** a section in [player/0001](../findings/player/0001-creation.md) (or `docs/findings/player/0002-party.md`
  if it passes 150 lines); `tools/player.py` updated; the emulation run's record in `docs/findings/player/experiments.md`.
- **Done when:** the emulated outputs match the model for every generated set (count stated), the member cap and the
  distance bound's edge are stated with the deciding instruction, and G0/G6 are `[I]` or better with anchors.

### Phase 2 — The page
- **Owner skill:** spec-writer (Opus)
- **What:** `docs/specs/player/party.md`: who shares (J4), how much (J4, G3–G4), what the player count changes at
  creation and at a kill (monsters/stats C, items/tc, combat, items/economy G4, quests), each rule restated with its tag
  and a link; Phase 1's results raise J4 for n ≥ 3 in player/creation itself, and the page links it.
- **Outputs:** `docs/specs/player/party.md`; player/creation J4 updated; `docs/specs/player/README.md`; research-map
  row `player/party`.
- **Done when:** every player-count reader the five specs name is listed with its input (the monster's frozen stat 100
  or the current count), each line links its owning section, and the gate is green.

### Phase 3 — Wiki
- **Owner skill:** spec-writer (wiki; Sonnet)
- **What:** a section of `docs/wiki/characters.md` (or its own page), no claims of its own.
- **Done when:** the section links the page and the wiki index is current.

## Resources and limits

- No harness slot in the recommended form. Ghidra at most one session, inside the two-Ghidra limit. P1 fits a static
  lane slot between 0052's and 0055's batches, or the archivist-free spec-writer queue for P2.
- **Estimate:** P1 one short reverser run; P2 one spec-writer run; P3 one short run.

## Owner questions (recommendations)

1. **A plan at all, or a section of the quirks index?** *Recommendation: this small plan*, because a reimplementer
   looks for "player count" in one place and the n ≥ 3 split is a real `[I]`.
2. **n ≥ 3 by emulation or by play?** *Recommendation: emulation* (ADR-0015 gives `[C]` for a function body over its
   inputs). A three-client run needs slot 0 and the owner; keep it an optional owner session.
3. **Row or section?** *Recommendation: its own file and row `player/party`* under Creation paths, since it is read by
   six specs.
4. **The death loss (J3) and the experience cap:** *Recommendation: leave them to the companion `[I]` sweep* (queued
   after 0055·P2a), which has the harness slots; name them there as targets.

## Open questions

- Whether `/players` changed mid-game re-reads any party rule (monsters keep their creation count; the drop count and
  the gold share are read at the event): stated from the code in Phase 1, run only if the companion sweep takes it.

## Implementation log

_(lanes append dated entries as phases land: what was found, the confidence reached, surprises)_

- **2026-10-30 — Drafted (architect, `lane/plans57`).** Status `draft`; rank 2. The survey found the split already
  specified (player/creation J4, `[C]` for n = 2), so the plan covers only n ≥ 3, the credit edges and the composed
  page; four owner questions.
