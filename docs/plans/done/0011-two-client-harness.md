# 0011 — Two-client harness: the party NoDrop case and a champion kill

> **Status:** done (2026-10-12)
> **Created:** 2026-10-11
> **Owner skill(s):** reverser
> **Related ADRs:** 0003-runtime-experiments, 0004-boundary-oracles-in-reproduction, 0008-two-client-harness (proposed)

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
- **2026-10-12 — Phase 1 done (reverser).** [run:2026-10-12-two-clients](../../findings/items/experiments.md#run2026-10-12-two-clients):
  one wine session refuses a second copy ("Only one copy of Diablo II may run at a time", `FindWindowA` at
  `0x004F5610`), so the joiner runs in a second prefix `workspace/wineprefix2` on display `:8` and the two meet in a
  TCP/IP game over `127.0.0.1`; gdb is on the host, which runs the server game (open question 1 answered: every
  resolver call is in the host's process). Both characters in the party screen and in one party; `tc-party.gdb`
  (= `tc-drops.gdb` + player/party/position lines) logged 31 calls, 31 reproduced by `tools/tc.py replay`, every
  `TCR` with `g6a=2` (single player: 3). Kill tools committed: `tools/d2hunt.py` gained `relaunch` (run once, 2
  attempts); `tools/d2run.py` gained `--prefix` and a pidfile per display. Recipe in tooling.md § *Two clients in one
  game*. **Departures from ADR-0003** for the architect: a second (undebugged) process, a second prefix and display, a
  TCP/IP game (TCP 4000 listening on all interfaces while hosting), and a tool-built save placed by hand in the new
  prefix's saves directory (outside `saves.py`).
- **2026-10-12 — Phase 2 partly done (reverser, owner played the host in session 2).**
  [run:2026-10-12-tc-party](../../findings/items/experiments.md#run2026-10-12-tc-party): 175 calls, 175 reproduced.
  (a) met: 44 calls with the partied joiner in the killer's level at 26–375 subtiles (37 beyond two screens), all
  `party = 2`, `NoDrop'` matching the x87 model (`n = 2`); the `contradicted` verdict stands and items/0001's party
  count and `party ≥ 2` NoDrop' are `[C]`. (b) met: unpartied in the same level 4 calls, partied in another level 84
  calls, all `party = 1`. FPU control word in the TCP/IP host `0x027F` (68 `NDIN` lines). (c) **not met**: no champion
  in 175 calls; a Nightmare session with the owner's `LightSorc` (tool-built, loads fine) ran scripted alone (the
  level-50 joiner has no Nightmare access) and the Sorceress died after 9 calls. Case (c) needs an owner-played
  session. `/players` in a TCP/IP game not tested. Also fixed: `tools/tc.py replay` attached a `DROP` with no
  resolver call (base TC 0) to the next chest call; a `DROP` now belongs to a call only with the same source.
- **2026-10-12 — Phase 1 and Phase 2 (partial) reviewed (architect): accept.** Checked: `tools/tc.py replay` on
  `tc-party-1/2/3.log` gives 31/31, 166/166, 9/9, and the 328 calls of plan 0004 (`tc-run{2,4,5,6,9,10,13,16,17,18,19}`)
  still reproduce after the TC-0 pairing fix; the party check is computed from the logged player positions, levels
  and party list (game state, no seed from the log); r2 at `0x004F5623` (`FindWindowA`, the single-instance check);
  gate green. Case (a): 44 partied calls in the killer's level, 37 beyond two screens, all `party = 2` and `NoDrop'`
  matching; the party count (level-id test, no distance test) is `[C]` and the community "two screens" claim stays
  contradicted, now by run. Case (b) and the FPU control word (`0x027F`, TCP/IP host) met. The method departs from
  ADR-0003 (second undebugged process, second prefix and display, a TCP/IP game listening on TCP 4000 on all
  interfaces, a tool-built joiner save outside `saves.py`): recorded as [ADR-0008](../../adrs/0008-two-client-harness.md),
  **proposed** until the owner accepts the network exposure. Case (c), a champion kill, is open: none in 206 calls;
  the next session is owner-played, `LightSorc` as host in Nightmare (it loads; the joiner needs a Nightmare-capable
  character). `items/tc` stays short of `reviewed` until (c) lands.
- **2026-10-12 — Phase 2 case (c) met (reverser, owner played single player).**
  [run:2026-10-12-tc-champion](../../findings/items/experiments.md#run2026-10-12-tc-champion): the owner played
  `LightSorc` (tool-built, level 80) alone in Nightmare with `tc-party.gdb` logging; 124 calls, 124 reproduced
  (normal 98, minion 17, champion 2, unique 4). Both champions are class 61 with `mflags=0d` (`0x04` together with
  `0x08` and `0x01`) and logged base TC 698 `Act 1 (N) Champ C` = `TreasureClass2(N)`, not the `TreasureClass3(N)`
  (783) that a unique of the same class logged, then upgraded within group 18 to 700 at mlvl 44. items/0001: champion
  column and champion-before-unique order `[C]` (summary, §3), the champion group walk and one `boss` call (Andariel,
  upgrade level 0) added to the §4 observed part; the superunique-first order, Normal/Hell champions and the classic
  branch stay `[I]`. r2 re-read of `MONSTER_DropItems` at 0x005A66A0–0x005A66FA. Single player: `g6a=3`, no second
  client, no listener. One aborted launch before it (0 calls). Plan status and review left to the architect.
- **2026-10-12 — Phase 2 (c) reviewed; plan closed (architect).** Verdict: **accept**. Checked: `tools/tc.py replay`
  rerun on `workspace/logs/tc-champion-1.log` (124/124; normal 98, minion 17, champion 2, unique 4); the two champion
  `TCR` lines (818, 948: `sclass=61`, `mflags=0d`, `DROP base=698 lvl=44`) and the same-class unique (568,
  `mflags=09`, `DROP base=783`) read against the raw log; r2 at 0x005A66C0–0x005A66DD (flag 4 test, `+0x88` read, then
  flag 8) and 0x005A0180. The `[C]` is scoped to Nightmare, expansion, single player, class 61; superunique-first,
  Normal/Hell and classic stay `[I]`. The Andariel call (one `boss` monster at upgrade level 0) in the §4 observed part
  is in scope: it is a logged, replayed value, and the §4 gate bullet stays `[I]`. Inputs were a tool-built save
  installed through `tools/saves.py` (restored, manifest verified); no intervention. Plan done: (a), (b), (c) and the
  FPU control word are met. ADR-0008 stays **proposed** until the owner accepts the network exposure; (c) itself ran
  single player and opened no listener. Follow-ups: the `items/tc` tag pass (backlog, spec-writer), then the
  `items/tc` review.
