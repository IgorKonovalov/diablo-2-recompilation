# 0011 — Two-client harness: the party NoDrop case and a champion kill

> **Status:** approved (2026-10-11)
> **Created:** 2026-10-11
> **Owner skill(s):** reverser
> **Related ADRs:** 0003-runtime-experiments, 0004-boundary-oracles-in-reproduction

## TL;DR

**Question:** does 1.14d count a partied player toward NoDrop when they are in the killer's level but far away, as
the code read says (level-id equality, no distance test), and not "within two screens" as both community sources say?
And does a champion take its drop from `TreasureClass2`? These are the last two `[I]` claims standing between
`items/tc` and `reviewed`. Answering the first needs a second game client, which the harness (ADR-0003) cannot run
yet. When this plan is done, the harness can run two clients in one multiplayer game under gdb, the committed kill
tools replace the scratch scripts of plan 0004, and items/0001's party and champion claims are `[C]` or corrected.

## Context

- Plan 0004 Phase 2 was accepted with fixes on 2026-10-11 with the party case blocked (one client) and the champion
  branch left `[I]` (no champion among 328 calls). Both are backlog entries; the party one blocks `items/tc` from
  `reviewed`.
- The claims: items/0001 §6, `sub_005405A0_PartyForEachInLevel` `0x005405A0` (party members counted by room → level
  id, no distance test), `contradicted` against `src:pd-item-generation` and `src:hrus-mf-guide` in Phase 1b; and the
  `MONSTER_DropItems` `0x005A6600` column choice for type flag `0x04` (`Act 1 Champ A`, `Picks = -2`).
- A multiplayer game also shows the values of `game+0x6A` other than 3 (items/0001 open question), and the
  `party ≥ 2` branch of the NoDrop formula, still `[I]`.
- Later users of the same harness: `monsters/stats` (player-count scaling), `items/quest-drops`.
- Two harness defects are folded in, since two clients make both worse: the `d2run.py` driver that kills a later
  run's game, and the kill scripts left in a session scratchpad (both in the backlog).

## Phases

### Phase 1 — Harness: kill tools and a second client
- **Owner skill:** reverser
- **What:** commit the plan 0004 kill tools, fix the driver, and get two clients into one game with gdb on the side
  that runs the server game.
- **Outputs:** `tools/` scripts (hunt loop, auto-relaunch, waypoint finder, pointer/screenshot recorder) with
  `--help`; the `d2run.py` fix (driver exits when its game is gone, a pidfile refuses or kills a stale driver);
  a two-client recipe in `.claude/skills/reverser/references/tooling.md` (game type, one or two prefixes, one or two
  displays, how the second client is driven, which process gdb attaches to); a `run:YYYY-MM-DD-two-clients` record in
  `docs/findings/items/experiments.md`.
- **Done when:** the record shows two characters in one game (both visible in the party screen), invited into one
  party, with `tc-drops.gdb` logging a kill that the existing `tools/tc.py replay` reproduces, and a TCR line whose
  `game+0x6A` differs from single player. If the binary refuses two instances, or wine cannot host both, the record
  says what was tried and the architect decides the next step (two machines, a second prefix and display, or
  leaving the claim `[I]`). The scratch scripts are no longer referenced from experiments.md as uncommitted.
  If the method departs from ADR-0003 (a second process, a network game), the record says how, for the architect
  to judge whether an ADR is needed.

### Phase 2 — Party and champion runs
- **Owner skill:** reverser (a human may play either client, as in plan 0004)
- **What:** record the kills that settle the two claims.
- **Outputs:** `run:YYYY-MM-DD-tc-party` in `docs/findings/items/experiments.md`, promoted or corrected tags in
  items/0001, the plan 0004 backlog entries struck through.
- **Done when:** `tools/tc.py replay` reproduces every call of the run, and the run includes:
  - (a) a kill with the partied second player **in the killer's level but far away** (well beyond two screens; give
    the distance in tiles or screens from the logged positions), with `party = 2` at `TC_ResolveDrops` and `NoDrop'`
    matching the x87 model;
  - (b) the same with the second player **unpartied**, and with it partied but **in another level**, each giving
    `party = 1`;
  - (c) at least one **champion** kill (type flag `0x04`), whose base TC is `monstats` `TreasureClass2` (checked by the
    replay's base-TC check), in Nightmare if reachable so the upgrade walk runs on group 18 too;
  - the FPU control word at NDIN in the multiplayer game.
  If (a) shows `party = 1`, the finding is corrected and the `contradicted` verdict becomes `held`, not the other way
  round by assumption. Promoted claims cite the run; the classic branch and Hell stay `[I]`.

## Open questions

- Which side runs `TC_ResolveDrops` in a TCP/IP game: only the host's process? Phase 1 confirms it before logging.
- Does `/players` apply in a multiplayer game? The finding says "some game types"; the run records it.

## Implementation log

_(lanes append dated entries as phases land)_

- **2026-10-11 — Drafted (architect).** From the plan 0004 Phase 2 review (party fallback accepted, champion left
  `[I]`) and the backlog entries for the driver bug and the kill scripts.
- **2026-10-11 — Approved (human).** No changes to the draft.
- **2026-10-11 — d2run.py driver fix done early (reverser, during plan 0008 Phase 2).** The driver child now writes
  `workspace/runtime/d2run-driver.pid`, polls the game during `--after` and exits **without** `wineserver -k` once
  the game is gone; a new `d2run.py` kills a live stale driver named in the pidfile first. Seen working in
  run:2026-10-11-drlg-roomk (sessions ended by hand with `wineserver -k`: no orphan driver, pidfile removed). The
  rest of Phase 1 (kill tools, second client) is untouched.
