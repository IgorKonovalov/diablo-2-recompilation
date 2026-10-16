# 0003 — Special monsters: mod selection, mod handlers, minion transfer, superuniques, names

> **Subsystem:** monsters/special
> **Question:** once the population pass (or a preset) has made a monster special, which mods does it get, which draws do the mod handlers make, which mods pass to minions, how is a superunique built from its record, and where and how is its name rolled?
> **Date:** 2026-10-14   **Plan:** 0018 (Phase 1, static reading; existing logs of run:2026-10-13-mon-spawn re-read)   **Status:** answered (Phase 1); Phase 1b cross-check done 2026-10-14 (§ Leads used); Phase 2 reproduction done 2026-10-14 (run:2026-10-14-mon-special, § 10)

## Answer (summary)

- [C] **Champion or unique.** `sub_005A0760_SpecialModsRoll(unit, game, allowChampion)`: with `allowChampion` ≠ 0 it draws
  `Range(unit.seed, 100)` and, below MonUMod row 0 `constants` (20), sets flag `0x04` and appends **one** champion mod from
  `sub_005A0500_ChampionModPick`. Otherwise (or with `allowChampion` = 0, which skips the `Range(100)` draw) it draws
  `Range(unit.seed, 1)` (always 0) and picks `1 + difficulty` unique mods, one `sub_005A0600_UniqueModPick` each. Reproduced
  in all 70 rolls of run:2026-10-14-mon-special (66 with the champion roll, 4 MonPlace 2 rolls without it; all three
  difficulties, classic and expansion): mods and exit seed predicted. (fn:sub_005A0760_SpecialModsRoll@0x005A0760, 0x005A07E7, 0x005A0871–0x005A0899, tbl:MonUMod.txt:constants, run:2026-10-14-mon-special)
- [I] Not reached at run time: the roll is skipped when the monster already has 8 mods, the unique count is cut so that the
  list stays ≤ 9, and the loop stops early when a pick returns 0. (0x005A07CD, 0x005A088F, 0x005A08FA)
- [C] **The two weighted picks** walk all 43 MonUMod rows in row order. A row is a candidate when its weight for the
  difficulty (`cpick` u16 at `+0x0E + 2·d`, `upick` at `+0x14 + 2·d`, read signed) is > 0, its `champion` byte (`+0x08`) is
  set (champion pick) or clear (unique pick), it passes `sub_005A03E0_ModEligible` (`enabled`; `version` < 100 unless the
  game is expansion; neither `exclude1` nor `exclude2` is a type of the monster; the `fPick` test), and, for the unique pick
  only, it is not already among the monster's mods. One draw `Range(unit.seed, Σweights)` then selects by cumulative
  weight. In run:2026-10-14-mon-special the candidate list, total and draw of all 169 picks (16 champion, 153 unique, incl.
  the superunique extras) and the result of all 153 `MonTypeIsA` calls matched the model. (fn:sub_005A0500_ChampionModPick@0x005A0500, fn:sub_005A0600_UniqueModPick@0x005A0600, fn:sub_005A03E0_ModEligible@0x005A03E0, tbl:MonUMod.txt:cpick, tbl:MonUMod.txt:upick, run:2026-10-14-mon-special)
- [I] Not reached at run time: an empty candidate list (no draw, result 0) and an exclusion by `exclude1`/`exclude2` (no
  special of MonType `sandleaper` was rolled). (0x005A06C4, fn:sub_005A0070_MonTypeIsA@0x005A0070)
- [C] **Draw counts on the unit seed, as logged.** From the champion roll to the end of `SpecialModsRoll` the boss's unit
  seed moves 1 step for a champion and `1 + (1 + difficulty)` steps for a unique: 2 in all 5 normal-difficulty uniques,
  4 in all 15 hell uniques, 1 in all 4 champions of run:2026-10-13-mon-spawn (`SMR1` → `SMRX`). (fn:sub_005A0760_SpecialModsRoll@0x005A0760, run:2026-10-13-mon-spawn)
  Phase 2 replays those 24 rolls with `tools/monspecial.py`: mods and exit seeds predicted, 0 mismatches (run:2026-10-14-mon-special, step 4).
- [C] **Mod handlers draw nothing but the name seed.** `sub_005A2120_SpecialModsApply` first makes a unique's minions,
  then calls the handler of mods 1, 2, 3, 4 (always) and of every mod in the monster's list, from the table at
  `0x0073C008`. Only the `rndname` handler (mod 1) touches the unit seed: one step, whose low 16 bits become the
  **name seed** (`MonsterData+0x14`). The others draw nothing on the unit, room or game seed; `aura` (30) draws on a local
  seed made from the name seed. In the run every handler window moved the unit seed by exactly the number of `rndname`
  calls (1, or 2 for Megaflow Rectifier, whose `Mod1` is `rndname`) in all 67 windows, and kept the room and game seeds in the 30 windows that logged them (inside a pass).
  In run:2026-10-14-mon-special each call was logged on its own: 606 handler calls on bosses, pack members and superuniques
  and 1667 calls on group members (flag 0) kept the unit, room and game seeds, except `rndname`'s one step on its own unit
  (130 steps, each name seed predicted), and the 12 aura draws were predicted on their local seed.
  (fn:sub_005A2120_SpecialModsApply@0x005A2120, fn:sub_005A0CE0_UModRndName@0x005A0CE0, fn:sub_005A1650_UModAura@0x005A1650, data:g_UModHandlers@0x0073C008, run:2026-10-13-mon-spawn, run:2026-10-14-mon-special)
- [C] **Minions.** A unique's minions (and a superunique's) copy the boss's mods whose `xfer` is set into their own mod
  list at creation (`sub_005A0930_ModsXferCopy`), which is after the boss's mods are rolled and before its handlers run.
  The boss's handlers are then also applied, with "minion" parameter 0, to every member of the boss's group, for **every**
  mod of the boss, `xfer` or not (`sub_0058F380_MonGroupForEach`). Champion-pack members are not minions: each gets mod 16
  (`champion`) appended, whatever the boss's champion mod, and its own `SpecialModsApply`. In run:2026-10-14-mon-special the
  mod list of every minion after the copy was predicted (277 minions took a mod), and the mods and handlers of each pack
  member and MonPlace 3 champion (49). (fn:sub_005A0C00_UniqueMinions@0x005A0C00, fn:sub_005A0930_ModsXferCopy@0x005A0930, fn:sub_0058F380_MonGroupForEach@0x0058F380, fn:sub_005A48C0_ChampionMemberMark@0x005A48C0, tbl:MonUMod.txt:xfer, run:2026-10-14-mon-special)
- [I] **Superuniques** (`sub_005A49B0_SuperUniqueSpawn`) never call `SpecialModsRoll`. The record's `Mod1`–`Mod3` are
  MonUMod row indices written as they are (stop at the first 0; `thief`, 24, is skipped; `aura`, 30, is kept and its handler
  called once more afterwards), then `difficulty` extra unique picks are drawn on the unit seed. Minions are
  `MinGrp + d .. MaxGrp + d` (`d` = difficulty, added only when both are non-zero) of `minion1`, or of the superunique's own
  class when it has no `minion1`. `AutoPos` ≠ 0 discards the preset point for a random point in the room. 15 records have a
  hard-coded tail keyed by the record index (Countess, Radament, council members, seal bosses, Cow King, Siege Boss,
  Ancient Barbarians, Nihlathak, Baal Subject 2), and every superunique ends with mod 22 (`questcomplete`) appended.
  `[C]` for the counts: in the run three hell superuniques moved the unit seed by 2 before their minions (the two extra
  picks) and got `MinGrp + 2` minions (Rakanishu 10, Treehead WoodFist 4, Pitspawn Fouldog 6); three normal ones moved it by 0.
  (fn:sub_005A49B0_SuperUniqueSpawn@0x005A49B0, tbl:SuperUniques.txt:Mod1, tbl:SuperUniques.txt:MinGrp, tbl:SuperUniques.txt:AutoPos, run:2026-10-13-mon-spawn)
- [C] **Superuniques at run time.** 11 superuniques of run:2026-10-14-mon-special (Rakanishu ×4, Griswold ×4, Bishibosh,
  Threash Socket, Beetleburst; normal, nightmare and hell, classic and expansion) are reproduced from `SuperUniqueSpawn`'s
  entry: the placement (exact for `AutoPos` 0; `SpawnPosPick` anywhere in the room for `AutoPos` 1, 6 cases), the fixed
  mods after the monster's post-create mods, the `difficulty` extra picks (1 in nightmare, 2 in hell), the minion count
  `MinGrp + d .. MaxGrp + d` (Rakanishu 8, 9, 10; one `RangeB(1)` and no minion for `MinGrp` 0), the default tail and
  mod 22. (fn:sub_005A49B0_SuperUniqueSpawn@0x005A49B0, fn:sub_005A09E0_SpecialMonPlace@0x005A09E0, tbl:SuperUniques.txt:AutoPos, run:2026-10-14-mon-special)
- [C] **MonPlace 2 and 3** (§ 7) are reproduced in Tristram in four games (normal classic and expansion, nightmare, hell):
  case 2 as a unique with no `Range(100)` and 3..6 minions, case 3 as a champion with mod 16 at the preset point and its
  pack. (fn:sub_0054E600_PresetMonSpawn@0x0054E600, run:2026-10-14-mon-special)
- [C] **Names are rolled on the client, on the low byte of the name seed.** All 94 client rolls of
  run:2026-10-14-mon-special ran on `Init(nameSeed & 0xFF)` of the same unit's server name seed, in the order below
  (`sub_0045F190_ClientMonAssign` keeps the low byte at `0x0045F387`, § 8). (fn:sub_004AC870_ClientMonNameBuild@0x004AC870, fn:sub_0045F190_ClientMonAssign@0x0045F190, run:2026-10-14-mon-special)
- [I] **Names are rolled on the client.** The server sends the 16-bit name seed with the monster's flags, superunique id
  and mod list (`sub_0053E2E0_MonUnitPacketBuild`). The client name builder `sub_004AC870_ClientMonNameBuild` gives a
  superunique its record's `Name` string, a champion "<champion-mod word> <MonStats NameStr>", and a random unique a name
  drawn on `Init(nameSeed & 0xFF)`: suffix, then prefix (`"%0 %1"`), then `Range(100) < 50` → appellation, suffix, prefix again
  (`"%0 %1 %2"`). `UniqueTitle` is loaded and freed but never read. (fn:sub_004AC870_ClientMonNameBuild@0x004AC870, fn:sub_00653ED0_UniquePrefixRoll@0x00653ED0, fn:sub_00653F10_UniqueSuffixRoll@0x00653F10, fn:sub_00653F50_UniqueAppellationRoll@0x00653F50, tbl:UniquePrefix.txt:Name)
- [I] **Boundary recommendation for Phase 2:** model every draw (the two picks, the eligibility tests, the unique-minion
  count, the `rndname` step, the superunique extra picks and minion counts, Radament's escort count, the aura index and the
  client name roll) and remove the special-mod seed oracles of monsters/0002 § 9. Handler *effects* stay out of scope;
  their deep callees (skill and AI setup, quest hooks) become seed-asserted calls, not oracles (§ 9). Done in Phase 2
  (§ 10): no oracle is left on the special path. (fn:sub_005A2120_SpecialModsApply@0x005A2120, fn:sub_005A1650_UModAura@0x005A1650)
- [I] Not reached at run time (§ 10): the hard-coded superunique tails (Radament's `Range(5)` + 2 escorts, the quest hooks,
  `EscortSpawn`), the `thief` skip, an `aura` superunique and the Lord De Seis index, a superunique with ≥ 5 mods at creation,
  and a client fixed-name class. (fn:sub_005A49B0_SuperUniqueSpawn@0x005A49B0, 0x005A4CD1)

## Leads used

The finding was written from code and from the logs of run:2026-10-13-mon-spawn (Phase 1), with no lead. The sources
below were fetched and read afterwards, on 2026-10-14, for the plan 0018 Phase 1b cross-check (blind first):
`src:arreat-summit-bonuses` and `src:d2dfg-blizzard` again, and the new `src:arreat-summit-monster-pages` and
`src:fandom-d2-elite-monsters`. None of them has code. `src:d2dfg-blizzard` names no version and describes at least one
column that 1.14d does not have (`SpawnUniqueMod`), and `src:fandom-d2-elite-monsters` mixes eras, so a contradiction with
either may be a version difference. Agreement promotes nothing. The three `contradicted` claims are required cases of
Phase 2 (backlog, 2026-10-14 reverser → reverser); one of them is already settled by the run.

Re-read with r2 on 2026-10-14 for the two `contradicted` verdicts that the run does not settle: the champion pick's
`champion` test (`cmp byte [rec+8], 0` / `je` skip at `0x005A056F`–`0x005A0573`) and the `AutoPos` branch
(`0x005A4A2B`–`0x005A4A35` zero x and y; `SpecialMonPlace` calls `SpawnPosPick` when both are 0, `0x005A09EF`–`0x005A0A0D`).
Both read as in § 3 and § 6, so nothing is corrected and the tags stay `[I]`.

**Mod counts**

- [L] src:arreat-summit-monster-pages: in Nightmare unique monsters "gain one bonus ability", in Hell "two".
  **held with refinement**
  Detail: `n = Range(unit.seed, 1) + 1 + difficulty` picks, cut so that the list holds at most 9 mods, skipped when it
  already holds 8, and ended early by an empty candidate list (§ 2).
- [L] src:fandom-d2-elite-monsters (Unique Monsters): superuniques "always have 3-6 minions. They have one bonus on Normal,
  two on Nightmare and Three on Hell". **contradicted** (backlog 2026-10-14 reverser → reverser, case 3)
  Detail: the sentence's subject is the superunique. A superunique gets its record's `Mod1`–`Mod3` (0 to 3, `thief` dropped)
  plus `difficulty` unique picks, and `MinGrp + d .. MaxGrp + d` minions (§ 6); the run had 3 to 10 minions (Rakanishu 10,
  Megaflow Rectifier 8) and 2 extra picks in hell (`[C]`, § 6). The numbers fit random uniques (`1 + d` mods, 3..6 minions, § 1–2), which is likely what was
  meant. Phase 2 reproduced Rakanishu 8, 9 and 10 and the extras in nightmare and hell (run:2026-10-14-mon-special, § 6).
- [L] src:arreat-summit-monster-pages and src:fandom-d2-elite-monsters (Super Unique Monsters): superuniques have only their
  set bonuses in Normal and gain 1 random unique bonus in Nightmare and 2 in Hell, "in addition to any other Magical Bonuses
  they may already have". **held with refinement**
  Detail: the extras are `UniqueModPick` draws on the unit seed with the fixed mods already in `have`, so an extra never
  repeats a fixed mod; they pass `ModEligible`, which the fixed mods skip (§ 6).
- [L] src:fandom-d2-elite-monsters (Super Unique Monsters): superuniques "have a set amount of minions (or no minions),
  always with 1 more minion on Nightmare and 2 more on Hell". **held with refinement**
  Detail: `d` is added to both bounds only when `MinGrp` and `MaxGrp` are both non-zero (`0x005A4B72`–`0x005A4B86`), so a
  record with no minions keeps none and still costs one `RangeB(1)` draw (§ 6).
- [L] src:d2dfg-blizzard: SuperUniques `MinGrp`/`MaxGrp`: "a random number will be chosen between the MinGrp and MaxGrp
  values". **held with refinement**
  Detail: `min + RangeB(boss.seed, max − min + 1)`, one draw also when they are equal, after the difficulty bonus above
  (§ 5, § 6).
- [L] src:fandom-d2-elite-monsters (Super Unique Monsters): superuniques "except Act Bosses, have 1-3 special attributes
  that are fixed". **held with refinement**
  Detail: from data, four records have none (Ancient Barbarian 1–3, Nihlathak Boss); in code `thief` is never written, so
  Lord De Seis has two, and Megaflow Rectifier's `rndname` gives no visible bonus (§ 6).
- [L] src:arreat-summit-monster-pages: the "Special Attributes" of each superunique on the act pages. **held**
  Detail: they are the `Mod1`–`Mod3` of the records compared (data). Lord De Seis lists no thief, because `thief` is
  dropped, and "Aura Enchanted (Fanaticism)", because his aura index is forced to 5 and row 5 of the aura table holds skill
  122 (§ 4, § 6).

**Mod choice and exclusions**

- [L] src:arreat-summit-bonuses: "All permitted bonuses have an equal chance of selection, and are applied in displayed
  order." **held with refinement**
  Detail: each pick is one `Range(unit.seed, Σw)` over the candidates in row order. The chances are equal only because every
  stock `upick` is 6. The handlers run for mods 1–4 first and then in list order (§ 3, § 4).
- [L] src:arreat-summit-bonuses: Magic Resistant "Cannot be randomly selected in Normal". **held**
  Detail: `resist` has `upick` 0/6/6, read at `+0x14 + 2·d` (§ 3; data).
- [L] src:arreat-summit-bonuses: "Leapers cannot spawn Lightning Enchanted". **held**
  Detail: `lightning` has `exclude1` = `sandleaper`, tested by `MonTypeIsA` (§ 3). The matrix builder is still unread
  (*Open questions*).
- [L] src:arreat-summit-bonuses: Multishot "cannot be selected for all monster types". **held with refinement**
  Detail: `fPick` 2 refuses classes with `isMelee` or `nomultishot` (§ 3).
- [L] src:d2dfg-blizzard: `fPick` 1 = needs `mA1`, 2 = not `IsMelee` and not `nomultishot`, 3 = needs `mWL`. **held**
  Detail: the three `ModEligible` cases read the same columns (§ 3).
- [L] src:d2dfg-blizzard: `exclude1 & exclude2` name the monster types that may not have the mod. **held with refinement**
  Detail: the test is "is-a" through the MonType bit matrix, and the loop stops at the first value ≤ 0 (§ 3).
- [L] src:d2dfg-blizzard: `enabled` 0 means the mod "will never be used", and `version` < 100 is classic, 100 expansion.
  **held with refinement**
  Detail: both are `ModEligible` tests, with the expansion flag `game+0x70`. They do not apply to a superunique's fixed
  mods, so the disabled `thief` is filtered by its own test in `SuperUniqueSpawn` (§ 3, § 6).
- [L] src:d2dfg-blizzard: `cpick`/`upick` values are summed into one denominator and each acts as its numerator.
  **held with refinement**
  Detail: they are read as signed 16-bit values, and only those > 0 count. One `Range` is drawn over the sum, with no draw
  when the sum is < 1 (§ 3).
- [L] src:d2dfg-blizzard: `champion`: "If equals 1, then this monster modifier will only be used by Champion monsters. If
  equals 0, then the monster modifier can be used by any type of special monster." **contradicted** (backlog 2026-10-14
  reverser → reverser, case 1)
  Detail: the first half holds. The second half does not: the champion pick skips every row whose `champion` byte is 0
  (`0x005A056F`, re-read), so a `champion` = 0 mod is never a champion's mod. With stock data no `champion` = 0 row has a
  non-zero `cpick`, so the two readings give the same game. Only an edited table can tell them apart.
- [L] src:arreat-summit-bonuses: champions come in groups of 2–4, "all but one are always Champion, with the remaining
  having an equal chance of being Champion, Berserker, Fanatic, Ghostly or Possessed". **held with refinement**
  Detail: the special that starts the pack gets `ChampionModPick` (five weights of 1); every pack member gets mod 16 (§ 5).
  In a classic game the other four have `version` 100, so the pick is always `champion`. A MonPlace 3 preset champion gets
  mod 16 with no pick (§ 7), which the page does not cover.
- [L] src:fandom-d2-elite-monsters (Champion Monsters): Ghostly, Fanatic, Berserker and Possessed champions come with Lord
  of Destruction. **held**
  Detail: the four rows have `version` 100, refused in a classic game (§ 3).
- [L] src:d2dfg-blizzard: MonStats `SpawnUniqueMod`, a mod the monster "should always spawn with". **not covered**
  Detail: 1.14d's `monstats.txt` has no such column; the per-class fixed mods are hard-coded by `BaseId` in
  `MonPostCreateMods` and `MonPostCreateBoss` (§ 1). A later build's feature.

**Transfer to minions (`xfer`) and minion bonuses**

- [L] src:d2dfg-blizzard: `xfer` = 1 means the mod "can be transferred from the Boss monster to his Minion monsters,
  including auras". **held with refinement**
  Detail: the mods are copied into each minion's list when it is created (`ModsXferCopy`, § 5). `aura` has `xfer` 0 in
  stock data, so no aura is copied. Separately, every boss mod's handler, `xfer` or not, also runs on each group member with
  flag 0 (§ 4, § 5).
- [L] src:arreat-summit-bonuses and src:fandom-d2-elite-monsters (Minions): minions of Extra Strong, Extra Fast and the
  enchanted uniques get bonuses (the elemental ones "+33-50%" in Nightmare and Hell only); Aura Enchanted minions "may gain
  the benefit of the aura"; Spectral Hit minions get random elemental damage. **held with refinement**
  Detail: the handlers of `strong`, `fast`, `fire`, `lightning`, `cold` run on group members with flag 0 (§ 4). "Nightmare
  and Hell only" fits the data, since MonUMod `constants` rows 16–21 (minion elemental min/max %) are 0 in Normal and 33/50
  after. The aura handler does nothing with flag 0, so the minions' benefit is the aura's own area effect. The
  `spectralhit` handler is `resist` and does nothing with flag 0, so a minion's elemental hit would come from its copied list
  (`xfer` 1) at hit time. The effects themselves are `monsters/stats`.
- [L] src:arreat-summit-bonuses and src:fandom-d2-elite-monsters (Unique Monsters): unique and minions get level +3 and ×5
  experience; champions get level +2. **held with refinement**
  Detail: mod 4 `leveladd` (level + 3, experience × 5) always runs, and also runs on group members because it has no flag
  test. The `champion` handler takes 1 level off again. These are only named here (§ 4).
- [L] src:arreat-summit-bonuses: "Unique spawns with 3-6 minions". **held**
  Detail: `SpecialModsApply(…, 3, 6, minions 1)` from `SpecialMonSpawn` (§ 1, § 5).
- [L] src:arreat-summit-bonuses: Spectral Hit "Pick from Magic, Fire, Lightning, Cold and Poison". **not covered**
  Detail: handler 27 makes no draw at spawn (§ 4), so the element is chosen later, presumably per hit, outside this finding.
- [L] src:arreat-summit-bonuses: Cursed casts Amplify Damage on hit. **not covered**
  Detail: `curse` (7) has no server handler (§ 4); its effect is elsewhere.

**Aura choice**

- [L] src:arreat-summit-bonuses: possible auras Might (monlvl/6), Holy Fire (/6), Blessed Aim (/5), Holy Freeze (/7), Holy
  Shock (/8), Conviction (/8), Fanaticism (/8), minimum level 1, and "Holy Shock cannot be selected at mlvl <20". **held**
  Detail: the eight rows `{minLevel, add, mul, div, skill}` at `0x0073BF68` (dumped with r2) are (0,0,1,6,98),
  (0,0,1,6,102), (0,0,1,5,108), (0,0,1,7,114), (0,0,1,8,123), (0,0,1,8,122), (20,0,1,8,118) and (999,0,0,1,103). The level is
  clamped to 1..99, and the index is `Range(local, n)` on a seed made from the name seed (§ 4).

**Placement and colour of superuniques**

- [L] src:d2dfg-blizzard: `AutoPos` = 1: the superunique "will randomly spawn within a radius of its designated position".
  **contradicted** (backlog 2026-10-14 reverser → reverser, case 2)
  Detail: the preset point is discarded (x = y = 0) and `SpawnPosPick` draws a point anywhere in the room rectangle, on the
  room seed (§ 6, re-read). It is "near" only because the preset lies in that room.
  Settled in Phase 2: six `AutoPos` superuniques of run:2026-10-14-mon-special were placed as the model predicts (§ 6).
- [L] src:d2dfg-blizzard: `AutoPos` = 0: "spawn at exact coordinates of its designated position". **held with refinement**
  Detail: an exact `SpawnAtPos`, then radius 5 if that fails (§ 6).
- [L] src:d2dfg-blizzard: `Stacks` = 0: the superunique "can only spawn once in the same game". **held**
  Detail: the per-game placed bit at `game+0x1D30` is tested only when `Stacks` is 0 (§ 6).
- [L] src:d2dfg-blizzard: `hcIdx` IDs "are hardcoded for specific scripts". **held with refinement**
  Detail: the tail switch reads the record's `+0x08`. That field and `+0x00` both hold the row index (SuperUniques table
  doc), so which one is `hcIdx` does not change stock behaviour (§ 6).
- [L] src:d2dfg-blizzard: `Mod1`–`Mod3` take the MonUMod `id`. **held**
  Detail: `id` = row = handler index (§ 6).
- [L] src:d2dfg-blizzard and src:fandom-d2-elite-monsters: a `Utrans` value ≥ 30 falls back to the default palette 2
  (Pitspawn Fouldog 31, Stormtree 35, Battlemaid Sarina 36, Dac Farren 36 use default colours); 0 or empty means random.
  **held with refinement** for ≥ 30; **not covered** for 0
  Detail: the client code at `0x0046668F`–`0x004666A8` reads the record's byte `+0x28 + k` (`k` from `0x0044DCD0`, a byte at
  `0x007A060C`, probably the difficulty; not checked). A non-zero byte replaces the colour index, and anything ≥ 30 becomes 2.
  A 0 keeps the index computed before it, and no draw was seen there. No stock record has 0 (values 4..38). The colour is
  drawn on the client, outside the server's seeds, and the client name roll re-initialises its own seed (§ 8), so this
  cannot shift a modelled draw (*Open questions*).

**Names**

- [L] src:d2dfg-blizzard: UniquePrefix and UniqueSuffix are "always added"; UniqueAppellation is added with "a 50%
  chance", and the name then uses `Monster2Format` (1722) in place of `Monster1Format` (1721). **held with refinement**
  Detail: the roll is on the client, on `Init(nameSeed)`. Its order is suffix, prefix, `Range(100) < 50`, then appellation
  and a fresh suffix and prefix, so the first pair is discarded when the appellation is used (§ 8).
- [L] src:d2dfg-blizzard: SuperUniques `Name` "uses a string for the Super Unique monster's name". **held**
  Detail: the client takes the record's `Name` string for flag `0x02` (§ 8).
- UniqueTitle: no source read has a section on it (`src:d2dfg-blizzard` has no UniqueTitle.txt section). **not covered**
  Detail: the finding says it is loaded and never read (§ 8).
- The champion name "<mod word> <NameStr>" and the server/client split of the name roll. **not covered**
  Detail: no source read describes either.

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x005A0760` | `sub_005A0760_SpecialModsRoll` | champion roll, champion pick or `1 + d` unique picks | C |
| `0x005A0500` | `sub_005A0500_ChampionModPick` | weighted pick over `cpick`, `champion` = 1 rows | C |
| `0x005A0600` | `sub_005A0600_UniqueModPick` | weighted pick over `upick`, `champion` = 0 rows, minus present mods | C |
| `0x005A03E0` | `sub_005A03E0_ModEligible` | `enabled`, `version` vs expansion, `exclude1`/`exclude2`, `fPick` | C |
| `0x005A0070` | `sub_005A0070_MonTypeIsA` | MonType bit matrix (`DataTables+0xC44`) test of the class's MonType against a type | I |
| `0x0046C140` | `sub_0046C140_MonModeAllowed` | MonStats2 `+0xF0` mode bit of a class | I |
| `0x005A0260` | `sub_005A0260_ModCount` | mods up to the first 0, at most 9 | I |
| `0x005A02E0` | `sub_005A02E0_ModAppend` | write a mod into the first free slot (none if 9 are used) | I |
| `0x005A4850` | `sub_005A4850_ModAppendApply` | append a mod, call its handler; with arg 1 also `MonMarkSpecial` | I |
| `0x005A0930` | `sub_005A0930_ModsXferCopy` | copy the `xfer` mods of one monster into another's list | C |
| `0x005A2120` | `sub_005A2120_SpecialModsApply` | unique minions, then handlers of mods 1–4 and of the list, each also on the group | C |
| `0x005A2100` | `sub_005A2100_UModHandlerThunk` | callback of the group walk: handler of mod `EDX` with the passed flag | I |
| `0x0058F380` | `sub_0058F380_MonGroupForEach` | calls a callback on each member of the unit's leader's minion list | I |
| `0x005A0C00` | `sub_005A0C00_UniqueMinions` | `min + RangeB(max−min+1)` minions unless champion; xfer copy, link, flag `0x10` | C |
| `0x005A49B0` | `sub_005A49B0_SuperUniqueSpawn` | superunique from its record | C |
| `0x005A0200` | `sub_005A0200_MonSuperUniqueIdSet` | `MonsterData+0x26` = superunique id | I |
| `0x005B24E0` | `sub_005B24E0_EscortSpawn` | `n` × `SpawnNearUnitNoBox(class)`, linked to the unit | I |
| `0x005A48C0` | `sub_005A48C0_ChampionMemberMark` | pack member or preset champion: special, flags `0x05`, mod appended, `SpecialModsApply` | C |
| `0x005A4440` | `sub_005A4440_SpecialMonRestore` | inactive-unit restore of a special: saved mods and name seed, `SpecialModsApply` without minions | I |
| `0x005A46E0` | `sub_005A46E0_MinionRestore` | inactive-unit restore of a minion: saved mods, handlers with flag 0 | I |
| `0x005A4940` | `sub_005A4940_MonMakeSpecial` | an existing monster made special (`SpecialModsRoll(…, 1)`, apply without minions) | I |
| `0x005B21B0` | `sub_005B21B0_MonPostCreateMods` | MonSpawnTry post-create: per-`BaseId` fixed mods (flag 0) | I |
| `0x005B1CF0` | `sub_005B1CF0_MonPostCreateBoss` | MonSpawnTry post-create: act and uber bosses, fixed mods (flag 1) and quest hooks | I |
| `0x005A0CE0` … `0x005A1F90` | the 22 server handlers | table below | I |
| `0x005A00F0` | `sub_005A00F0_UModConstant` | MonUMod `constants` of a row (`+0x1C`) | I |
| `0x005A21D0` | `sub_005A21D0_UModElemDamage` | elemental damage % from `constants` rows 28 and 31 (`monsters/stats`) | I |
| `0x0054E600` | `sub_0054E600_PresetMonSpawn` | MonPreset dispatch; MonPlace cases 2, 3, `0x11`–`0x20` | I |
| `0x0054E2A0` | `sub_0054E2A0_PresetFallenVariant` | `fallen1`/`fallenshaman1` → act-1 variant by level id | I |
| `0x0063EC70` | `sub_0063EC70_LevelClassVariant` | the level's version of a base class (its `mon` list, else `NextInClass` by `Level`) | I |
| `0x0054E090` | `sub_0054E090_PresetGroupSpawn` | normal-difficulty MonPlace `0x18`/`0x1A`: a group in the preset's box | I |
| `0x0053E2E0` | `sub_0053E2E0_MonUnitPacketBuild` | server → client monster record: flags, superunique id, mods, name seed | I |
| `0x004AD020` | `sub_004AD020_ClientMonModsApply` | client: handlers of mods 1–4 and of the list from `0x00724D78` | I |
| `0x004AC870` | `sub_004AC870_ClientMonNameBuild` | client handler of mods 1, 12, 16, 36–39: the display name | C |
| `0x004AE320` | `sub_004AE320_ClientMonIsChampion` | flag `0x04` test | I |
| `0x0045F190` | `sub_0045F190_ClientMonAssign` | client reader of the monster record; keeps the low byte of the name seed (`0x0045F387`) | C |
| `0x00466360` | `sub_00466360_ClientMonCreate` | client monster unit from that record; stores the name seed and the mod list | I |
| `0x004AC780` | `sub_004AC780_ClientMonNameSeedSet` | client `MonsterData+0x14` = name seed (u16 write) | I |
| `0x00658520` | `sub_00658520_MonTypeLoad` | loads `montype`, builds the MonType bit matrix at `DataTables+0xC44` | I |
| `0x00658460` | `sub_00658460_MonTypeReachable` | `j` reachable from `i` through `equiv1`..`equiv3` (depth-first, stack 128) | I |
| `0x00653ED0` / `0x00653F10` / `0x00653F50` | `sub_00653ED0_UniquePrefixRoll` / `sub_00653F10_UniqueSuffixRoll` / `sub_00653F50_UniqueAppellationRoll` | `RangeB(seed, n)` row → string | C |
| `0x00653DB0` / `0x00653E20` | `sub_00653DB0_UNameTableLoad` / `sub_00653E20_UNameTablesFree` | load one / free all four name tables | I |
| `0x0065A400` | `sub_0065A400_MonsterTablesLoad` | loads `uniquetitle`, `uniqueprefix`, `uniquesuffix`, `uniqueappellation`, then the monster tables | I |

## Walkthrough

### 1. Where the special path is entered

| Caller | Unit | `SpecialModsRoll` | `SpecialModsApply` (minions?) |
|---|---|---|---|
| `sub_005A43E0_SpecialMonSpawn` (pass, MonPlace 2) | new boss | `allowChampion` as passed | yes, range 3..6 |
| `sub_005A48C0_ChampionMemberMark` (champion pack, MonPlace 3) | pack member / preset champion | no; mod 16 appended | yes, range 0..0 (skipped: champion) |
| `sub_005A49B0_SuperUniqueSpawn` (MonPreset superunique) | superunique | no; record mods | yes, `MinGrp+d .. MaxGrp+d` |
| `sub_005A4440_SpecialMonRestore` (inactive restore) | restored special | no; saved mods | no |
| `sub_005A4940_MonMakeSpecial` (caller `0x00583050`, not read) | existing monster | `allowChampion` = 1 | no |

- [I] The argument registers: `SpecialMonSpawn` calls `SpecialModsApply(game, boss, EDX = box, ECX = 3, EAX = 6, minions = 1)`
  (`0x005A4421`–`0x005A442C`); `ChampionMemberMark` zeroes `EAX`, `ECX` and `EDX` (`0x005A4926`–`0x005A492A`); `SuperUniqueSpawn`
  passes `EDX = 0`, `ECX = min`, `EAX = max` (`0x005A4B6C`–`0x005A4B8E`). `UniqueMinions` takes them as (box, min, max).
  (fn:sub_005A43E0_SpecialMonSpawn@0x005A43E0, fn:sub_005A48C0_ChampionMemberMark@0x005A48C0, fn:sub_005A49B0_SuperUniqueSpawn@0x005A49B0)
- [I] Before any of these, `MonSpawnTry`'s post-create helpers may already have put mods in the list:
  `sub_005B21B0_MonPostCreateMods` by `BaseId` (flag 0: `brute2` 13 `rage`, `scarab1` 20 `scarab`, `mummy1` 10 `poisondead`,
  `duriel` 11 + 22, traps 14 `spcdamage`, `boneprison1..4` 15 `partydead`, `reanimatedhorde1` 34, `suicideminion1` 33,
  `frozenhorror1` 35, `ancientbarb1..3` 22), and `sub_005B1CF0_MonPostCreateBoss` for the act bosses, Blood Raven (12 +
  22), the Maggot Queen, `firegolem` (31) and the uber bosses (e.g. `ubermephisto`: 22, 30, 17, 8, 6). These count as
  "mods already present" below. (fn:sub_005B21B0_MonPostCreateMods@0x005B21B0, fn:sub_005B1CF0_MonPostCreateBoss@0x005B1CF0, tbl:MonStats.txt:BaseId)
- [C] `MonPostCreateMods` appends its mods after the creation (after the `MU` line of the logger) and none of them has a server
  handler, so they draw nothing. In run:2026-10-14-mon-special the superunique Beetleburst (`scarab2`, `BaseId` `scarab1`) and
  its `scarab2` minions entered `SuperUniqueSpawn` and `ModsXferCopy` with mod 20 already present, as the model predicts.
  (fn:sub_005B21B0_MonPostCreateMods@0x005B21B0, 0x005B21B0–0x005B22A6, run:2026-10-14-mon-special)

### 2. `SpecialModsRoll`

```text
SpecialModsRoll(unit, game, allowChampion):                 ; fn:sub_005A0760_SpecialModsRoll, unit in ECX
  if game = 0 or game.difficulty >= 3 or unit is not a monster with data: return
  k <- ModCount(unit.mods)                                  ; mods at MonsterData+0x1C, u8[9], up to the first 0
  if k >= 8: return                                         ; 0x005A07CD
  if allowChampion != 0:                                    ; 0x005A07E7
    c <- MonUMod[0].constants (+0x1C) if the table has rows, else 0
    if Range(unit.seed, 100) < c:                           ; draw 1 (signed compare)
      unit.flags |= 0x04                                    ; MonsterData+0x16
      ModAppend(unit, ChampionModPick(unit, game))          ; draw 2; appends nothing when it returns 0
      return
  n <- Range(unit.seed, 1) + 1 + game.difficulty            ; one draw, always 0
  if k + n >= 9: n <- 9 - k                                 ; 0x005A088F
  have[0..nMonUMod) <- 0;  have[m] <- 1 for each present mod
  repeat while n > 0:
    m <- UniqueModPick(unit, game, have)                    ; one draw unless no candidate
    if m = 0: stop
    append m;  have[m] <- 1;  n <- n - 1
```

- [I] Integer widths: the weights are u16 read as signed shorts (`movsx`); `Range` is `RNG_Range` (`n < 1` → 0 and no
  step, rng/0001). The unique pick inlines the same draw (`total & (total−1) = 0` → mask, else unsigned `mod`).
  (fn:RNG_Range@0x0045C390, 0x005A06CC–0x005A070A)
- [C] With `allowChampion` = 0 the `Range(100)` draw is not made at all (the `je 0x005A0871` skips it), so a MonPlace 2
  special is always a unique and costs one draw less: 4 MonPlace 2 rolls of run:2026-10-14-mon-special. (0x005A07E7, run:2026-10-14-mon-special)
- [C] The champion branch appends one mod only; a champion never gets unique mods from this function: 16 champion rolls of
  run:2026-10-14-mon-special. (0x005A0843–0x005A0853, run:2026-10-14-mon-special)
- [C] The draw counts, by the logged unit seeds of run:2026-10-13-mon-spawn (`SMR1` after the `Range(100)`, `SMRX` at
  exit): 1 step for each of the 4 champions; 2 for each of the 5 normal uniques (`Range(1)` + one pick); 4 for each of
  the 15 hell uniques (`Range(1)` + three picks), and no logged roll ran out of candidates. (run:2026-10-13-mon-spawn)

### 3. The two picks and `ModEligible`

```text
ChampionModPick(unit, game):                                ; fn:sub_005A0500_ChampionModPick
  cand <- []
  for r in 0 .. nMonUMod-1 (stop at 256 candidates):
    w <- s16 MonUMod[r] +0x0E + 2*difficulty                ; cpick, cpick (N), cpick (H)
    if w > 0 and MonUMod[r].champion (+0x08) != 0 and ModEligible(MonUMod[r], game.expansion, unit):
      cand += (r, w)
  x <- Range(unit.seed, sum w)                              ; no draw when the sum is < 1
  return the first r whose cumulative weight exceeds x, else 0

UniqueModPick(unit, game, have):                            ; fn:sub_005A0600_UniqueModPick
  as above with w <- s16 MonUMod[r] +0x14 + 2*difficulty    ; upick, upick (N), upick (H)
  and MonUMod[r].champion = 0 and have[r] = 0
  if sum w < 1: return 0                                    ; no draw

ModEligible(rec, expansion, unit):                          ; fn:sub_005A03E0_ModEligible, unit in EBX
  if rec.enabled (+0x06) = 0: no
  if expansion = 0 and rec.version (+0x04, u16) >= 100: no
  for t in rec.exclude1 (+0x0A), rec.exclude2 (+0x0C), stopping at the first t <= 0 (s16):
    if MonTypeIsA(unit.class, t): no                        ; fn:sub_005A0070_MonTypeIsA
  case rec.fPick (+0x09):
    1: yes only if MonModeAllowed(unit.class, 4)            ; MonStats2 +0xF0 bit 4 (mA1)
    2: no if MonStats[class] +0x0C bit 1 (isMelee) or +0x0E bit 1 (nomultishot)
    3: yes only if MonModeAllowed(unit.class, 2)            ; bit 2 (mWL)
  yes
```

- [C] The expansion flag is the dword `game+0x70`, the only expansion read on the special path. Classic games therefore have
  one champion candidate (`champion`, 16; the other four have `version` 100) and the same 12 or 13 unique candidates: the
  logged candidate lists of the classic games of run:2026-10-14-mon-special (normal, nightmare, hell) are those.
  (0x005A0523, 0x005A03F4–0x005A03FF, tbl:MonUMod.txt:version, struct:Game+0x070, run:2026-10-14-mon-special)
- [C] `fPick` is a row's extra test (every logged candidate list of run:2026-10-14-mon-special agrees, over the classes rolled): `teleport` (1) needs the class to have mode `A1`, `multishot` (2) is refused to melee and
  `nomultishot` classes, `fast` (3) needs mode `WL`. `sub_0046C140_MonModeAllowed` reads the class's MonStats2 record
  (`MonStats+0x18`) and tests bit `mode` of the bitfield at `+0xF0`, the `mDT…mRN` columns.
  (0x005A0436–0x005A04E9, fn:sub_0046C140_MonModeAllowed@0x0046C140, tbl:MonStats2.txt:mA1, tbl:MonStats.txt:isMelee, tbl:MonStats.txt:nomultishot, tbl:MonUMod.txt:fPick)
- [I] `MonTypeIsA(class, t)` reads the class's MonType (`MonStats+0x1C`) and tests bit `classType` of row `t` in the u32 bit
  matrix at `DataTables+0xC44` (row length `DataTables+0xC48` dwords, `DataTables+0xC40` types), with `t` and `classType`
  in `[0, nTypes)`. (fn:sub_005A0070_MonTypeIsA@0x005A0070, tbl:MonUMod.txt:exclude1, tbl:MonStats.txt:MonType)
- [I] **The matrix builder** (read in Phase 2, 2026-10-14). `sub_00658520_MonTypeLoad` loads `montype` (records of 12 bytes:
  `+0x02`, `+0x04`, `+0x06` = `equiv1`..`equiv3`, s16), allocates `nTypes` rows of `(nTypes + 31) / 32` dwords, and sets bit
  `j` of row `i` for every pair with `sub_00658460_MonTypeReachable(i, j)` ≠ 0 (`0x00658670`–`0x006586C6`). That function
  returns 0 when `j` ≤ 0 or `i` is not in `(0, nTypes)`; otherwise it walks depth-first from `i` with a stack of 128: pop
  `c`; `c = j` → 1; `c` ≥ `nTypes` or more than 124 entries left → 0; push `equiv1` if > 0, then `equiv2` if ≠ 0, then
  `equiv3` if ≠ 0 (the later ones only after a pushed earlier one). So row `t` holds the types reachable from `t`, `t`
  itself included, and `MonTypeIsA(class, t)` is "the class's MonType is reachable from `t`": an `exclude` type excludes its
  own classes and those of the types it lists as `equiv`, not the classes of types that list it.
  (fn:sub_00658520_MonTypeLoad@0x00658520, fn:sub_00658460_MonTypeReachable@0x00658460, 0x00658460–0x0065851F)
- [I] With stock data the only exclusion is `lightning` ↛ `sandleaper`, and `sandleaper` lists no `equiv`, so the test
  refuses `lightning` exactly to the classes of MonType `sandleaper`; the two possible directions of the closure agree on
  stock data, because no MonType lists `sandleaper` as an `equiv`. (fn:sub_00658460_MonTypeReachable@0x00658460, tbl:MonUMod.txt:exclude1)
- [I] The candidate order is the row order and the draw is one `Range` over the total; with stock weights (champion: five
  1s; unique: twelve or thirteen 6s) each candidate is equally likely. (tbl:MonUMod.txt:upick)

### 4. `SpecialModsApply` and the per-handler draw table

```text
SpecialModsApply(game, unit, EDX = box, ECX = min, EAX = max, minions):   ; fn:sub_005A2120_SpecialModsApply
  if minions != 0: UniqueMinions(unit, box, min, max)                       ; § 5
  for m in (1, 2, 3, 4):                                                    ; dwords at 0x006E2168
    if UModHandlers[m]: UModHandlers[m](ECX = unit, EDX = m, flag 1)
    MonGroupForEach(unit, m, flag 0, UModHandlerThunk)                      ; the same handler on each group member
  for i in 0..8 while unit.mods[i] != 0:
    m <- unit.mods[i]; the same two calls
```

- [I] The handler table `g_UModHandlers` (`0x0073C008`) has one code pointer per MonUMod row; rows 0, 3, 7, 10–15, 19–22,
  24, 29, 31–35, 40 and 42 are null. The flag argument is 1 for the special itself and 0 for a group member or a minion
  restore. (data:g_UModHandlers@0x0073C008, data:g_UModAlwaysMods@0x006E2168)
- [I] `sub_0058F380_MonGroupForEach(unit, mod, flag, cb)` looks up the unit's leader through `MonsterData+0x28`
  (`+0x28` ≠ 0, leader type and id at `+0x2C`/`+0x30`, `sub_00552F60_GameFindUnit`) and calls `cb(flag)` with `ECX` = each unit
  of the leader's list at `+0x34`, `EDX` = `mod`. (fn:sub_0058F380_MonGroupForEach@0x0058F380, struct:MonsterData+0x28)

**Draws per handler** (flag 1 = the special; flag 0 = a group member):

| Mod (row) | Server handler | Unit seed | Room / game seed | Other | Flag 0 | Effect (named only, `monsters/stats`) |
|---|---|---|---|---|---|---|
| 1 `rndname` | `sub_005A0CE0_UModRndName` | **1 step**; name seed = low 16 bits | — | — | nothing | name seed `MonsterData+0x14` |
| 2 `hpmultiply` | `sub_005A0DC0_UModHpMultiply` | — | — | — | runs | HP + `constants` % |
| 4 `leveladd` | `sub_005A0E40_UModLevelAdd` | — | — | — | runs (no flag test) | level + 3 (stat 12), experience × 5 (stat 13) |
| 5 `strong` | `sub_005A17E0_UModStrong` | — | — | — | runs | to-hit and damage % from `constants` 12–15 |
| 6 `fast` | `sub_005A1910_UModFast` | — | — | — | runs | velocity % (stat 67) from MonStats `Velocity` |
| 8 `resist`, 27 `spectralhit`, 28 `stoneskin` | `sub_005A1370_UModResist` | — | — | — | nothing | resistances |
| 9 `fire`, 17 `lightning`, 18 `cold`, 23 `poisonhit`, 25 `manahit` | `sub_005A1990_UModFire`, `sub_005A1B00_UModLightning`, `sub_005A1C70_UModCold`, `sub_005A1E00_UModPoisonHit`, `sub_005A1F90_UModManaHit` | — | — | — | runs (the `resist` part is skipped) | enchant damage from MonLvl and `constants`, then `resist` |
| 16 `champion` | `sub_005A0E80_UModChampion` | — | — | — | nothing | level − 1, experience, to-hit and damage %, velocity |
| 26 `teleport` | `sub_005A1600_UModTeleport` | — | — | skill setup `0x0056DEB0`, `0x006439F0`, `0x00644340`, `0x005DD250` | nothing | teleport skill |
| 30 `aura` | `sub_005A1650_UModAura` | — | — | **local seed** `Init(nameSeed)`: `Range(local, n)` | nothing | aura skill and level (`0x0056DEB0`, `0x005701B0`) |
| 36 `ghostly`, 37 `fanatic`, 38 `possessed` | `sub_005A1080_UModGhostly`, `sub_005A11F0_UModFanatic`, `sub_005A1230_UModPossessed` | — | — | — | nothing | flag `0x40`/`0x20`, then `champion`'s effects |
| 39 `berserk` | `sub_005A1280_UModBerserk` | — | — | — | nothing | life −75 %, damage and to-hit; **no** `champion` part ([monsters/0004 § 8](0004-stats.md), `[C]` on run:2026-10-15-berserk-forced) |
| 41 `always_run_ai` | `sub_005A1330_UModAlwaysRunAi` | — | — | AI event `0x005417D0` | runs (no flag test) | AI timer |

- [I] Static: `tools/ghidra.sh rngcallgraph - <handler>` on 18 of the 19 distinct handlers finds no LCG step and no RNG
  call in the stat handlers (2, 4, 5, 8/27/28, 9, 16, 17, 18, 23, 25, 36–39: 573–582 functions each, 0 RNG-bearing; their 56
  indirect calls, the stat callbacks, are not followed), the single step of `rndname`, the local-seed draw of `aura`, and
  RNG reachable only through the skill and AI callees of `teleport`, `aura` and `always_run_ai` (depth ≥ 5). `fast`
  (`0x005A1910`) is a 35-instruction stub with one call (stat set). (fn:sub_005A0CE0_UModRndName@0x005A0CE0, fn:sub_005A1600_UModTeleport@0x005A1600, fn:sub_005A1330_UModAlwaysRunAi@0x005A1330, fn:sub_005A1910_UModFast@0x005A1910)
- [C] At run time (run:2026-10-13-mon-spawn, 67 handler windows `SMA1` → `SMAX`, bosses and pack members, normal and
  hell, including uniques with `teleport` and `aura`): the unit seed moved by the number of `rndname` calls in all 67, and
  the room and game seeds did not move in the 30 windows inside a pass that logged them (the others log none). The single 2-step window is Megaflow Rectifier (record 49, `Mod1` = `rndname`): mod 1 runs
  once from the fixed list and once from the mod list. (fn:sub_005A2120_SpecialModsApply@0x005A2120, run:2026-10-13-mon-spawn)
- [I] **Aura choice.** `n` counts the rows of the 8-row table at `0x0073BF68` (`{minLevel, add, mul, div, skill}`, 0x14 bytes)
  whose `minLevel` ≤ the monster's level (stat 12, after `leveladd`); stock rows give 6 below level 20 and 7 from 20 on
  (Might, Holy Fire, Blessed Aim, Holy Freeze, Conviction, Fanaticism; Holy Shock from 20; the eighth row, Thorns, has
  `minLevel` 999). The index is `Range(local, n)` on a local seed `RNG_SeedInit(local, nameSeed)`, forced to 5 for
  superunique 37 (Lord De Seis). Skill level = `(add + level)·mul / div` (signed), clamped to 1..99. Class 704
  (`ubermephisto`) skips this and gets Conviction at level 20. Because the seed is local, the aura draws touch no
  persistent seed. (fn:sub_005A1650_UModAura@0x005A1650, data:g_UModAuraTable@0x0073BF68, fn:RNG_SeedInit@0x00650E40)
- [I] **The handler in instruction order, with its guards** (written 2026-10-15 from the disassembly; stock data reaches
  none of the guards, since the aura table's first rows have `minLevel` 0 and a monster's level is ≥ 1) (fn:sub_005A1650_UModAura@0x005A1650, data:g_UModAuraTable@0x0073BF68):
  ```text
  UModAura(unit = ECX, flag = [esp+4])                       ; fn:sub_005A1650_UModAura@0x005A1650, stdcall 1 arg
    if unit = null or unit.type != 1 or flag = 0: return      ; 0x005A1659-0x005A1670
    lvl <- STATS_GetUnitStat(unit, 12)                        ; 0x005A167B
    if lvl <= 0: lvl <- 1                                     ; 0x005A1685-0x005A1687 (signed jg)
    n <- #{ r in AuraTable[0..7] : r.minLevel <= lvl }         ; 0x005A1694-0x005A16EB, a count, not a prefix length
    if n = 0: n <- 1                                          ; 0x005A16EE-0x005A16F2
    s <- MonsterData ? MonsterData+0x14 (u16 name seed) : 0x1506   ; 0x005A16F7-0x005A170B
    RNG_SeedInitOne(local); RNG_SeedInit(local, s)            ; 0x005A1712, 0x005A171D
    i <- RNG_Range(local, n)                                  ; 0x005A1727
    if MonsterData and MonsterData+0x26 = 37: i <- 5          ; 0x005A172C-0x005A1743 (Lord De Seis)
    if unit.class = 704: UnitSkillAdd(123, 20); sub_005701B0(123); return   ; 0x005A1748-0x005A1773
    k <- (AuraTable[i].add + lvl) * mul / div                 ; 0x005A1776-0x005A178F, signed idiv, lvl the guarded value
    k <- 1 if k <= 1; 99 if k >= 99                           ; 0x005A1795-0x005A17A4, 0x005A17CE
    UnitSkillAdd(AuraTable[i].skill, k); sub_005701B0(AuraTable[i].skill)   ; 0x0056DEB0, 0x005701B0 (sets the skill mode)
  ```
  - The level guard maps `lvl ≤ 0` to 1, and that guarded level is also the one in the skill-level formula. The count
    guard maps `n` = 0 to 1, so `Range(local, 1)` returns 0 (one step on the local seed) and row 0 is used. Both match
    `tools/monspecial.py` (`Data.aura`). (0x005A1685, 0x005A16EE, fn:sub_005A1650_UModAura@0x005A1650)
  - `n` counts every row with `minLevel ≤ lvl` and the index then reads rows `0..n−1`, so the pick equals "the first `n`
    rows" only because the stock table is sorted by `minLevel`. (data:g_UModAuraTable@0x0073BF68)
  - The draw comes **before** the class-704 and Lord De Seis tests, so `ubermephisto` and Lord De Seis also consume one
    step of their local seed; the seed is local, so no persistent seed sees it. (0x005A1727, 0x005A1748)
  - Without a `MonsterData` (not reachable for a monster unit) the seed would be `0x1506`. (0x005A1704)
- [C] The draw: in run:2026-10-14-mon-special 12 aura uniques drew `Range(Init(nameSeed), n)` as predicted, with n = 6 once
  (normal, level 5) and n = 7 eleven times (indices 0 to 6 all seen). The level the handler reads equalled `MonStatsInit` + 3
  (`leveladd`) in the 10 expansion cases but was the bare MonStats `Level(N)` (50, not 53) in the 2 classic nightmare cases;
  that rule is `monsters/stats` (*Open questions*), and both give n = 7 there. Lord De Seis and class 704 were not reached.
  (fn:sub_005A1650_UModAura@0x005A1650, fn:sub_005A0E40_UModLevelAdd@0x005A0E40, run:2026-10-14-mon-special)

### 5. Minions and `xfer`

```text
UniqueMinions(boss, box, min, max):                          ; fn:sub_005A0C00_UniqueMinions (EDI = boss)
  if boss is a champion (flags & 0x04): return
  cls <- UniqueMinionClass(boss)                             ; minion1, else the boss's class
  if cls invalid: return
  n <- min + RangeB(boss.seed, max - min + 1)                ; one draw, also when min = max
  repeat n:
    m <- box ? SpawnNearUnit(boss, box, cls, 1, radius 3, 0x40) : SpawnNearUnitNoBox(cls, 1, 3, 0x40)
    if m: ModsXferCopy(dst = m, src = boss, overwrite = 0); link m to the boss (0x0058F030, 0x0058F100); 0x005DD330
          m.flags |= 0x10
```

- [C] `ModsXferCopy` starts at the minion's first free slot (its own post-create mods stay) and walks the boss's list up to
  the first 0 or the ninth slot, copying each mod whose MonUMod `xfer` (`+0x07`) is set. The slot counter advances for
  every boss mod examined, copied or not. Every minion's list after the copy (`XF`) was predicted in
  run:2026-10-14-mon-special, incl. Beetleburst's `scarab2` minions, whose own post-create mod 20 comes first. (0x005A09A8, fn:sub_005A0930_ModsXferCopy@0x005A0930, tbl:MonUMod.txt:xfer, run:2026-10-14-mon-special)
- [C] The copy happens when each minion is created, inside `SpecialModsApply`, so the boss's rolled mods (and a
  superunique's fixed and extra mods) are already in its list. Mods appended later (mod 22 of a superunique, a
  champion's mod) are not copied. (0x005A0C8F, 0x005A4B8E, run:2026-10-14-mon-special)
- [I] What the copied mods do on the minion is not decided here: the minion's handlers are not called for its own list;
  the boss's handlers reach it with flag 0 through `MonGroupForEach` (§ 4), for every boss mod. The copied list is what the
  server sends to the client (§ 8) and what other code reads (`monsters/stats`). (fn:sub_0058F380_MonGroupForEach@0x0058F380, fn:sub_0053E2E0_MonUnitPacketBuild@0x0053E2E0)
- [C] A superunique without MonStats `minion1` gets minions of its own class: Megaflow Rectifier (class 453 `minion1`)
  got 8 minions of class 453 in run:2026-10-13-mon-spawn. (fn:sub_005A0BB0_UniqueMinionClass@0x005A0BB0, run:2026-10-13-mon-spawn)

### 6. Superuniques: `SuperUniqueSpawn`

```text
SuperUniqueSpawn(game ECX, room EDX, x, y, id):             ; fn:sub_005A49B0_SuperUniqueSpawn
  if game.difficulty > 2: return 0
  rec <- SuperUniqueGet(id);  if rec = 0 or rec.Class (+0x04) < 0: return
  if rec.Stacks (+0x26) = 0 and placed[id]: return          ; bit (1 << (id & 7)) of byte game+0x1D30 + (id >> 3)
  if rec.AutoPos (+0x24) != 0: x, y <- 0, 0                 ; random point in the room
  u <- SpecialMonPlace(room, box 0, x, y, -1, avoidWarp 0, class = rec.Class)
  if u = 0: return
  placed[id] <- 1;  u.flags |= 0x02;  u.superUniqueId (+0x26) <- id
  if ModCount(u.mods) >= 5: return                          ; 0x005A4AD4: nothing below runs
  aura <- 0
  for j in 0..2: m <- rec.Mod[j] (+0x0C + 4j);  if m = 0: stop
    if m = 24 (thief): skip                                  ; not written
    if m = 30 (aura): aura <- 1
    append m; have[m] <- 1
  repeat game.difficulty times:                              ; 0 / 1 / 2 extra mods
    m <- UniqueModPick(u, game, have);  if m = 0: stop;  append m;  have[m] <- 1
  (min, max) <- (rec.MinGrp +0x1C, rec.MaxGrp +0x20); if both != 0: min += d; max += d
  SpecialModsApply(game, u, box 0, min, max, minions 1)      ; § 4, § 5
  if aura: UModAura(u, mod 30, flag 1)                       ; a second time
  switch rec.hcIdx (+0x08): hard-coded tails (below)
  ModAppendApply(u, 22 questcomplete, 1)                     ; every record, after its tail
```

- [C] `SpecialMonPlace` with no box and radius argument −1 tries an exact `SpawnAtPos(x, y, class, 1, −1, 0x40)` and then
  `SpawnAtPos(…, 5, 0x40)`. With `AutoPos` it first draws a point with `SpawnPosPick(no box, avoidWarp 0)` over the room
  rectangle (room-seed draws as in monsters/0002 § 6). The superunique is marked special (region `+0x2C8`) and gets flag
  `0x01`. Reproduced for 5 exact placements and 6 `AutoPos` placements (Phase 1b case 2: e.g. Griswold at (25141, 5179) for
  the preset point (25131, 5191)), with the collision predicates on the `SNP` snapshot. (fn:sub_005A09E0_SpecialMonPlace@0x005A09E0, 0x005A4A2B–0x005A4A4E, tbl:SuperUniques.txt:AutoPos, run:2026-10-14-mon-special)
- [I] `Mod1`–`Mod3` are MonUMod row indices: they are written into the mod list unchanged and dispatched through
  `g_UModHandlers[m]`. `thief` (24, `enabled` 0, Lord De Seis's `Mod3`) is dropped; `aura` (30, Bremm Sparkfist, Lord De
  Seis, The Feature Creep) is kept and its handler runs twice (same local seed, same result). Fixed mods skip
  `ModEligible`: `rndname`, `poisonhit` and the `fPick`/`exclude` tests do not apply. (0x005A4AF0–0x005A4B22, tbl:SuperUniques.txt:Mod1)
- [C] The extra picks use the unique pick of § 3 with the fixed mods in `have`, so they never repeat a fixed mod; mods the
  monster had before (its post-create mods, e.g. Beetleburst's 20) are not in `have` (`memset` at `0x005A4ABB`, then only
  the written fixed mods). 7 superuniques of run:2026-10-14-mon-special drew 1 or 2 extras as predicted.
  (0x005A4B24–0x005A4B6A, run:2026-10-14-mon-special)
- [C] In run:2026-10-13-mon-spawn the unit seed moved 0 steps between the superunique's placement and `SpecialModsApply` in
  normal difficulty (Beetleburst, Megaflow Rectifier, Sharp Tooth Sayer) and 2 steps in hell (Rakanishu, Treehead
  WoodFist, Pitspawn Fouldog), and the logged minion counts were 3 (Beetleburst 3..3), 8 (Megaflow 8..8), 3 (Sharp Tooth
  Sayer 3..3), 10 (Rakanishu 8..8 + 2), 4 (Treehead 2..2 + 2) and 6 (Pitspawn 4..4 + 2), each after one draw. (fn:sub_005A49B0_SuperUniqueSpawn@0x005A49B0, run:2026-10-13-mon-spawn)
- [I] A record with `MinGrp` = `MaxGrp` = 0 still costs one `RangeB(1)` draw and makes no minion; one with only one of the
  two non-zero does not get the difficulty bonus. (0x005A4B72–0x005A4B86)

**Hard-coded tails**, by the record index at `+0x08` (`Superunique` key = row index); calls are named only:

| Record | Superunique | Tail | Draws |
|---|---|---|---|
| 6 | The Countess | state 118 (`0x00639DB0`), quest hook 5 (`0x005436B0`), AI mode 13 (`0x005B0E00`) | — |
| 10 | Radament | `2 + Range(unit.seed, 5)` × `skeleton5`, then one each of `skmage_pois3`, `skmage_cold4`, `skmage_fire3`, `skmage_ltng3`, all `SpawnNearUnitNoBox(…, 1, radius 4, 0x40)` | **1 unit draw**, then room and game draws of each spawn |
| 26, 27, 29 | Ismail Vilehand, Geleb Flamefinger, Toorc Icefist | quest hook 19, `0x00545B50` | — |
| 36, 37, 38 | Infector of Souls, Lord De Seis, Grand Vizier of Chaos | quest hook 23 | — |
| 39 | The Cow King | quest hook 4 | — |
| 42 | Siege Boss | `EscortSpawn(minion1, radius 20, 20 ×, flags 0)`, quest hook 31, `0x00545B50`, state 118 | spawns |
| 43, 44, 45 | Ancient Barbarian 1–3 | quest hook 35, `0x00545B50` | — |
| 60 | Nihlathak Boss | links itself, `EscortSpawn(LevelClassVariant(minion1), radius 10, 20 ×, 0x40)`, quest hook 34 | spawns |
| 62 | Baal Subject 2 | `EscortSpawn(skmage_cold3, radius 20, 10 ×, 0x40)` | spawns |

- [I] Case 10's count is `RNG_Range(u+0x20, 5) + 2` at `0x005A4CD1`; the escorts get no mods and no transfer. The
  `EscortSpawn` members are linked to the superunique (`0x0058F030`, `0x0058F100`). (fn:sub_005B24E0_EscortSpawn@0x005B24E0, 0x005A4CD1–0x005A4D4B)
- [I] The `Stacks` byte is the only "may repeat" switch; there is no quest test inside `SuperUniqueSpawn` itself (the quest
  hooks register the unit, they do not gate it). (0x005A4A09–0x005A4A25, tbl:SuperUniques.txt:Stacks)

### 7. MonPlace presets 2 and 3, and `0x11`–`0x20`

`sub_0054E600_PresetMonSpawn(game ECX, room EDX, id, x, y, mode)`; a MonPlace index is `id − nMonStats − nSuperUniques`.
At `0x0054E651` the function overwrites its first argument with the room's level id, which later code reads.

- [C] **Case 2** (a unique from the region): `PickClass(game, region, room, threshold 0, special 1)` and, if valid,
  `SpecialMonSpawn(box 0, class, allowChampion 0, x 0, y 0, avoidWarp 1)`: the preset point is **not** used; the boss stands
  at a random point of the room away from warps, rolls `1 + d` unique mods without the `Range(100)` draw, and gets 3..6
  minions. Reproduced in Tristram in four games (run:2026-10-14-mon-special). (0x0054E850–0x0054E890, fn:sub_005BDE80_MonRegionPickClass@0x005BDE80, run:2026-10-14-mon-special)
- [C] **Case 3** (a champion at the point): the same class pick, then `SpawnAtPos(x, y, class, mode, −1, flags 0)` (MonStats
  minions are made), `ChampionMemberMark(u, 16)` (special, flags `0x05`, mod `champion` appended, `SpecialModsApply`: one
  `rndname` draw), then `ChampionPack(no box, class)` (`seed mod 3 + 1` members, each with mod 16). There is no
  `ChampionModPick`: a preset champion is always mod 16. Reproduced in the same four games. (0x0054E8A0–0x0054E909, fn:sub_0054E1E0_ChampionPack@0x0054E1E0, run:2026-10-14-mon-special)
- [I] **`0x11`–`0x20`** (fixed classes at the point): 17 `fallen1`, 18 `fallenshaman1`, 22 `fetish1`, 23 `fetishshaman1`;
  29 `minion1`, 30 `imp1` (`deathmauler1` in level 110), 31 `act5barb1`, 32 `reanimatedhorde3`, these four with mode 12;
  19–21 and 24 class 0; 25 and 28 nothing. The class goes through `sub_0063EC70_LevelClassVariant(room, class)` (the level's
  `mon` entry with the same `BaseId`, else the `NextInClass` chain while `Level` ≤ the level's `MonLvl1Ex` + 1) and then
  `sub_0054E2A0_PresetFallenVariant(class, levelId)`: `fallen1` → `fallen2` in level 6 and `fallen3` in levels 7, 12, 16;
  `fallenshaman1` → `fallenshaman2` in 6 and 7, `fallenshaman3` in 12 and 16. The spawn is `SpawnAtPos(…, −1)` then radius 4,
  flags 8 when the class is `neverCount`; `reanimatedhorde3` (438) draws `Range(u.seed, 50)` for an AI timer; mode 12 sets unit
  `+0xC4` bit 25. (0x0054E96D–0x0054EA9D, fn:sub_0054E2A0_PresetFallenVariant@0x0054E2A0, fn:sub_0063EC70_LevelClassVariant@0x0063EC70, tbl:Levels.txt:mon1, tbl:MonStats.txt:NextInClass, tbl:MonStats.txt:Level)
- [I] `0x18` and `0x1A` are normal-difficulty only: `sub_0054E090_PresetGroupSpawn` with class `imp1`/`deathmauler1`
  (by level 110) or `minion1`, a leader in the preset's box and `MinGrp − 1 + RangeB(leader.seed, MaxGrp − MinGrp + 1)` members around it.
  (0x0054EAA8–0x0054EAF9, fn:sub_0054E090_PresetGroupSpawn@0x0054E090, tbl:MonStats.txt:MinGrp)

### 8. Names: server seed, client roll

- [I] **Server.** The only server state behind a name is the name seed (`MonsterData+0x14`, u16), written by `rndname` (§ 4)
  and restored with saved units (`SpecialMonRestore`). The monster record sent to clients
  (`sub_0053E2E0_MonUnitPacketBuild`, sent when the monster has mods or unit `+0xC4` bit 9) carries one bit each for flags
  `0x04`, `0x08`, `0x02`, `0x10`, `0x40`, the 16-bit superunique id when `0x02`, the mod list as bytes ending with 0, and
  the 16-bit name seed. (0x0053E4BF–0x0053E5D6, fn:sub_005A0140_MonNameSeedGet@0x005A0140)
- [I] **The client keeps the low byte** (Phase 2 correction, 2026-10-14). The client's reader of that record,
  `sub_0045F190_ClientMonAssign`, reads the name seed with `BITBUF_ReadUnsigned(16)` and then keeps only its low byte
  (`movzx cx, al` at `0x0045F387`) before it passes it to `sub_00466360_ClientMonCreate`, which stores it with
  `sub_004AC780_ClientMonNameSeedSet` at the client unit's `MonsterData+0x14`. The client roll below therefore runs on
  `Init(nameSeed & 0xFF)`: only 256 random-unique names are possible. Phase 1 read only the server side and said the name
  roll used the 16-bit value. (fn:sub_0045F190_ClientMonAssign@0x0045F190, 0x0045F37C–0x0045F387, fn:BITBUF_ReadUnsigned@0x00411020, fn:sub_00466360_ClientMonCreate@0x00466360, fn:sub_004AC780_ClientMonNameSeedSet@0x004AC780)
- [I] **Client.** `sub_004AD020_ClientMonModsApply` calls the client handler table `0x00724D78` for mods 1–4 and for the
  list, passing flag `0x08` (special) as the argument. Rows 1, 12, 16 and 36–39 point at the name builder:

```text
ClientMonNameBuild(unit, mod EDX, special):                 ; fn:sub_004AC870_ClientMonNameBuild
  if not special: return
  nameSeed <- unit.data+0x14
  if flags & 0x02: name <- String(SuperUniques[unit.data+0x26].Name (+0x02), 5382 if 0); return
  if flags & 0x04:                                          ; sub_004AE320_ClientMonIsChampion
    k <- index of mod in (16, 36, 37, 38), else 4           ; table 0x006DA488; entry 4 is (39, 11087)
    name <- Format(String(11072) "%0 %1", String(k's word), String(MonStats[class].NameStr +0x06)); return
  RNG_SeedInit(unit.seed (+0x20), nameSeed)                 ; client unit seed: low = nameSeed (server value & 0xFF), high = 666
  if mod = 12: name <- String(3111) "Blood Raven"; return
  if class in {156, 211, 242, 243, 256, 333, 544, 704..709}: fixed boss string; return
  s <- UniqueSuffix[RangeB(seed, nSuffix)];  p <- UniquePrefix[RangeB(seed, nPrefix)]
  name <- Format(String(1721) "%0 %1", p, s)
  if Range(seed, 100) < 50:
    a <- UniqueAppellation[RangeB(seed, nApp)]; s <- UniqueSuffix[RangeB(…)]; p <- UniquePrefix[RangeB(…)]
    name <- Format(String(1722) "%0 %1 %2", p, s, a)
  set the unit's name (0x0063E810)
```

- [C] The order is the call order, read from the disassembly: suffix before prefix in both rounds, appellation first in the
  second (`0x004ACAF6`–`0x004ACB47`). When the 50 % branch is taken the first pair is drawn and discarded. All 94 client
  rolls of run:2026-10-14-mon-special follow it (41 with one pair, 53 with the appellation round). An entry whose
  string index is 0 or unresolved gives an empty string (`0x0096D4B4`). (fn:sub_00653F10_UniqueSuffixRoll@0x00653F10, fn:sub_00653ED0_UniquePrefixRoll@0x00653ED0, fn:sub_00653F50_UniqueAppellationRoll@0x00653F50, tbl:UniqueSuffix.txt:Name, tbl:UniqueAppellation.txt:Name, run:2026-10-14-mon-special)
- [I] The string indices are fixed in the code: 1721 `Monster1Format` and 1722 `Monster2Format` (`string.tbl`), 11072 `"%0 %1"`
  and 11084–11087 `champghostlyX`…`champberserkX` (`patchstring.tbl`), 3220 `Champion`, 3111 `Bloodraven`. For a champion
  the dispatcher calls the builder for mod 1 (no match: entry 4, "Berserker") and again for the champion mod in the list; the
  last call sets the name. (data:g_ChampionNameStr@0x006DA488, data:g_ClientUModHandlers@0x00724D78)
- [I] Minions (flag `0x10`, not `0x08`) get no name from this path, so the transferred `rndname`-free lists do not name them.
  (0x004AD05A–0x004AD061, fn:sub_004AD020_ClientMonModsApply@0x004AD020)
- [I] **UniqueTitle is never read.** The pointer `0x0096D488` is written by the loader `0x0065A463` and by the generic
  single-table loader `sub_00653DB0_UNameTableLoad`, and cleared by `sub_00653E20_UNameTablesFree`; nothing else references
  it or its count `0x0096D498`. The three roll functions read only the prefix, suffix and appellation pointers. (data:g_pUniqueNameTables@0x0096D488, fn:sub_0065A400_MonsterTablesLoad@0x0065A400, tbl:UniqueTitle.txt:Name)

### 9. Boundary decision for Phase 2 (recommendation)

**Recommend: no new oracle; model every draw; handler effects out of scope behind seed assertions.** Reasons:

1. [I] Every draw of the special path is in code read here and is short: the champion roll, the two weighted picks with
   `ModEligible` (table data plus the MonType matrix), the unique-minion count, the `rndname` step, the superunique extra
   picks and minion counts, Radament's `Range(5)`, the aura index on its local seed and the client name roll. (An
   uncommitted replay of this reading agreed on 24 of 24 logged rolls; informal, not evidence.) (fn:sub_005A0760_SpecialModsRoll@0x005A0760)
2. [C] The handlers' effects draw nothing on the unit, room or game seed (67 logged windows, room and game seeds in 30 of them, § 4), so modelling them
   adds nothing to the seed chain. Their deep callees (`0x005701B0`, `0x0056DEB0`, `0x006439F0`/`0x00644340`/`0x005DD250`,
   `0x005417D0`, the quest hooks `0x005436B0`/`0x00545B50`, `0x00639DB0`, `0x005B0E00`) are logged with the three seeds on
   entry and exit and **asserted unchanged**; any change is a failure, not a taken value. (run:2026-10-13-mon-spawn)
3. [I] The escort spawns of the superunique tails and the minion spawns go through `MonSpawnTry`, already modelled by
   `tools/monspawn.py` under its existing oracles (collision and the other value predicates, `SUnitCreate`'s unit seed).
   Those stay; nothing new is added. (fn:sub_005B24E0_EscortSpawn@0x005B24E0)
4. [I] The MonType bit matrix is the one input not read: Phase 2 either reads its builder or logs the `MonTypeIsA` calls
   as a value oracle. With stock data it is called only for `lightning`, so the run can assert the predicted result.
   (fn:sub_005A0070_MonTypeIsA@0x005A0070)

Out of scope and named only: the stat effects of every handler (`monsters/stats`), the `constants` rows 1–33, the client
handlers other than the name builder, the quest hooks, the inactive restore and `MonMakeSpecial` paths. Phase 2 logging
(addresses for `tools/gdb/mon-spawn.gdb`): pick entry/exit `0x005A0500`/`0x005A0600` (unit seed, `have`, result),
`ModEligible` `0x005A03E0` (row, result), every handler call at `0x005A2153`/`0x005A21AC` (mod, three seeds) and the group
walk `0x005A2160`/`0x005A21B9`, `ModsXferCopy` `0x005A0C8F` (both lists), `SuperUniqueSpawn` `0x005A4B8E` (mod list, min,
max) and `0x005A4BE4` (record index), the aura index after `0x005A1727`, and on the client the three roll functions
`0x00653ED0`/`0x00653F10`/`0x00653F50` (row) with the name seed at `0x004AC9C7`.

### 10. Phase 2 reproduction (run:2026-10-14-mon-special)

`tools/monspecial.py` is the model of §§ 1–8; `tools/monspawn.py` runs it at every special in a log, inside the population
pass and, for superuniques and the MonPlace 2 and 3 presets, from their own entry line in the presets window. No oracle is
left on the special path (the boundary of § 9 as ruled): the mod picks with `ModEligible` and the read `MonTypeIsA` matrix,
`Range(1)`, the unique-minion count, the transfer, the handlers (their deep callees asserted to keep the unit, room and game
seeds), the superunique build and the client name roll are all predicted.

- [C] Twelve sessions (normal, nightmare, hell; classic and expansion): 70 special-mods rolls, 169 picks, 606 handler calls on
  specials and 1667 on group members, 130 `rndname` steps, 12 aura draws, 277 minions with a transferred mod, 11
  superuniques, 4 MonPlace 2 and 4 MonPlace 3 presets, 94 client name rolls; 20 champion packs and 54 unique groups;
  `monspawn: 390144 checks, 0 mismatches`. (run:2026-10-14-mon-special, fn:sub_005A0760_SpecialModsRoll@0x005A0760)
- [C] The logs of run:2026-10-13-mon-spawn and run:2026-10-14-collision replay with the special-mod and handler oracles
  replaced (24 + 7 rolls, 30 + 14 handler windows), 0 mismatches. (run:2026-10-14-mon-special, run:2026-10-13-mon-spawn, run:2026-10-14-collision)
- [I] Not reached, so still `[I]` by reading only: the `lightning` × `sandleaper` exclusion, an empty candidate list, the
  ≥ 8 and ≤ 9 mod caps, the superunique tails (Radament, the quest hooks, `EscortSpawn`), `thief`, an `aura` superunique and
  the Lord De Seis index, `ubermephisto`'s aura, a superunique with ≥ 5 mods at creation, a client fixed-name class, and the
  inactive-restore and `MonMakeSpecial` paths. (fn:sub_005A49B0_SuperUniqueSpawn@0x005A49B0, fn:sub_005A1650_UModAura@0x005A1650)

## Data touched

- `tbl:MonUMod.txt:id` (= row, the handler index), `tbl:MonUMod.txt:version` (`+0x04`), `tbl:MonUMod.txt:enabled` (`+0x06`),
  `tbl:MonUMod.txt:xfer` (`+0x07`), `tbl:MonUMod.txt:champion` (`+0x08`), `tbl:MonUMod.txt:fPick` (`+0x09`),
  `tbl:MonUMod.txt:exclude1`/`exclude2` (`+0x0A`/`+0x0C`), `tbl:MonUMod.txt:cpick` (`+0x0E + 2d`), `tbl:MonUMod.txt:upick`
  (`+0x14 + 2d`), `tbl:MonUMod.txt:constants` (`+0x1C`: row 0 here; rows 10–15, 28, 31 and the per-row getter only named).
  No reader of `fInit` (`+0x1A`): the eight functions that address `DataTables+0xC50` (`findscalar 0xc50`) read every
  other field and not this one.
- `tbl:SuperUniques.txt:Class` (`+0x04`), `tbl:SuperUniques.txt:Superunique` (`+0x08`, the tail switch),
  `tbl:SuperUniques.txt:Mod1`–`Mod3` (`+0x0C`..`+0x14`), `tbl:SuperUniques.txt:MinGrp`/`MaxGrp` (`+0x1C`/`+0x20`),
  `tbl:SuperUniques.txt:AutoPos` (`+0x24`), `tbl:SuperUniques.txt:Stacks` (`+0x26`), `tbl:SuperUniques.txt:Name` (`+0x02`,
  client). Not read on this path: `hcIdx` (`+0x00`), `EClass`, `Replaceable`, `Utrans*`, `MonSound`.
- `tbl:UniquePrefix.txt:Name`, `tbl:UniqueSuffix.txt:Name`, `tbl:UniqueAppellation.txt:Name` (client); `tbl:UniqueTitle.txt:Name`
  loaded only.
- `tbl:MonStats.txt:minion1`, `tbl:MonStats.txt:MonType` (`+0x1C`), `tbl:MonStats.txt:isMelee`, `tbl:MonStats.txt:nomultishot`,
  `tbl:MonStats.txt:Velocity`, `tbl:MonStats.txt:NameStr` (client), `tbl:MonStats.txt:BaseId`, `tbl:MonStats.txt:NextInClass`,
  `tbl:MonStats.txt:Level`; `tbl:MonStats2.txt:mA1`, `tbl:MonStats2.txt:mWL`; `tbl:Levels.txt:MonLvl1Ex`, `tbl:Levels.txt:mon1`;
  `tbl:MonLvl.txt:Level` (enchant handlers, named).
- `struct:MonsterData+0x14` name seed, `struct:MonsterData+0x16` flags, `struct:MonsterData+0x1C` mods, `struct:MonsterData+0x26`
  superunique id, `struct:MonsterData+0x28` AI/group control; `struct:MonUModRec+0x00`…`+0x1C`; `struct:SuperUniqueRec+0x00`…`+0x30`;
  `struct:UModAuraRow+0x00`; `struct:Game+0x06D`, `struct:Game+0x070`; game `+0x1D30` placed bits.

## Dead ends

- `0x005A1910` (`fast`) has no Ghidra function; `decompile` reports "no function there". It is read from the disassembly
  (35 instructions) and created by the symbol import.
- The `SpecialModsRoll` decompile compares `allowChampion` with a garbage `EDX` from `ModCount`; the disassembly zeroes `EDX`
  first (`0x005A0777`), so the test is `allowChampion ≠ 0`.
- `sub_0054E2A0_PresetFallenVariant` looks like a switch on the MonPlace index; its `EDI` is the level id that
  `PresetMonSpawn` stored over its own first argument at `0x0054E651`.

## Open questions

- ~~[L] The monster level the aura handler reads in a classic game~~ answered in
  [monsters/0004 § 5](0004-stats.md#5-classic-nightmare-and-hell-sub_0063eef0_monclassicdiffadjust): it is MonStats
  `Level` + 25·d + 3 (the classic adjustment's level stat, then `leveladd`), `[C]` by run:2026-10-15-mon-stats.
- [L] What reaches `sub_005A4940_MonMakeSpecial` (caller `0x00583050`, likely a skill) and whether it occurs in normal play.
- [L] The client draws its name on the client unit's own seed; whether that seed is used for anything else on the client
  after the name is set was not checked. It cannot feed the server.
- [L] A unique's random colour (src:d2dfg-blizzard: `Utrans` 0 means random; src:fandom-d2-elite-monsters: palettes
  8–29 for random uniques and champions). The client reader of SuperUniques `Utrans` (`0x00466680`) was read only from
  `0x004665F9` on. That stretch also reads a class record's `+0x122 + k` byte, and its 255 case calls `0x004791B0`; no draw
  was seen in it. Where the random palette is drawn, and on which client seed, is unread. The colour is display only and
  cannot reach the server's seeds; the client name roll re-initialises its seed from the name seed (§ 8).
- [L] The stat effects of every handler and the readers of `constants` rows 1–33 (`0x005A00F0` callers, `0x005A0E80`,
  `0x005A17E0`, `0x005A21D0`): `monsters/stats`.

## Change notes

- 2026-10-16 (reverser, follow-up): § 4 handler table: `berserk` (39) split from 36–38; it has no `champion` part
  (monsters/0004 § 8, `[C]` on run:2026-10-15-berserk-forced). `re/symbols.csv` row of `sub_005A1280_UModBerserk`
  I → C, evidence monsters/0004.
