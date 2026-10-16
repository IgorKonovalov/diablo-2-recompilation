# 0044 — Multiplayer branches: the two-client cases of the reviewed specs

> **Status:** proposed (needs [ADR-0008](../adrs/0008-two-client-harness.md) accepted by the owner, with the slot reading below)
> **Created:** 2026-10-16
> **Owner skill(s):** reverser, spec-writer
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0003-runtime-experiments, 0004-boundary-oracles-in-reproduction, 0008-two-client-harness, 0011-harness-slots, 0014-scope-game-simulation

## TL;DR

**Question:** do the multiplayer branches that the reviewed specs read from the code behave as read, when a second
real player is in the game? When it is done, the branches below are reproduced in two-client games, or named with the
reason they could not be reached, and the specs are re-tagged. No new subsystem.

## Context

- **What waits on two clients.** Plan 0038 files 14 rows as d-2c, plus four partial halves: items/tc (NoDrop party
  scaling with real players), items/vendors (the stale flag when a player leaves, stock shared between players),
  items/quest-drops (the per-player loops, the party record, the forge's `n` > 1), player/creation (party experience
  share), hirelings, items/sockets-runewords (the trade part). The specs' open questions add: items/quality
  (multiplayer magic find), monsters/spawn (multiplayer not logged), objects (multiplayer not logged), monsters/stats
  (the player-count terms with real players), and combat/0001 § 12 (player against player and hostile states,
  ADR-0014 § Multiplayer). Plans 0040–0043, if they run first, add their own party cases.
- **The harness exists.** Plan 0011 ran two copies in a local TCP/IP game (run:2026-10-12-tc-party): the host's
  process holds the server, so gdb on the host sees every server event.
- **The gate.** ADR-0008 is `proposed`; the owner's open point is network exposure (the hosting game listens on TCP
  port 4000 on all interfaces). ADR-0011 places the host on slot 0 and the joiner on slot 1, but slot 0 is now the
  owner's. This plan asks for the host (gdb attached) and the joiner on **two non-zero slots**, the two harness
  lanes' slots (for example 1 and 2). That reading is part of the owner's decision on ADR-0008.
- **Slots.** A two-client session holds **both harness lanes** at once: no other harness phase runs during it.

## Phases

### Phase 1 — The case list
- **Owner skill:** reverser
- **What:** re-read each multiplayer branch named in *Context* (the code is already read; this is a check, not a new
  reading), and write the case list: for each branch, the server entry point, the condition two clients must create
  (party or not, positions, who kills, who leaves), the logger that already sees it, and the expected outputs.
- **Outputs:** `docs/findings/multiplayer/0001-cases.md` (or a section in each owning finding, as the reverser
  chooses at the start); a `d2pilot.py` mode that drives the joiner's character (follow, party, leave, trade), on
  top of plan 0011's `two-*.steps` files.
- **Done when:** every d-2c row and every multiplayer open question listed in *Context* has a case or a reason it can't
  be staged (for example a third player); the joiner's driver is tested on a non-zero slot; the architect's review
  rules the case list.

### Phase 2 — Two-client runs
- **Owner skill:** reverser (agent-driven; **two slots together**, both harness lanes)
- **What:** run the cases, with the existing loggers on the host (`tc-party.gdb`, `vendors.gdb`, `quests.gdb`,
  `player.gdb`, `combat.gdb` and the others the case list names) and their checkers.
- **Done when:** `run:YYYY-MM-DD-two-clients` reproduces with **0 mismatches** under each checker, and every case of the
  case list is reached or named as a shortfall; at least: 100 party kills with drops, 30 vendor stock events with two
  players, 20 party experience shares, 10 quest events with both players present, 200 player-against-player attack
  events if Phase 1 stages hostility. The joiner's saves are set aside and restored per slot, as for any run.

### Phase 3 — Re-tag
- **Owner skill:** spec-writer
- **What:** re-tag the specs whose multiplayer statements the run raises; narrow their open questions.
- **Done when:** each raised statement cites the run; the gate is green; the architect's review passes.

## Open questions

- **More than two players.** Two clients are the most the memory budget allows; party sizes 3–8 stay `[I]` except where
  `/players` stands in for them.
- **Network exposure.** If the owner accepts ADR-0008 only with a firewall rule or a loopback-only bind, Phase 1 states
  how the sessions meet it.

## Implementation log

_(lanes append dated entries as phases land: what was found, the confidence reached, surprises)_

- **2026-10-16 — Drafted (architect, `lane/plans39`).** Status `proposed`; gated on ADR-0008.
