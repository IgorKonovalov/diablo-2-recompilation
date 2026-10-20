# Multiplayer: runtime experiments

Run records for [multiplayer/0001](0001-cases.md) (plan 0044 Phase 2: two clients, ADR-0008). Harness and evidence
rules: ADR-0003, ADR-0004, ADR-0008, ADR-0011; [tooling](../../../.claude/skills/reverser/references/tooling.md),
[harness-play](../../../.claude/skills/reverser/references/harness-play.md). Every record starts with the port-4000
precondition of [multiplayer/0001 § 5](0001-cases.md#5-the-hosts-binding-and-the-port-4000-precondition): which
check held, with the commands and their output.

## run:2026-10-20-two-clients

- **Question:** plan 0044 Phase 2. Do the multiplayer branches of [multiplayer/0001](0001-cases.md) behave as the
  reviewed readings predict when a second real player is in the game: the party and player counts of the drop resolver,
  the party experience share, the stores and the hire list with two players, the hostility declaration and the two
  travel gates, player against player combat, the aura filter, the quest credit, and the monster player-count terms?
- **Precondition (port 4000, the owner's condition on ADR-0008).** Held as a *confirmed existing block*. The owner's
  `sudo ufw status verbose` of 2026-10-17 (plan 0044 log: active, deny incoming, no ALLOW IN rule covering 4000/tcp)
  is the root step. Before the first hosting session (10:51, after a reboot at 07:49), the lane re-read without root:
  `systemctl is-active ufw` → `active`, `is-enabled` → `enabled`; `/etc/default/ufw` `DEFAULT_INPUT_POLICY="DROP"`;
  `/etc/ufw/ufw.conf` `ENABLED=yes`; `user.rules` and `user6.rules` hold only the 53317 (udp, tcp) and the two
  `allow-docker-dns` rules, no 4000; `before.rules:21` / `before6.rules:20` accept `-i lo` first; every rule file's
  mtime is 2026-09-21 or earlier, so none changed since the owner's listing; the sha256 of `/etc/default/ufw`, the six
  `/etc/ufw/*.rules` and `ufw.conf` became the baseline (`07db07bb…` default, `125c8b51…` user.rules, `76d8928c…`
  user6.rules, `d63bc8bb…` before.rules, `e31099b4…` before6.rules, `6f8e15ff…` after.rules, `70bd2895…` after6.rules,
  `254cb3ad…` ufw.conf). While hosting, `ss -ltn` showed `0.0.0.0:4000` (the listener §5 reads). Before every later
  session the same re-read (`systemctl`, the two policy lines, `sha256sum -c` against the baseline) ran and logged
  `OK` for all eight files: 20 re-reads for the 18 later sessions (kills-3 and kills-5 were each checked twice, once
  before an aborted launch), every one 1–3 s before its session's host log opens; no root step was repeated and no
  rule was changed. Commands and output: `workspace/logs/p44h-ufw-initial.txt`, `workspace/logs/p44h-ufw.log`, the
  baseline `p44h-run/ufw-baseline.sha256`. Review notes (2026-10-20): `p44h-ufw-initial.txt` was written at 13:14 from
  the 10:51:34 command output (the review compared it with the lane's tool output of that time: identical, except that
  `ip -br addr` is abridged to the IPv4 addresses); the baseline file was written at 11:02:31 from the same hashes;
  `drivers/ufwcheck.sh` always exits 0 (its verdict is the printed `UFW-OK`, so the drivers' `|| exit 1` never fires,
  and its `Policy="ACCEPT"` pattern cannot match the upper-case line). A changed file would still have shown as
  `FAILED` in the log, and the log has none; a later run's check must stop the driver itself.
- **Setup.** Slots 1 (host: `:8`, `workspace/wineprefix-1`, gdb by `tools/d2run.py`) and 2 (joiner: `:9`,
  `workspace/wineprefix-2`, no debugger), owner's condition on ADR-0008. Both saves directories were empty and set
  aside with `tools/saves.py --slot N aside p44h` before the first session, re-set per launch, and restored at the end
  (`restore p44h`: 0 files, sha256 match, aside removed; `status`: harness idle). Characters: `tools/mp_saves.py build
  workspace/merged/data/global/excel workspace/runtime/mp-saves-p44h` (`mp_saves.py check`: 27 recipes, 18 pairs, 0
  bad), sha256 prefixes: MpNovaHost `1a3e95eb…`, MpNovaWeak `402fe178…`, MpMagicHost `f5e7b031…`, MpTankJoin
  `a3dc1446…`, MpPvpHost `83ad704d…`, MpPvpJoin `9dbb422b…`, MpDenHost `51664080…`, MpDenJoin `be658b16…`,
  MpQuestHost `f1c693fb…`, MpQuestJoin `6b6d5e19…`, MpScrollJoin `87b31bca…`, MpPalJoin `f27b3a9f…`, MpMercHost
  `c190ed0b…`. Every session is Normal, expansion, a TCP/IP game over `127.0.0.1` (host `two-host-normal.steps`, the
  difficulty box added; joiner `two-join.steps`), agent-driven (no owner play). Session drivers (bash, kept with their
  output in `workspace/logs/p44h-run/drivers/`): `two.sh` (launch both), `meet.sh` (party, then both to an Act I
  waypoint through the Rogue Encampment's), `farm.sh` (host `d2pilot.py farm --sweep`, joiner `join follow --teleport
  --cross`) and one script per case group.
- **Loggers** (host only): `tools/gdb/two-pilot.gdb` (live test), `two-kills.gdb` (pilot, two-players, player,
  tc-party, tc-drops), `two-combat.gdb` (combat.gdb plus two-players), `two-vendors.gdb` (vendors.gdb and
  hirelings.gdb files plus two-players), `two-quests.gdb` (quests.gdb plus two-players and tc-party),
  `two-monstats.gdb` (mon-stats.gdb plus two-players, `MONSPAWN_WATCH=` empty). `tools/gdb/two-players.py` grew during
  the run; each revision only adds lines or fields: r0 `ccefe6b4…` (Phase 1, live-1); r1 adds the server-frame tick at
  `0x0052D870` (live-2); r2 adds `"u"` and PLRK (kills-1); r3 `65145820…` (commit 01b5d12) adds the MP24 lines
  HD0..GPP (kills-2..5, pvp-1, vend-1); r4 adds `"qr"` (den-a, qjoin-1, den-a2, den-c); r5 `1806ab1d…` (d48d0cf) adds
  AF (pal-1, mstat-1, merc-1, vend-2, vend-3, den-c2). `tools/gdb/tc-party.py`'s owner fields (`otype`, `oid`) exist
  from merc-1 on (08f58aa).
- **The driver's live test** (Phase 1 checkpoint, sessions live-1 and live-2, before any case session), the six steps:
  (1) host and join, `join where` lists both (ids 1 and 2); (2) `party invite` and `accept`: PLRS shows party 3 with
  both; (3) `follow` across one level: the host walked into the Blood Moor, the joiner followed it there and to within
  6 sub-tiles, then `party leave` (PLRS: no party); (4) measured from screenshots (`workspace/logs/p44h-live-2/`,
  `p44h-run/two-party-hostile-s2.png`): the hostile button is the row's left button (103, 147), the exit item SAVE AND
  EXIT GAME (400, 260), the "Agree to trade" OK (320, 103), the trade check button (318, 461), the own offer grid at
  (97, 316); a trade of one scroll completed; (5) `party hostile` with both at level 9 or more: the joiner's `+0x160`
  went 0 → 11772308 and its pair stamp to 11832308 (= `tk` + 60 000), then `leave`: the joiner gone from PLRS in
  0.5 s; (6) screenshots under `workspace/logs/`. Fixes found by the test: PLRS stopped while both players stood (r1
  adds the frame tick); the four positions above replaced the uncalibrated defaults; after a rejoin `"join"` now names
  the joiner present (a new unit id); the `give:` tokens must be quoted (`>`).

| session | host save | joiner save | seed | logger | what |
|---|---|---|---|---|---|
| live-1, live-2 | MpNovaHost | MpNovaWeak | 1 | two-pilot | driver live test |
| kills-1, kills-2 | MpMagicHost | MpTankJoin | 1 | two-kills | Blood Moor, Cold Plains: host sweeps, joiner follows |
| kills-3 | MpMagicHost | MpTankJoin | 2 | two-kills | Stony Field: `/players` 3 (host), 5 (joiner), 8, 1; joiner left behind; party leave |
| kills-4 | MpMagicHost | MpTankJoin | 3 | two-kills | Black Marsh: joiner in town (another level); not partied; the joiner kills, host follows (MP19) |
| kills-5 | MpMagicHost | MpNovaWeak | 4 | two-kills | Black Marsh: the weak joiner dies; the host kills before and after its respawn |
| merc-1 | MpMercHost | MpTankJoin | 8 | two-kills | Cold Plains: the host does not cast; its Rogue kills (MP04) |
| pvp-1 | MpPvpHost | MpPvpJoin | 1 | two-combat | MP24 gates, then MP23 player against player in the Cold Plains |
| vend-1 | MpNovaHost | MpTankJoin | 1 | two-vendors | MP09 ×2 rounds, MP15, MP07 a/b, MP11 |
| vend-2, vend-3 | MpMagicHost, MpNovaHost | MpTankJoin | 9, 1 | two-vendors | MP10 (vend-3), MP08 (both) |
| den-a, den-a2, den-c, den-c2 | MpDenHost | MpDenJoin | 5, 7, 7, 7 | two-quests | MP28 (a), (c) |
| qjoin-1 | MpQuestHost | MpQuestJoin, MpScrollJoin | 6 | two-quests | MP29, MP30 |
| pal-1 | MpNovaHost | MpPalJoin | 1 | two-combat | MP25 (b), (a), (c) |
| mstat-1 | MpNovaHost | MpTankJoin | 3 | two-monstats | MP22, MP20 |

- **Checks** (`workspace/logs/p44h-run/check-run.txt`, `9d743798…`, written by `drivers/check_all.sh` at tools
  `97da6a0`; every checker 0 mismatches):
  - `tc.py replay`: 6 logs, 686 calls, 686 reproduced. Party model per call (`-v`): party 2 with 2 players 276 (+ 33 by
    the mercenary), party 2 with 3 players 95, party 2 with 8 players 13, party 1 with 2 players 147, party 1 with 1
    player 106, not predicted (no KILL context or a killer that is neither a player nor owned) 16.
  - `mp_check.py xpshare` (new): 690 kills; 649 with the members predicted equal to the XP_Compute calls; 770 party
    share inputs (n = 2) and 264 single inputs predicted; 40 mercenary kills and 1 kill cut off by the session's end not
    predicted.
  - `player.py check`: every XP_Compute, AddExperience and LevelUp of the six kill logs reproduced.
  - `quality.py check` (the logged QKMF magic find): 427 pairs, 427 reproduced.
  - `combat.py check --no-shield 1,2` (pvp-1; new option: the two recipes hold no shield, combat/0001 § 4's "0 without a
    shield"): 243 events, 0 mismatches; without the option the 66 melee events whose defender holds no shield fail on
    DRB (the checker computed the shield formula), the same 0 otherwise.
  - `mp_check.py gates` (new): live-2 and pvp-1, 0 mismatches (below).
  - `vendors.py check` (vend-1..3) and `hirelings.py check` (vend-1): 0 mismatches. `vendors.py` now reads
    `tools/gdb/affixes.py`'s renamed `ETB0/ETB1` lines as the item model's `ETH0/ETH1` (the tags plan 0027 Phase 3
    renamed; before that fix, 11 failures, every one an `ETB0` the model did not expect, and the store events after
    them resynchronised).
  - `questdrops.py check` (5 logs) and `mp_check.py quests` (new): 0 mismatches.
  - `mp_check.py aura` (new): 0 mismatches. `monstats.py check` (mstat-1): 780 checks, 0 mismatches, after it counts
    the live players from PLRS (before: 64 mismatches, all the MonPlayerBonus of the 16 creations made with the joiner
    in the game and the stats derived from them); `monspawn.py check`: 2691 checks, 0 mismatches; collision 280, 0.
- **Results by case** (expected outputs from multiplayer/0001 § 2 and § 4):
  - **MP01** reached: kills-5, the joiner dead in level 6 (mode 17; the PLRS dead bit stayed 0) and the host killing:
    106 drops with party 1 and players 1, 108 kills with one XP member. Predicted, 0 mismatches.
  - **MP04** reached: merc-1, 40 kills by the Rogue (class 271, `ktype` 1), each KILL line's owner `otype 0 oid 1`; the
    party model from the owner gives party 2 for 33 calls and 1 for 3 (the joiner elsewhere); 0 failed.
  - **MP06** reached: kills-3, `/players 3` → 95 calls with players 3 (the joiner's `/players 5` in the middle of them
    changed nothing), `/players 8` → 13 calls with 8, `/players 1` → players 2 (two alive) for the rest.
  - **MP16** reached in all five branches: (a) 385 shares; (b) 9 kills with the other member beyond d² 6400 (5 of
    them within 800 of the bound) and 1 member; (c) 106 with the other member in another level; (d) 42 not partied;
    (e) 108 with the other member dead. Every member set and every input predicted. J4's split: the inputs equal
    `trunc(level × q)` with `q` rounded to f32 and the product **not** rounded to f32: in 98 inputs the f32-rounded
    product would give one more (e.g. E 63, levels 81 and 81: 41, where 42 would follow from rounding).
  - **MP19** reached: kills-4, 10 drops by the joiner with QKMF 0 while the partied host wears 472; 20 by the host with
    472; quality reproduced from the logged value both ways.
  - **MP22** reached: mstat-1, 44 creations with 1 player (before the join and after the leave) and 16 with 2 while the
    joiner was in, HP and experience +50 % (MonPlayerBonus `[50, 50, 0, 0, 2]`). Stat 100 after the leave not read.
  - **MP20** partly: the joiner explored 44 hops of the Blood Moor on its own and monspawn reproduced every room of the
    session (2691 checks), but no line names which player activated a room.
  - **MP23** reached: pvp-1, 230 attack events between the two players (70 melee with the left-button Attack, 160 Nova
    missiles), every reduction percent P = 17 (226 RDP lines; 4 melee misses have none): physical and lightning only, the other
    scaled fields are a shortfall of this pair. The "defender in town" branch
    is a shortfall: the client disables skills in town.
  - **MP24** reached (pvp-1, gates check): the declaration (HDR passed, HDS = now + 60 000, `+0x160` ← now, the pair
    entry holds the stamp: 2 of 2); a declaration again 50 s later refused by the pair stamp (stamp > now by 9.3 s, no
    HDS); the waypoint gate refused 4.4 s after the declaration and passed 33 s after (`lim` = `tk` + 10 000 on 4 of 4
    lines); the portal gate refused 2.4 s after a declaration and withdrawal and passed at 62 s and 84 s (`lim` = `tk`
    + 5000 on 4 of 4 lines); a hostile joiner on the host's portal refused before the gate (PH 1, PO operator 2 owner 1,
    no GP), the hostile host on its own portal through the gate. The withdrawal (HD0 hostile 0) left `+0x160` as it was
    (16131301 before and after). Counter cases: a declaration outside town is refused by the client ("Must be toggled
    in town.", no packet, no HD0), so the server's town test (HDO) is unreached; the level-below-9 counter case was not
    run.
  - **MP26** reached (pvp-1): not partied, the joiner's click on the host's town portal passed the 5 s gate and left it
    in town; partied, the same click moved it to the field end (level 3).
  - **MP07** reached (vend-1): (a) the joiner left from the Rogue Encampment with the host in town: townEmpty 0, Gheed
    (built 351.6 s earlier) marked stale, Akara and Charsi kept; (b) the host in the Blood Moor: townEmpty 1, the three
    built stores reset. Both leaves went through the connection drop (`slots.py stop 2`) after the menu click did not
    remove the joiner in 6 s (a), or after the driver lost the rejoined joiner's id (b).
  - **MP08** reached (vend-2, vend-3): a leave from Harrogath (109) logged PIEND and no STALE with the return
    0x005375FC (the Rogue Encampment leave of vend-1 has one).
  - **MP09** reached: 12 opens, each store built once at the host's first open and kept at the joiner's.
  - **MP10** reached (vend-3): Akara built, marked stale 266.5 s later by the joiner's town leave; with the joiner
    talking, the host's open has `sole` 0 and keeps the stock (no RESET, no BS0); after the joiner's talk ended, `sole`
    1, RESET, BS0.
  - **MP11** reached once (vend-1): the joiner, alone in town with Akara's trade open, dropped (`slots.py stop 2`):
    STALE (return 0x005375FC, townEmpty 1) came before its PIEND, and no RESET followed, the branch with an interactor.
    The record list of that STALE line is empty (the logger reads the act argument as a pointer there), so the stale
    byte itself is not seen.
  - **MP15** reached: Kashya's list built once (first builds 1) and the joiner's open received listed entries.
  - **MP25** reached for Might (`0x12003`): 16 filter passes partied, 17 refusals with neither, 28 refusals hostile.
    The offensive auras (`0x8000`) are a shortfall: the recipe's right skill is Might only.
  - **MP28** (a) reached (den-a2): the Den cleared, the partied joiner in the Rogue Encampment got word 1 bits 13 and 1
    from the PartyCredit sites (returns 0x0059017A, 0x00590184 after the calls at 0x00590175, 0x0059017F). (c) a
    shortfall: in den-a, den-c and den-c2 one Den room was never reached by the pilot, so the quest never completed. In
    all four games both records got word 1 bit 4 when the host entered the Den, partied or not (not in the case list).
  - **MP29** reached (qjoin-1): the game record's writes (words 1–3 bit 15, word 22 bit 13) came at the host's creation;
    at each join only the joiner's own record was written (word 36 bit 4, word 10 bit 9 cleared; log lines 1011–1012 and
    1535–1536, the record the next PLRS line's `qr` gives the joiner).
  - **MP30**: the joiner holding the Bark Scroll left; no quest line appeared at the leave. The e9/e10 effects are not
    logged by `quests.py`: a shortfall (logger).
- **Shortfalls (not reached):** MP02, MP03, MP05 (not stageable, Phase 1 ruling c); MP12 (the forge), MP13 and MP14
  (Andariel), MP17 (the Ancients): no session (the plan's owner-play fallback was not asked); MP18 (no recipe with a
  rune and a socketed item for the joiner); MP21 (plan 0040's lifecycle logger not merged into these loggers); MP27
  (no `QuestFlag` portal session); MP28 (b), (c); MP30 (logger); MP31, MP32 (no prediction written before the run,
  Phase 1 ruling d); the MP23 in-town defender and the MP24 below-9 and outside-town server branches; MP25's offensive
  auras; MP20's per-player attribution; MP16 had no kill near the bound on the inside (d² ≤ 6400 within 800).
- **Counts vs Done-when** (`p44h-run/check-run.txt`, `p44h-run/count-run.txt` from `drivers/count_events.py`):
  party kills with drops (party ≥ 2 at the drop): **417** (309 with 2 players, 95 with 3, 13 with 8; ≥ 100); party experience shares
  (n = 2): **385** (≥ 20); vendor stock events with two players (TO, BS0, STALE, RESET while the last PLRS line listed both):
  vend-1 30 (15 TO, 6 BS0, 4 STALE, 5 RESET), vend-2 7, vend-3 9: **46** (≥ 30); quest-bit writes on a player's record
  with both players present: den-a 2, den-a2 6, den-c 2, den-c2 2: **12** (≥ 10; 8 are the Den-entry word 1 bit 4
  writes, two per game at 0x0058FD0A, and 4 are den-a2's clear, bits 13 and 1 on each player's record; qjoin-1's 2 joiner-record writes came
  before PLRS listed the joiner and are not counted); player-against-player
  attack events: **230** (≥ 200).
- **Logs** (`workspace/logs/`, sha256 of 163 files in `workspace/logs/p44h-run/manifest.sha256`, `b6eefb02…`;
  `sha256sum -c` from `workspace/logs`; `count-run.txt` `935a00a0…`): every `p44h-*-host.log` and `-join*.log` of the table, the screenshots, `p44h-ufw*.txt|log`, and
  `p44h-run/` (drivers, check-run.txt). The aborted launches of kills-3 and kills-5 (the slot still busy) left no log.
