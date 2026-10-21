# 0044 — Multiplayer branches: the two-client cases of the reviewed specs

> **Status:** done (approved 2026-10-16, owner, unattended; closed 2026-10-20; P1, P2 and P3 accepted with fixes); [ADR-0008](../../adrs/0008-two-client-harness.md) accepted 2026-10-16 on the port-4000 condition (Phase 2)
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
  session starts until this is recorded. The steps are [multiplayer/0001 § 5](../../findings/multiplayer/0001-cases.md#5-the-hosts-binding-and-the-port-4000-precondition)
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
  delays and the portal closing ([quests/0002 § Phase 1b verdicts](../../findings/quests/0002-travel.md#phase-1b-verdicts),
  § 9). Two stamps gate leaving town: waypoint travel waits 10 000 ms (`0x0054C5D0`) and another player's portal 5000 ms
  (`0x00584870` via `0x0055B6C0`), both on `GetTickCount`; the only writer is `0x0055B720`, called once, from
  `0x005A5E50`, which also closes the player's portal. The community lead (one 10-second delay for both) is contradicted
  for portals on the condition that `0x005A5E50` is the hostility declaration. The case: player B declares hostility
  on A, then each tries a waypoint and A's portal before and after 5 s and 10 s; log the stamp, the tick at each gate,
  and the portal pair. Also from 0042: a party member using another player's portal into a `QuestFlag` level without
  the quest (the portal gate of quests/0002 § 6).
- **2026-10-17 — Phase 1 landed (reverser, `lane/p44r` from `main` `1083b92`, static), review requested; the live
  driver test is a checkpoint below.**
  - **Case list:** [multiplayer/0001](../../findings/multiplayer/0001-cases.md), one finding rather than a section in each
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
    ([combat/0001 § 7](../../findings/combat/0001-formulas.md#7-reductions-combat_applyreductions)). `combat.gdb` logs the
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
- **2026-10-20 — Phase 2 run (reverser, `lane/p44h` from `main` `f8de60b`, slots 1 and 2), review requested.**
  - **Precondition:** a confirmed existing block. The owner's 2026-10-17 listing stands; before the first hosting
    session the lane re-read without root (ufw active and enabled, input policy DROP, no rule for 4000, `lo` accepted
    first, every rule file unchanged since 2026-09-21) and hashed the eight files; before each later session the same
    re-read matched the hashes (20 re-reads for 18 sessions; corrected at review). No rule was changed and no root step was repeated.
    ([record](../../findings/multiplayer/experiments.md#run2026-10-20-two-clients))
  - **The driver's live test** (the six steps of the Phase 1 checkpoint) passed before any case session: where,
    invite and accept, follow into the Blood Moor, leave the party, hostile (the joiner's `+0x160` and pair stamp
    written), leave. Measured: the hostile button (103, 147), the exit item (400, 260), the trade accept (320, 103), the
    trade check (318, 461), the offer grid (97, 316). Screenshots under `workspace/logs/p44h-live-2/`. Driver fixes: the
    PLRS line also fires on the server frame (standing players), and `"join"` names the joiner present after a rejoin.
  - **19 sessions**, every checker 0 mismatches (`workspace/logs/p44h-run/check-run.txt`). Done-when: 417 party kills
    with drops, 46 vendor stock events with two players, 385 party experience shares, 12 quest-bit writes with both
    players present, 230 player against player attack events.
  - **Reached:** MP01, MP04, MP06–MP10, MP15, MP16 (a, b, c, d, e), MP19, MP22, MP23, MP24, MP25 (the `0x10000`
    filter), MP26, MP28 (a), MP29; partly MP11 and MP20. **Shortfalls:** MP02, MP03, MP05 (not stageable); MP12, MP13,
    MP14, MP17 (no session; owner play not asked); MP18 (no recipe); MP21 (no lifecycle logger); MP27; MP28 (b), (c)
    (the Den did not complete in three of four games); MP30 (no e9/e10 line); MP31, MP32 (no prediction written before
    the run); MP23's in-town defender and MP24's server town test (the client refuses both); MP25's offensive auras.
  - **Found on the way:** J4's member input is the x87 product of the f32 `q` and the level, not rounded to f32 (98
    separating inputs); a withdrawal leaves `+0x160` alone (one case); the stock client refuses a declaration outside
    town; a dead player is mode 17 with `+0xC6` bit 0 clear; the host's Den entry sets word 1 bit 4 on every player's
    record. All in [multiplayer/0001 § 6](../../findings/multiplayer/0001-cases.md#6-phase-2-results-run2026-10-20-two-clients).
  - **Tools:** `tools/mp_check.py` (xpshare, gates, aura, quests); loggers `two-kills`, `two-combat`, `two-vendors`,
    `two-quests`, `two-monstats`.gdb; `two-players.py` PLRK, the MP24 gate lines, `qr`, AF; `tc-party.py` the killer's
    owner; checker changes in `combat.py` (`--no-shield`), `monstats.py` (live players from PLRS), `vendors.py` (the
    renamed ETB tags), `tc.py` (the owner). Saves restored on both slots; both slots stopped.
  - **Backlog:** the review request to the architect; Phase 3's re-tags to the spec-writer; the Phase 1 follow-ups
    entry closed.
- **2026-10-20 — Phase 2 reviewed (architect, `lane/p44h` at `b41043d`, `main` `2ebd473` merged in as `40677a6`,
  clean): accept with fixes. Phase 2 is done; Phase 3 (spec-writer re-tag) may start.** `backlog.py archive` changed
  nothing.
  **The port-4000 precondition (the owner's condition on ADR-0008): met, as a confirmed existing block.** The owner's
  root listing of 2026-10-17 (above) is the root step. The no-root re-read before live-1 ran at 10:51:34, two minutes
  before live-1's host log opened (10:53:34); the review found the command's output in the lane's own tool output of
  that time and it matches `p44h-ufw-initial.txt` line for line (the file itself was written at 13:14, and its
  `ip -br addr` line drops the IPv6 addresses; § 5 shows no IPv6 listener). The eight hashes equal
  `ufw-baseline.sha256` (written 11:02:31) and every rule file's mtime is 2026-09-21 or earlier. `p44h-ufw.log` holds
  20 re-reads, each 1–3 s before a host log opens, covering all 18 later sessions (kills-3 and kills-5 twice, for an
  aborted launch); 0 `FAILED`, ufw active and enabled, input policy DROP every time. No rule was edited and no root
  step repeated. Two weaknesses, neither touching the condition: `ufwcheck.sh` always exits 0, so the drivers'
  `|| exit 1` would not have stopped a session on a change (the log would still have shown it, and it shows none);
  the record said "18 times" for 20 entries. Both corrected in the record; the script fix is filed to the reverser.
  **Checks:** `sha256sum -c` of the 163-file manifest from `workspace/logs`: all OK (manifest `b6eefb02…`).
  `drivers/check_all.sh` re-run under `systemd-run --user --scope -p MemoryMax=4G` at `40677a6`: identical to
  `check-run.txt` but for `monspawn.py`'s count (2764 checks against 2691, both 0 mismatches; `main`'s monspawn
  changed since `97da6a0`). Every checker 0 mismatches. Counts recomputed from `count-run.txt` and `check-run.txt`:
  417 party kills (276 + 33 + 95 + 13), 46 vendor events, 385 shares, 12 quest writes, 230 PvP events; 686 resolver
  calls. Anchors: 0x0058FD0A and 0x0059017F are `call 0x0065C360` with return 0x0058FD0F and 0x00590184, as the QS
  lines give; `XP_PartyShare` 0x0057E754–0x0057E77B is `fild`/`fidiv`/`fstp dword`, then `fild` level, `fmul dword`,
  `call CRT_ftol2`; `CRT_ftol2` (0x00682FD0) truncates on both paths.
  **Rulings on the four checker changes (each: the checker, not the game, was wrong):**
  - (a) `combat.py --no-shield 1,2`: **accepted.** `tools/d2s.py dump` of `MpPvpHost` (`83ad704d…`) and `MpPvpJoin`
    (`9dbb422b…`), the hashes the record names, lists three items each (`tsc`, `isc`, `tbk`), all in the inventory,
    nothing equipped; the recipes have no shield. The game logged DRB `b` 0 on all 66 events; without the option the
    checker fails exactly those 66 on DRB, because it applied the shield formula to a player holding none, the case
    combat/0001 § 4 and combat/to-hit `BlockChance` already give as 0. The option is hand-fed input; a logged shield
    flag is filed as a later improvement.
  - (b) `monstats.py` live players from PLRS: **accepted.** The checker hard-coded one player; the 64 earlier
    mismatches are the four MonPlayerBonus-derived fields of exactly the 16 creations made while PLRS listed both
    players, and the game's `[50, 50, 0, 0, 2]` is the two-player row. Scope: 8 of the other 44 fall between a
    one-player and a two-player PLRS line, so the sampling decides them; no death in mstat-1, so the dead-mode
    exclusion is not exercised. § 6 says so.
  - (c) `vendors.py` ETB tags: **accepted.** A pure tag rename (plan 0027 Phase 3; `affixes.py` already maps it as
    `ETB_LEGACY`); `two-vendors.gdb` sources no `props.py`, so the mapped `ETH0` cannot collide with that logger's
    own `ETH0`.
  - (d) `tc.py` the killer's owner: **accepted, as a model extension, not a repair.** Before it, a monster killer gave
    `party=None` and the PARTY check was skipped (no mismatch); now MP04's owner path is checked on 36 of 40
    mercenary calls (33 party 2, 3 party 1), which a "monster killer counts as party 1" reading would fail 33 times.
  **Rulings:**
  - (e) **The quest count, 12 ≥ 10: met, thin.** Composition (from the QS lines): 8 are the Den-entry word 1 bit 4
    writes (two per game, four games, partied in den-a and den-a2, not in den-c and den-c2), 4 are den-a2's clear (bits
    13 and 1 on each player's record). Every counted line is a real write on a player's record with both present, so
    the count stands; MP28 (a)'s `[C]` rests on the one clear, which a no-credit reading could not match. The record
    now gives the split.
  - (f) **Shortfalls: all named, accepted.** Unstageable with the stock client or two players: MP02, MP03, MP05,
    MP23's in-town defender, MP24's server town test and below-9 branch. Owner-play candidates MP12, MP13, MP14, MP17:
    out of this plan, one human entry (optional). Agent-stageable later (MP18, MP21, MP27, MP28 b and c, MP30, MP25's
    offensive auras, MP20's attribution, MP16 just inside the bound; MP31, MP32 after a prediction): out of this plan,
    one reverser entry. None is raised.
  - (g) **J4's float rule `[C]`**: the code reading above plus 98 separating inputs. Stated for a reimplementer: the
    product of the integer level and the f32 `q` is exact in f64, then truncated. Routed in the Phase 3 entry.
  - (h) **The Den-entry bit 4 `[I]`: right.** Not in the case list and not predicted (ADR-0004), seen in four games
    with the site resolved; it stays `[I]` until a reading of 0x0058FD0A's caller names the event.
  - (i) **Phase 3 inputs** added to the open spec-writer entry: J4's wording, combat/to-hit's no-shield line (66
    events), and the scoping of the PvP and monster raises.
  **Fixes, 9:** stale cross-reference 2 (multiplayer/0001's "not yet live-tested" driver line; Data touched's
  "`+0x160`, `+0x38` not yet in save.h"), miscount 2 ("18 times" for 20 re-reads; MP16 "four of five branches" with
  five listed), overclaim 1 (PvP "P = 17 on every reduction" with physical and lightning only, which the `lane/arc6`
  review asked to name), omission 2 (the quest count's split; combat/to-hit's no-shield line missing from the Phase 3
  routing), other 2 (`ufwcheck.sh`'s inert exit; the initial ufw record written after the fact without saying so).
  **Follow-ups:** spec-writer (Phase 3, open entry, additions); human (owner play MP12–MP14, MP17, optional); reverser
  (the shortfalls and the ufw check script).
- **2026-10-20 — Case added from plan 0047 (architect, P1 review of `lane/p47r`).** For the case list: **open wounds
  on the player** (stats/states *Open questions*): stat 135 is written only by item properties, and no MonStats,
  MonProp or MonUMod cell names it, so only a hostile player wounds a player. The case: player B, hostile, wearing an
  open-wounds item (tool-built, ADR-0013 § Neutral), hits player A; the stats logger's state and tick lines on A.
  ([plan 0047 log](../0047-simulation-shortfalls.md#implementation-log), Phase 1 review, ruling 2)
- **2026-10-20 — Phase 3 re-tag (spec-writer, `lane/p44s` from `main` `26d8978`), review requested.** Source:
  [multiplayer/0001 § 6](../../findings/multiplayer/0001-cases.md#6-phase-2-results-run2026-10-20-two-clients) as fixed by
  the Phase 2 review, each raise checked against it and the run record; every raised statement cites
  run:2026-10-20-two-clients. Front-matter `[C]` +28 over 11 specs (before → after):
  - **items/tc** C 45 → 49, I 82 → 81: F1 the monster killer's owner (the mercenary, 33 + 3 calls); F3 a dead member not
    counted; F2 `/players` on a TCP/IP host, the host's setting only, a dead player not in `PlayerCount`, and the
    maximum rule with two live players; the reimplementation note on `/players` (types 2 and 3; type 1 stays `[I]`).
    More than two players, the clamp at 8 and a member without a room stay `[I]`.
  - **player/creation** C 81 → 85: the party bonus constant (89/256; the 6400 bound split out and kept `[I]`: no kill
    inside it came within 800); J4 `[C]` for n = 2, with the member's input rewritten as
    `trunc((f64) level_i × (f64) q_f32)` (the review's wording, the 98 separating inputs) and `q` as the
    `fild`/`fidiv`/`fstp dword` the finding reads; the J2–J5 "not run" note narrowed.
  - **items/quality** C 69 → 70: M2, the magic find is the killer's alone with a partied second player.
  - **monsters/stats** C 105 → 106, I 57 → 58: C1, real players counted with one and two live players (16 / 44
    creations; the 8 sampling-decided ones named); whether a dead player counts stays `[I]`, as the review scoped.
  - **combat/reductions** C 38 → 40: P = 17 between two players for physical and lightning only (constants row and an A2
    note); fire, cold, magic, poison, a hireling attacker and a defender in town stay open.
  - **combat/to-hit** C 32 → 33: `BlockChance`'s "holds no shield → 0" cites the 66 pvp-1 events (review addition 2).
  - **quests/travel** C 68 → 73, I 80 → 82: D1 and G3 the two gates with a declared stamp; G3 the hostile operator
    refused before the gate; J2 widened to two clients; a new J3 for the declaration (pair stamp, `+0x160`, the repeat
    refused) `[C]`, its town and level conditions, the portal close and the party leave `[I]` (code; the client's
    outside-town refusal named), and the withdrawal `[I]` (one case).
  - **quests/progression** C 114 → 116, I 320 → 321: word 1's Den party credit `[C]` for a partied member in the Rogue
    Encampment (the act test and the unpartied case stay `[I]`); the Den-entry b4 on both records added as `[I]`.
  - **stats/states** C 43 → 44, I 46 → 47: F3 the filter's player bits as an `[I]` reading (MP25 prediction), and
    `0x10000` `[C]` for Might (16 / 17 / 28).
  - **items/vendors** C 71 → 77, I 38 → 37: the TownPlayerRemove entry row; A2 the shared stock; C1 a built store kept
    at the other player's open (the same player's reopen stays `[I]`) and the two-interactor stale case; C2 the leave
    with and without a player left in town and Harrogath's missing case (the drop versus *Save and Exit* scope named);
    C3 split, the MP11 branch kept `[I]`.
  - **hirelings** C 94 → 95: one hire table per game with two players (Kashya).
- **Open questions narrowed, 11** (none struck, so no `[L]` count changed): items/tc 2 (parties; `game.type` and
  `/players`), items/quality 1, combat/reductions 1, combat/README 1, quests/travel 1 (the un-declare path),
  quests/README 1 and its *Not covered* paragraph, stats/states 1, stats/README 1, items/vendors 1, hirelings 1.
- **Not raised, as the review ruled:** MP12–MP14, MP17, MP18, MP21, MP27, MP28 (b, c), MP30, MP31, MP32, MP25's
  offensive auras, MP20's attribution, MP16's inside edge, the dead player in the monster count, the Den-entry bit and
  the withdrawal. Also not raised: **MP26** (the portal's party gate): the run record reaches it, but § 6 has no
  bullet for it, so quests/travel's party test stays `[I]` (a point for the review). MP29 (the join) and MP11 stay
  `[I]` as § 6 tags them.
- **Overlap with plan 0038 Phase 3:** these raises cover 0038 inventory d-2c rows items/tc 43, 44, 46; items/vendors
  1, 10, 13, 16, 17; hirelings 11; player/creation 6, 31 (the party half of 33 too). *(Corrected at the review: vendors
  17 is MP11, kept `[I]`, and 33's party half is MP17, a shortfall; neither is raised. tc 43, 44 and player/creation 6
  are raised in part.)* The inventory files were not
  edited and no non-0044 row was re-tagged; 0038's ledger can mark them raised by plan 0044. quest-drops 6, 12, 36, tc
  27's party half and sockets 22 are shortfalls (MP12–MP14, MP18) and stay.
- **Wiki** (contradictions only, `based_on` bumped): combat (P = 17, the shieldless block, the open list), characters
  (party share, the shared hire table), items (the party count, the open lists), items-other-paths (the vendor
  multiplayer cases), monsters (real players), quests (party credit, hostility check, the real-time waits, the open
  list), stats-and-states (the party aura); saves only the date. The process pages how-we-know and README said the
  two-client run had not happened: reworded.
- **Plan status:** with this phase accepted, every phase of plan 0044 is done; the shortfalls are routed out of the
  plan (human and reverser entries of the Phase 2 review). The architect closes it at review.
- **2026-10-20 — Phase 3 review (architect, `lane/p44s` at `d3205f3`, `main` merged: up to date): accept with fixes.
  Plan 0044 closed.** `backlog.py archive`: nothing to move. Every raise checked against
  [multiplayer/0001 § 6](../../findings/multiplayer/0001-cases.md#6-phase-2-results-run2026-10-20-two-clients) and the
  run record: the counts quoted (686 resolver calls, 253 party-1 calls, 33 + 3 owner calls, 95 / 13 `/players` calls,
  385 shares and 98 separating inputs, 16 / 44 creations, 230 PvP events and 226 RDP lines, 66 shieldless events,
  16 / 17 / 28 filter calls, 12 opens, 351.6 s and 266.5 s, 4 of 4 compares per gate) match. Scoping as the Phase 2
  review ruled: P = 17 physical and lightning only (reductions A2 and the constants row, the 17 from a hireling and the 25
  kept `[I]`); the monster count with the 8 sampling-decided creations named and a dead player `[I]`; the 6400 bound
  split out and kept `[I]`. The new `[I]` code readings (states F3's filter bits, travel J3's conditions, progression's
  Den-entry b4) carry the finding's tags. The shieldless block (to-hit C2) rests on Phase 2 ruling (a)'s `d2s.py dump`
  of the two recipes; accepted.
  **Rulings:**
  - (a) **MP26 stays `[I]` until § 6 has a bullet: routed to the reverser.** The run record reaches it in one sentence
    (one click each way, outcome only: "left it in town", "moved it to the field end"); the party test's compare
    (`0x00554630`) is not a logged line. § 6 is where the finding states what each case reproduced and with what scope,
    and a spec raise cites that conclusion, not a record line the reverser has not concluded on (the record's
    *Conclusion* is the finding's to write, evidence-rules § Experiments). The entry asks for the bullet with its scope
    (pvp-1, one refusal and one pass, which lines show the outcome), then a one-line re-tag of travel G3's party test.
  - (b) **J4's wording.** `trunc((f64) level_i × (f64) q_f32)` says no more than the finding (§ 6 and the Phase 2
    ruling (g)). The new `q` line wrote `(f32) (total ÷ Σ levels)`, and `÷` is integer division in the pseudocode
    conventions, so it read as an integer quotient: rewritten `(f32) ((f64) total / (f64) Σ levels)` with the `fidiv`
    noted, and a step note `[I]` that this one rounding to f32 equals the x87 `fidiv` and `fstp dword` at any precision
    (f64 has at least 2 × 24 + 2 bits). player/creation I 48 → 49.
  - (c) **Plan 0038 overlap: the architect records it now** (inventory § 2.6, "Plan 0044 Phase 3"): 7 statements move
    d-2c → raised (tc 46; vendors 1, 10, 13, 16; hirelings 11; player/creation 31); tc 43, 44 and player/creation 6
    are raised in part and stay d-2c for their remainders (three or more players and the clamp at 8; a member without
    a room; the 6400 edge); vendors 17 (MP11 `[I]`) and player/creation 33's party half (MP17) are not raised. Totals
    recomputed once there: blocked 409 (d-2c 7), raised 17.
  - (d) **The plan 0047 case added to this log** (open wounds on a player, from a hostile player's item) was never run:
    it joins the open reverser entry of agent-stageable shortfalls, out of this plan.
  **Fixes, 6** (made in the documents): misread 2 (J4's `q` written with integer `÷`; how-we-know's "a trade" among the
  branches "read from the code", while plan 0043 left trading unread); overclaim 2 (the overlap note counting vendors 17
  and player/creation 33's party half as covered; vendors C2's Harrogath leave "called no `NPCSTORE_ActStale`", where
  the log shows no call from `TownPlayerRemove`, return 0x005375FC); miscount 1 (J4's note gave the branch counts as a
  partition of the 649 kills, but 9 + 106 + 108 + 42 = 265 against 264 single inputs; the run record's one-kill
  difference is filed to the reverser); other 1 (wiki/quests called the client's refusal outside town a code reading).
  The wiki README's 0044 bullet is moved to the closed plans by the close.
  **Close:** status done, moved to `done/`, links fixed; plan index row closed; research map rows refreshed for items/tc,
  items/quality, items/vendors, monsters/stats, hirelings, player/creation, combat, stats/states, quests/progression and
  quests/travel, and the multiplayer paragraph. **Backlog:** the review request closed; new reverser entry (MP26's § 6
  bullet, then the spec-writer's G3 re-tag; the 264/265 count); the owner-play human entry (MP12–MP14, MP17) and the
  agent-stageable reverser entry stay open, out of the plan. Gate green.

- **2026-10-20 — reverser, `lane/mp26` (after the close, backlog work out of this plan).** Static only (no harness, no
  Ghidra). (1) MP26: [multiplayer/0001 § 6](../../findings/multiplayer/0001-cases.md#6-phase-2-results-run2026-10-20-two-clients)
  has its bullet, `[C]` raised in part: one click each way on the host's town portal, outcome only (pvp-1 lines
  7421–7423 refused after GPP with both players in no party; 7521–7523 passed in party 3, the joiner in level 3 at
  7663). The party test is not logged; objdump places the refusal at 0x00584915 (the operator's `0x00554630` is
  `0xFFFF`), the only reachable refusal after GPP for level 3; the different-ids compare (0x0058493A) and the
  no-owner-unit pass (0x00584927) stay `[I]`. quests/0002 § 6's block now has the three steps. G3 re-tag filed to the
  spec-writer. (2) 264/265: the cut-off kill is kills-5's last (line 9688), counted by `mp_check.py xpshare`'s
  `pair:` counter at its XK0 in the "another level" branch, so (c) is 105 predicted; record and § 6 corrected.
  (3) `tools/ufwcheck.sh`, the fixed successor of the run's `drivers/ufwcheck.sh` (kept unchanged): exit 1 on any
  change; self-test exit 0 on the real state, 1 on each of three changed copies. Kept output `workspace/logs/mp26/`
  (`manifest.sha256`, `check-mp26.txt` `106cd63e…`). The agent-stageable shortfalls entry stays open for (2)–(4).
  Review request: [backlog](../../backlog/archive/2026-10-20-reverser-architect-review-lane-mp26.md).

- **2026-10-20 — review (architect, `lane/mp26` at `7354b09`, `main` merged at `461dcc2`): accept with fixes (3).**
  Checked against the kept logs (`workspace/logs/p44h-run/manifest.sha256` and `mp26/manifest.sha256` pass from
  `workspace/logs/`): pvp-1 host lines 7421–7423 (PH hostile 0, GP `lim` 16136301 < `now` 16193226, GPP), 7489 (party 3
  formed, the joiner still at (5680, 5847) in level 1), 7521–7523 and 7663 (level 3, (5492, 5426)) read as cited;
  kills-5 host line 9688 is the last XK0 (161 XK0, last XC0 at 9529, line 9689 the debugger's exit), 9687 its PLRK
  (host level 6, member 2 level 1). Arithmetic from `check-mp26.txt` § B: another-level counters 53 + 53 = 106, 105
  predicted; single inputs 9 + 95 + 160 = 264 = 9 + 105 + 108 + 42; shares 18 + 151 + 148 + 68 = 385, inputs 770;
  649 + 1 + 40 = 690. objdump of 0x005848E7–0x00584A39 and 0x00540710 (`PartyIdOfUnit`: `0xFFFF` when the unit is in
  no party) matches the § 6 bullet; the function tail read to 0x00584BC0.
  - **Ruling 1 (MP26 `[C]`, raised in part).** Two sources: the run (one refusal and one pass whose only logged
    difference is the party, the partied click a control through every later step) and the code (after GPP, the only
    party-dependent refusal; with both ids `0xFFFF` the id compare would pass, so the refusal is the `0xFFFF` test at
    0x00584911/0x00584915). Two outcome-only clicks suffice here because the control passes the same portal and
    destination 22.5 s later and no other refusal after GPP reads party state; the branch attribution is the code's,
    held by the run's elimination. The different-ids compare and the no-owner pass stay `[I]`, as filed.
  - **Ruling 2 (264).** The record's correction holds; (c) is 105.
  - **Ruling 3 (`tools/ufwcheck.sh`).** Read-only (no root, no ufw command; one append to the log). It now fails
    closed on every error tried: `workspace/logs/mp26-review/selftest-review.txt` (manifest
    `mp26-review/manifest.sha256`, base `workspace/logs/`; revision `3fda9b40…`). Every future hosting driver calls
    it as `tools/ufwcheck.sh … || exit 1` before launching the host; the rule is in the reverser's
    [tooling reference](../../../.claude/skills/reverser/references/tooling.md) (two-client section).
  - **Fixes:** (1) *omission*: the list of refusals after GPP left out the free-spot search's exit at 0x00584B18
    (`0x0064E7B0` returns 0: return 0, no refusal call); added to the multiplayer/0001 § 6 bullet (party-independent,
    passed by the partied click) and to quests/0002 § 6's OBJOP_Portal block. (2) *overclaim*: "every baseline hash
    checks" — `sha256sum -c` without `--strict` passed a baseline holding a malformed line beside one good line
    (exit 0, shown with the lane's revision); now `--strict`. (3) *omission*: a log that could not be appended to left
    the verdict unrecorded and still exited 0; now exit 2. The experiments record names both revisions.

- **2026-10-20 — spec-writer, `lane/g3` (after the close, backlog work out of this plan).** Static only. The
  [G3 re-tag entry](../../backlog/archive/2026-10-20-reverser-spec-writer-travel-g3-party-test-re-tag-mp26.md) done in
  [quests/travel § Using a portal](../../specs/quests/travel.md#using-a-portal): the operator's `0xFFFF` (no party)
  refusal is `[C]`, scoped as ruling 1 (two outcome-only clicks, the partied one the control, and the code at
  0x00584911/0x00584915); the different-ids compare (0x0058493A/0x0058493D), the no-owner pass (0x00584927) and the
  quest-word test stay `[I]`. G3's pseudocode follows quests/0002 § 6's block, the free-spot exit at 0x00584B18 included
  (its own `[I]` note). Inputs row and wiki/quests' portal paragraph updated. Tags C 73 → 74, I 82 → 84, L 4; no open
  question changed. Review request:
  [backlog](../../backlog/archive/2026-10-20-spec-writer-architect-review-lane-g3.md).
  - **Review (architect, 2026-10-20): accept with fixes (2).** Checked against multiplayer/0001 § 6's MP26 bullet and
    quests/0002 § 6's block; ruling 1 held (the `[C]` rests on the run and the code; the different-ids compare and the
    no-owner pass stay `[I]`); tags recounted C 74, I 84, L 4; wiki/quests carries no tags or anchors; the spec stays
    `reviewed`. (1) *omission*: the `[C]` note's code argument said "the only party-dependent refusal"; it now names
    the other refusals after the gate (two null-record guards, the quest gate, the free-spot search), which read no
    party state and which the partied click passed at the same end. (2) *omission*: the party id at the test is read
    through 0x00554630, which returns `0xFFFF` for a non-player unit and otherwise jumps to `PartyIdOfUnit`
    (0x00554645, objdump); the note now cites both.
