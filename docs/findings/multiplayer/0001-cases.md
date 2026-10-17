# 0001 — Multiplayer cases: the two-client branches of the reviewed specs, and how to stage them

> **Subsystem:** cross-cutting (plan 0044; the owning rows are named per case)
> **Question:** for each multiplayer branch that a reviewed spec reads from the code, which server entry point runs
> it, what two clients must do to reach it, which logger already sees it, and what the model predicts?
> **Date:** 2026-10-17   **Plan:** 0044   **Status:** open (Phase 1 case list; Phase 2 runs it)

## Answer (summary)

- **32 cases: 29 stageable, 3 not.** The not stageable ones need more than two players in one party (MP02, MP03) or a
  player with no room, which no input holds open (MP05). Of the 29, three have no prediction yet: their code is not
  read (MP25 auras, MP31–MP32 trade and gold, plan 0043). One depends on whether the stock client sends the packet
  at all (MP18). Two may need owner play: MP17 (the Ancients) and MP14 (a joiner death in Andariel's level).
  § 2 maps every source row to its cases.
- **Coverage.** All 14 d-2c rows of plan 0038's inventory have a case, and so do the four partial halves (tc 27,
  sockets 22, quest-drops 25, player/creation 33). The other sources covered: the eight multiplayer open questions
  of *Context*, plans 0040–0043 (0041's party auras, 0043's trade and gold), plan 0042 Phase 1 (the portal party and
  quest gates, party credit, the join and the leave events), and the contradicted hostility lead. Plan 0039 routed
  nothing here by name. The d-2c count is recomputed in § 2.
- [I] **The host binds every listening socket to all IPv4 interfaces.** `bind` is called from two places,
  0x006C321D and 0x006C3C26. Each passes a `sockaddr_in` that it zeroed itself: family 2 (`AF_INET`), port
  `htons(arg)`, address 0 (`INADDR_ANY`). There is no IPv6 socket: every `socket` call uses family 2, and `inet_addr`
  `WSASocket`, `getaddrinfo` and `inet_pton` are not imported. Run:2026-10-12-two-clients saw the listener on TCP
  4000. So the Phase 2
  precondition concerns IPv4 TCP 4000 on every non-loopback interface. (0x006C31F8–0x006C321D,
  0x006C3BF4–0x006C3C26, § 5)
- [I] **The travel gates read the operator's own tick.** The waypoint packet waits for the player's PlayerData
  `+0x160` plus 10 000 ms. The portal operate waits for the operator's own `+0x160` plus 5000 ms. Both call
  `0x0055B6C0` with no other player (EDX = 0). The only writer called is `0x0055B720`, from the hostility
  declaration `0x005A5E50`. So the delay starts when the player declares hostility, and no portal is exempt, the
  operator's own included. Plan 0042 Phase 1 (lane/p42r) read "an own portal is never delayed"; § 4 corrects
  that. (0x0054C5FC–0x0054C612, 0x005848B7–0x005848CF, 0x0055B6C0–0x0055B715)
- [I] **Declaring hostility** requires the declarer to stand in a town, and base character level (stat 12,
  `STATS_GetUnitBaseStat`) 9 or more on both players; a declaration toward a player not yet hostile also needs the
  other's full level (`STATS_GetUnitStat`, stat 12) at 9 or more. For that pair it writes a stamp of `GetTickCount() + 60000`, and a second declaration before that
  stamp is refused. It also sets the declarer's `+0x160` to `GetTickCount()`, closes the declarer's town portal,
  and leaves the party when both players are in the same one. (0x005A5E5F–0x005A5E9D,
  0x005A5EE4–0x005A5EFF, fn:sub_006426A0_LevelIsTown@0x006426A0, 0x005A5F0F–0x005A5F96, § 4)
- [I] **A player hostile to anyone cannot use a portal it does not own.** The portal operate tests this before the
  5 s gate. Plan 0042 Phase 1b left this claim of the lead as not covered. (0x0058488F–0x005848B1,
  0x00535B10–0x00535B44, § 4)
- **Driver.** `tools/d2pilot.py join` runs one client from the host's log: `where`, `follow`, `party
  invite|accept|leave|hostile` (plan 0011's steps files plus `two-party-hostile.steps`), `leave` and `trade
  TOKEN…`. `--me` on any other command (`wp`, `npc`, `explore`) also steers by the new `PLRS` lines of
  `tools/gdb/two-players.py`. Game-free tests: `tools/test_joiner.py`, 16 OK. Not yet live-tested: see the plan log
  checkpoint.

## Leads used

No source was fetched in this phase. The contradicted lead re-read in § 4 is plan 0042 Phase 1b's verdict on lane/p42r.
That lane is under review and its source entry is not on `main` yet. Leads used only to locate code: none.

## Functions

Read for the first time in this finding. No symbol rows were added. Lane/p42r's proposed names are quoted so the
merge keeps them (review fix 5).

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x006C3B50` | (unnamed) | creates a TCP socket (`socket(2, 1, 0)`), sets options, `bind(INADDR_ANY:port)`, `listen(s, 25)`; port from EDX | I |
| `0x006C321D` | (call site in an unnamed function) | the other `bind(INADDR_ANY:port)`, then `listen(s, 250)` | I |
| `0x0055B6C0` | `PlayerTickGet` on lane/p42r | (player, other): other = 0 → PlayerData `+0x160`; else the stamp of other's entry in PlayerData `+0x38` | I |
| `0x0055B720` | `PlayerTickSet` on lane/p42r | (player, other, value): the pair entry's stamp ← value; PlayerData `+0x160` ← `GetTickCount()` | I |
| `0x005A5E50` | (unnamed; one reference, the table entry `0x006E2228`) | the hostility toggle between two players | I |

## Walkthrough

### 1. How a case runs

Each case is a two-client session as ADR-0008 decides it. The owner's condition puts host and joiner on two non-zero
slots. The host runs the server game with gdb attached and its logger. The joiner has no debugger, so its driver
reads both players from the host's log (§ 3).
A case names:
- **Entry:** the server entry point. Each `fn:` anchor was checked to start a function in the pinned binary: all 38
  follow `int3` padding or a `ret` (command in § 2). The column's 13 bare addresses are five function starts
  (0x00539DA0, 0x0054C5D0, 0x00554630, 0x00584870, 0x005A5E50, checked the same way) and eight sites inside cited
  functions (for example 0x0055A8E4, the clamp in `TC_ResolveDrops`).
- **Condition:** what the two clients do.
- **Logger:** the existing logger that sees it, and its checker.
- **Expected:** what the reviewed reading predicts.
- **Stage:** whether it can be staged, and the driver steps. "J" is the joiner and "H" the host. Party actions are
  `d2pilot.py join … party …`.

Characters are tool-built (ADR-0008). Every case that declares hostility needs both characters at level 9 or more
(§ 4). Recipes with two distinct names are an archivist request (backlog).

### 2. The case list

**Count, kept command.** The 14 d-2c rows are the inventory rows that have a cell exactly equal to `d-2c`. Five
more rows mention d-2c in their notes: tc 27, sockets 22, quest-drops 25 and player/creation 33 (the partial
halves), and monsters/pool 1. Plan 0038 re-classified pool 1 as d-none because `GameCreateA` has no caller, so it is
not a case here.

```text
grep -H "^| [0-9]" docs/plans/0038-inventory/*.md \
  | awk -F'|' '{for(i=2;i<=NF;i++){g=$i; gsub(/^ +| +$/,"",g); if(g=="d-2c"){n++; break}}} END{print n}'   # 14
```

**Entry check, kept command** (`objdump -d -M intel --no-show-raw-insn workspace/install/app/game.exe > game.asm`,
then for each entry address *a*: `grep -m1 -B1 "^  a:" game.asm`). For all 38 `fn:` anchors cited below and the five bare
function starts, the line before is `int3` or `ret`; the other eight bare addresses are sites, not entries.

#### items/tc (NoDrop with real players)

| Case | Source | Entry | Condition | Logger | Expected | Stage |
|---|---|---|---|---|---|---|
| MP01 | tc 43 (dead member), tc 44 (dead) | fn:TC_ResolveDrops@0x0055A6D0 → fn:sub_005408E0_PartyCountInLevel@0x005408E0 → fn:sub_005404F0_PartyCountAliveCb@0x005404F0 | H and J partied in one level, J dead (corpse, before it respawns), H kills | `tc-party.gdb` (PLR dead bit, PTY, PARTY); `tc.py replay` | party = 1, `PlayerCount` = 1 (a dead player is not counted), n = 1 | yes: J is killed in the field (a hostile H, MP23, or a pack), then H kills before J respawns |
| MP02 | tc 43 (more than two players), tc Open questions | as MP01 | three or more partied players | — | — | **no**: a third client exceeds ADR-0008's two and the memory budget; `/players` stands in for `PlayerCount` only, not for the party count |
| MP03 | tc 43 (the clamp at 8) | fn:TC_ResolveDrops@0x0055A6D0 at 0x0055A8E4 (the clamp) | eight partied players in the killer's level | — | — | **no**: needs eight clients |
| MP04 | tc 43 (monster killer → owner), tc 27 (party half) | fn:sub_0058F0D0_MonsterOwner@0x0058F0D0, then MP01's path | H's hireling (or J's summon) kills, the other player partied in the level | `tc-party.gdb` (KILL `ktype` 1); logger addition: the owner unit (MonsterOwner's result) on the KILL line | party = 2, counted from the owner | yes: `mercnova`-type recipe for H; J `follow` |
| MP05 | tc 44 (member without a room) | fn:sub_005404F0_PartyCountAliveCb@0x005404F0 | a partied player with no room when the other kills | `tc-party.gdb` (PLR `lvl` −1) | skipped, party = 1 | **no**: a player has no room only while its act loads, and no input holds that open. Logged if a session meets it |
| MP06 | tc 46 (`/players` with real players) | fn:sub_00535790_PlayerCount@0x00535790 | H and J alive; H types `/players 3`, then `/players 1`, then `/players 8`; J types `/players 5` | `tc-party.gdb` (PLAYERS, PARTY); `tc.py replay` | `PlayerCount` = max(2 alive, H's setting); n = party + (count − party) ÷ 2. J's `/players` changes nothing: the setting is a global of the process (data:g_PlayersOverride@0x00883D70), and the server runs in H's process | yes |

#### items/vendors (the town's other player)

| Case | Source | Entry | Condition | Logger | Expected | Stage |
|---|---|---|---|---|---|---|
| MP07 | vendors 1, 16 | fn:sub_00537580_TownPlayerRemove@0x00537580 → fn:NPCSTORE_ActStale@0x00537230 | stores of the act built; J leaves the game from an Act I–IV town. (a) H in the same town; (b) H outside town in that act | `vendors.gdb` (STALE/STALEX with ret 0x005375FC, RESET) | (a) `townEmpty` 0: only stores built more than 240 000 ms earlier are marked stale; (b) `townEmpty` 1: each built store is reset, or cleared if its NPC unit is gone | yes: `join leave` (or `slots.py stop` on J's slot, a dropped connection; record which) |
| MP08 | vendors 16 (Harrogath) | as MP07 | J leaves the game from Harrogath (109) | `vendors.gdb` | no STALE line from 0x005375FC: 109 is missing from the switch | yes |
| MP09 | vendors 10 | fn:NPCSTORE_FindRec@0x00535EA0, fn:NPC_TradeOpen@0x00579430 | H opens a store (it builds); J opens the same NPC's store | `vendors.gdb` (TO, BS0); `vendors.py` | J's open finds `built` = 1: no BS0, the same stock | yes |
| MP10 | vendors 13 | fn:NPC_MenuAction@0x00579D60 (0x00579E08) → fn:sub_00572DA0_NpcInteractCount@0x00572DA0 | a stale store (H built it, waited more than 240 s, changed act and came back); H and J both talking to the NPC; H opens the trade | `vendors.gdb` (MA, TO `sole`, RESET, BS0) | `sole` = 0: the stale stock is kept, with no RESET and no BS0. Then J ends its talk and H re-opens: `sole` = 1, RESET, then BS0 | yes (about 5 minutes per pass) |
| MP11 | vendors 17 | fn:NPCSTORE_ActStale@0x00537230 | J alone in town with an NPC's trade window open, H outside town in that act; J leaves the game with the window open | `vendors.gdb` (PIEND, STALE) | from the logged `NpcInteractCount`: 0 → RESET; otherwise `stale` ← 1. The order of PIEND and STALE shows which branch ran | yes. If PIEND always comes first, the branch with an interactor stays unreached; name it as a shortfall |

#### items/quest-drops

| Case | Source | Entry | Condition | Logger | Expected | Stage |
|---|---|---|---|---|---|---|
| MP12 | quest-drops 6, 25 | fn:sub_005B5C10_A4Q3_ForgeOperate@0x005B5C10 → fn:sub_005B6710_A4Q3_ForgeWave@0x005B6710 | H strikes the forge for the third time. J is in Act IV with word 27 bits 0 and 1 clear; counter case: J with bit 0 set | `quests.gdb` (QDI forge data `n`, QGS); `questdrops.py check` | `n` = 2 gives 2 gems per wave (8 `QuestPick(7)` draws), then the rune in expansion; J gets bits 13 and 1. Counter case: `n` = 1 | yes (plan 0032's forge saves, one per player) |
| MP13 | quest-drops 12, tc 27 | fn:QUESTS_PlayerRecord@0x00543520 (B6) | H kills a `TCQuestId` boss (Andariel) with J partied nearby. The two hold opposite word states, then swap | `quests.gdb` (B60, B6P, B6G, B6X) | the record read is the resolved killer's only (B6P `rec` = H's); the TC follows H's bits | yes (`questb6`-type recipes, two states) |
| MP14 | quest-drops 36 | fn:sub_00596210_A1Q6_SetKilled@0x00596210 → fn:sub_005537D0_GameForEachUnit@0x005537D0 | Andariel dies with J in level 37: (a) alive; (b) dead (state 7) | `quests.gdb` (QS per record) | (a) J's word 6 gets bits 13 and 1; (b) no write to J's record | yes; (b) needs J to die in level 37. Owner play is the fallback |

#### hirelings, player/creation, items/sockets-runewords, items/quality

| Case | Source | Entry | Condition | Logger | Expected | Stage |
|---|---|---|---|---|---|---|
| MP15 | hirelings 11 | fn:HIRE_SendList@0x00576770 | H opens a hire list (Kashya: it builds); J opens the same list | `hirelings.gdb`; `hirelings.py` | one build per game; J receives the same entries | yes |
| MP16 | player/creation 6, 31 | fn:XP_OnMonsterKill@0x0057E990 → fn:XP_PartyShare@0x0057E6C0 → fn:sub_0057E5A0_PartyXpCollect@0x0057E5A0 | H kills, partied with J: (a) in the same level within distance² 6400; (b) same level, beyond that; (c) another level; (d) not partied; (e) J dead | `player.gdb` (XK0, XA0 for each grant); `player.py` (the checker needs J4's party branch) | (a) J4: `total = exp + (n − 1)·exp·89 ÷ 256`, split by level, `ftol`; (b)–(e) the killer alone | yes; at least 20 shares |
| MP17 | player/creation 33 (party half of J2) | fn:sub_0058C9A0_A5Q5_AncientDeath@0x0058C9A0 → fn:sub_0058C7E0_A5Q5_SummitExpGrant@0x0058C7E0 → fn:sub_0058C6D0_A5Q5_PartyExpGrant@0x0058C6D0 | H at the summit (level 120) kills the last Ancient. J is partied in another Act V level, with word 39 bit 0 clear and base level ≥ 20·(d + 1); counter case: J below that level | `player.gdb` (XA0), `quests.gdb` (QS word 39) | J granted once; bit 0 set before the grant; nothing for the counter case | yes, but the Ancients are hard to script; owner play is the fallback |
| MP18 | sockets 22 (trade part) | fn:SOCK_PacketInsert@0x0054B650 (0x0054B6DB–0x0054B6F4) | J in an open trade with H tries to put a rune into a socketed item of its own inventory | `sockets.gdb` (PKT, INSX) | no `ITEMS_InsertSocket` call (no INSX) and no error 3 | conditional: only if the stock client sends packet `0x28` with the trade window open. If it never does, the branch needs a forged packet (d-edit) |
| MP19 | items/quality Open questions (multiplayer) | fn:ITEMS_DropMagicFind@0x005585D0 | J kills, partied with H, where H wears MF gear (`uniqnova`, 472) and J wears none | `tc-drops.gdb` (quality lines); `quality.py` | the MF is J's stat 80 (plus J's owner if J is a summon), never H's | yes |

#### monsters, objects, drlg (rooms the joiner activates)

| Case | Source | Entry | Condition | Logger | Expected | Stage |
|---|---|---|---|---|---|---|
| MP20 | monsters/spawn and objects Open questions (multiplayer) | fn:sub_0066EE40_DrlgRoomReseed@0x0066EE40 and the population passes | J explores rooms H never reaches (`explore --me join`) | `mon-spawn.gdb` + `objects.gdb`; `monspawn.py check`, `objects.py check` | 0 mismatches with no player term (spawn reads no player count) | yes |
| MP21 | plan 0040 (activation with two players) | fn:sub_0061B390_DrlgRefAddNear@0x0061B390, fn:sub_0061A910_ActiveRoomFree@0x0061A910 | H and J in one level, more than three rooms apart, then one leaves | plan 0040's lifecycle logger (when merged), else `drlg-roomk.py` RRESEED | the active set is the union of the two near lists; a shared room is freed only when both have left | yes |
| MP22 | monsters/stats (player-count terms with real players) | fn:sub_00573930_MonPlayerBonus@0x00573930 | no `/players`: monsters made before J joins, while J is in the game, and after J leaves | `mon-stats.gdb` (SI1 `players`); `monstats.py check` | 1 / 2 / 1 players, so HP and XP +50 % only while J is in; stat 100 keeps its creation count | yes |

#### combat, stats/states and the hostility gates

| Case | Source | Entry | Condition | Logger | Expected | Stage |
|---|---|---|---|---|---|---|
| MP23 | combat/0001 § 12 (player against player) | fn:COMBAT_MeleeHitTest@0x0057EC10, fn:COMBAT_DamagePercent@0x0057C060, fn:sub_00554200_UnitsHostile@0x00554200 | H and J hostile (MP24), outside town, attack each other (Nova); then one stands in town | `combat.gdb` (players on both sides); `combat.py check` | P = 17 % on every scaled field; stat events and leech with D = 100; a defender in town takes no damage (0x0057C6D5–0x0057C78E) | yes; at least 200 events |
| MP24 | the contradicted lead (portal 5 s, waypoint 10 s), plan 0042 | `0x005A5E50`; waypoint 0x0054C5D0; portal operate 0x00584870 | J, in town, declares hostility to H (`party hostile`), then: J's town waypoint at once, again after 10 s; J, still hostile, clicks H's town-end portal (the hostility test refuses); J declares, withdraws at once, and is invited back, then clicks H's portal within 5 s and after (the gate, then nothing); J walks out of town, opens a portal and uses it (likely past 5 s; the `tk` gap is logged); J declares again within 60 s; counter cases: J below level 9, J outside town | `two-players.py` (PLRS `tk`, `hl`); logger addition: the two gates' compare inputs and outcome (0x0054C60F, 0x005848CD) and the declaration (0x005A5E50 entry, its 0x005A5F22 refusal) | § 4: the hostility test refuses portals J does not own; the gates close until `tk` + 10 000 / 5000; the pair stamp is `tk` + 60 000; the repeat is refused; J's portal closes and J leaves the party; the counter cases change nothing. The withdraw step depends on the un-declare path (not read): log `tk` around it | yes |
| MP25 | plan 0041 (party auras, hostile states) | fn:EVENT_SelectedAuraTick@0x0056FCB0 → fn:SKILLS_ForUnitsInRange@0x0056B7E0 → fn:AURA_ApplyToTarget@0x005CEDC0 | J is a Paladin with an aura. H in range: (a) partied; (b) not partied; (c) hostile | `combat.gdb` / plan 0041's state logger | **no prediction yet**: which `aurafilter` bits pass a party member or a hostile player is not read (stats/0002 names the filter only) | yes, as an observation; the reading is a static request (backlog) |

#### quests and travel (plan 0042 Phase 1, lane/p42r)

| Case | Source | Entry | Condition | Logger | Expected | Stage |
|---|---|---|---|---|---|---|
| MP26 | plan 0042 P1 (the portal's party gate) | portal operate 0x00584870 (party id `0x00554630`) | H opens a portal in the field and goes to town; J (a) not partied, (b) partied, clicks H's portal | plan 0042 P2's travel logger (OBJOP_Portal in and out) | (a) refused; (b) J moved to the field end | yes |
| MP27 | plan 0042 P1 (the portal's quest gate) | 0x00584870 (0x005849BB–0x00584A19) | H's portal from a `QuestFlag` level (101, word 21; expansion `QuestFlagEx`); J partied, word bit 0 (a) clear, (b) set | as MP26 | (a) refused, (b) allowed; H's own end is not tested | yes (built quest words) |
| MP28 | plan 0042 P1 (party credit) | `PartyCredit` of each quest via fn:sub_00540510_PartyForEach@0x00540510 (Den of Evil: 0x00590175, 0x0059017F) | H completes the Den with J partied (a) in an Act I level, (b) in Act II, (c) not partied | `quests.gdb` (QS) | (a) J gets bits 13 and 1; (b), (c) nothing | yes |
| MP29 | plan 0042 P1 (the join) | fn:sub_00546270_QuestsPlayerJoin@0x00546270 | H creates the game with some quests finished; J joins with others finished | `quests.gdb` + plan 0042 P2's join lines | the game record and deactivations come from H alone; J's join changes neither | yes |
| MP30 | plan 0042 P1 (e9, e10) | fn:sub_00543BD0_QuestsInvItemEvent@0x00543BD0 (from 0x00539DA0) | J holds a quest item (`bks`) and leaves the game | `quests.gdb` | e9: the item's quest count drops by 1 (the last scroll resets word 4's state); e10 removes J from the private lists | yes |

#### economy (plan 0043, in flight)

| Case | Source | Entry | Condition | Logger | Expected | Stage |
|---|---|---|---|---|---|---|
| MP31 | plan 0043 (trading between players) | not read on `main` (plan 0043 Phase 1 on lane/p43r) | H and J trade an item and gold (`join trade request`, `accept`, `give:…`, `ok`) | to be named by plan 0043 | **no prediction yet** | yes, as driver steps; the expected outputs wait for plan 0043's reading |
| MP32 | plan 0043 (shared gold in a party) | as MP31 | partied players pick up gold | as MP31 | **no prediction yet** | as MP31 |

**Coverage.**

| Source | Cases |
|---|---|
| tc 43, 44, 46; tc 27 | MP01–MP06; MP04, MP13 |
| vendors 1, 10, 13, 16, 17 | MP07–MP11 |
| quest-drops 6, 12, 36; 25 | MP12–MP14; MP12 |
| hirelings 11 | MP15 |
| player/creation 6, 31; 33 | MP16; MP17 |
| sockets 22 (trade) | MP18 |
| items/quality, monsters/spawn, objects, monsters/stats, combat § 12 | MP19, MP20, MP20, MP22, MP23–MP25 |
| plans 0040, 0041, 0042 P1, 0043 | MP21; MP25; MP24, MP26–MP30; MP31–MP32 |
| the contradicted lead (portal 5 s, waypoint 10 s) | MP24 |
| plan 0039 | none: its plan routes "two clients (plan 0044)" only as a class of questions it leaves out, with no item named |

**Sessions for Phase 2** (they reach the plan's minimum counts):
1. Kills with drops (MP01, MP04, MP06, MP16, MP19, MP22): 100 party kills, 20 shares.
2. Vendors and hirelings (MP07–MP11, MP15): 30 store events.
3. Quests (MP12–MP14, MP26–MP30): 10 quest events with both players present.
4. Hostility (MP23, MP24): 200 attack events.
5. Rooms (MP20, MP21).

MP17 and MP25 come last. MP31–MP32 wait for plan 0043.

### 3. The joiner's driver

- [I] **The PLRS line** (`tools/gdb/two-players.py`). At most every 0.25 s, at the player-mark breakpoint
  (0x0064EA90, mask 0x80) and the path breakpoint (0x00648C30), the host's logger lists every player unit of the
  server game. Per player: id, class, mode, sub-tile position, room, level id and dead bit, from the offsets
  tc-party.py uses. Also the travel tick PlayerData `+0x160` and the hostility list `+0x38` (§ 4), and the party
  list. The pilot's PLR line alternates between the two players' marks in a two-client game, so `--me` ignores it.
  (fn:COLL_PatternMark@0x0064EA90, struct:Unit+0x0E4, fn:UNIT_GetPlayerData@0x006221A0)
- **Modes.**
  - `join <log> where` prints both players.
  - `follow` walks (or, with `--teleport`, teleports) the joiner to within `--near-lead` sub-tiles of the leader. It
    says `level` when the two are in different levels.
  - `party invite|accept|leave|hostile` replays plan 0011's steps files on that client's slot and waits for the
    effect in the log: the shared party id, no party, or a changed `+0x160`.
  - `leave` presses Escape, clicks the exit item, and waits for the joiner to disappear from PLRS.
  - `trade TOKEN…` covers request (click the other player), accept, `give:inv:c,r>tr:c,r`, ok, key, sleep and
    shot.
  - "host" is the first id the log lists (the host is in game before anyone joins), and "join" the next one.
- **Uncalibrated.** Four positions are not measured yet: the hostile button, the exit menu item, the trade accept
  box and the trade grid. The live test measures them from screenshots and replaces the defaults in
  `tools/joiner.py` and `two-party-hostile.steps`.
- **Tests** (`python3 -I tools/test_joiner.py`, 16 OK, no game or display) cover: PLRS parsing; the host/join roles
  in order of first appearance; the party, leave and hostile checks; follow's clamp and level case; the screen
  mapping; the gates with u32 wrap; the plan 0011 steps files; the trade plan; `LogState` with and without `--me`;
  and `join where` from the command line.

### 4. The hostility declaration and the two travel gates

```text
0x005A5E50(game, player P, other O, hostile)                                           [I]
  P's room must be in a town: 0x0061AB00(UnitGetRoom(P)) = LevelIsTown(RoomLevelId(room)), else *out ← 1, return
                                    ; fn:sub_0066BAB0_RoomLevelId@0x0066BAB0, fn:sub_006426A0_LevelIsTown@0x006426A0
  base stat 12 (level) ≥ 9 on P and on O, else *out ← 1, return       ; STATS_GetUnitBaseStat, 0x005A5E7A–0x005A5E9D, 0x005A5FDE
  0x0055B140 both ways (the pair's entries)
  if the pair's relation bit 8 already equals the request: refresh both, return
  if relation bit 8 is clear and STATS_GetUnitStat(O, 12) < 9: return              ; 0x005A5EE4–0x005A5EFF
  if hostile:
    if PlayerTickGet(P, O) > GetTickCount(): message 0x13 to P, refused                ; the pair's stamp
    PlayerTickSet(P, O, GetTickCount() + 60000)                                         ; also P +0x160 ← GetTickCount()
    0x005A5DC0; PlayerPortalClose(P) (0x00535430)
    if P and O are in the same party (0x00554630): 0x005A5D20 (leave)
  (the other way, hostile = 0, at 0x005A5FA4: not read)
Waypoint packet 0x49 (0x0054C5D0): refuse while PlayerTickGet(P, none) + 10000 > GetTickCount()   (u32)
Portal operate (0x00584870):       refuse while PlayerTickGet(operator, none) + 5000 > GetTickCount()
```

- [I] `0x0055B6C0(player, other)`: with other = 0, it returns PlayerData `+0x160`. With other ≠ player, it walks
  the PlayerData `+0x38` list (next `+0x10`) for an entry whose `+0x00` is other's unit id, and returns its `+0x08`
  (0 when there is none). Both gate calls pass EDX = 0 (`xor edx, edx` at 0x0054C5F5 and 0x005848BA), so each gate
  reads the operator's own `+0x160`. (0x0055B6C0–0x0055B715)
- [I] `0x0055B720(player, other, value)` writes the pair entry's `+0x08` and then PlayerData `+0x160` ← `GetTickCount()`
  (import `0x006CC260`). Its only call is 0x005A5F51 (`tools/xrefscan.py 0x0055B720`: 1 hit). Direct writes to
  `+0x160` elsewhere were not scanned (unfollowed). (0x0055B720–0x0055B774)
- [I] **The portal's first test is hostility itself.** Before the 5 s gate, the portal operate refuses when
  `0x00535B10(game, operator)` is non-zero and the portal's owner (`0x00552B10`) is not the operator. For a player
  unit, `0x00535B10` walks every player of the game (`0x005538D0`: the lists at `game+0x1120`, players in state 7
  skipped) with the callback `0x00535AF0`. The callback sets the result when `0x0055B300(operator, that player, 8)`
  is non-zero. Bit 8 is the relation the declaration toggles (`0x0055B300(P, O, 8)` at 0x005A5EBD). So a player
  hostile to anyone cannot use a portal it does not own. Plan 0042 Phase 1b left "a hostile player cannot use other
  players' portals" as not covered; this reading covers it. (0x0058488F–0x005848B1, 0x00535B10–0x00535B44,
  0x00535AF0–0x00535B0D, 0x005538D0–0x00553922)
- [I] **Then the 5 s gate**, which exempts no portal, the operator's own included. While the declarer is still
  hostile, the test above already refuses every portal it does not own. Its own pair was closed at the declaration,
  and a scroll is refused in town, where the declaration was made. So the gate decides in two cases: (a) a player
  who declared and then withdrew within 5 s, provided the un-declare path (not read) leaves `+0x160` alone, and who
  then uses a portal; (b) the declarer's own new portal, which it can only open outside town. A player who never
  declared has `+0x160` = 0, which no gate notices once the machine has been up 10 s. The waypoint gate delays the
  declarer's waypoint travel for 10 000 ms, and it can be reached straight from town. The community lead's
  10-second delay holds for waypoints; for portals the wait is 5 s. MP24 settles both. (0x0054C601, 0x005848C1)

### 5. The host's binding and the port-4000 precondition

- [I] Both `bind` calls (`tools/xrefscan.py 0x006C9B76`: 2 calls; the thunk is the only reference to the import at
  `0x006CC558`) pass a 16-byte `sockaddr_in` on the stack. The function zeroed all four dwords, then wrote family 2
  and `htons(port)`, and nothing writes the address dword before the call. So every listener binds `0.0.0.0`
  (`INADDR_ANY`). There are seven `socket` calls (`tools/xrefscan.py 0x006B016E`: 7 calls to the import's thunk), each with family
  2 (`push 2` as the last push before 0x0040D9B1, 0x0040DFD1,
  0x0051F417, 0x0051F759, 0x0052A6A2, 0x006C3173, 0x006C3B77), so there is no IPv6 listener. Which call opens 4000
  was not traced statically: `0x006C3B50` takes the port in EDX from its callers 0x006BF563 and 0x006BFAB0.
  Run:2026-10-12-two-clients observed the listener. (0x006C31F8–0x006C3225, 0x006C3BF4–0x006C3C2E)
- **The machine today** (read-only, 2026-10-17; no rule changed):
  - `systemctl is-active ufw` → `active` (enabled);
  - `/etc/default/ufw` has `DEFAULT_INPUT_POLICY="DROP"`;
  - `/etc/ufw/user.rules` and `user6.rules` allow only TCP/UDP 53317 and two DNS rules to `172.17.0.1`, with no rule
    for 4000;
  - `/etc/ufw/before.rules` accepts `-i lo` (line 21) before any user rule;
  - interfaces: `lo`, `wlp4s0` (192.168.0.12/24), `enp3s0` (down), plus Docker's `172.17.0.1`.

  So the **configuration** already drops inbound TCP 4000 on every non-loopback interface and keeps loopback open
  for the joiner's `127.0.0.1`. The **loaded** ruleset needs root to list (`ufw status` and `nft list ruleset` say
  "Operation not permitted"), and this lane has no root.
- **Phase 2 precondition: what the run record must hold** before the run's first hosting session (the owner's
  condition: port 4000 unreachable from outside loopback, by a firewall rule or a confirmed existing block, and how
  it was made sure of, recorded). One of:
  1. **Confirmed existing block** (preferred, no change). The owner runs `sudo ufw status verbose`; it must show
     `Status: active`, `Default: deny (incoming)`, and no ALLOW IN rule that covers 4000/tcp (a rule naming 4000, a
     port range containing it, or a rule with no port). The lane pastes the output, with its date, into the record.
  2. **A firewall rule**, only if 1 does not show that: the owner runs `sudo ufw deny proto tcp from any to any port
     4000`. The `-i lo` accept in `before.rules` comes first, so the joiner's `127.0.0.1` stays open. The record
     keeps the command and its output.

  Hosting starts only after the record names which of the two held. Before each later session of the same run, the
  lane re-reads what it can without root (`systemctl is-active ufw`, `/etc/default/ufw`, and the sha256 of
  `/etc/default/ufw` and the `/etc/ufw` rule files, against the hashes in the record) and logs it; if any of them
  changed, step 1 or 2 is repeated before hosting. That re-read is the lane's own change detector, not part of
  the owner's step.
- **Not a confirmation.** A probe from this machine to its own 192.168.0.12 enters on `lo`, which ufw accepts, so it
  tests nothing. A probe from another LAN host to 192.168.0.12:4000 against a stand-in listener would also confirm
  the block on `wlp4s0`, but it needs a second machine and is not asked for; a probe from a container on the Docker
  bridge covers only `docker0`.

## Data touched

struct:Unit+0x0E4 (the player lists the PLRS line walks). PlayerData `+0x160` and `+0x38` (§ 4) are not yet in
`re/types/save.h`'s `PlayerData`. The two-client recipes are the archivist's (backlog).

## Dead ends

- Probing 192.168.0.12:4000 from this machine tests nothing: the packet enters on `lo`.
- `ufw status` and `nft list ruleset` without root fail, so the loaded ruleset cannot be read here.

## Open questions

- [L] Which `bind` call opens TCP 4000. Tracing the port from `0x006BF563` and `0x006BFAB0` would settle it;
  Phase 2's precondition does not need it.
- [L] The un-declare path of `0x005A5E50` (hostile = 0, 0x005A5FA4) and what table `0x006E2228` dispatches. MP24
  logs both directions.
- [L] Whether `aurafilter` passes a party member or a hostile player (MP25): read `SKILLS_ForUnitsInRange`'s
  player tests before Phase 2.
- [L] Whether the stock client sends the socket insert while a trade is open (MP18).
- [L] Whether `slots.py stop` on the joiner (a dropped connection) takes the same server removal path as *Save and
  Exit* (MP07, MP08, MP30): log the removal's caller in both.
