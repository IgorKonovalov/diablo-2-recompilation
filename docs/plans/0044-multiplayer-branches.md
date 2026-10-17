# 0044 — Multiplayer branches: the two-client cases of the reviewed specs

> **Status:** approved (owner, 2026-10-16; unattended); [ADR-0008](../adrs/0008-two-client-harness.md) accepted 2026-10-16 on the port-4000 condition (Phase 2)
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
- **The gate.** ADR-0008 was accepted on 2026-10-16 on one condition (network exposure: the hosting game listens on
  TCP port 4000 on all interfaces): before any hosting run, port 4000 is unreachable from outside loopback. ADR-0011 places the host on slot 0 and the joiner on slot 1, but slot 0 is now the
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
- **Precondition (owner's condition on ADR-0008, 2026-10-16):** before the first hosting session of the run, and again
  after any reboot or firewall change, the lane makes sure TCP port 4000 cannot be reached from outside loopback:
  it blocks the port with a host firewall rule limited to non-loopback interfaces, or confirms that an existing rule
  already blocks it (for example by listing the rules and probing the port from a non-loopback address). The run
  record states which, with the commands used and their output. No hosting session starts until this is recorded.
- **What:** run the cases, with the existing loggers on the host (`tc-party.gdb`, `vendors.gdb`, `quests.gdb`,
  `player.gdb`, `combat.gdb` and the others the case list names) and their checkers.
- **Done when:** the port-4000 precondition is recorded in the run record; `run:YYYY-MM-DD-two-clients` reproduces with **0 mismatches** under each checker, and every case of the
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
- **Network exposure.** Settled by the owner's condition (Phase 2 precondition); Phase 1 checks which way the host
  machine's firewall can meet it.

## Implementation log

_(lanes append dated entries as phases land: what was found, the confidence reached, surprises)_

- **2026-10-16 — Drafted (architect, `lane/plans39`).** Status `proposed`; gated on ADR-0008.
- **2026-10-16 — Approved (owner, via the main session).** Plans 0039–0044 approved to run unattended, like 0027–0038. ADR-0008 accepted the same day on the port-4000 condition, now Phase 2's precondition; host and joiner on two non-zero slots, slot 0 stays the owner's.
- **2026-10-17 — Case added from plan 0042 (architect, P1 review of `lane/p42r`).** For Phase 1's list: the hostility
  delays and the portal closing ([quests/0002 § Phase 1b verdicts](../findings/quests/0002-travel.md#phase-1b-verdicts),
  § 9). Two stamps gate leaving town: waypoint travel waits 10 000 ms (`0x0054C5D0`) and another player's portal 5000 ms
  (`0x00584870` via `0x0055B6C0`), both on `GetTickCount`; the only writer is `0x0055B720`, called once, from
  `0x005A5E50`, which also closes the player's portal. The community lead (one 10-second delay for both) is contradicted
  for portals on the condition that `0x005A5E50` is the hostility declaration. The case: player B declares hostility
  on A, then each tries a waypoint and A's portal before and after 5 s and 10 s; log the stamp, the tick at each gate,
  and the portal pair. Also from 0042: a party member using another player's portal into a `QuestFlag` level without
  the quest (the portal gate of quests/0002 § 6).
- **2026-10-17 — Phase 1 landed (reverser, `lane/p44r` from `main` `1083b92`, static), review requested; the live
  driver test is a checkpoint below.**
  - **Case list:** [multiplayer/0001](../findings/multiplayer/0001-cases.md), one finding rather than a section in each
    owning finding, because the cases share sessions. It has **32 cases**:
    - **29 stageable.** Three of these have no prediction yet, because the code is not read: MP25 (`aurafilter` with
      a second player) and MP31–MP32 (trade and party gold, plan 0043 Phase 1 on `lane/p43r`). MP18 depends on
      whether the stock client sends the socket insert during a trade. MP14 (a joiner death in Andariel's level) and
      MP17 (the Ancients' party grant) may need owner play.
    - **3 not stageable:** MP02 (more than two partied players: a third client exceeds ADR-0008 and the memory
      budget), MP03 (the clamp at 8: eight clients), MP05 (a partied player with no room: no input holds it open;
      logged if met).
  - **Coverage.** All 14 d-2c rows of the plan 0038 inventory have a case. The count is recomputed with the kept
    `grep`/`awk` in § 2 (tc 43, 44, 46; vendors 1, 10, 13, 16, 17; quest-drops 6, 12, 36; hirelings 11;
    player/creation 6, 31). So do the four partial halves (tc 27, sockets 22, quest-drops 25, player/creation 33)
    and the eight *Context* open questions. Plans 0040 and 0041 have a case each, plan 0043 two, and plan 0042
    Phase 1 six (MP24, MP26–MP30: the portal party and quest gates, party credit, the join, e9/e10). Pool 1 is
    d-none (`GameCreateA` has no caller), so it is not a case. Plan 0039 routed nothing here by name.
  - **The check.** All 38 entry addresses the cases cite start a function in the pinned binary (the `objdump`/`grep`
    command in § 2).
  - **Re-read on the way, all `[I]`:**
    - (a) **The travel gates read the operator's own PlayerData `+0x160`** (`0x0055B6C0` with EDX = 0 at both
      sites): waypoint + 10 000 ms, portal + 5000 ms. The only writer called is `0x0055B720`, from the hostility
      declaration. Lane/p42r's quests/0002 reads "an own portal is never delayed"; the code exempts no portal.
    - (b) **The declaration** (`0x005A5E50`) needs the declarer in a town (`0x0061AB00` → `LevelIsTown`) and level
      ≥ 9 on both players. It stamps the pair `now + 60000` and refuses a repeat before that. It closes the
      declarer's portal and leaves the party.
    - (c) **A player hostile to anyone cannot use a portal it does not own** (`0x00535B10`, before the 5 s gate).
      That is p42r's "not covered" verdict, now covered.
    - The contradicted lead stands: 10 s for waypoints, 5 s for portals. MP24 stages it, and the hostile steps
      add the counter cases.
  - **Host binding** (§ 5, `[I]`): both `bind` calls use `INADDR_ANY` IPv4 (0x006C321D, 0x006C3C26). All seven
    `socket` calls are `AF_INET`, and no IPv6 API is imported. Which call opens 4000 is not traced; the run
    observed it.
  - **Phase 2 precondition (owner's condition), recorded in § 5.** Read-only today (no rule changed):
    - ufw is active and enabled, `DEFAULT_INPUT_POLICY="DROP"`, and the user rules have no 4000. `before.rules`
      accepts `lo` first.
    - The loaded ruleset needs root, so before hosting the record must hold **(1)** `sudo ufw status verbose`
      (deny incoming, no 4000 allow) with the rule files' hashes, or **(2)** a probe from outside loopback (LAN host
      or Docker bridge) that times out against a stand-in listener on `0.0.0.0:4000` while `127.0.0.1:4000`
      connects.
    - **(3)** `sudo ufw deny proto tcp from any to any port 4000` only if (1) or (2) fails.
    - A probe from this machine to its own 192.168.0.12 does not count (it enters on `lo`).
    - This session's permission check refused the lane's look into a local container image, so (2) needs the
      owner's approval (backlog to human).
  - **Driver:** `tools/d2pilot.py join`.
    - Actions: `where`, `follow`, `party invite|accept|leave|hostile` (plan 0011's `two-party-*.steps` plus the new
      `two-party-hostile.steps`), `leave` and `trade TOKEN…`. `--me` on every other command steers by the host's
      new `PLRS` lines.
    - `tools/gdb/two-players.py` writes PLRS: every player's position, level, dead bit, party, travel tick and
      hostility stamps. `tools/gdb/two-pilot.gdb` is `pilot.py` plus `two-players.py`.
    - The pure logic is `tools/joiner.py`. `python3 -I tools/test_joiner.py`: 16 tests OK, no game or display;
      `test_slots.py` still 33 OK.
    - The tooling recipe (§ Two clients) now uses two non-zero slots and states the precondition.
  - **Phase 2 tooling still to add** (listed in the cases):
    - the owner unit on tc-party's KILL line (MP04);
    - the gate compare lines at 0x0054C60F, 0x005848CD and the declaration entry (MP24);
    - J4's party branch in `player.py` (MP16);
    - plan 0042 P2's travel and join lines (MP26–MP29).
  - **CHECKPOINT: driver live test pending a free slot.** Both harness slots were busy, so the driver has not run
    against a game. When two non-zero slots are free, and only after the port-4000 record:
    1. Host and join as above, then `join where`.
    2. `party invite` and `accept`, checked in PLRS.
    3. `follow` across one level, then `party leave`.
    4. Measure the hostile button, the exit item, the trade accept box and the trade grid from screenshots, and
       replace the uncalibrated defaults in `tools/joiner.py` and `two-party-hostile.steps`.
    5. `party hostile` with both players at level 9 or more, then `leave`.
    6. Put the screenshots under `workspace/logs/` and add a dated line here.

    Until then the Phase 1 *Done when* item "the joiner's driver is tested on a non-zero slot" is open.
  - **Backlog:** a review request to the architect; two-client recipes to the archivist; the precondition's root
    step or probe approval to the human; and to the reverser, the quests/0002 corrections for when lane/p42r merges
    and the `aurafilter` read for MP25.
