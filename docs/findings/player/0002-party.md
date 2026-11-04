# 0002 — Who shares a kill's experience: the credit, the party collector and the mercenary's award

> **Subsystem:** player/creation (row `player/party` once plan 0058 Phase 2 lands)
> **Question:** for n = 1 to 9 partied players, what do `XP_OnMonsterKill`, `XP_PartyShare` and the collector do, who is credited, and where exactly are the member cap and the distance bound?
> **Date:** 2026-11-03   **Plan:** 0058   **Status:** answered

## Answer (summary)

Run: run:2026-11-03-party-emu, 6 166 emulated kills, 15 628 `XP_Compute` calls, 14 908 `PLAYER_AddExperience` calls,
720 `MERC_AddExp` calls compared with `tools/player.py` `kill_events`, 0 mismatches, 3 482 shares (n = 2 to 8: 1 514, 488,
284, 274, 273, 271, 378). Each `[C]` below is the code's map under ADR-0015, with the scope of § 9.

**The model was wrong in two places, and player/0001, multiplayer/0001 and spec J4 said the same; both are corrected:**

- [C] **The distance is to the killed monster, not to the credited player.** `XP_PartyShare` stores its second stack
  argument, the victim `XP_OnMonsterKill` passes, at the collector's block `+0x00` (0x0057E6DA, 0x0057E6E7, pushed at
  0x0057EA6D–0x0057EA75); the collector reads that unit's position (0x0057E5BE–0x0057E620). The control `fromcredit`, the old
  reading, fails 1 775 cases. (fn:XP_PartyShare@0x0057E6C0, fn:sub_0057E5A0_PartyXpCollect@0x0057E5A0, run:2026-11-03-party-emu)
- [C] **The credited player is tested like every member, and n = 1 pays the credited player whoever the member was.**
  At n = 1 the code uses `EBX` (the credited player, 0x0057E6D3, 0x0057E726) and the level argument (0x0057E718), not the
  block's slot. So in a party, a credited player beyond the bound or dead with one other member in range takes the whole
  award, at its own level and with no bonus, and the member in range gets nothing (243 such cases, 309 with the credited
  player as the member; control `n1member` fails 282: those 243, and 39 of `evaluated-n1`, where the member is the credited player and only the level differs). At n = 0 nobody gets anything. A player in no party has no test at
  all. (0x0057E70D–0x0057E733, 0x0057EA64–0x0057EAA1, run:2026-11-03-party-emu)

The rest:

- [C] **The member cap is a fatal path, not a clip.** `cmp eax,8` (0x0057E662) `jl` (0x0057E665): a ninth member that
  passes every test reaches `0x00408090(0xF25)` at 0x0057E66C, the fatal path; members that fail a test first do not
  count, so eight in a longer list is fine. Reached 60 times with nine eligible and 60 with ten; control `cap` fails 60.
  (fn:sub_0057E5A0_PartyXpCollect@0x0057E5A0, run:2026-11-03-party-emu)
- [C] **The distance bound's edge is inclusive.** `cmp edx,0x1900` (0x0057E654) `ja` (0x0057E65A, unsigned): d² = 6400
  stays in, 6401 is out. Every (dx, dy) with d² in 6396..6410 ran in all four signs, for a second member and for the
  killer. Controls: `le` fails 1 193, `bound` (6401) fails 49. d² is 32-bit and wraps (§ 6). (run:2026-11-03-party-emu)
- [C] **The party and the level are the credited player's.** `sub_005405A0_PartyForEachInLevel` walks the party record
  of `sub_00554630_UnitPartyId(credited)` in list order, and takes each member whose room's level id equals the credited
  player's; the victim's level is not read. (0x005405C7–0x00540636, run:2026-11-03-party-emu)
- [C] **Credit (G0):** a player killer is credited itself; a monster killer's owner link is; a state in the `exp` mask
  (conversion, attract, confuse) on the killer, then on the victim, replaces it with the owner of a stat list with flag
  `0x800`; the result counts only if it is a player. § 4. (fn:sub_0057E7B0_XpCreditPlayer@0x0057E7B0, run:2026-11-03-party-emu)
- [C] **The mercenary (G6):** only the credited player's own, before the share and whatever the share does: its
  `XP_Compute` runs at the monster's full experience and its own level, ends in `MERC_CapExpGain`, and is cut to
  `gain × 86 ÷ 256` unless the mercenary is the killer. § 5. (fn:XP_OnMonsterKill@0x0057E990, fn:MERC_CapExpGain@0x0057E3F0, run:2026-11-03-party-emu)
- [C] Re-checked on the game's own logs: the corrected model predicts every member set **in order** and every input of
  run:2026-10-20-two-clients's six logs, now with the 40 mercenary kills: 689 of 690 kills (the other cut off by the session's end),
  267 single and 844 share inputs. **No kill there separates either correction:** the two distances decide 431 pairs alike and
  0 apart (4 partied kills have no `KILL` line and take the killer's position, so their pairs are alike by construction), and all 648
  partied credited players are in range, so every sole member there is the credited player. (`tools/mp_check.py xpshare`, run:2026-11-03-party-emu)
- [C] **What each correction rests on.** Both are the code's map (ADR-0015 (3)), read at the instructions above and separated by `fromcredit` and `n1member` under emulation; no
  logged kill separates them. What the game's own logs do give: the pointer at `[esp+4]` of 0x0057E990 is the killed monster (`XK0` logs it, and at n = 1 the input equals its base stat 13),
  and its X is non-zero at that moment, since partied kills pay (the `X = 0` return would give n = 0). (0x0057E9C9, 0x0057EA6D, 0x0057E620, run:2026-10-20-two-clients)
- [I] The position getters on the victim and on a member are one route (`sub_0045ADF0_UnitGetSubX`, `sub_006488C0_PathGetX`, both `I`); their meaning, the sub-tile position, is carried by the member sets the logged player positions predict, not by the emulation. (0x0057E5D9–0x0057E620, 0x0057E62B–0x0057E636)
- [I] The float steps stay as J4 states them: `q`, the product and `CRT_ftol2` agree with the model in every case on both
  `CRT_ftol2` paths, but ADR-0015 (5) keeps x87 results out of emulation's evidence; run:2026-10-20-two-clients shows them
  at n = 2, 98 inputs separating, on the same instructions. (0x0057E754–0x0057E77B, fn:CRT_ftol2@0x00682FD0)

## Leads used

- [L] src:arreat-summit-experience: the verdicts stand in [player/0001](0001-creation.md) *Leads used*, whose distance
  detail this finding corrects (the page's "within 2 screens"; the code measures from the monster). **held with refinement**
  Detail: bound and origin per 0x0057E654 and 0x0057E6E7. No new page was read.

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x0057CCB0` | `sub_0057CCB0_UnitKilled` | calls the gate at 0x0057CD51 | C |
| `0x005A4EF0` | `sub_005A4EF0_KillExpGate` | no call when a unit is null or the victim has flag bit 26 of `+0xC4` | I |
| `0x0057E990` | `XP_OnMonsterKill` | the award | C |
| `0x0057E7B0` | `sub_0057E7B0_XpCreditPlayer` | the credit | I |
| `0x0057E6C0` | `XP_PartyShare` | collects, then pays n = 1 or the split; members and inputs logged at n = 1 and 2 | C |
| `0x0057E5A0` | `sub_0057E5A0_PartyXpCollect` | alive, distance to the victim, the cap; logged member sets at n = 1 and 2 | C |
| `0x005405A0` | `sub_005405A0_PartyForEachInLevel` | party list, the credited player's level | C |
| `0x00554630` | `sub_00554630_UnitPartyId` | the party id or 0xFFFF | I |
| `0x00540710` | `sub_00540710_PartyIdOfUnit` | guid search over every party's list | I |
| `0x00540290` | `sub_00540290_PartyFind` | first record of an id | I |
| `0x005541B0` | `sub_005541B0_UnitIsDead` | the alive test | I |

`XP_PartyShare` and the collector are raised on the logged side (their `XP_Compute` calls on the game's own data), not on
the emulation (`lane/p46m12` ruling 7); `sub_0057E7B0_XpCreditPlayer` stays I because the logs meet only its player and
mercenary branches and do not log its return.

## 1. The chain

```
sub_0057CCB0_UnitKilled ── 0x0057CD51 ──> sub_005A4EF0_KillExpGate(killer, victim, game)
      killer, victim non-null; victim +0xC4 bit 26 clear  ── 0x005A4F12 ──> XP_OnMonsterKill(game, killer, victim)

XP_OnMonsterKill:
  killer, victim non-null; killer type 0 or 1; E ← base stat 13 of the victim; E ≤ 0 (signed): end
  credit ← XpCreditPlayer(killer, game, victim); none: end
  mlvl ← base stat 12 of the victim
  merc ← the credited player's pet type 7: first node with flag bit 0 clear, unit type 1 by its id
  if merc: L ← merc's base stat 12; gain ← XP_Compute(E, L, mlvl); if killer ≠ merc: gain ← gain × 86 ÷ 256
           MERC_AddExp(gain, merc, credit, L)
  clvl ← base stat 12 of credit
  if UnitPartyId(credit) = 0xFFFF: PLAYER_AddExperience(credit, clvl, XP_Compute(E, clvl, mlvl)); end     ; no test at all
  XP_PartyShare(credit, E, game, victim, clvl, mlvl)

XP_PartyShare:
  block: +0x00 victim, +0x04 unit[8], +0x24 level[8], +0x44 n, +0x48 Σ            ; memset 0x4C, 0x0057E6C9–0x0057E6D5
  PartyForEachInLevel(game, credit, Collect, block)
  n ≤ 0 or Σ ≤ 0: end                                                              ; 0x0057E6FB–0x0057E707
  n = 1: PLAYER_AddExperience(credit, clvl, XP_Compute(E, clvl, mlvl)); end        ; the credited player, not unit[0]
  total: i32 ← E + ((n − 1) × E × 89) ÷ 256                                        ; every product i32, ÷ truncates
  q: f32 ← total / Σ
  for i in 0..n−1: in ← trunc(level[i] × q); PLAYER_AddExperience(unit[i], level[i], XP_Compute(in, level[i], mlvl))

PartyForEachInLevel(game, credit, cb, block):
  room ← credit's room; none: cb(credit); end
  lid ← room's level id;  pid ← UnitPartyId(credit); 0xFFFF: cb(credit); end
  rec ← first party record with word id = pid; none: end
  for node in rec's list, in order: u ← player by node's guid; if u and u's room and its level id = lid: cb(u)

Collect(u, block):
  UnitIsDead(u): return
  if block.victim:                                             ; only the direct calls of the emulation send null
    (X, Y) ← victim's position; X = 0: return                  ; Y = 0 is not tested
    (x, y) ← u's position; x = 0: return
    d² ← u32((Y − y)² + (X − x)²); d² > 6400 unsigned: return
  n ≥ 8: fatal
  unit[n] ← u; level[n] ← STATS_GetUnitStat(u, 12); Σ += level[n]; n += 1
```

- [C] The above, as a map from the declared image to the sequence of calls with their sites and arguments, the block
  at each member's `XP_Compute`, the f32 bit pattern of `q` compared, and each player's stats 13 and 29 after the kill.
  (fn:XP_OnMonsterKill@0x0057E990, fn:XP_PartyShare@0x0057E6C0, fn:sub_0057E5A0_PartyXpCollect@0x0057E5A0,
  fn:sub_005405A0_PartyForEachInLevel@0x005405A0, run:2026-11-03-party-emu)
- [I] The chain's first two lines are not in that map: every case enters at 0x0057E990 or 0x0057E6C0 (`*.cases`), so `sub_0057CCB0_UnitKilled`'s call and the gate are read and pinned, not run. (0x0057CD51, 0x005A4EFE–0x005A4F12)
- [C] `level[i]` comes from `STATS_GetUnitStat` (the evaluated list, 0x0057E68F), `clvl` from `STATS_GetUnitBaseStat`
  (0x0057EA53). They differ only if a list changes stat 12, which this finding did not look for; tags `evaluated`,
  `evaluated-n1`. (fn:STATS_GetUnitStat@0x00625480, fn:STATS_GetUnitBaseStat@0x006253B0, run:2026-11-03-party-emu)
- [C] A duplicate guid in a party list is collected twice (`dup-guid`), and a guid with no unit is skipped
  (`nine-missing`); whether a list ever holds either was not read. (0x0054060E–0x00540617, run:2026-11-03-party-emu)
- [I] **Consequences of the two corrections:** a partied player whose hireling or summon kills more than 80 sub-tiles
  from it does not share by its own position: with one other member near the victim it still takes the whole award alone
  (n = 1), and with no member near nobody gets any, while an unpartied player in the same place gets it all. A dead killer
  with one living member in range is paid, the living member is not. (0x0057E6FB–0x0057E733, 0x0057E654–0x0057E65A)

## 2. The party definition

- [C] The party id is found by a guid search over **every** party's list: the guid is the unit's `+0x0C`, or inventory
  `+0x24` when the unit has an inventory whose `+0x00` is `0x01020304` (else −1); the first list holding it gives the
  record's word `+0x00`. A unit that is not a player or has no game word is 0xFFFF. Then the list walked is the **first
  record of that id**, which may not be the one the guid was found in (`same-id`). Record: `+0x00` id, `+0x04` list head, `+0x08`
  next; node: `+0x00` guid, `+0x04` next; root at game `+0x1D2C`, first record at its `+0x04`. (fn:sub_00554630_UnitPartyId@0x00554630,
  fn:sub_00540710_PartyIdOfUnit@0x00540710, fn:sub_00540290_PartyFind@0x00540290, fn:INV_GetOwnerId@0x0063D450, run:2026-11-03-party-emu)
- [I] The writers of the list, what makes two players one party, and whether a list can hold nine players were not read.
  `sub_005405A0_PartyForEachInLevel` has 4 references (`static.txt`): the share's 0x0057E6F3,
  `sub_005408E0_PartyCountInLevel` 0x005408F4, `sub_00540900_PartyGoldShare` 0x0054091E, and 0x005408CB in an unnamed
  function before them, not read. (0x005408CB, 0x005408F4, 0x0054091E)
- [C] Alive: `sub_005541B0_UnitIsDead` is true for flag bit 0 of `+0xC6` or a player in mode 0 or 0x11, tags `n1-dead`,
  `n0-dead`, `nine-dead` and the share family. (fn:sub_005541B0_UnitIsDead@0x005541B0, run:2026-11-03-party-emu)
- [I] For a monster it is mode 0 or 0xC, and any other type is always dead; no member is one. (0x005541CB–0x005541E6)

## 3. The cap and the edge: the deciding instructions

| Rule | Instruction | Below | At | Above |
|---|---|---|---|---|
| Member cap | 0x0057E662 `cmp eax,8` / 0x0057E665 `jl` (`eax` = n so far) | n ≤ 7: stored | n = 8: fatal path, 0x0057E667 `push 0xF25`, 0x0057E66C `call 0x00408090` | not reached |
| Distance | 0x0057E654 `cmp edx,0x1900` / 0x0057E65A `ja` (`edx` = d²) | collected | d² = 6400: collected | d² ≥ 6401: skipped |

- [C] Both from `static.txt` (0 of 36 pinned instruction forms differ) and the cases above. (0x0057E654, 0x0057E65A, 0x0057E662, 0x0057E665, run:2026-11-03-party-emu)
- [I] After 0x00408090: `0x00408A60` then `0x00681E09(−1)`, the fatal path of the other findings; it was not run (the case ends at the first
  call, ADR-0021). (0x0057E671–0x0057E681)

## 4. G0, the credit (`sub_0057E7B0_XpCreditPlayer`)

```
credit(killer, game, victim):
  killer type 0: return killer
  killer type ≠ 1: return none                       ; cannot arrive: XP_OnMonsterKill filters 0x0057E9B6–0x0057E9BF
  owner ← MonsterOwner(killer)                       ; AI control +0x28 game, +0x2C id, +0x30 type, by GameFindUnit
  s ← none
  if UnitHasExpState(killer): s ← StatListFindFlag(killer, 0x800)
  if victim and UnitHasExpState(victim): s ← StatListFindFlag(victim, 0x800)    ; the victim's wins, even a none
  if s: owner ← GameFindUnit(game, type of s's owner, id of s's owner)          ; the link does not come back
  return owner if owner is a player, else none
```

- [C] Every line, tags `player`, `owner`, `owner-far`, `owner-monster`, `no-link`, `no-mdata`, `no-ctl`, `link-lost`, `state-killer`,
  `state-victim`, `state-both`, `state-nolist`, `state-victim-nolist`, `state-outside`, `state-second-node`, `state-owner-monster`,
  `state-owner-lost`. (fn:sub_0057E7B0_XpCreditPlayer@0x0057E7B0, fn:sub_0058F0D0_MonsterOwner@0x0058F0D0,
  fn:sub_0063A690_UnitHasExpState@0x0063A690, fn:sub_00625760_StatListFindFlag@0x00625760, run:2026-11-03-party-emu)
- [C] A player killer ignores a state on the victim (`player`). 40 mercenary kills in the game's own logs credit the owner: the
  mercenary's `XP_Compute` first, then the owner's party by the same rules. (fn:XP_OnMonsterKill@0x0057E990, run:2026-10-20-two-clients, run:2026-11-03-party-emu)
- [C] The mask is `tbl:States.txt:exp`: 53 `conversion`, 57 `attract`, 59 `confuse`, the rows of [States.md](../../tables/States.md); the emulation's mask holds those three and a state outside it (60) does nothing. What holds the `0x800` list
  in play (the state's caster, by [items/0010](../items/0010-quest-drops.md)) keeps that finding's tag. (tbl:States.txt:exp, 0x0057E7E4, 0x0057E7F3)
- [C] A player can be the victim as far as this code goes: its base stat 13 stands for E, its base stat 12 for mlvl
  (`victim-player`). `sub_0057CCB0_UnitKilled` has a player branch (0x0057CD28), so a player killing a player reaches it
  unless the gate's flag stops it; none of the 690 `XK0` lines has `mtype` 0 (`xk0-victim-types.txt`), but those six logs are kill sessions and the player-against-player session has no `XK0` logger, so that says nothing, and whether play reaches it stays [I]. Open question below.
  (0x0057CD28–0x0057CD51, fn:sub_005A4EF0_KillExpGate@0x005A4EF0, run:2026-11-03-party-emu)
- [I] The gate's flag bit 26 has 9 writers (`static.txt`), for example 0x0056D8A4 right before a `sub_0057CCB0_UnitKilled` call; what each means was not read.
  (0x005A4EFE–0x005A4F0A, 0x0056D8A4)

## 5. G6, the mercenary's credit

- [C] Only the credited player's pet of type 7; other members' mercenaries get nothing. It is paid before the party test
  and is the same whether the owner shares, is alone or is out of range (`merc-owner-far`: the award stands, the owner gets
  the n = 1 or n = 0 outcome). (0x0057E9F9–0x0057EA46, run:2026-11-03-party-emu)
- [C] `XP_Compute` on a non-player takes MaxLvl from class column 0 (0x0057E497–0x0057E4AF), its own stat 85, and ends in
  `MERC_CapExpGain`: for a player unchanged (0x0057E3FD–0x0057E400), else `min(gain, (ExpForLevel(L + 1) − ExpForLevel(L)) >> 6)`, an unsigned compare, with
  `ExpForLevel(L) = (L + 1) × L × L × row.Exp/Lvl`, or 0 with no owner link (`merc-nolink`). The cap's run is hirelings G4.
  (fn:XP_Compute@0x0057E480, fn:MERC_CapExpGain@0x0057E3F0, fn:HIRELING_ExpForLevel@0x00663790, run:2026-11-03-party-emu, run:2026-10-27-sweep-hirelings)
- [C] `gain × 86 ÷ 256` is signed truncating, not applied when the killer is the mercenary (`merc-kills`, compared at the full gain). Control `mercfull`, no cut at all, fails 353 on the other tags: it separates the cut; the exemption rests on `merc-kills`' comparison. (0x0057EA28–0x0057EA39, run:2026-11-03-party-emu)
- [C] A first node with flag bit 0 is skipped (`merc-flag`), only such nodes give no mercenary (`merc-dead`), no table too (`nopets`), a node whose unit is gone likewise (`merc-lost`). (fn:PETS_GetUnitOfType@0x00574EC0, run:2026-11-03-party-emu)

## 6. Wrap bounds (kept: `check.txt`, the last block)

- [C] The total's product `(n − 1) × E × 89` is i32. Largest E that fits, first that wraps: n = 2: 24 129 029 / 24 129 030;
  3: 12 064 514 / 12 064 515; 4: 8 043 009 / 8 043 010; 5: 6 032 257 / 6 032 258; 6: 4 825 805 / 4 825 806; 7: 4 021 504 /
  4 021 505; 8: 3 447 004 / 3 447 005. Past it the wrapped product truncates toward zero and the total may go negative (n = 8,
  E = 3 447 005: −4 941 601); each member's input is then ≤ 0, and `XP_Compute` returns 1 for that (tag `wrap-total`; control `floortotal`
  fails 92). Whether a monster's frozen stat 13 reaches these was not checked. (0x0057E739–0x0057E74B, 0x0057E4A1–0x0057E4AA, run:2026-11-03-party-emu)
- [I] *Dated note (2026-11-03, `lane/s67` review):* in the bullet above, "each member's input is then ≤ 0" passes the float steps, so by ADR-0015 (5) that clause is `[I]`, like the Answer's last bullet. The total's value and `XP_Compute`'s return of 1 for an input ≤ 0 stay `[C]`. (0x0057E754–0x0057E77B)
- [C] d² is `imul`, `imul`, `add` in 32 bits, compared unsigned, with `dx`, `dy` differences of u16 words for a unit with a path. |dx| = |dy| = 46 340
  gives 4 294 791 200, which fits; 46 341 gives 4 294 976 562, which wraps to 9 266. A wrapped value inside the bound passes: dx = 65 534,
  dy = 512 is 2³² + 4, so d² = 4 (tag `wrap`; control `unwrapped` fails 4). No level this finding knows spans that; nothing was checked for it. (0x0057E64C–0x0057E65A, run:2026-11-03-party-emu)

## 7. The player count (`/players` and the kill)

- [C] No traced read in any case touches `data:g_PlayersOverride@0x00883D70`, and no traced site lies in `sub_00535790_PlayerCount`: the split reads the
  party, not the player count. The count reaches a kill only through the monster's stat 13, frozen at creation (monsters/stats C1). (`check.txt` read list, run:2026-11-03-party-emu)
- [I] This answers the plan's open question from the code. `sub_00535790_PlayerCount` has 2 direct references: `TC_ResolveDrops` (0x0055A8F4, at the event) and
  `sub_00573930_MonPlayerBonus` (0x00573974); `MonPlayerBonus` has 5: `sub_00573CB0_MonStatsInit` (0x00573DBC, frozen at creation) and **four think functions that call it at their own run**:
  `sub_005E8810_AiDiabloDecide` (0x005E8D61), `sub_005E9750_AiDiabloDecideUnref` (0x005E9C82), `sub_005F0B00_AiCorruptRogue` (0x005F0B32), `sub_005FC450_AiBaalDecideRanged` (0x005FC542). *Corrected 2026-11-03, `lane/s67` review (this bullet said a changed `/players` is re-read there):* each reads only the block's word `+0x0C`, the difficulty (0x005E8D6B, 0x005E9C8C, 0x005F0B37, 0x005FC54C; [ai/0012 § 2.3](../ai/0012-batch11.md#23-diablos-decision-fnsub_005e8810_aidiablodecide0x005e8810)), so the count computed there goes unread. `data:g_PlayersOverride@0x00883D70` is named by two instructions: the setter 0x00535785 and the reader 0x005357B9.
  `sub_00540900_PartyGoldShare` has no direct reference to the count; its callees past the party walk were not followed. Indirect calls not followed. (`static.txt`)

## 8. The 265/264 entry

- [C] Closed, and it was this code's record, not the code. The filed difference is the 106 "another level" pair of `mp_check.py`, counted at a kill that was cut off by the
  session's end (kills-5's last): 9 + 105 + 108 + 42 = 264, as lane/mp26 found and multiplayer/experiments states. The re-run agrees: `check-xpshare-kills.txt` has 222 partied and 42 unpartied n = 1 kills, 264 single inputs, 649 kills, 1 cut off. The
  archived entry is [2026-10-20-architect-reverser-plan-0044-p3-review-mp26-section-6-bullet](../../backlog/archive/2026-10-20-architect-reverser-plan-0044-p3-review-mp26-section-6-bullet.md); no entry is open. Spec J4's note "sum to 265 … filed to the reverser" is stale (backlog to the spec-writer).
  (`tools/mp_check.py xpshare`, run:2026-10-20-two-clients, fn:XP_PartyShare@0x0057E6C0)

## 9. Scope, reached and not reached

- **Boundaries (ADR-0021):** `0x00408090` (arguments: line 0xF25, site 0x0057E671) and `PLAYER_LevelUp` 0x00570880 (128 cases; ECX game, EDX unit, site 0x0057E57E). Every other callee ran emulated, `XP_Compute` and `PLAYER_AddExperience` included. **Not covered:** the level-up and every later member of such a case; the fatal path past its first call; `MERC_AddExp` past its owner's-level test (generated L ≥ the owner's level; its run is hirelings G5).
- **Declared reads:** 118 traced read sites, all image constants: the two `XP_Compute` factor tables, the hash offsets at 0x006E10E0, the stat masks 0x006CE270 and 0x006CE278, and 0x00624DD0's switch. 0 traced writes. The Experience table and hire rows are synthetic; this covers no stock row.
- **Reached:** all of the tags above, 5 families; both `CRT_ftol2` paths (489 share cases at flag 0, 2 993 at 1); the static victim's branch (types 2, 4, 5), the null victim (direct calls only: the single call site passes a checked non-null).
- **Not reached:** a member of another type (the static branch of `sub_0045ADF0_UnitGetSubX`); a member with y = 0 (`mem-y` is y = 30 000; read: only x is tested, 0x0057E63B–0x0057E640); a party id with no record (it was found in one); the `0x00540734` and `0x0054029A` fatals; pets row bound `DataTables+0xBF0` ≤ 7; `MERC_CapExpGain` with no pet info or no hire row (hirelings G4 `[I]`).
- **Tool limits (ADR-0015 (5)):** Ghidra 12.1; x87 values as stated in the Answer.

## Data touched

tbl:States.txt:exp; tbl:Experience.txt (`perClass`, `ExpRatio`) by offset, synthetic here; tbl:Hireling.txt:Exp/Lvl by offset, synthetic here.
struct:Unit: `+0x00` type, `+0x04` class, `+0x0C` guid, `+0x10` mode, `+0x14` data, `+0x2C` path, `+0x5C` stat list, `+0x60` inventory, `+0x80` game, `+0xC4` flags, `+0xC6` byte, `+0xE4` hash next. Game `+0x70`, `+0x1120` hash of players, `+0x1320` of monsters, `+0x1D2C` party root.

## Dead ends

- The old `mp_check.py` distance matched all 649 kills because, in that play, killer and monster were never on opposite sides of the bound: logs cannot tell them apart, so "reproduced" there was not evidence for the origin. Rule: name what a run separates.
- `sub_0057E5A0_PartyXpCollect` takes the party from nowhere: the party test is in the iterator.

## Open questions

- [L] Does a player killing a player get an award in play? The code path exists (§ 4); no log holds one, and the gate's flag was not traced on such a victim. For a later two-client case, not blocking.
- [L] Does a kill with an `exp` state credit the way § 4's code map says? (2026-11-04, `lane/a68` review.) The credit for a kill with an `exp` state (tags state-killer, state-victim, state-both, and the player case's state on the victim) is the code's map only: no logged kill carries such a state, and the `XK0` logger (`tools/gdb/player.py`) reads no state, so the six kill logs cannot say whether one had a state. [items/0010](../items/0010-quest-drops.md)'s "the caster" stays `[I]` for the same reason. A session would log the killer's and the victim's `exp`-mask states and the `0x800` list's owner at `XK0` with a converted monster's kill (Conversion) and a kill of a converted monster. Optional, not blocking: [States](../../tables/States.md) and player/party already state the scope.
- [L] A live case of the corrected reading: a partied killer's far mercenary or summon with one member near the victim. The logs have none. It would need a session and a monster position line, which `KILL` already gives. Optional, for the owner's three-client or a two-client run.
