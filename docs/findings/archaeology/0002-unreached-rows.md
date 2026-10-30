# 0002 — The unreached data: table rows no stock reader names

> **Subsystem:** archaeology
> **Question:** per table, which rows does no stock path reach, from the readers the specs already name, and how many?
> **Date:** 2026-10-30   **Plan:** 0062 (Phase 2)   **Status:** for review (`lane/a62`)

Numbered 0002 as plan 0062 names it; `archaeology/0001-switches.md` (Phase 1, the command-line switches) does not exist yet.
Findings only, no spec row (plan 0062 owner question 1). Data only: no Ghidra, no harness. Every count below is a line of
`python3 -I tools/unreached.py workspace/merged/data/global/excel` (`SURVEY table=…`); `--table T --list --rows N` prints the
unreached rows. The tables are the merged pinned data (`.txt`, the same cells the game compiles into its `.bin`). Counts are
by record position, in classic-and-expansion data together (the tables carry both; no difficulty split applies to a row
count), and name matches are case-insensitive.

**What "unreached" means here.** A row is *reached* when at least one reader a spec names takes its name or index out of
another table or out of the code's fixed ranges; it is *unreached by table readers* when none does. That is an **upper
bound** on the truly unreachable rows: code that passes a class, skill or state id as an immediate (a spawn function, a
state setter, a portal) is invisible to the tool. Each section says where such a reader is known and where it is not read.

## Summary

| Table | Rows | Reached | Unreached by table readers | Reader definition |
|---|---:|---:|---:|---|
| Levels | 137 | 132 | 5 | § 1 |
| MonStats | 734 | 605 | 129 (98 enabled, 31 not) | § 2 |
| Skills | 357 | 344 | 13 | § 3 |
| States | 185 | 127 | 58 | § 4 |
| Weapons | 306 | 299 (+7 quest) | 0 | § 5 |
| Armor | 202 | 202 | 0 | § 5 |
| Misc | 151 | 108 (+17 quest) | 26 | § 5 |

- [C] Each count is reproduced by `tools/unreached.py` over the pinned data (`SURVEY table=levels rows=137 … unreached=5`,
  `monstats … unreached=129`, `skills … unreached=13`, `states … unreached=58`, `items … unreached=26`). (tool:unreached.py,
  tbl:Levels.txt:Vis0, tbl:MonStats.txt:Id, tbl:Skills.txt:skill, tbl:States.txt:state, tbl:Misc.txt:code)

## 1. Levels (137 rows, ids 0–136)

Reach, from [drlg/warps](../../specs/drlg/warps.md) and [quests/travel](../../specs/quests/travel.md): a level is reached when it is
a `Vis0..7` destination of another level, lies in an act link list's border or seam range (`ActLinkInit` names 1–17, 40–46,
75–83, 103–106 and 109–112), has a `Waypoint` other than 255, or is an end of a permanent portal pair (1↔39, 4↔38,
46↔74, 109↔121, 111↔125, 112↔126, 117↔127, the tomb→73).

- [I] The link ranges are read from `ActLinkInit`'s `LevelBorderAdj`/`LevelSeamsByTouch` calls; the `Vis` cells alone miss
  104–106 and 110–112, which only those lists link, and the permanent-portal list is that of the quest spec's G5. (fn:sub_00678AD0_ActLinkInit@0x00678AD0,
  fn:OBJINIT_Portal@0x0054FE70, tbl:Levels.txt:Vis0)
- [C] 115 levels are a `Vis` destination, 41 lie in the link ranges, 39 carry a waypoint and 15 are portal ends; 5 levels are in
  none of them: 0 `Null`, 133 `Pandemonium 1` (it names `Vis0` 17 but nothing names it), 134, 135 and 136 (Finale). (tool:unreached.py,
  tbl:Levels.txt:Waypoint)
- [C] 134–136 have no creator in stock: the cube's two Pandemonium portal outputs are stubs and no `PortalObjectCreate` call
  passes a level in 133–136 ([drlg/outdoor](../../specs/drlg/outdoor.md), level 134 note). 133 is the same set; row 0 is the
  null level. (fn:sub_0056D130_PortalObjectCreate@0x0056D130, run:2026-10-15-drlg-outdoor)

## 2. MonStats (734 records)

Reach, from [monsters/pool](../../specs/monsters/pool.md) and its neighbours: a class is reached when a Levels `mon`, `nmon`
or `umon` slot names it (365 classes), a `cmon` critter slot (10), `SuperUniques.Class` (62), `MonPreset.Place` (95; a name in
the act lists, not proof that a DS1 uses the entry), MonStats `minion1`/`minion2`/`spawn` (96), Skills `summon` (31),
`Hireling.Class` (4), `PetType.mclass1..4` (0, the stock cells are blank), or is the `NextInClass` successor of a reached class
(57 more; the pool picks a chain position by difficulty).

- [I] The slot lists are those of the pool build (candidates up to the first blank, `NumMon` picks); the chain closure is
  `MonClassChainStep`'s walk. (fn:sub_005475E0_MonRegionPool@0x005475E0, fn:sub_0054DA60_MonClassChainStep@0x0054DA60,
  tbl:Levels.txt:mon1, tbl:MonStats.txt:NextInClass)
- [C] 605 records are reached and 129 are not: 98 with `enabled` 1 and the 31 records whose `enabled` is blank. All 31 blank-`enabled`
  records are in the unreached set (`chaoshorde1..4`, `darkguard1..5`, `bloodmage1..5`, `evilhole2..5`, `suckernest1..4`,
  `firebeast`, `familiar` among them). (tool:unreached.py, tbl:MonStats.txt:enabled)
- [C] Illustrative unreached enabled rows: 34–37 `gorgon1..4`, 73 `clawviper1`, 157/158 `bird1/2`, 313–317 `quillbear1..5`, 348–350
  `turret1..3`, 704–709's uber bosses (all six `uber*`), 333 `diabloclone`; and six `npc` rows (`act2child`, `cain5`, `rogue2`,
  `act2guard2`, `izualghost`, `drehyaiced`). (tool:unreached.py --table monstats --list, tbl:MonStats.txt:Id)
- [I] The upper bound is loose for classes the code creates by id: the uber bosses by the Uber Tristram handlers, the
  traps and turrets by skill spawn functions, the `evilhole` and `suckernest` families by their spawners. `SpawnClassByBase`
  (do 140) and the death handlers name some; no list of the code-created class ids exists, so those rows stay under
  "unreached by table readers" here. (fn:sub_0063EFA0_SpawnClassByBase@0x0063EFA0, tbl:MonStats.txt:Id)
- [C] Without the preset names, 359 classes are not named by any Levels slot (`SURVEY table=monstats.levels_only`), the figure
  the pool spec's "no stock spawner" question compares against. (tool:unreached.py, tbl:Levels.txt:mon1)

## 3. Skills (357 rows)

Reach: a class skill with a `SkillDesc` in `SkillPage` 1–3 (210); named by MonStats `Skill1..8` (152), `Hireling` `Skill1..6`
(19), CharStats `StartSkill`/`Skill 1..10` (11); named as the parameter of an item property that takes a skill (`skill`,
`oskill`, `aura`, `charged`, the six `*-skill` triggers, `skill-rand`) in Uniques, Sets, the affix tables, Runes, Gems,
CubeMain and Automagic (158); or a `sumskill1..5` of a reached skill (29).

- [I] The property codes are those whose Properties `func1` is 11, 12, 19 or 22, the functions that read the parameter as a
  skill. (tbl:Properties.txt:func1, fn:PROP_Func21_ValParam@0x0065FB50)
- [C] 344 skills are reached and 13 are not: 165 `Jump`, 174 `VampireHeal`, 175 `VampireRaise`, 183 `MissileSkill1`, 187 `PrimeBlaze`,
  189 `PrimeSpike`, 190 `PrimeIceNova`, 191 `PrimePoisonball`, 202 `HireableMissile`, 209 `MonFrozenArmor`, 286 `Baal Monster
  Spawn`, 289 `Suck Blood`, 320 `EvilHutSpawner`. All have a blank `charclass`. (tool:unreached.py --table skills --list,
  tbl:Skills.txt:skill)
- Scope note: a skill id passed as an immediate by an AI think function or a skill handler is not seen by the tool, so the 13 are
  unreached by table readers only; no function was read for them here.

## 4. States (185 rows)

Reach: named by Skills `aurastate`, `auratargetstate`, `passivestate`, `State1..3` or `nocostinstate` (119 states), or by Misc
`state`/`cstate1`/`cstate2` (9).

- [C] 58 States rows are named by no cell: 0, 6, 7, 12, 18, 21, 25, 29, 39, 52, 54, 62, 85, 86, 90–93, 96, 98, 99, 102, 104, 105,
  107–110, 115, 116, 118, 121, 128–137, 142, 146, 154, 164–173, 175, 176, 184. (tool:unreached.py --table states,
  tbl:States.txt:state)
- [I] [stats/0002 § Phase 0 surprise (f)](../stats/0002-states.md#phase-0-surprise-f-the-56-rows-no-data-names) is headed "the 56
  rows no data names"; the rows its body lists are 59, of which 57 `attract`, 100 `healthpot` and 106 `manapot` are named by Misc
  (its "tested only" bullet), leaving 56, all of them in the tool's 58. The two more are 175 `fullsetgeneric` and 176
  `monsterset` (named by the stat 98 parameter, not by a column; stats/0002 does not list them). The setters stats/0002 traces
  (shrines 128–137, set bonuses 165–170, `STATE_ApplyTimed`/`STATE_Set` immediates) are code paths this tool does not read. The
  disagreement (56 vs 58) is routed to the owner of stats/0002 (backlog 2026-10-30, archivist to reverser).
  (fn:STATE_Set@0x00639DB0, fn:STATE_ApplyTimed@0x0056E970, tbl:States.txt:state)
- [I] Of the 58, the code scan of stats/0002 finds no immediate setter for seven (6 `resistmagic`, 25 `fetishaura`, 29
  `convicted`, 39 `lightningbolt`, 116 `dragonflight`, 164 `debugcontrol`, 171 `runeword`), the same seven left under that
  finding's open questions; for the other rows that finding names setters. (fn:STATE_Set@0x00639DB0)

## 5. Items (659 base items: 306 Weapons, 202 Armor, 151 Misc)

Reach: an item is reached when it is in an auto item-type TC (`quest` 0, `spawnable` ≠ 0, `L − 3 < level ≤ L` for an `L` in 3, 6, …,
96, of a type whose `ItemTypes.TreasureClass` is set, with the `tpot` exclusion; 493), is named in a TreasureClassEx item
cell (114), has a vendor `Max` or `MagicMax` above 0 and `spawnable` ≠ 0 (151), is a CubeMain output (68), a CharStats start
item (11) or a MonEquip item (31). Items with `quest` set are counted apart.

- [I] The auto-TC test is items/tc I1, with "of type t" read through `Equiv1`/`Equiv2` for both the item's `type` and `type2` (`ITEMS_IsType`; `type2` changes no count); the vendor test is items/vendors B1.
  (fn:TC_BuildAutoTCs@0x006541C0, fn:VENDOR_BuildList@0x00536D50, tbl:ItemTypes.txt:TreasureClass, tbl:Weapons.txt:spawnable)
- [C] 609 are reached, 24 are quest items none of the readers names, and 26 (all Misc) are unreached: 23 with `spawnable` 0 (`hpo`,
  `mpo`, `hpf`, `mpf`, `tch`, `ear`, `hrb`, the small and large `rps`/`rpl`/`bps`/`bpl` potions, thirteen rows named `Not used`
  such as `hrt`, `brz`, `jaw`) and 3 with `spawnable` 1: `elx` (`elixir`, level 21), `0sc` (`Scroll`, level 0) and `std`
  (`Standard`, level 90). Weapons and Armor have none. (tool:unreached.py --table items --list, tbl:Misc.txt:spawnable)
- Scope note: the tool does not read item-creation call sites (potions, the ear, the quest items), so none of the 26 is
  proved unreachable; the unreached set is the rows no table names.

## Gaps (what the tool does not do)

- MonStats: classes created by an immediate id (uber bosses, trap and turret skills, spawners) and a DS1's actual preset use
  (the 95 `MonPreset` names are the act lists, not the placed entries) are not read.
- Skills and States: ids passed as immediates by the AI functions and skill handlers are invisible; the States code scan is the
  stats/0002 one, not rerun here.
- Levels: the link ranges and portal ends are transcribed from the specs (`LINK_RANGES`, `PORTAL_LEVELS` in the tool), not parsed.
- Objects, Missiles, Shrines, Cubemain recipes, ItemTypes, uniques and sets, and the affix tables were not surveyed (plan 0062
  names the first five groups only).

## Open questions

- [L] Which of the 129 MonStats classes, 13 skills and 26 Misc items are created by code with an immediate id; a reader scan like
  `tools/state_setters.py` over the monster-creation and skill-spawn functions would turn the upper bound into a count.
