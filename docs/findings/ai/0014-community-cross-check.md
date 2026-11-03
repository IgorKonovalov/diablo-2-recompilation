# 0014 — Community cross-check of the AI catalogue (plan 0052 Phase 1b)

> **Subsystem:** monsters/ai
> **Question:** which claims about monster, boss and summon behaviour do the community documents make that a
> reimplementer would act on (target choice, skill choice, chances and ranges, boss behaviour), and what verdict does
> each get against the catalogue findings ai/0001 to ai/0012 (and ai/0013, read from the `lane/r52l` copy)?
> **Date:** 2026-11-03   **Plan:** 0052 (Phase 1b)   **Status:** for review (`lane/r52m`)

No Ghidra, no game and no emulation: this lane read the findings and, for one claim (C21), the kept objdump of
`workspace/logs/r52k/b11-asm-e.txt`. The community pages were fetched in session (ADR-0007) and are registered in
`docs/sources.md` (`src:arreat-summit-boss-pages`, `src:arreat-summit-bestiary`, `src:arreat-summit-summon-skills`,
`src:d2mods-monstats-guide`, `src:wue-d2-ai-slides`, and `src:arreat-summit-hirelings` re-fetched). No page reproduced
decompiled code. The catalogue findings were all written blind (their *Leads used* say "None"); the reading of the
catalogue side in this finding is theirs, tagged as they tag it. **Agreement promotes nothing:** every claim here stays
`[L]`, and the `[I]` or `[C]` of the catalogue side is unchanged. A verdict is not a statement about the community's
right to be wrong: Arreat Summit pages describe LoD at 1.10 or later with no patch named, so a difference may be a
version difference until the Phase 2 case settles it (stated in the row).

## Answer (summary)

- [L] **67 claims compared** from 5 registered sources (and `src:arreat-summit-hirelings` re-fetched): 35 `held`, 23
  `held with refinement`, 6 `not covered`, **3 `contradicted`** (§ 4). All three are reachable on stock data and are
  listed as required cases of Phase 2 in the plan log: Duriel's melee choice (C10; the page's 17/33/50 are `aip2` and
  `aip3` read as marginal chances, where the code draws one after another, giving about 33/33.5/33.5;
  fn:sub_005F67B0_AiDuriel@0x005F67B0), the same for Über Duriel (C11, row 44's record 708), and Greater Mummy's
  champion exception (C40; the callback tests the unique bit only; fn:sub_005F2B10_AiGreaterMummy@0x005F2B10).
- [L] The community material on AI is thin: the Arreat Summit pages are mostly stat tables and skill lists, and the one
  source that would describe each AI, "The AI Compendium", could not be found (§ 3). Where a page lists a monster's
  skills, the list was compared with the AI function's `SkillK` slots (those are the skills the *AI* commands; a page
  skill that the AI never commands is a refinement, not a contradiction).
- [I] Nothing was found that moves a catalogue claim. Two refinements the catalogue should carry into the spec: the
  Fallen's flight is triggered by any monster dying within 15, not only a Fallen (C31), and the Zakarum Priest's heal
  takes only classes 235 and 238 (C53). (fn:sub_005F02C0_AiFallen@0x005F02C0, fn:sub_005F72D0_AiZakarumPriest@0x005F72D0)

## Leads used

The register of this finding is § 2. Sources, one line each (full rows in `docs/sources.md`):

- [L] src:arreat-summit-boss-pages: read in full 2026-11-03; 15 boss pages; rows C10 to C30 (C27 to C30 `not covered`).
- [L] src:arreat-summit-bestiary: 23 monster pages; rows C31 to C58.
- [L] src:arreat-summit-summon-skills: 3 skill pages; rows C59 to C62 and C67.
- [L] src:arreat-summit-hirelings: re-fetched; rows C64 to C67.
- [L] src:d2mods-monstats-guide: rows C01 to C06.
- [L] src:wue-d2-ai-slides: rows C07 to C09.
- Read and unused: the Amazon Basin wiki pages Mephisto, Diablo, Baal, Duriel (no behaviour statements; § 3).

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| 0x005F67B0 | `sub_005F67B0_AiDuriel` | row 44 think, the contradicted C10 and C11 | I |
| 0x005F2B10 | `sub_005F2B10_AiGreaterMummy` | row 22 think, the contradicted C40 | I |

No new names: both are in `re/symbols.csv` from ai/0008 and ai/0003. No symbol is raised or added by this finding.

## Walkthrough

### 1. Verdict vocabulary and rules used

`held`: the catalogue reading says the same thing. `held with refinement`: the same, but the catalogue reading adds a
condition, a limit or a scope the source does not state. `contradicted`: the catalogue reading excludes what the
source says (here only where the arithmetic or a stock table value settles the difference). `not covered`: the
catalogue reading does not reach the claim (a table value, a skill's own effect, an Über driver not found, or a
mechanism no AI function holds). A `contradicted` claim is re-read in the finding it cites, not in the binary
(this lane has no Ghidra); the cited reading is tagged in its own finding, so the verdict is a Phase 2 case, not a demotion (§ 4).

### 2. The compared claims

Anchors name the catalogue section (finding, section, function). A column says why in one clause.

#### 2.1 Machinery (AI column and `aip` cells; `src:d2mods-monstats-guide`, `src:wue-d2-ai-slides`)

| # | Source and claim [L] | Catalogue anchor | Verdict | Why |
|---|---|---|---|---|
| C01 | d2mods: the `AI` column tells the game which AI to use | ai/0001 Answer, `g_MonAiTable`@0x0073CA18 indexed by MonStats `+0x1E` (fn:sub_005B15D0_MonAiEntryGet@0x005B15D0) | held | The AI byte indexes the 148-row table. |
| C02 | d2mods: the `aip1`–`aip8` cells "pass on parameters (in percentage)" | ai/0002 § 2 (Fallen `aip1` as a draw threshold) and ai/0006 § 2.10 (`aip8` a skill id), ai/0008 § 2.4 (`aip4` frames, `aip7` a distance) | held with refinement | Most cells are `draw < aip` thresholds, but others are frames, event counts, distances, bit masks (Vampire `aip5`) or skill ids (rows 105, 106). |
| C03 | d2mods: most AIs "will do absolutely nothing" without aip values | ai/0013 Answer (every `aip` slot 0 in 13 rows); ai/0008 § 2.1 (Griswold, constants 80 and 50), ai/0006 § 2.1 (Hydra, constant 60) | held with refinement | Many thinks read no `aip` and still act; with zeros the draws fail and the fallback (walk, idle) runs (Duriel `aip4` = 0 never takes A2). |
| C04 | d2mods: the Imp AI "is special and uses multiple rows" | ai/0010 § 2.8 and § 2.10 (fn:sub_005E2FF0_AiImp@0x005E2FF0; slots read from the fixed records `imp1`..`imp4`; state row 16) | held | The imp reads other classes' records and has its own state row. |
| C05 | d2mods: a boss scarab orders a raid with a chance given by `aip5` of the Scarab AI | ai/0003 § 2.4 (fn:sub_005F2540_AiScarab@0x005F2540: `chance(aip5)` for a unit that owns itself, within 20) | held | The leader test is `MonsterOwner(U) == U`, which the source reads as "boss". |
| C06 | d2mods: while raiding, scarabs always use SK1 instead of A1 and A2 | ai/0003 § 2.4 (kind-1 head record: `Skill1` once in melee, then the record is dropped; out of melee a charge walk) | held with refinement | One `Skill1` per record, and only with `Skill1 >= 0`; out of melee it walks (override 2, 100). |
| C07 | slides: the AI is strongly distance-driven (a range switches the behaviour) | ai/0001 § 6 (nearest by the AI distance, `aidist`), ai/0002 Answer (the `melee` and distance tests of every row) | held with refinement | True of the target search and the thinks' `melee`/`dist` tests; some rows (spawners, towers, traps) run on frame timers and counts instead. |
| C08 | slides: typical behaviour is a random choice of skill 1, 2 or 3 | ai/0002 Answer (one or two `chance` draws), ai/0003 Answer | held with refinement | Draws pick among attacks, but most skills are also gated by life, a cooldown frame or a counter (Sand Raider, Sand Maggot, Vampire). |
| C09 | slides: some AIs also use the monster's current life | ai/0002 § 2.10 (Baboon below `aip1`), ai/0003 § 2.13 (Bat Demon), § 2.12 (Vampire below 33 %), ai/0008 § 2.3 (Mephisto's `L`) | held | At least six rows branch on life. |

#### 2.2 Bosses (`src:arreat-summit-boss-pages`)

| # | Source and claim [L] | Catalogue anchor | Verdict | Why |
|---|---|---|---|---|
| C10 | Duriel: "17% chance of selecting Melee Attack 1", 33 % Smite, 50 % Jab | ai/0008 § 2.2 (fn:sub_005F67B0_AiDuriel@0x005F67B0: `draw < aip2` Skill3, then `draw < aip3` Skill2, then `draw < aip4` A2, else A1; `aip2` 33, `aip3` 50, `aip4` 0) | **contradicted** | Each test is a fresh draw: Smite 33 %, Jab 0.67 × 0.50 = 33.5 %, A1 33.5 %. The page's 33 and 50 equal `aip2` and `aip3` read as marginal chances, its 17 their remainder. The map is `[C]` (run:2026-10-30-ai-cat-emu-6, `duriel`); the frequencies are arithmetic on it. Version difference unlikely: stock Normal, Nightmare and Hell share `aip2`..`aip4`. |
| C11 | Über Duriel: the same 17/33/50 (Hell) | ai/0008 § 1 (row 44 records 211 and 708 agree on every `aip`) | **contradicted** | The same think and the same values; one case covers both rows if the Über event can be staged, else row 211 stands for 708. |
| C12 | Duriel "does not use Charge" | ai/0008 § 2.2 (`aip5` 0: `draw < 0` never taken, though it still draws) | held | Stock `Charge` arm unreachable; the draw is still made. |
| C13 | Duriel: Holy Freeze level 5 in Normal and Nightmare, 6 in Hell | ai/0008 § 2.2 (`UnitSkillAdd(U, Skill4, aip1, 1)`, `aip1` 5/5/6) | held | Same numbers, by difficulty. |
| C14 | Andariel: a deadly poison attack she casts when you get up close | ai/0008 § 2.1 (fn:sub_005F5830_AiAndariel@0x005F5830: in melee `Skill1` AndrialSpray on `aip1` 30/35/35) | held | The spray is her melee-range skill. |
| C15 | Lilith (Über Andariel): skills Poison Spray, Poison Bolt | ai/0008 § 1, § 2.1 (record 707 `uberandariel` has the same values; `Skill1` spray, `Skill2` AndyPoisonBolt) | held | The two slots are the two skills named. |
| C16 | Mephisto uses Lightning, Charged Bolt, Poison Nova, Skull Missile, Frost Nova, Blizzard | ai/0008 § 2.3 (fn:sub_005F78B0_AiMephisto@0x005F78B0: six stock slots; `Skill5` Frost Nova and `Skill6` Blizzard only when the difficulty byte is above 0) | held with refinement | In Normal only three of the six are cast; the page lists the skills without a difficulty. |
| C17 | Diablo: Fire Nova, Red Lightning Hose, Cold Touch, Fire Wall, Firestorm, Bone Prison, Charge, Taunt | ai/0012 § 2.2, § 2.3 (fn:sub_005E9170_AiDiablo@0x005E9170: actions DiabLight, DiabFire, DiabCold, DiabWall, DiabPrison, DiabRun, PrimeFirewall; Taunt and a separate Fire Nova have no action) | held with refinement | Seven action skills match skills in the list; the page's "Taunt (does nothing)" is not an AI action, and which of Fire Nova and Firestorm is DiabFire is not settled by the catalogue. |
| C18 | Diablo casts Bone Prison around your Town Portals | ai/0012 § 2.2 case 15 (`PlayerPortalGet`, `UseSkill(Sk7mode, Skill7, NULL, guid, 2)`; weight `w15` needs the portal in level 108 within 85 of home) | held | Action 15 is a prison at the portal, on the Chaos Sanctuary only. |
| C19 | Diablo casts Bone Prison on you and your hirelings | ai/0012 § 2.3 (fn:sub_005E9170_AiDiablo@0x005E9170, pick callback 0x005E8EB0; action 9 DiabPrison at the picked target; the pick walks the eight player lists, ai/0001 § 6) | held | Hirelings are in the lists the pick walks; `[I]` as the pick is. |
| C20 | Baal can teleport | ai/0012 § 2.9 (fn:sub_005FCB60_AiBaalAct@0x005FCB60 action 14: `Skill5`, a point 25 subtiles away from the target) | held | |
| C21 | Baal's clone is created with the same percentage of life as Baal | ai/0012 § 2.9 (fn:sub_005FC860_BaalCloneSpawn@0x005FC860; kept asm `b11-asm-e.txt` 0x005FCACF–0x005FCB11: stat 7 = `UnitGetMaxHp(U)` / 3 and stat 6 = stat 6 of U / 3, both `0x55555556`) | held with refinement | Both stats are a third, so the same percentage up to the two roundings; the page does not say a third. The finding's wording "set to U's maximum life and life divided by 3" is ambiguous and is cleared here from the asm. |
| C22 | Baal and the Succubus cast Defense Curse on a target with more Life than Mana, Blood Mana otherwise (page: "if you have more Life than Mana … Defense; Blood Mana only affects you if you have more Mana than Life") | ai/0012 § 2.9 action 8 (`Skill6` when max life > max mana or the target is not a player; `Skill7` on a player) | held | Same split as the Succubus (C43); the tie goes to Blood Mana in both. |
| C23 | Nihlathak: Summon Minion, Minion Frenzy, Corpse Explosion, Arctic Blast, Teleport | ai/0012 § 2.5 (fn:sub_005EE5D0_AiNihlathak@0x005EE5D0: `Skill1` Imp Teleport, `Skill2` Overseer Whip, `Skill3` Corpse Explosion, `Skill4` Arctic Blast, `Skill5` MinionSpawner) | held | Five slots, five skills. |
| C24 | Nihlathak explodes the corpses of your minions | ai/0012 § 2.5 (`CorpsePickNear(U, t; Skill3, level)` then `UseSkill(Sk3mode, Skill3, c, 0, 0)` on `aip3`) | held | The cast target is a corpse picked near the player. |
| C25 | Izual uses Frost Nova | ai/0008 § 2.5 (fn:sub_005F89B0_AiIzual@0x005F89B0: `Skill1` Frost Nova on `aip4` in melee or `aip3` within 10) | held | |
| C26 | The Summoner: Glacial Spike, Frost Nova, Fire Ball, Fire Wall, Weaken | ai/0008 § 2.4 (fn:sub_005F85C0_AiSummoner@0x005F85C0: `Skill1` Glacial Spike, `Skill2` Frost Nova, `Skill3` Fire Ball, `Skill4` VampireFirewall, `Skill5` Weaken) | held | |
| C27 | Griswold curses with Amplify Damage if he can hit you | ai/0008 § 2.1 (fn:sub_005E5AC0_AiGriswold@0x005E5AC0: A1 on `draw < 80` in melee, no skill call) | not covered | The think commands A1 only; where an on-hit curse comes from is the skill and attack tables, not read here. |
| C28 | Über Diablo "can summon Pit Lords", regenerates at twice the rate | ai/0012 § 2.10 (row 147 fn:sub_005E9DF0_AiUberDiablo@0x005E9DF0 is `ret 4`) | not covered | The think returns; what drives the event is open (plan 0052 Phase 1c). |
| C29 | Über Mephisto summons Returned, Horror Archers, Burning Dead and Horror Mages, Bone Mages | ai/0008 § 2.6 (row 146 fn:sub_005F81C0_AiUberMephisto@0x005F81C0 is `ret 4`) | not covered | As C28. |
| C30 | Über Baal summons Specters and Dark Lords; Vile Effigy follows Hoarfrost | ai/0012 § 2.10 (row 145 fn:sub_005FD200_AiUberBaal@0x005FD200 is `ret 4`; class-709 teleport unreached) | not covered | As C28. |

#### 2.3 Tier and catalogue AIs (`src:arreat-summit-bestiary`)

| # | Source and claim [L] | Catalogue anchor | Verdict | Why |
|---|---|---|---|---|
| C31 | Fallen "quickly retreat at the sight of one of their brethren falling" | ai/0002 § 2.5 (fn:sub_005F02C0_AiFallen@0x005F02C0: the near rooms' last four dead monsters, a monster in mode 0 within AI distance 15, a step 12 away) | held with refinement | The scan takes any monster dying within 15 (it tests the mode, not the class), not only a Fallen. |
| C32 | Fallen "may run away" (a chance) | ai/0002 § 2.5 (the step is taken whenever the scan hits; the `mod 20` draw only sets unit event 17 on 1 in 20) | held with refinement | The flight is deterministic once a dying monster is in range; the chance gates only the event, whose client effect is unread. |
| C33 | Fallen Shamans raise Fallen | ai/0002 § 2.11 (fn:sub_005F1440_AiFallenShaman@0x005F1440: `Skill1` Resurrect on a dead minion of the group, or classes 19 and 58 for a unique) | held | |
| C34 | Fallen Shamans shoot Firebolts | ai/0002 § 2.11 (`Skill2` ShamanFire, ShamanIce or ShamanFireEx by record) | held with refinement | The missile is fire or ice by record, not always fire. |
| C35 | Fetishes use hit-and-run tactics | ai/0003 § 2.14 (fn:sub_005F53E0_AiFetish@0x005F53E0: after `aip3` melee decisions against a target above `aip4` percent life, step 14 away, return after two events) | held | |
| C36 | Fetish Shamans revive their fallen kin | ai/0005 § 2.3 (fn:sub_005F9A80_AiFetishShaman@0x005F9A80: `Skill3` Resurrect2 on a dead class 141 or 396 within `aip5`) | held | |
| C37 | Fetish Shaman skills: Resurrect, Inferno, Fetish Aura | ai/0005 § 2.3 (`Skill1` FetishInferno, `Skill3` Resurrect2; no aura call) | held with refinement | The aura is not commanded by this think. |
| C38 | Greater Mummy raises and heals other undead | ai/0003 § 2.6 (fn:sub_005F2B10_AiGreaterMummy@0x005F2B10: `Skill1` Resurrect2 on a corpse, `Skill2` Bestow on a wounded one) | held | |
| C39 | ... with Unique monsters an exception | ai/0003 § 2.6 (callback: not a unique, `MonTypeFlag(unit, 8)`; Radament, class 229, takes uniques too in Normal) | held with refinement | The unique exclusion is there, with Radament's Normal exception. |
| C40 | ... with Champion monsters an exception | ai/0003 § 2.6 (fn:sub_005F2B10_AiGreaterMummy@0x005F2B10, callback 0x005F2A00–0x005F2B03 tests flag 8 only; the champion flag is 4, monsters/0003) | **contradicted** | No champion test in the callback; a champion corpse in range becomes `corpse`. `[I]`: the skill's own target test (`MonSkillTargetOk`) is not read for champions. Required Phase 2 case (§ 4). |
| C41 | Greater Mummy: Unholy Bolts from a distance, a poison breath close in | ai/0003 § 2.6 (`Skill3` UnHolyBolt at a hostile on `aip4`; `dist < 5` A2 on `aip1`) | held with refinement | The bolt is not distance-gated (any range with a hostile); A2 as the breath is not named by the catalogue. |
| C42 | Vampire: Life Steal Missile, Fireball, Fire Wall, Meteor | ai/0003 § 2.12 (fn:sub_005F4A70_AiVampire@0x005F4A70: `Skill1` Fireball and `Skill4` VampireMissile, `Skill2` Firewall on bit 1, `Skill3` Meteor on bit 2) | held | |
| C43 | Succubus: Defense Curse when you have more Life than Mana, Blood Mana when you have at least as much Mana as Life | ai/0010 § 2.3 (fn:sub_005E1E00_AiSuccubus@0x005E1E00: `Skill3` when max life > max mana or a monster, `Skill4` on any other player) | held | The tie goes to Blood Mana in both. |
| C44 | Succubi weaken from a distance with a curse, then close in | ai/0010 § 2.3 (curses first on `aip3` within `aip4`, then melee or walk) | held with refinement | The curse needs a target without the stat-list flag 0x20 within `aip4`; the walk-in is a 2-in-100 type draw, not a phase. |
| C45 | Overseer's whip throws a minion into bloodlust, it mutates, charges and dies in an explosion | ai/0010 § 2.5 and § 2.9 (`Skill3` Whip on a non-unique `minion1`; `WhipChangeClass` sets state row 15, row 117 SuicideMinion) | held | |
| C46 | Overseer creates a healing vortex that seeks damaged minions | ai/0010 § 2.5 (fn:sub_005E27A0_AiOverseer@0x005E27A0: `Skill2` at a minion under 50 % life within 24) | held | |
| C47 | Overseer: Cry Help (Attract) | ai/0010 § 2.5 (`Skill1` at the stored hostile, cooldown `aip1` 250 frames) | held | |
| C48 | Overseer skills: Cry Help, Healing Vortex, Minion Frenzy, Smite | ai/0010 § 2.5 (`Skill1`–`Skill3`: Cry Help, Healing Vortex, Overseer Whip) | held with refinement | Smite is not an AI command (it is A1 or A2 in melee on `aip6`). |
| C49 | Blood Lord: Frenzy, strictly melee | ai/0010 § 2.13 (fn:sub_005E36F0_AiBloodLord@0x005E36F0: `Skill1` mode 5 on `aip3` in melee; at range only a walk) | held | |
| C50 | Megademon: an Inferno-like attack it may use within melee range | ai/0009 § 2.5 (fn:sub_005E0C80_AiMegademon@0x005E0C80: at range inside the skill level on `aip1` 50–90, in melee on `aip2`, both with an `aip6` cooldown) | held with refinement | The breath is also used at range, with the higher chance. |
| C51 | Regurgitators walk to corpses to eat them | ai/0005 § 2.8 (fn:sub_005FA710_AiRegurgitator@0x005FA710: walks to a dead monster, `Skill1`) | held | |
| C52 | Vile Mothers spawn offspring | ai/0005 § 2.5 (fn:sub_005FA010_AiVileMother@0x005FA010: `Skill1` toward the target while fewer than `aip2` children are within 25) | held | The page gives no limit; the code has one. |
| C53 | Zakarum Priests heal other monsters / wounded followers | ai/0004 § 2.11 and § 2.12 (fn:sub_005F72D0_AiZakarumPriest@0x005F72D0: `Skill1` on 25 %, callback takes classes 235 and 238 at or below 60 % life) | held with refinement | The heal reaches only `zealot1` and `cantor1`-based units, and the last qualifying one in search order. |
| C54 | Zakarum Priest skills: Lightning, Heal, Teleport, Blizzard | ai/0004 § 2.11 (`Skill1` ZakarumHeal, `Skill2` ZakarumLightning, `Skill3` MonTeleport below 33 % life, `Skill4` MonBlizzard) | held | |
| C55 | Oblivion Knight: Bestow, Bone Armor, Bone Spirit, Decrepify, Lower Resist, Weaken, Life Tap, Amplify Damage | ai/0005 § 2.11 (fn:sub_005FAF00_AiOblivionKnight@0x005FAF00: `Skill1` DoomKnightMissile, `Skill3` MonBoneSpirit, `Skill4` Decrepify, `Skill6` MonCurseCast) | held with refinement | Bone Spirit and Decrepify match; the other curses go through the one `MonCurseCast` slot; Bestow and Bone Armor are not commanded by this think (Bone Armor is the Abyss Knight's, C56). |
| C56 | Abyss Knights can use Bone Armor | ai/0005 § 2.10 (fn:sub_005FAB80_AiAbyssKnight@0x005FAB80: `Skill2` MonBoneArmor below `aip1` percent life) | held | |
| C57 | Vulture Demons must land to attack | ai/0003 § 2.7 (fn:sub_005F3170_AiVulture@0x005F3170: the `melee` attack arm is after the landing arm) | held with refinement | A vulture whose landing is refused sets 8 more flight events and, by the pseudocode, still reaches the melee test in that event; unchecked in asm here. |
| C58 | Sand Raiders have a Fire Hit attack like Enchant | ai/0002 § 2.7 (fn:sub_005F0700_AiSandRaider@0x005F0700: `Skill1` Fire Hit once armed, state 90 or 91) | held | |

#### 2.4 Summons and hirelings (`src:arreat-summit-summon-skills`, `src:arreat-summit-hirelings`)

| # | Source and claim [L] | Catalogue anchor | Verdict | Why |
|---|---|---|---|---|
| C59 | Minions "may warp in around you if you get too far away" | ai/0006 § 2.2 and § 2.3 (fn:sub_005E4CF0_AiNecroPet@0x005E4CF0: owner distance above 50, `PetMove` kind 3, `UnitTeleport` next to the owner) | held | Threshold 50 subtiles. |
| C60 | Minions "may disappear or no longer be under your power" when far | ai/0006 § 2.2 (no despawn in the pet think) | not covered | A despawn, if any, is not in the AI function. |
| C61 | Revived monsters "retain much of their original thoughts and tendencies" | ai/0006 § 1 (a revived monster keeps its own AI row, `MonAiInit` state 0) | held | |
| C62 | Wolves and the Grizzly draw monsters' attention from the Druid | ai/0001 § 6 (target search over the ten target lists, the player's summons after the player, nearest by AI distance) | held with refinement | A nearer summon is chosen by distance alone; no summon-kind weight was read. |
| C63 | A Grizzly makes monsters target the Druid more than three Dire Wolves do | ai/0001 § 6 (nearest by AI distance) | not covered | No per-summon weight in the search; any such effect would be distance and count. |
| C64 | The Hireling follows you and automatically attacks monsters nearby | ai/0007 Answer (fn:sub_005E52D0_AiHireable@0x005E52D0: follow bands, `FindHostile` at distance below 25 → the fight step) | held | |
| C65 | A stuck hireling is brought to your side by a waypoint, portal or level change | ai/0007 Answer (follow kind 3, a teleport beside the owner, when the distance is above 100 on any event) | held with refinement | The teleport is a distance rule, not tied to portals; the level change sets the owner's room, not read here. |
| C66 | You cannot choose the hireling's spells; the set depends on the type | ai/0007 Answer (`MERCAI_PickSkill`: `Skill1..6` and the weights from the Hireling row) | held | |
| C67 | Hirelings "fight to the death"; no retreat described | ai/0007 Answer (no life test in row 61; ranged hirelings, `aip1` = 0, back off within 4 on 50 %) | held with refinement | No flight on life, but ranged hirelings do keep a distance. |

### 3. Sources searched and not used

- The Amazon Basin wiki pages Mephisto, Diablo, Baal, Duriel (revisions of 2013-09-01) were read and hold no behaviour
  statements.
- `src:diablowiki-d2-monsters` (Pit Lord circling, Baboon Demon flight at low life, Warped One flight, Viper bosses'
  Skeleton AI), `src:lurker-monster-ai-threads` and the Siramy DS1 manual (NPC path points) answered HTTP 403 or 409: not read, nothing used. The search
  snippets that name those behaviours are not leads (ADR-0007). A retry could cover the Baboon (ai/0002 § 2.10) and the Pit Lord rows.
- "The AI Compendium" (cited by `src:d2mods-monstats-guide` and `src:wue-d2-ai-slides`) was not found by two searches.
- Strategy-guide pages (moat trick, farming guides) describe pathing and player tactics; none was compared.

### 4. Verdict counts and the Phase 2 cases

Counted from the rows of § 2 by `grep` over the verdict column (the command and output are in the plan log entry).

**Required cases of Phase 2** (every `contradicted` claim reachable on stock data):

- **P1b-1 (C10, C11): Duriel's melee decision.** Row 44 `Duriel` (MonStats 211; 708 if the Über event can be staged),
  Normal difficulty, a player in melee range, at least 300 melee decisions. Model: Smite on `draw < 33`, Jab on a
  second `draw < 50`, else A1 (A2 never, `aip4` = 0). Expected 33 : 33.5 : 33.5; the page predicts 33 : 50 : 17. The log
  line needed: the AI decision's command (mode 5 with Skill3, mode 5 with Skill2, or mode 4) and the three draws.
- **P1b-2 (C40): a champion corpse for a Greater Mummy.** Row 22 `GreaterMummy` (MonStats `greatermummy1`), a champion
  `mummy` pack leader dying within `aip5` of the Greater Mummy in the same near rooms, Normal. Check the callback's
  `corpse` slot (0x005F2A00–0x005F2B03) and whether `MonSkillTargetOk(Skill1, corpse, 0, 0)` accepts it and the
  `Resurrect2` is commanded. Control: the same with a unique corpse (excluded by flag 8). A tomb level in Hell holds
  these classes; stage by the harness's monster placement if the natural case does not occur.

## Data touched

`tbl:MonStats.txt:aip1`..`aip8`, `tbl:MonStats.txt:Skill1`..`Skill8`, `tbl:MonStats.txt:AI` (read as in the cited
findings). No new table read.

## Dead ends

- Search snippets (diablowiki, Lurker Lounge) name AI behaviours of single monsters; their pages could not be fetched,
  so those claims are not leads (§ 3).
- "The AI Compendium" would have been the one document describing each AI; not found.

## Open questions

- Is the Greater Mummy's `MonSkillTargetOk` (fn:sub_005FD470_MonSkillTargetOk@0x005FD470) the place a champion corpse
  is refused? It decides whether C40 stands in play, not the callback's reading. Resolve with P1b-2.
- Fire Nova against Firestorm for DiabFire (C17): one of the two names has no AI action; the Skills row of DiabFire
  would settle it (archivist).
