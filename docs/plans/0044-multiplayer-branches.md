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
  be staged (for example a third player); the joiner's driver is tested on a non-zero slot (moved to Phase 2's first
  step by the Phase 1 review, 2026-10-17); the architect's review rules the case list.

### Phase 2 — Two-client runs
- **Owner skill:** reverser (agent-driven; **two slots together**, both harness lanes)
- **Precondition (owner's condition on ADR-0008, 2026-10-16):** before the first hosting session of the run, the lane
  makes sure TCP port 4000 cannot be reached from outside loopback: a host firewall rule that leaves loopback open,
  or a confirmed existing block. The run record states which, with the commands used and their output. No hosting
  session starts until this is recorded. The steps are [multiplayer/0001 § 5](../findings/multiplayer/0001-cases.md#5-the-hosts-binding-and-the-port-4000-precondition)
  (Phase 1 review, 2026-10-17): the owner's root listing, or the owner's deny rule; the lane re-checks the ufw state
  and file hashes without root before each later session, and repeats the owner's step only if they changed.
- **First step: the driver's live test** (Phase 1's checkpoint, carried here by the Phase 1 review): the six steps
  of the Phase 1 log entry, after the precondition, before any case session.
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
- **2026-10-17 — Phase 1 reviewed (architect, `lane/p44r`, `main` `cf1d6e1` merged in as `4aa03c9`): accept with
  fixes; Phase 2 opens with the driver's live test as its first step, after the port-4000 record.** Merge: only this
  plan's log conflicted (both entries kept, in date order); `tools/backlog.py migrate` changed nothing. Gate green.
  **Checks** (my own objdump of the pinned `Game.exe`, sha256 `631066c1…`, not the lane's dump):
  - All **38 `fn:` anchors** of § 2 name the `re/symbols.csv` row at that address and follow `int3` or `ret`. The
    Entry column also holds 13 bare addresses: five function starts (0x00539DA0, 0x0054C5D0, 0x00554630, 0x00584870,
    0x005A5E50, also after `int3`) and eight sites (0x0055A8E4 is the clamp `cmp edi, 8` in `TC_ResolveDrops`), so
    "all 38 entries" is reworded and MP03 cites its function.
  - **The gates:** `xor edx, edx` at 0x0054C5F5 and 0x005848BA before `call 0x0055B6C0`, which returns PlayerData
    `+0x160` when EDX = 0 (0x0055B6C8–0x0055B6D4); `add eax, 0x2710` / `lea edi, [eax+0x1388]`, `GetTickCount`, `jbe`
    (unsigned). `0x0055B720` writes `+0x160` ← `GetTickCount()` for its ECX player (0x0055B759–0x0055B76B), called at
    0x005A5F51 with ECX = the declarer. **Both readings hold.**
  - **The portal's hostility test:** 0x0058488F `0x00535B10(game, operator)`, then owner id (`0x00552B10`) vs the
    operator's `+0x0C`; `0x00535AF0` sets the result on `0x0055B300(operator, player, 8)`. Holds.
  - **The declaration** (0x005A5E50–0x005A5FED): town, levels, pair stamp `+ 0xEA60`, refusal message 0x13, portal
    close, party leave all as read. The lane missed two details: the two level reads are `STATS_GetUnitBaseStat`
    (0x006253B0), and a declaration toward a player not yet hostile also needs `STATS_GetUnitStat(O, 12)` ≥ 9
    (0x005A5EE4–0x005A5EFF); the early refusals set an out flag (0x005A5FDE). § 4 and the summary corrected.
  - **Binding:** both `bind` sites zero a 16-byte `sockaddr_in`, write family 2 and the port, and pass it
    (0x006C31F8–0x006C321D, 0x006C3BF4–0x006C3C26). Holds.
  - `test_joiner.py` 16 OK, `test_slots.py` 33 OK. The lane's d-2c command gives **14** (tc 43, 44, 46; vendors 1,
    10, 13, 16, 17; quest-drops 6, 12, 36; hirelings 11; player/creation 6, 31); `grep d-2c` adds exactly the four
    halves and pool 1. Tags: every behavioural line is `[I]` with an anchor; `[L]` only under *Open questions*.
  **Rulings:**
  - (a) **One cross-cutting finding: accepted.** The research map's multiplayer paragraph now names it; Phase 3 re-tags
    the owning rows.
  - (b) **The checkpoint is carried into Phase 2**, as its first step: the live test hosts a game, so it needs the
    port-4000 record anyway. Phase 1's *Done when* item says so. No case session runs before the driver passes,
    and the four uncalibrated positions are measured then.
  - (c) **MP02, MP03, MP05 unstageable: accepted.** MP02 and MP03 stay `[I]` (this plan's open question; `/players`
    stands in for `PlayerCount` only). MP05 is a named shortfall unless a session meets it.
  - (d) **MP25, MP31–MP32 without a prediction:** they may be staged, but a run raises nothing unless the prediction
    is written before the session that reaches it (ADR-0004). MP25's comes from the open `aurafilter` entry (static,
    before Phase 2); MP31–MP32 wait for plan 0043 Phase 1's acceptance (`lane/p43r`, under review); if Phase 2 runs
    first, they are shortfalls, not observations to fit.
  - (e) **MP18's packet condition: accepted.** Phase 2 tries the stock client once with the trade open; if no PKT
    `0x28` line appears, MP18 is a shortfall (d-edit). A forged packet is out of this plan (pinned client only,
    ADR-0002 defers network tooling).
  - (f) **The quests/0002 correction is folded here**, since `lane/p42r` is on `main` and the review re-read the
    instructions: quests/0002 § 6 pseudocode, § 9, the closing list, the three hostility verdicts (the portal one
    "not covered" → "held"; the 10 s one keeps "contradicted for portals" on the operator's own tick) and the
    `0x005A5E50` open question (narrowed to the un-declare path). The research-map row says so. The reverser entry
    is closed. The earlier log entry above ("another player's portal 5000 ms") is superseded by this reading.
  - (g) **The firewall plan: accepted with the precondition reworded to the owner's condition and no more.** The
    owner's condition is "a firewall rule, or a confirmed existing block, recorded, before any hosting run". § 5 and
    this plan's Phase 2 text now ask the owner for one thing, once per Phase 2 run: `sudo ufw status verbose`
    (active, deny incoming, no ALLOW IN covering 4000/tcp), or, if it does not show that, `sudo ufw deny proto tcp
    from any to any port 4000`. Dropped: the probe option (a Docker-bridge probe covers only `docker0`, and a LAN
    probe needs a second machine), the `nft`/`iptables` listing (ufw's deny-incoming chain drops the packet whatever
    other tables say), and the owner's repeat after every reboot (the lane re-reads the ufw state and file hashes
    without root before each session, and asks again only if they changed). The human entry is reworded to match;
    tooling.md § Two clients too. No firewall was touched.
  **Fixes, 4:** omission 1 (the declaration's base/full level reads and out flag), wrong anchor 1 (MP03's entry and
  "38 entries" over 51 addresses), overclaim 1 (a Docker-bridge probe offered as confirming every non-loopback
  interface), other 1 (precondition steps beyond the owner's condition, partly from this plan's own text). Not a
  lane fix: the quests/0002 fold (routed correctly while p42r was unmerged).
  **Follow-ups:** reverser (Phase 2 start): name `0x005A5E50` and `0x00535B10` in `re/symbols.csv` and add PlayerData
  `+0x38`/`+0x160` to `re/types/save.h`; spec-writer (0042 Phase 3): quests/travel takes the corrected gates.
- **2026-10-17, Phase 2 precondition (port 4000) met (owner).** The owner ran `sudo ufw status verbose`. The output:
  - `Status: active`;
  - `Default: deny (incoming), allow (outgoing), deny (routed)`;
  - ALLOW IN rules only for `53317/tcp` and `53317/udp` (IPv4 and v6, from Anywhere), and for `172.17.0.1 53/udp` from `172.16.0.0/12` and from `192.168.0.0/16` (`allow-docker-dns`).

  No rule names 4000, no range contains it, and no rule is portless. So TCP 4000 is dropped on every non-loopback interface, and loopback is accepted by `before.rules`. This meets ADR-0008's condition. Before each hosting session, the lane re-reads the ufw state and the rule-file hashes without root. It asks the owner again only if they changed.
- **2026-10-17 — `lane/arc6` MP23 pair reviewed (architect, `main` `925d060` already in). Verdict: accept with fixes.**
  - **Ruling: the low-damage pair is right for MP23.** The prediction is P = 17 % on every scaled field
    ([combat/0001 § 7](../findings/combat/0001-formulas.md#7-reductions-combat_applyreductions)). `combat.gdb` logs the
    packet in 1/256 life and `combat.py` checks the RDP percent and the RD1 packet exactly after `MulDiv(v, 17, 100)`,
    so a 1-point field is already 256 units. A Nova 1 lightning field of 256 to 5120 separates P = 17 from 16 or 18 and
    from any other rounding. Large hits would reach only `MulDiv`'s large-value branch (more than 4096 life in one
    field), which MP23 does not predict. No potions, Energy Shield or sturdier class are needed, and no archivist
    follow-up was filed.
  - **Checked:** class 1 = Sorceress and right skill 48 = Nova (skills.txt `Id`); Nova `EMin` 1, `EMax` 20, `HitShift` 8,
    `EDmgSymPerCalc` blank; `mp_saves.py check` 27 recipes 0 bad, 18 pairs 0 bad; `test_d2s.py` 45 OK; `d2s.py survey`
    27 files 0 errors and `roundtrip` 0 item and 0 file differences on a fresh build, with the two new hashes as pinned.
  - **Fix (misread):** the bound ignored the player's resistance penalty. `COMBAT_ResistFor` adds `ResistPenalty`
    for a player defender (−40 Nightmare, −100 Hell in expansion), so a player with no resistance takes ×2 in Hell.
    The check now multiplies by `(100 − lowest ResistPenalty) / 100`: 7 points for Nova 1, 1400 ≤ 8000, and the pair
    survives in any difficulty. d2s.md says so.
  - **For the Phase 2 session:** the pair can reach row 0 (the left-button `Attack`, unarmed, through
    `COMBAT_MeleeHitTest`, the case's entry) and row 2 (Nova). Run both kinds of attack. The other scaled rows (fire,
    cold, magic, poison) stay a shortfall of this pair, and the session must name that shortfall rather than claim
    "every scaled field".
- **2026-10-20 — Case added from plan 0047 (architect, P1 review of `lane/p47r`).** For the case list: **open wounds
  on the player** (stats/states *Open questions*): stat 135 is written only by item properties, and no MonStats,
  MonProp or MonUMod cell names it, so only a hostile player wounds a player. The case: player B, hostile, wearing an
  open-wounds item (tool-built, ADR-0013 § Neutral), hits player A; the stats logger's state and tick lines on A.
  ([plan 0047 log](0047-simulation-shortfalls.md#implementation-log), Phase 1 review, ruling 2)
