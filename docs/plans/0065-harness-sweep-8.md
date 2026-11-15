# 0065 — Harness sweep 8: the backlog's live cases in one batch per slot plan

> **Status:** in progress: Phase 0 (staging) accepted with fixes 2026-11-15 (`lane/n65p`, Tier A as the audit); Phase 1 (single-client batch and P12) accepted with fixes 2026-11-15 (`lane/n65h`, Tier A as the audit; P12 not separated, owner ruling (a)); Phase 2 next, when the owner starts it; MP28 (b), (c) postponed by the owner 2026-11-15 (owner play, not dropped); approved 2026-11-10 by the owner, as recommended: Phase 2 runs (the pairing with plan 0067 Phase 2 lapsed: 0067 closed first, see the log)
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
  case is named with its reason. Both entries are closed or annotated. Review: Tier B. *MP28 (b), (c) are out of these
  criteria for now: postponed by the owner 2026-11-15 until an owner-played Den clear (Phase 0 review).*

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

### 2026-11-15 — Phase 0 (staging), `lane/n65p` (reverser, no slot, no game, no wine, no Ghidra)

Branched from `main` `389cb19d`. Every case of § Context has a recipe, a pair or session entry, a logger and a check, with
its prediction written here and in `tools/sweep8_check.py predict` before any run, except MP28 (b), (c), a named
shortfall. Nothing ran in a game; every tag stays as it was.

**Plan 0067 no longer shares the two-client set-up.** It closed (2026-11-15) after its own Phase 2 on slots 1 and 2
(run:2026-11-10-trade), so this plan's Phase 2 pays the port-4000 re-read and the two-client set-up alone. The scope is
unchanged. One consequence: MP31 is already met (row 16).

**Staging table.** Single-client cases run in Phase 1 through `tools/sweep8_sessions.py` (runner library, one fresh
process per session, `stage=NO_SHARING`: each case has its own character and logger, and C2, P12 and the exp-state kills
depend on the map seed; no sharing opt-in). Two-client cases run in Phase 2 from the pairs of `tools/mp_saves.py`
(Phase 2's lane writes the two-client runner on the library). "New" marks a file or line added by this lane.

| # | Case | Recipe / pair | Session | Logger | Check | Prediction (written before any run) |
|---|---|---|---|---|---|---|
| 1 | C2 (skills/0002 § 12) | new `sw8-nova` (SweepNova, Nova 1, life 3000, Act I) | `c2`: seed 3, Normal; walk out of the camp, then 60 pilot hops in the Blood Moor, no casting, so the quill rats live to shoot | `skills.gdb` rev 5, unchanged | `skills.py check` (`MC.vel`); new `sweep8_check.py c2` (spike1 only, the separating count) | `spike1` (Missiles row 7, `Vel` 10, `VelLev` 8) created at level `l`: velocity `tdiv((((8·l) ÷ 8) + 10) << 8 · 75, 100)` = 2112 at `l` 1, 2304 at 2; the lead's `VelLev·(l − 1) + Vel` gives 1920, 3456. Every creation separates (`8l − 8 + 10 = l + 10` has no integer root). Route: seed 3 Normal held two `quillrat1` packs in level 2 (`p44h-mstat-1-host.log` lines 7039, 7471, a TCP host game); that a single-player game at seed 3 has the same packs is expected, not shown |
| 2 | P12 (skills/missiles D3; verdict, Tier A at Phase 1) | `sw8-nova` | `p12`: seed 3, Normal; walk out, new `p12go` (re-pick from the session's own `CB` lines, hop to the stand cell), 6 Nova bursts there, then 25 hops of Nova over the level | new `p12.gdb` (`pilot.py` + new `p12.py`: `MMC` at 0x005AE2CB, the own-cell word `c`, point, size, cache flag; `MMR` at 0x005AE3F1 / 0x005AE3C3, returns 2 / 1); class filter `P12_CLS` 90 (`nova`: `pSrvDoFunc` 1, `CollideType` 3) | new `sweep8_check.py p12` | D3: a word with `c & 5 ≠ 0` at the missile's own point is followed by `MMR` 2 and no later `MMC` of that missile (freed, no hit function). The lead (flag 01 "allow missiles pass") predicts a later `MMC` for a bit-0-only word. Separating: a fresh (path `+0x7C` 0) word with `c & 5 = 1`. Control: words with `c & 5 = 0` step on. Pick from the kept grid (`sweep8_check.py pick`, seed 3): cell (4645, 4690), word `0x0001` (a 2×2 block in open ground), stand (4647, 4688), free on the whole diagonal through it; 28 930 of the 76 800 level-2 cells there have `c & 5 = 1`. **Open question 2:** stock bit-0-only cells lie on missile paths, so the lane proposes no forced cell (ADR-0013); **ruled at the review: no forced cell** |
| 3 | H2 (items/0017 H2; items/use F1f) | new `sw8-h2` (SweepPot: life 300 of 6000, mana 100 of 3000; page 0 cells 0..9: hp1 hp4 hp5 hp2 mp1 mp4 mp5 mp2 mp3 mp3) | `h2`: four pairs 1.2 s apart (hp1→hp4, hp5→hp2, mp1→mp4, mp5→mp2), 14 s between pairs; then 150 s of mana regeneration and the two mp3 | new `sweep8-use.gdb` (`pilot.py`, `inventory.py`, new `use-sweep8.py`: `URM` 0x005BE480 list/rem/len/state, `UBL` 0x005BE6C1 numerator/denominator, `UFL` 0x00580650, `UFM` 0x005807B7 the frees) | `inventory_check.py` (draws, fresh rates); new `sweep8_check.py h2` | The second use of a pair finds the first list (`list ≠ 0`, `rem > 0`): numerator `old·rem + v`, denominator `len + rem`, rate `trunc(num ÷ den)`; the wrong reading `trunc(v ÷ len)`. Fresh rates for a Sorceress, plain / doubled: hp1 40/80, hp2 96/192, hp4 240/480, hp5 320/640, mp1 80/160, mp2 160/320, mp4 600/1 200, mp5 1 000/2 000. Different tiers make `old ≠ v ÷ len`, so each blend separates unless the truncations meet (counted, not assumed). A `UFM` when mana reaches its maximum, and the next mana use finds no list |
| 4 | H3 (items/0017 H3; items/use D3, D5) | new `sw8-h3` (SweepMerc: CombatSor's hireling, alive; belt boxes 0..3 and 5: mp1 hp1 rvs yps wms; the same five in page 0 cells 0..4) | `h3`: Shift + 2 twice (hp1, then wms fallen to box 1), Shift + 3, Shift + 4, Shift + 1 twice; then each page-0 cell on the cursor, clicked on the hireling's portrait (request 0x61) and back | `sweep8-use.gdb` (new `T26` 0x00562453 flag/item, `T26A/B/C` the three `ITEMS_UnitIsType` results, `T26P` the pet, `T61` and `T61A/B/C` at 0x0054D230.., `IU0` `ItemUse` entry 0x005BF240) | new `sweep8_check.py h3` | Flagged 0x26 in an expansion game, tests 0x4C, 0x51, 0x50 in order, stopping at the first pass (ItemTypes' Equiv closure): mp1 (mpot) 0, 0, 0, refused, no `ItemUse`; hp1 (hpot) pass at 0x4C; rvs (rpot, Equiv1 hpot) pass at 0x4C; yps (apot) pass at 0x50; wms (wpot) pass at 0x51; each pass reaches `ItemUse` with the hireling (unit type 1) as user. The lead (The Arreat Summit) gives mp1 to the hireling: the mp1 lines separate. 0x61: the same three tests, counted. **Measured in the dev session:** the portrait point (`MERC_PORTRAIT` (20, 20) is a guess) |
| 5 | B8 (items/0017 B8; items/inventory F6) | new `sw8-b8room` / `sw8-b8full` (life 5 of 60, `hbl` worn, 16 boxes filled hp1 mp1 yps wms by column; page 0 empty / 40 `isc`) | `b8room`, `b8full`: waypoint to the Cold Plains, pilot hops with no potion until the first hit kills | `sweep8-use.gdb` (new `CCR` 0x0057F700 the item list, `CCN` 0x0057F72D the corpse path's count, `CMB` 0x0057F410, `BOV0`/`BOV1` `BeltOverflow` entry and return with the item lists) + `inventory.py`'s `IPG` | new `sweep8_check.py b8 --room / --full` | At the corpse's call (return 0x0057F47F, belt word 0, so `numboxes` 4): boxes 4..15 leave the belt in box order; b8room: page 0 at (9,3), (9,2), (9,1), (9,0), (8,3), (8,2), (8,1), (8,0), (7,3), (7,2), (7,1), (7,0) (`item_inventory.spot_find`, a player's page); b8full: each to the ground (an `IPG` before `BOV1`). Boxes 0..3 counted, not predicted. **Pre-check:** that a belt item's `x` in the logged list is its box |
| 6 | Exp-state kills (player/0002 § 4; a68 entry) | new `sw8-xs` (SweepConv: Paladin, Conversion 20 on the right button and F1) | `xs`: waypoint to the Cold Plains, 40 walking hops of Conversion cast at the nearest live monster (`explore --melee --curse-keys F1`) | new `sweep8-xs.gdb` (`pilot.py` + `player.py` revision 2: `XK0` gains `kxs`/`vxs`, the killer's and victim's states inside the exp mask, read as 0x0063A130 reads them; new `XSO`..`XSR` at `XpCreditPlayer`'s steps 0x0057E7DF..0x0057E84B) | new `sweep8_check.py xs`; `player.py check` | § 4: a converted monster (state 53) that kills credits the owner of its `0x800` list, the Paladin, where `MonsterOwner` gives none (separating); a monster that kills a converted one credits the owner of the victim's list (the victim's wins); `XSK ≠ 0` iff `kxs` non-empty, `XSV ≠ 0` iff `vxs` non-empty |
| 7 | 0058 live (a) far credited player, and MP16 near the bound | new pair "0058a MP16" (MpMercHost, MpTankJoin) | H farms with its Rogue, then teleports past 80 sub-tiles while the Rogue fights; J partied, parked by the fight (no `follow`), then parked at the level's waypoint while H sweeps outward | `two-kills.gdb` (`player.py` r2 adds lines only) | `mp_check.py xpshare` (counts the pairs), `player.py check` | player/0002 § 1: members collected by `d² ≤ 6400` from the **killed monster**; a far credited player with the other member near: n = 1 (the near member alone collected) and the credited player takes the whole award. MP16: pairs in `5600 < d² ≤ 6400` collected, `6400 < d² ≤ 7200` not (the plan's "kills just inside") |
| 8 | 0058 live (b) a dead killer | new pair "0058b" (new `mp-merc-weak`: MpMercHost's Rogue, life 40, Act I; MpTankJoin) | H stands among a pack until it dies; its Rogue kills beside the living J | `two-kills.gdb` | `mp_check.py xpshare` | § 1: the dead credited player is not collected, the living member is; n = 1 pays the credited player, not the member |
| 9 | 0058 live (c) a player kills a player | new pair "0058c" (MpNovaHost, MpNovaWeak; hostile) | H declares hostility in town, both walk out, H Novas J to death | `two-kills.gdb` + `two-players.py` (`HD*`) | `player.py check`; `mp_check.py xpshare` (counted) | § 4 *victim-player*: `XK0` with `mtype` 0, the gate passes (bit 26 is never set on a player, § 10), the credit is H; `XC0` with E = J's base stat 13 and mlvl J's base stat 12 |
| 10 | MP18 | plan 0051 P1a: pair MP18 (mp-sock-join) | unchanged | `two-sockets.gdb`, unchanged | `sockets.py` | multiplayer/0001 § 2: no `INSX`, no error 3; no `PKT 0x28` makes it a shortfall (Phase 1 ruling e) |
| 11 | MP20, MP21 | new pair "MP20 MP21" (MpNovaHost, MpTankJoin) | J explores rooms H never reaches; both stand in one room, then J leaves, later H | new `two-rooms.gdb` (the room files of `two-monstats.gdb` + plan 0040's `rooms.py`: `CE`/`CL`, `RP`, `FREE`, `CRC`, `ACTA`). Known clash: `rooms.py`'s `GP` tag is `two-players.py`'s portal `GP`; no portal in this session | new `mp_check.py rooms`; `monspawn.py check` | MP21: a room's `+0x78` is the count of clients holding it in their near lists at every `CE`/`CL`/`RP`; a `FREE` only of a room no client holds; separating: a room both held, kept while one stays, freed after both left. MP20: each activation attributed to the client of the latest `CRC`; the population with no player term |
| 12 | MP25 offensive auras | plan 0051 P1a: pair "MP25 offensive" | unchanged | `two-combat.gdb` (now with `sh`) | `mp_check.py aura` | multiplayer/0001 § 4 *MP25 prediction*: `0x8000` passes iff hostile |
| 13 | MP27 (a), (b) | pairs MP27a, MP27b (plan 0044) | H takes waypoint 26 to level 101, opens a town portal, goes to town; the partied J clicks it | `two-quests.gdb` (`two-players.py` r6: new `PQF` 0x00584A19, `PQR` 0x00584A1E, the quest gate) | new `mp_check.py portalquest --expect refuse / pass` | quests/0002 § 2: the gate reads `QuestFlagEx` 21 of level 101; (a) J's word 21 bit 0 clear: result 0, refused; (b) set: passes |
| 14 | MP28 (b), (c) | pair MP28 | — | — | — | **Shortfall** (below) |
| 15 | MP30 | plan 0051 P1a: pair MP30 | unchanged | `two-quests.gdb` | `mp_check.py leave` | multiplayer/0001 § 2 |
| 16 | MP31 | — | **met**: run:2026-11-10-trade case T1, 0 mismatches ([multiplayer/0003 § 13](../findings/multiplayer/0003-trade.md#13-phase-2-run-run2026-11-10-trade-lanen67h)); its counter cases are T3 and T5 there | `two-trade.gdb` | `trade_check.py` | no new session; Phase 2 cites the run when it annotates the 0044 entry |
| 17 | MP32 | new pairs "MP32" (new `mp-gold-join`: level 9, gold 0) and "MP32 full" (new `mp-gold-full`: gold 89 995 of 90 000) | H, partied with J alive in the level, picks up monster gold; counter cases J in town, J dead, not partied | new `two-gold.gdb` (`pilot.py`, `two-players.py`, new `two-gold.py`: `GP0`, `GPO`, `GS0`, `GSN`, `GC`, `GSF`, `GA`, `GPR`, `GPE`) | new `mp_check.py gold` | multiplayer/0002 § 3: J `+min(⌊A/2⌋, 10 000·L(J) − gold(J))`, H the rest plus J's overflow, clipped at H's cap; the counter cases: H alone. Separating: an odd `A` at n = 2, and an overflow (any pile of 12 or more on MP32 full) |
| 18 | Open wounds on a player | plan 0051 P1a: pair "open wounds" | unchanged | `two-wounds.gdb` (now with `sh`) | `combat.py check`, `stats.py check`, `mp_check.py gates` | stats/0002 § 2, § 6 |
| 19 | The shield flag for `combat.py --no-shield` | any two-client combat pair | rides rows 12 and 18 | `combat.py` gdb rev 10: `DRB` carries `sh`, `sub_0063C8F0_InvItemQuery(inventory, 0)` inside `UnitBlockChance` (0x0062279C) | `combat.py check` reads `sh` in place of `--no-shield` (a `--no-shield` on a defender with `sh` set is a mismatch) | MpPvpHost, MpPvpJoin, MpWoundJoin hold no shield: `sh` 0, block chance 0, as `--no-shield 1,2` gave on pvp-1; a defender with a shield takes the formula |

**Shortfall: MP28 (b), (c).** The Den clear needs every Den room reached. In run:2026-10-20-two-clients the pilot missed
a room in three of four games (den-a, den-c, den-c2), so the quest never completed; staging these again needs a pilot
route that sweeps every room of level 8 and kills the last monster, which is pilot work beyond a logger line. The
loggers, pair and checks exist (`two-quests.gdb`, MP28, `mp_check.py quests --word 1`). For the owner: the Den clear
by owner play with the scripted joiner (a few minutes), or MP28 (b), (c) named out of this plan.

**Checks of this phase** (kept: `workspace/logs/n65p/`, `manifest.sha256`, `commands.txt`, `tools-revisions.txt`):
- `mp_saves.py check`: 37 recipes, 29 pairs, 0 bad. `sweep8_sessions.py check`: 6 recipes, 0 bad, 7 sessions. The nine
  new recipes are pinned in `tools/test_d2s.py` (built twice, byte-identical); `RecipeTest.test_recipes_build` and
  `test_mp_saves_check` pass. `test_every_recipe_has_a_base` still fails for the same 11 recipes as on `main` (none of
  this lane's).
- `tools/test_sweep8.py`: 27 tests OK: each check on synthetic lines with a passing and a failing case; the shield
  flag's three branches; every new breakpoint address an instruction start of the pinned image, decoded from its
  function's start; the recipes; gdb arming the four new loggers. `test_p51_staging.py` 9 OK.
- gdb parses and arms, with no process, `p12.gdb`, `sweep8-use.gdb`, `sweep8-xs.gdb`, `two-gold.gdb`, `two-rooms.gdb`
  and the edited `two-combat`, `two-wounds`, `two-quests`, `two-kills`, `two-sockets` (`gdb-parse.txt`: every
  ready line, no `LOGERR`).
- Rule 17: the new logger files hold no memory or register write (`readonly-grep.txt`, 0; *review:* the edited `player.py`, `combat.py`, `two-players.py` and the sourced `pilot.py`, `rooms.py` 0 too, `review-readonly-grep.txt`). `sweep8-use.gdb` sources
  `inventory.py`, whose armed request edit fires only when its arm file exists: `sweep8_sessions.py` points
  `INV_RUNTIME` at a directory of its own and refuses to start if it is not empty.
- `combat.py check` on the pre-0065 pvp-1 log (no `sh`): 243 events, 0 mismatches, as before.

**Before Phase 1 (one slot).** The smoke session per new or edited logger revision (harness-play.md § Before the batch:
`p12.gdb`, `sweep8-use.gdb`, `sweep8-xs.gdb`) with the pre-checks named above: the hireling's portrait point (H3), the
belt item's box in the logged list (B8), the P12 re-pick on the dev log's own grid, and Conversion reaching a monster
by `explore --melee`. *Review order (fix 1):* before the `p12` session, `sweep8_check.py p12` also looks up the session's `CB`
grid at every `MMC` point and counts, as the lead's case, a word with `c & 5 = 0` (and a later `MMC`) at a point whose grid
word has `c & 5 = 1`; the verdict line names that count beside `separating`. Then `c2`, `p12`, `h2`, `h3`, `b8room`, `b8full`, `xs` as kept sessions; P12's verdict is
its own record (Tier A).

**Review request:** [Tier B](../backlog/archive/2026-11-15-reverser-architect-review-plan-0065-p0-staging.md).

### 2026-11-15 — Phase 0 review (architect, Tier A as the audit of the fifth Tier B lane since `lane/n66d`, `lane/n65p`)

- **Verdict: accept with fixes** (2 fixes: omission 1, tool not kept 1). Every case of § Context is staged with its
  prediction or named a shortfall with its reason; the gate is green after merging `main` (`31246d78` → merge).
- **Re-run, all as the log says.** `tools/test_sweep8.py` 27 OK (before and after the merge); `mp_saves.py check
  workspace/merged/data/global/excel` 37 recipes, 29 pairs, 0 bad; `sweep8_sessions.py check` 6 recipes, 0 bad, 7
  sessions; `combat.py check` on `p44h-pvp-1-host.log --no-shield 1,2` 243 events, 0 mismatches; `manifest.sha256` all OK
  (16 files with the review's one); every file of `tools-revisions.txt` hashes to the committed tree;
  `test_every_recipe_has_a_base` fails for the same six recipe names on the branch and on `main`.
- **Predictions written before any run, and derived.** No session has run (no kept game log after the branch point).
  C2 from skills/missiles B1 (`((VelLev·lvl) ÷ 8 + Vel) << 8`, then `× 75 ÷ 100`): 2112 / 1920 at level 1; the root
  argument (`l + 10 = 8l + 2` has none) holds. P12 from D3 and the image: `test al,5` at 0x005AE2CB, `jne` 0x005AE3EF
  straight to `mov eax,2` at 0x005AE3F1 with no call, the hit function 0x005ADF10 reached only from 0x005AE3EA. H2 from
  items/0017 H2 and F1f (`num`, `den` read at the `idiv` 0x005BE6C2). H3's three tests in order at 0x00562464..0x00562486
  and the Equiv closure. B8 from items/inventory F6 and `item_inventory.spot_find`. The exp-state kills from player/0002
  § 4 and the image (0x0063A130 through 0x00625BB0: `+0x5C`, flag `0x80000000` at `+0x10`, `+0x58`; the victim's
  `0x800` list read after the killer's, so it wins). 0058 (a), (b) from § 1's consequences, (c) from § 4 and § 10.
  MP32 from multiplayer/0002 § 3 (the room 5 of MP32 full makes any `A ≥ 12` overflow). MP27 from quests/0002 § 2
  (0x00584A03..0x00584A20). MP16 on the inclusive 6400.
- **Breakpoints.** The 44 new ones (`test_sweep8.py`'s `NEW_BPS`) sit in 17 functions, each a row of `re/symbols.csv`, and `ImageTest` decodes each as an instruction start from its function's start; spot
  reads against objdump: `MMC`/`MMR` (registers live at each), `T26A..C`, `XSK..XSR`, `GSN` (the `idiv`), `GC`, `GP0`,
  `PQF`/`PQR`, `sh` at 0x0062279C. Addresses named only in comments (0x0063D5F0, 0x00626090) carry no breakpoint.
- **Rule 17.** No write in any new, edited or sourced logger file except `inventory.py:254`, the armed request edit,
  which `sweep8_sessions.py` keeps unarmed (its own `INV_RUNTIME`, refused when not empty).
- **Fixes (2), written into this log above.**
  1. *Omission:* `sweep8_check.py p12` reads the session's grid only for a freed bit-0-only word. P12's Phase 1 must state
     which reading holds "either way", and the lead's observable is a Nova stepping on over ground the grid marks
     `c & 5 = 1`; the word `c` has been through `CollisionTest` over the missile's size (0x00648EB0, `+0x44`), so it is
     not the grid's cell word (reverser review-fixes rule 10: name what the observed value has been through). Ordered
     for Phase 1, before the `p12` session (§ Before Phase 1).
  2. *Tool not kept:* the kept read-only grep covered the new files only; the edited `player.py`, `combat.py`,
     `two-players.py` and the sourced `pilot.py`, `rooms.py`, `inventory.py` are now in `review-readonly-grep.txt` (with
     each file's hash), added to `manifest.sha256` and `commands.txt`.
- **Ruling, open question 2 (P12's forced cell): no forced cell.** Stock bit-0-only words lie on the Nova's paths (28 930
  of 76 800 level-2 cells at seed 3, the pick (4645, 4690) with free ground on both sides), so ADR-0013's condition
  for a forced cell is not met. If the `p12` session logs no fresh bit-0-only word, P12 comes back as "not separated"
  for a ruling; the lane does not force a cell on its own. The control stays the stock `c & 5 = 0` words of the same log.
  *Context since the branch:* `main` raised `sub_005AE1F0_MissileMoveCollide` to `[C]` on its frame behaviour (plan
  0066, skills/0002 § 13) with the own-cell branch left `[I]`, so P12 still decides D3.
- **MP28 (b), (c): postponed by the owner (2026-11-15).** The options put to the owner were (1) an owner-played Den
  clear with the scripted joiner, two short games (J partied in Act II; J not partied) under `two-quests.gdb` and
  `mp_check.py quests --word 1`, which raises the two rows; or (2) naming them out of this plan, leaving the code reading
  `[I]`. The owner chose neither yet: **postponed, not dropped**. The case stays staged as a shortfall awaiting owner
  play, the 0044 entry stays open with the decision dated, and MP28 (b), (c) are out of Phase 2's done-criteria for now.
  Phase 1 is not affected.
- **Audit note.** A Tier B check would likely have passed the five request items as the lane ran them and found fix 2
  (the grep's scope is diff-visible). Fix 1 needed `PathCellCollision`'s body read against the check, outside a
  diff-scoped pass, so Tier B would probably have missed it; it is not reject-grade (the order lands before the run).
  No reject-grade problem.
- **Ledger cells:** `architect-review`, Fixes `audit of lane/n65p: omission 1, tool not kept 1`; no reject-grade miss.
  **Promotion:** neither fix is a second sighting outside an existing rule (fix 1 is reverser rule 10), so no rule added.

### 2026-11-15 — Phase 1 checkpoint (resume note), `lane/n65h` (reverser, slot 1; paused by the owner for a reboot)

Branch `lane/n65h` from `main` `7b41313b`. No kept (batch) session has run yet; everything below is development and smoke
work, kept as `dev-` logs under `workspace/logs/sweep8/dev/` (smoke through smoke7; smoke7 was cut by the pause: b8room
and xs, no claim rests on it). Slot 1 is idle (driver killed by pid, `saves.py --slot 1 status`: no aside, harness idle).

**Done**
- *Review fix 1 (P12 check), committed `76f15377`.* `sweep8_check.py p12` now counts the lead's observable apart: a
  missile at a point the session's `CB` grid marks `c & 5 == 1` whose logged word is 0 and that steps again (fresh word:
  verdict "against the grid reading"; cached word: counted, decides nothing); SEPARATING needs a fresh freed word *and*
  the grid's own cell bit-0-only (with size 2 or 3 the word holds the neighbours' bits). Three no-game tests added.
- *Uncommitted edits at the pause (commit with this note):* `sweep8_check.py h2` handles the fresh use's own `UBL`
  (smoke: `UBL` fires on a use with no list too, on the list the use just made, num = v, den = len; the first check
  version called those six lines mismatches; now 4 blends as predicted, all 4 separating, 6 fresh rates as predicted,
  2 `UFM` frees, 0 mismatches) plus two tests; `sweep8_sessions.py`: `MERC_PORTRAIT` (38, 40); `p12go` writes the pick to
  `<stem>.pick.json` (a case mark has a fixed event set); the Rogue Encampment waypoint is not reachable by `farm --wp`
  (its default click is the Act V point; "the waypoint list did not open", smoke5), so b8room, b8full and xs use
  `LEAVE_TOWN` and walk the Blood Moor on seed 3 (the seed whose town walk is proven); `--dead-below 0` in `LEAVE_TOWN` and
  the b8 explore (the pilot read the 5-of-60 life orb as death at hop 1); c2's explore has `--nova 0` (the default
  `--nova 2` killed the quill rats before they shot: 640 Nova creations, no `spike1`).
- `test_sweep8.py`: 31 OK.

**Pre-checks settled (smoke logs)**
- *Hireling portrait (H3):* the frame is about x 15..62, y 18..62 in the 800x600 frame; (20, 20) sat on its edge and the
  clicks dropped the potions on the ground. At (38, 40) smoke4 gave 0x26 flagged: hp1, rvs, yps, wms to the hireling,
  mp1 refused twice (`sweep8_check.py h3`: 6 flagged, 2 separating, 0 mismatches); 0x61: four requests (tests `[76 T]` x2,
  `[76 F, 81 T]`, `[76 F, 81 F, 80 T]`); the mp1 click on the portrait produced no `T61` (the item went down as a ground drop,
  request 0x17): a client refusal before the logged function, to be read as that, not as a `T61A..C` result.
- *B8 belt `x`:* a belt item's logged `x` is its box (0x26 lines: mp1 x 0, hp1 x 1, rvs 2, yps 3, and wms 1 after the fall).
  The b8 deaths themselves are not yet reached (smoke5/6: the character never left town; fixed as above, untested).
- *P12 pick on the session's own grid:* holds (smoke2, seed 3: cell (4645, 4690) word 1, stand (4647, 4688), 2 148 bit-0-only
  cells of 24 000 in the grid, the pilot hopped to (4647, 4688)).
- *C2 seed 3 quill rats:* present in single-player (class 63 seen 146 times in the dev log); with `--nova 0` smoke6 logged 3
  `spike1` creations, `sweep8_check.py c2` 3 separating, 0 mismatches.
- *Conversion by `explore --melee`:* not yet shown (smoke5: the town walk failed on seed 6505; smoke7 cut).

**P12 finding to carry (not yet a record):** in the smoke log all 15 759 `MMC` of class 90 carry path `+0x7C` of 2 608, 3 608
or 4 608 (non-zero), so `PathCellCollision` (0x00648EB0, `cmp [esi+0x7c], 0; jne 0x648EDD`) returns the path's cached word
`+0x54` and never runs `CollisionTest` at the missile's own point; `PathStepMove` (0x00650660) clears `+0x54` at each step
(0x00650673) and `PathMoveWithMark` (0x00650910) writes it (0x00650957, 0x006509A5). The word was 0 in 15 001, 0x80 in 755,
256 in 2 and 384 in 1; none had `c & 5`. 234 of the `MMC` lie at a grid bit-0-only point and the Nova steps on (cached word,
nothing tested there). So a Nova can never give the fresh bit-0-only word: the staged separating case is unreachable for
it (ruling stands: no forced cell; the verdict is "not separated"). Missiles with `pSrvDoFunc` 1, `CollideType` 3 and a
blank `Vel` (firestorm, `fireexplosion`, the fire trails and 40-odd more, `missiles.txt`) are the candidates whose `+0x7C` may
be 0 and so take the fresh branch; that is `[I]` until a run, and needs another character: an owner decision for the architect.

**Next**
1. Rerun `b8room` and `xs` as dev (smoke7), then `b8full`; check each; confirm `T61`-style pre-check for Conversion.
2. Kept batch `2026-11-15-sweep8-single` (use the actual date): `c2 h2 h3 b8room b8full xs` under
   `sweep8_sessions.py run --slot 1 --tag n65h --run <date>-sweep8-single ...`, then the checks (`skills.py check`,
   `inventory_check.py`, `player.py check`, each `sweep8_check.py`), manifests, addenda (skills/0002, items/0013-0016,
   player/0002, path/0007), the four backlog entries.
3. `p12` as its own kept record `<date>-sweep8-p12`; verdict "not separated" unless a fresh bit-0-only word appears; Tier A request.
4. Phase 1 log entry with Tier B (batch) and Tier A (P12) review requests.

### 2026-11-15 — Phase 1 (single-client batch), `lane/n65h` (reverser, slot 1), batch landed, P12 not separated

Resumed from the checkpoint above. Dev reruns (kept as `dev-2026-11-15-sweep8-smoke8` b8room and xs, `smoke9` b8full):
b8room 12 boxes to page 0, b8full 12 to the ground, xs 5 separating, all 0 mismatches. Kept batch
`run:2026-11-15-sweep8-single` (`c2 h2 h3 b8room b8full xs`, one fresh process each, 731 s, 6 kept at the first try, no
death), record in [items/experiments](../findings/items/experiments.md#run2026-11-15-sweep8-single); kept logs
`workspace/logs/sweep8/2026-11-15-sweep8-single-s1-*`, checks and `manifest.sha256` (24 lines, passes) in
`workspace/logs/n65h/`.

| Case | Result | Where |
|---|---|---|
| C2 | 3 `spike1` creations at level 1, 3 separating (velocity as read, not the lead's), `skills.py check` 0 mismatches | skills/0002 § 14 |
| H2 | 4 blends, all separating; 6 fresh rates; 2 frees; 0 mismatches | items/0015 |
| H3 | hp1, rvs, yps, wms to the hireling; mp1 refused twice (the Arreat Summit reading contradicted); 0 mismatches | items/0015 |
| B8 | boxes 4..15: page 0 with room, ground without; 0 mismatches | items/0013 § 11 |
| Exp-state | 3 monster-kills-converted cases credit the `0x800` list's owner, separating; a converted killer not reached | player/0002 § 11 |

`inventory_check.py` 73 predictions, 0 mismatches; `player.py check` 6 kills, 0 mismatches. Gate green. The slot is
clean (`saves.py --slot 1 status`: no aside, harness idle).

**P12: not separated (owner ruling 2026-11-15, option (a)).** The Nova session cannot give a fresh bit-0-only word: its
path's cached word at `+0x7C` makes `PathCellCollision` (0x00648EB0) return the cache, so `CollisionTest` never runs at the
missile's own point (all `MMC` of class 90 carry a non-zero `+0x7C`). The owner ruled to accept "not separated" for the bit-0
word and not to run a zero-velocity missile session with another character; the lane ran the staged session once to keep
the record. `run:2026-11-15-sweep8-p12` (slot 1, seed 3, `p12.gdb`, kept log `2026-11-15-sweep8-p12-s1-3-p12.log`,
`manifest-p12.sha256`): `sweep8_check.py p12`: 11 546 `MMC`, all cached words, 156 at a grid bit-0-only point whose cached word
steps on (counted, decides nothing), 0 separating, 0 against the grid reading, 0 mismatches; verdict "not separated (no fresh
bit-0-only word)". Neither reading is confirmed: the statement stays as the specs hold it, with the cause named. Whether the
blank-`Vel` rows (firestorm, `fireexplosion`, `[I]`) take the fresh branch stays untested, by the owner's ruling. P12 backlog
entry: annotated for the architect to close. **Review request:** Tier A for P12 (backlog entry filed with this entry).

**Short:** the converted-monster-kills branch of the exp-state case; `spike1` above level 1.

**Review request:** Tier B for the batch; Tier A for P12 (backlog entries filed with this entry).

### 2026-11-15 — Phase 1 review (architect, Tier A: P12 a verdict lane, and the audit of the fifth Tier B lane since `lane/n65p`, `lane/n65h`)

No game, no Ghidra (the owner's quiet machine); one objdump read of 0x00648EB0 and 0x00650910.

- **Verdict: accept with fixes** (13 fixes: overclaim 1, misread 1, omission 3, wrong anchor 2, stale cross-reference 5,
  other 1), all written into the documents named; gate green.
- **Re-checked.** `manifest.sha256` (24 lines) and `manifest-p12.sha256` pass from the repository root; every check
  output matches the counts the findings and this log give (`c2` 3/3, `h2` 4 blends 4 separating 6 fresh 2 frees, `h3` 6
  flagged 2 separating, `b8` 12 + 12 moved, `xs` 3/3, `inv` 73, `player` 6, `p12` 11 546 / 10 522 / 156); the tools did
  not change between the run's revision `5c55b73d` and `116d7239`. `XSF`/`XSR` give `[0, 3, 1]`, the Paladin, on the three
  state kills.
- **P12 (Tier A): not separated, accepted under the owner's ruling (a).** The image holds the lane's cause:
  `cmp [esi+0x7c], 0; jne 0x00648EDD` returns `+0x54`, and `+0x54` is the path move's word (0 at 0x00650957, the
  return of 0x0064EE70 at 0x006509A5), not a test of the own cell under `0x7FFF`. So the 156 grid bit-0-only steps are what
  both readings predict and decide nothing; D3 stays `[I]` and P12 stays an open question of skills/missiles with the
  cause named. The "a Nova can never give a fresh word" of the checkpoint is a count over two logs (27 305 `MMC`), not a
  reading of `+0x7C`'s writer: it is recorded as the logged count only (path/0007). Backlog entry closed.
- **The exp-state remainder (a converted monster that kills): no rerun.** That branch is § 4's first `if`, the same code as
  the emulated `state-killer` tag (run:2026-11-03-party-emu); play would add only whether such a kill reaches
  `XpCreditPlayer` with the state on. It stays in player/0002's Open questions, out of this plan; the a68 entry is closed.
- **Spec-writer retag (items/use, items/inventory after H2, H3, B8; skills/missiles C2 and D3; player/party).** Already
  routed: Phase 3 of this plan names each one, so no new entry. Phase 3's done-when covers Phases 1 and 2; whether it may
  take Phase 1's set before Phase 2 runs is the owner's call.
- **Fixes (13).**
  1. *Overclaim:* items/0015 H3's `[C]` held the reason for the mp1 `0x61` click ("a client refusal before the logged
     function"); now its own `[I]` bullet with the client site 0x0049356E (reverser rule 1).
  2. *Misread:* player/0002 § 11 said the `xs` walk started from the Cold Plains; `sweep8_sessions.py` walks out of the camp
     into the Blood Moor (`LEAVE_TOWN`).
  3. *Omission (rule 14):* the run compares the logged returns or effects of `sub_0057E7B0_XpCreditPlayer` (`XSR`, 6 of 6),
     `sub_005608C0_BeltOverflow` (24 of 24 moves) and `sub_00562390_PlayerUseBeltItem` (6 flagged uses); raised to C in
     `re/symbols.csv` and the Functions tables (player/0002, items/0013, items/0015, items/0012, skills/0015), with scope.
  4. *Omission (rule 10):* path/0007's P12 addendum was untagged and did not say what the cached word had been through;
     now a `[C]` count and an `[I]` reading with 0x00648EB7, 0x00650957, 0x006509A5.
  5. *Omission:* the `run:2026-11-15-sweep8-p12` record named no save, steps, command, tool revision or check counts; written,
     and the runner output `p12.out` added to `manifest-p12.sha256` (4 lines).
  6. *Wrong anchor:* items/0015 H3's flagged `0x26` claims were anchored to `MercGiveCursorItem` (`0x61`); now
     `fn:sub_00562390_PlayerUseBeltItem@0x00562390` and 0x00562453 beside it.
  7. *Wrong anchor:* items/0015 H2's blend was anchored to the `ItemUse` dispatcher; now
     `fn:sub_005BE3F0_ItemUsePotion@0x005BE3F0`, 0x005BE480, 0x005BE6C1.
  8. *Stale cross-reference:* items/0017's summary, H2, H3 and B8 entries, route table and Open question still said
     unrun; annotated.
  9. *Stale cross-reference:* items/0012's `0x26` and `0x61` readings, the live-potion note and the Open question ("the
     blend open"); annotated.
  10. *Stale cross-reference:* items/0013 § 4's `BeltOverflow` bullet; pointer to § 11.
  11. *Stale cross-reference:* skills/0002's *Leads used* `VelLev` verdict, § 11's remainder and § 12's C2 bullet; pointers to
      § 14.
  12. *Stale cross-reference:* the `exp`-state Open question of player/0002 kept the whole case open; the victim half
      is now marked answered.
  13. *Other:* skills/0002 § 14 wrote the velocity as `… << 8 * 75`, which a C reader parses as `<< 600`; parenthesised,
      and the level-1 limit said (the term is 1 under any order of product and division). items/0013 § 11's "(4 each)"
      reworded; the `sweep8-single` record's "open on an owner question" updated; player/0002 § 11's unreached
      bullet given its anchor (gate W1).
- **Backlog.** Closed: C2, P12, the 0060 live cases, a68, and this review request (`tools/backlog.py close`, then
  `archive`: links rewritten in five findings, plans and specs, paths only).
- **Audit (ADR-0023).** No reject-grade problem. A Tier B check would likely have found fixes 3 and 6 to 12 (rules 14 and 20,
  the anchor spot-checks, passes 7 and 8) and fix 2 (`LEAVE_TOWN` is in the diff). Fix 4 needed the image read outside a
  diff-scoped pass; fix 1 is rule 1's wording, a check reading the statement would see it. Fix 6 is the closest to a
  blocking anchor; the function it named is real and covers the bullet's last sentence, so it is not reject-grade.
- **Ledger cells:** `architect-review`, Fixes `audit of lane/n65h: overclaim 1, misread 1, omission 3, wrong anchor 2,
  stale cross-reference 5, other 1`; no reject-grade miss. **Promotion:** every fix is an existing rule (reverser 1, 10,
  12, 14, 20), so no rule added.

### 2026-11-15 — Phase 2 start (two-client batch), `lane/n65i` (reverser, slots 1 and 2): predictions and session list, written before any kept log

Branched from `main` `712c49e6`. **Port-4000 precondition re-read first** (multiplayer/0001 § 5): step 1 (confirmed existing
block) is the owner's `sudo ufw status verbose` of 2026-11-10 (active, deny incoming, no rule for 4000/tcp), kept as
`workspace/logs/n65i/ufw-owner-2026-11-10.txt` with its no-root baseline (`ufw-baseline.sha256`, the eight files, the same
hashes as run:2026-10-20-two-clients and run:2026-11-10-trade). Re-read today before any hosting: `tools/ufwcheck.sh`
`UFW-OK` (ufw active and enabled, `DEFAULT_INPUT_POLICY="DROP"`, `ENABLED=yes`, all eight hashes unchanged), and no listener on
4000 before the first launch. Nothing changed since the owner's listing, so step 1 still holds and no root step is repeated;
`ufwcheck.sh` runs at the head of every session's driver (`two.sh`, log `<session>/ufw.log`).

**Predictions: the Phase 0 staging table above (rows 7 to 13, 15, 17 to 19), unchanged, and `tools/sweep8_check.py predict`.**
No prediction is edited by this entry; a case that does not separate its readings is named as such in the run record.

**Session list** (one fresh pair of processes per session; saves from `tools/mp_saves.py build`, Normal, expansion, TCP/IP over
127.0.0.1; drivers kept in `workspace/logs/n65i/drivers/`, adapted from run:2026-10-20-two-clients' `workspace/logs/p44h-run/drivers`):

| Session | Rows | Pair | Logger | Checks |
|---|---|---|---|---|
| `mp25` | 12 | MpNovaHost, MpPalConv | `two-combat.gdb` | `mp_check.py aura`, `combat.py check` |
| `wounds` | 18, 19 | MpPvpHost, MpWoundJoin | `two-wounds.gdb` | `combat.py check`, `stats.py check`, `mp_check.py gates` |
| `mp30` | 15 | MpNovaHost, MpScrollJoin | `two-quests.gdb` | `mp_check.py leave` |
| `mp18` | 10 | MpNovaHost, MpSockJoin | `two-sockets.gdb` | `sockets.py` |
| `gold`, `goldfull` | 17 | MpNovaHost, MpGoldJoin / MpGoldFull | `two-gold.gdb` | `mp_check.py gold` |
| `kills-a` | 7 | MpMercHost, MpTankJoin | `two-kills.gdb` | `mp_check.py xpshare`, `player.py check` |
| `kills-b` | 8 | MpMercWeak, MpTankJoin | `two-kills.gdb` | same |
| `pk` | 9 | MpNovaHost, MpNovaWeak | `two-kills.gdb` | `player.py check`, `mp_check.py xpshare` |
| `rooms` | 11 | MpNovaHost, MpTankJoin | `two-rooms.gdb` | `mp_check.py rooms`, `monspawn.py check` |
| `portal` | 13 | MpDurHost, MpDurClosed / MpDurOpen | `two-quests.gdb` | `mp_check.py portalquest` |

MP31 (row 16) is met by run:2026-11-10-trade; MP28 (b), (c) are postponed by the owner (Phase 0 review). A session that needs
a driver fix is first a development session (`dev-` log, outside the manifest); the kept session is run again from a fresh
install. The first development session, `mp25` on `two-combat.gdb`, showed the three aura cases (hostile passes, partied and
neither refused, 0 mismatches) and that `party hostile` is refused in effect when the host is not yet in town; the driver
now checks both levels first.

### 2026-11-16 — Phase 2 (two-client batch), `lane/n65i` (reverser, slots 1 and 2), partial: checkpoint with a resume note

Record [run:2026-11-15-sweep8-two-clients](../findings/multiplayer/experiments.md#run2026-11-15-sweep8-two-clients); checks and manifest
(77 lines) in `workspace/logs/n65i/`. Port-4000: the owner's 2026-11-10 listing plus the no-root baseline, `UFW-OK` before every launch.
Both slots clean (saves restored, harness idle).

| Row | Case | Result |
|---|---|---|
| 12 | MP25 offensive (Conviction) | 44 `AF`: hostile 15 passed, neither 16 and partied 13 refused; 0 mismatches. Raised in part (Conviction only) |
| 18, 19 | open wounds on a player; the shield flag | 24 applications on a player, 1 857 ticks, 62 events, 0 mismatches; 28 `DRB` `sh` 0: the shield-held branch is not run. Raised in part |
| 15 | MP30 | leave order met, 0 mismatches; the e9 count drop not reached (callback returned early) |
| 11 | MP20, MP21 | 5 996 `RP` rows, 6 separating, 0 mismatches; MP20 attribution 6 of 14 activations |
| 9 | 0058c a player kills a player | the victim died, 0 `XK0`: prediction not met, `[I]` (no control in the session) |
| 8 | 0058b a dead killer | not reached (the host did not die, two sessions); 48 merc kills as samples, 0 mismatches |
| 7 | 0058a, MP16 | not reached (driver started in the Act IV town; three dev launches) |
| 10 | MP18 | not run (`mp18.sh` written) |
| 13 | MP27 a, b | not run: the pilot found no Kurast Docks waypoint |
| 17 | MP32, MP32 full | not run: the pilot has no ground-pile pickup |
| 16, 14 | MP31, MP28 (b), (c) | met by run:2026-11-10-trade; postponed by the owner |

Mismatches over the run: 0 in every check that had data (`aura`, `combat`, `stats`, `leave`, `rooms`, `monspawn`, `xpshare`, `player`).
Tool change: `tools/mp_check.py rooms` skips a `null` act of an `RP` line (it crashed on the first real log).

**Resume note** (the lane stopped at its token budget, not at a blocker). Drivers are in `workspace/logs/n65i/drivers/`. Next lane:
(1) `kills.sh a`: wait until `where` shows both players before `meet.sh`, then the Act I waypoint; the host's explore with the
joiner parked. For the far case, hop the host more than 80 sub-tiles away while the Rogue fights. (2) `kills.sh b`: the host must
die, so try `--walk` into a pack at Cold Plains, or leave the Rogue dismissed until the host stands among monsters. (3) `mp18.sh`
as written (trade, pick the rune up, click the cap). (4) `portal.sh`: needs the Kurast Docks waypoint position (read it from a
kept Act III log or add it to `--wp-at`). (5) MP32: a pile pickup, for example a click at the `KILL` position of a monster killed
by the host. The `pk` case wants a control (any monster kill in the same session). The Phase 3 re-tag may take what Phase 2
raised now (MP25, MP21, open wounds); the owner decides whether the rest runs.

**Review request:** [Tier B](../backlog/2026-11-16-reverser-architect-review-plan-0065-p2-two-clients.md).
