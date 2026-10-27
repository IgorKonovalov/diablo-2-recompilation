# MonAI (`data/global/excel/monai.txt` → `monai.bin`): the AI index

> **Source archive:** patch_d2 (`.txt` and `.bin`)   **Rows:** 148 (no `Expansion` marker)   **Record:** 2 B
> **sha256:** `.txt` `37df4743a210f1dadda41568e273ebc3d9dcc92d26382e26d537af91fab84dc7`, `.bin` `0c4c75bda2029730bf89bb1feaa7fb1ab1f008637e5d2ccb14359280d3ed8e1e`
> **Doc status:** layout complete; the index of every AI-table row with the stock records that reach it (plan 0052
> Phase 0); what each AI does is plan 0052 Phase 1's

## Purpose

A list of 148 AI names (`None`, `Idle`, `Skeleton`, `Zombie`, … `UberDiablo`). The row has no data besides its name and
eight comment columns. MonStats `AI` names a row; the compiled cell is the row index, and the same index selects the
row of `g_MonAiTable` in `Game.exe` that holds the AI's functions. This doc is the **AI index** of plan 0052: every row
of the table, with the MonStats records that use it and which stock PetType and Hireling rows reach it (owner decision,
question 8: the catalogue covers the whole table). Readers: `monsters/ai` ([plan 0052](../plans/0052-monster-ai.md)).
Survey: `python3 -I tools/ai_survey.py` (gate survey `ai`). Leads: the not-loaded `Aiparms.txt` and the comment columns,
for parameter names only (§ Leads).

## Row identity

- `[C]` Key column `AI`, 148 distinct values (also case-insensitively), none blank. `monai.bin` is a u32 count (148) and
  one u16 per row, equal to the row index (`ai_bin_is_row=148`; `python3 -I tools/excel_bin.py diff <excel-dir> monai`:
  148 cells, 0 mismatches), as [MonPlace](MonPlace.md)'s `code`. (tbl:MonAI.txt:AI)
- `[C]` **MonStats `AI` (`+0x01E` u16) stores the row index of the name**, the first row whose `AI` equals the cell:
  all 734 records resolve, none is blank, and every name matches its row exactly in case (`ms_ai_blank=0`,
  `ms_ai_bad=0`, `ms_ai_name_mismatch=0`). (tbl:MonStats.txt:AI)
- `[I]` In a stock run `monai.bin` is **not loaded**: `DATATBLS_LoadCodeLists` loads it only under `-txt`, to resolve
  `AI` names while compiling `monstats.txt` ([data/0001 § 3](../findings/data/0001-excel-loader.md#3-what-is-registered-datatbls_loadall-0x00619300),
  fn:DATATBLS_LoadCodeLists@0x00612750). The game therefore knows an AI only by its index.
- `[I]` **The index selects a 16-byte row of `g_MonAiTable`** (`0x0073CA18`): `sub_005B15D0_MonAiEntryGet` returns
  `0x0073CA18 + 16·AI` for `AI` < 148, and the AI function is the row's word at `+8`
  ([items/0001](../findings/items/0001-tc-resolution.md), data:g_MonAiTable@0x0073CA18,
  fn:sub_005B15D0_MonAiEntryGet@0x005B15D0). So the image table and `monai.txt` have the same 148 rows in the same order;
  the names below are the `.txt`'s, and only the index reaches the code.

## Columns

`[C]` layout: `python3 -I tools/excel_bin.py diff workspace/merged/data/global/excel monai`, 148 records × 1 field, **0
mismatches** (layout `monai` in `tools/excel_layouts.py`). Observed values from the `.txt`, by script.

| Column | Observed type / range | `.bin` field | Meaning | References | Tag |
|---|---|---|---|---|---|
| `AI` | str, 148 distinct, len ≤ 18, 0 blank | `+0x000` u16: the row's own index (0..147) | the AI's name; the record holds only its index | `monai:AI` (itself); named by MonStats `AI` | layout [C]; meaning [L] |
| `*aip1` … `*aip8` | str, 448 non-blank cells over 95 rows (`ai_comment_cells`, `ai_comment_rows`) | — (comment columns, not compiled) | an editor label per parameter slot (`Skeleton`: `approach?`, `stall time`, `attack?`, `att1/att2?`) | — | [C] value; meaning [L] |
| `*eol` | int, always 0 | — (not compiled) | end-of-line marker | — | [C] |

## The AI table in the image

`[C]` as bytes: `python3 -I tools/ai_survey.py index <excel-dir> workspace/install/app/game.exe` reads the 148 rows of
16 bytes at `0x0073CA18` from the pinned image (it refuses another hash) as four u32 words, `+0`, `+4`, `+8`, `+C`
(keys `tbl_*`). Only the `+8` word has a meaning from a finding; the other three are named here by offset alone.

- `[C]` The row after the last (index 148, `0x0073D358`) is 16 zero bytes. `[I]` The bound 148 is `MonAiEntryGet`'s
  (above), so no index past 147 reaches a row (data:g_MonAiTable@0x0073CA18).
- `[C]` `+8` is non-zero in all 148 rows and takes 147 distinct values (`tbl_fn8_distinct=147`): **rows 106
  `ShadowMaster` and 143 `ShadowMasterNoInit` hold the same word `0x005EB970`**, every other row its own. Rows 0 `None`
  and 1 `Idle` hold `0x005B0CC0` and `0x005B0CD0`; the other 146 lie in `0x005E0160`..`0x005FD210`. `[I]` By items/0001
  the `+8` word is the AI function, so rows 106 and 143 share their AI function; whether that function's path depends
  on the row is Phase 1's (data:g_MonAiTable@0x0073CA18).
- `[C]` `+0` takes 0 (26 rows), 1 (104), 2 (16), 4 (row 15 `SandMaggot`) and 5 (row 52 `FrogDemon`). The 26 zero rows
  are 0, 1, 31, 32, 41, 42, 54, 58, 60, 61, 66, 67, 81, 83, 84, 100–104, 108, 109, 112, 132, 135, 140; the 16 rows of
  2 are 56, 57, 77, 80, 86, 105–107, 110, 111, 127, 128, 131, 133, 134, 143. `[L]` A small count or kind; no
  finding reads it.
- `[C]` `+4` is set in 19 rows with 15 values; shared: `0x005F6630` by rows 43 `FoulCrowNest`, 45 `Sarcophagus` and
  121 `MinionSpawner`, `0x005EA290` by 101 `AssassinSentry` and 104 `DeathSentry`, `0x005EC6A0` by 110 `Vines` and 111
  `CycleOfLife`. The others: 59, 84, 102, 105, 106, 107, 122, 127, 128, 129, 134 and 143 (`0x005EB5C0`, against row
  106's `0x005EB490`). `[L]` An address in the AI code range, by its value only (row 143's name suggests an init
  function that row 143 does not share with 106; no finding reads the slot).
- `[C]` `+C` is set in 11 rows with 7 values; shared: `0x005E8480` by 51 `Diablo` and 147 `UberDiablo`, `0x005E5280`
  by 61 `Hireable` and 128 `Nihlathak`, `0x005FCF30` by 135 `BaalCrab`, 140 `BaalCrabClone` and 145 `UberBaal`; the
  others 15, 29, 52, 65. `[L]` As `+4`.

## The index

Generated by `python3 -I tools/ai_survey.py md workspace/merged/data/global/excel workspace/install/app/game.exe`
(`[C]` as data; regenerate, do not edit by hand). Columns:

- **slot `+8`**: the row's `+8` word (§ The AI table in the image).
- **n**, **MonStats records**: the records whose `AI` is the row, as record ranges (`a-b first..last`); a range is
  consecutive records, not one family.
- **reach**: P a record is a level pool class (Levels `mon1..10`, `nmon1..10`, `umon1..10`), U a superunique's class
  (SuperUniques `Class`), S a summon (a Skills row with a `pettype` names the record in `summon`, or a PetType `mclass`
  cell names it), H a hireling class (Hireling `Class`); `·` records but none of the four; **none** no stock record.
  The marks say which stock rows name a record, not that the game reaches the AI only that way (presets, minions,
  `spawn`, quest and skill spawns are not marked).
- **`aip` set**: the `aip<k>` slots non-zero in any difficulty of any of the records (blank and 0 both store 0).
- **`aidel` n/N/H**: the values of `aidel`, `aidel(N)`, `aidel(H)` over the records; 0 is a blank cell, which the
  mode start reads as 15 `[I]` (§ AI columns of MonStats).
- **skills**: the distinct Skills rows the records name in `Skill1..8`.
- **batch**: the Phase 1 batch proposal (§ Batches).

<!-- ai_survey.py md: begin -->
| # | AI | slot `+8` | n | MonStats records | reach | `aip` set | `aidel` n/N/H | skills | batch |
|---:|---|---|---:|---|---|---|---|---|---|
| 0 | `None` | `005B0CC0` | 0 | — | **none** | — | — | — | machinery |
| 1 | `Idle` | `005B0CD0` | 61 | 34-37 gorgon1..gorgon4, 106-109 chaoshorde1..chaoshorde4, 149 chicken, 151-152 rat..rogue1, 157-159 bird1..bat, 179 cow, 185 camel, 217-227 darkguard1..maggot, 268-269 bug..scorpion, 283 larva, 293 familiar, 318-320 snake..fish, 339-343 minispider..boneprison4, 356 dopplezon, 358 act2guard3, 366 compellingorb, 370 spiritmummy, 377-378 act2guard4..act2guard5, 392-393 window1..window2, 429 eagle, 432-434 barricadedoor1..prisondoor, 450-452 wolfrider1..wolfrider3, 524-525 barricadewall1..barricadewall2, 556 bunny, 567-569 injuredbarb1..injuredbarb3, 574 worldstoneeffect | S | 1 | 0,15/0,14,15/0,13,15 | Jab, Baal Taunt | machinery |
| 2 | `Skeleton` | `005EFCF0` | 9 | 0-4 skeleton1..skeleton5, 391 hellbovine, 648-649 skeleton6..skeleton7, 725 skeleton8 | PU | 1,2,3,4 | 15/14/13 | SkeletonRaise | rest-1 |
| 3 | `Zombie` | `005EFE20` | 5 | 5-9 zombie1..zombie5 | PU | 1,2,4 | 15/14/13 | — | rest-1 |
| 4 | `Bighead` | `005EFF50` | 10 | 10-14 bighead1..bighead5, 580-584 bighead6..bighead10 | PU | 1,2,3,4 | 15/14/13 | — | rest-1 |
| 5 | `BloodHawk` | `005F00E0` | 8 | 15-18 foulcrow1..foulcrow4, 590-593 foulcrow5..foulcrow8 | P | 1,2,3,4,5 | 15/14,15/13,15 | — | rest-1 |
| 6 | `Fallen` | `005F02C0` | 8 | 19-23 fallen1..fallen5, 642-644 fallen6..fallen8 | PU | 1,2,3,4 | 15/14/13 | — | rest-1 |
| 7 | `Brute` | `005EFB80` | 9 | 24-28 brute2..brute1, 446-449 snowyeti1..snowyeti4 | PU | 3,4 | 15/14/13 | — | rest-1 |
| 8 | `SandRaider` | `005F0700` | 10 | 29-33 sandraider1..sandraider5, 599-603 sandraider6..sandraider10 | PU | 1,2,3,4,5,6,7 | 15/9,14/7,13 | Fire Hit | rest-1 |
| 9 | `Wraith` | `005F0A20` | 9 | 38-42 wraith1..wraith5, 631-633 wraith6..wraith8, 732 wraith9 | P | 1,2,3 | 15/14/13 | — | rest-1 |
| 10 | `CorruptRogue` | `005F0B00` | 6 | 43-47 corruptrogue1..corruptrogue5, 721 corruptrogue6 | PU | 1,2,3,4,5 | 15/14/13 | CountessFirewall | rest-1 |
| 11 | `Baboon` | `005F0CD0` | 8 | 48-52 baboon1..baboon5, 295 baboon6, 665-666 baboon7..baboon8 | P | 1,2,3,4,5 | 15/14/13 | — | rest-2 |
| 12 | `Goatman` | `005F12A0` | 10 | 53-57 goatman1..goatman5, 585-589 goatman6..goatman10 | P | 1,2,3 | 15/14/13 | — | rest-2 |
| 13 | `FallenShaman` | `005F1440` | 8 | 58-62 fallenshaman1..fallenshaman5, 645-647 fallenshaman6..fallenshaman8 | PU | 1,2,3,4,5 | 15/14/13 | Resurrect, ShamanFire, ShamanIce, ShamanFireEx | rest-2 |
| 14 | `QuillRat` | `005F1140` | 8 | 63-67 quillrat1..quillrat5, 605-607 quillrat6..quillrat8 | PU | 1,2,4 | 15/12,14/9,13 | — | rest-2 |
| 15 | `SandMaggot` | `005F1800` | 7 | 68-72 sandmaggot1..sandmaggot5, 679 sandmaggot6, 716 sandmaggot7 | P | 1,2,3,4,5 | 15/14/13 | MagottUp, MagottDown, MagottLay | rest-2 |
| 16 | `ClawViper` | `005F1B60` | 5 | 73-77 clawviper1..clawviper5 | PU | 1,2,3,4,5,6 | 15/14/13 | SerpentCharge | rest-2 |
| 17 | `SandLeaper` | `005F20A0` | 7 | 78-82 sandleaper1..sandleaper5, 629-630 sandleaper6..sandleaper7 | P | 1,2,3,4 | 15/14/13 | Leap | rest-2 |
| 18 | `PantherWoman` | `005F22B0` | 6 | 83-86 pantherwoman1..pantherwoman4, 627-628 pantherwoman5..pantherwoman6 | PU | 1,2,3,4,5 | 15/13,14/12,13 | — | rest-2 |
| 19 | `Swarm` | `005F2460` | 5 | 87-90 swarm1..swarm4, 715 swarm5 | P | 1,2,3 | 15/14/13 | Swarm Move | rest-2 |
| 20 | `Scarab` | `005F2540` | 8 | 91-95 scarab1..scarab5, 654-655 scarab6..scarab7, 718 scarab8 | PU | 1,2,3,4,5 | 15/14/13 | Jab | rest-2 |
| 21 | `Mummy` | `005F2850` | 6 | 96-100 mummy1..mummy5, 703 mummy6 | PU | 1,2,3,4,5 | 15/14/13 | — | rest-2 |
| 22 | `GreaterMummy` | `005F2B10` | 10 | 101-105 unraveler1..unraveler5, 229 radament, 667-670 unraveler6..unraveler9 | PU | 1,2,3,4,5 | 15/14/13 | Resurrect2, Bestow, UnHolyBolt, UnHolyBoltEx | rest-3 |
| 23 | `Vulture` | `005F3170` | 5 | 110-113 vulture1..vulture4, 608 vulture5 | P | 1,2,3,4,5 | 15/13,14/11,13 | — | rest-3 |
| 24 | `Mosquito` | `005F3730` | 4 | 114-117 mosquito1..mosquito4 | P | 3,4,5 | 15/14/13 | Mosquito | rest-3 |
| 25 | `WillOWisp` | `005F39B0` | 8 | 118-121 willowisp1..willowisp4, 639-641 willowisp5..willowisp7, 733 willowisp8 | PU | 1,2,3 | 15/14/13 | Chain Lightning | rest-3 |
| 26 | `Arach` | `005F4510` | 7 | 122-126 arach1..arach5, 685 arach6, 717 arach7 | PU | 1,2,3,4,5 | 15/14/13 | SpiderLay | rest-3 |
| 27 | `ThornHulk` | `005F4850` | 5 | 127-130 thornhulk1..thornhulk4, 609 thornhulk5 | PU | 1,2,3,4,5,6 | 15/13,14/12,13 | MonFrenzy | rest-3 |
| 28 | `Vampire` | `005F4A70` | 9 | 131-135 vampire1..vampire5, 695-697 vampire6..vampire8, 731 vampire9 | P | 1,2,3,4,5 | 15/14/13 | VampireFireball, VampireFirewall, VampireMeteor, VampireMissile | rest-3 |
| 29 | `BatDemon` | `005F5040` | 7 | 136-140 batdemon1..batdemon5, 650-651 batdemon6..batdemon7 | PU | 1,2,3,4,5 | 15/14/13 | — | rest-3 |
| 30 | `Fetish` | `005F53E0` | 16 | 141-145 fetish1..fetish5, 212-216 bonefetish1..bonefetish5, 407 fetish11, 656-658 fetish6..fetish8, 690-691 bonefetish6..bonefetish7 | P | 1,2,3,4 | 15/14,15/13,15 | SkeletonRaise | rest-3 |
| 31 | `NpcOutOfTown` | `005E7880` | 2 | 146 cain1, 527 drehyaiced | · | — | 15/15/15 | — | rest-3 |
| 32 | `Npc` | `005E7130` | 35 | 147-148 gheed..akara, 150 kashya, 154-155 charsi..warriv1, 175-178 warriv2..fara, 198-202 greiz..lysander, 210 meshif1, 244-246 cain2..cain4, 252-255 asheara..ormus, 257 halbu, 264-265 meshif2..cain5, 297 natalya, 405 jamella, 511-515 larzuk..qual-kehk, 520 cain6, 535-536 act5barb3..act5barb4 | · | — | 15/15/15 | — | rest-4 |
| 33 | `HellMeteor` | `005F56D0` | 1 | 153 hellmeteor | · | 1,2,3 | 15/15/15 | HellMeteor | rest-4 |
| 34 | `Andariel` | `005F5830` | 2 | 156 andariel, 707 uberandariel | · | 1,2,3,4 | 15/11/9 | AndrialSpray, AndyPoisonBolt | bosses |
| 35 | `CorruptArcher` | `005F5A20` | 8 | 160-164 cr_archer1..cr_archer5, 613-614 cr_archer6..cr_archer7, 722 cr_archer8 | PU | 1,2,3,4,5,6,7,8 | 15/13,14/11,13 | MonBow, MonFireArrow, MonExplodingArrow, MonColdArrow, MonFreezingArrow | rest-4 |
| 36 | `CorruptLancer` | `005F5D50` | 9 | 165-169 cr_lancer1..cr_lancer5, 615-617 cr_lancer6..cr_lancer8, 723 cr_lancer8 | P | 1,2,3,4,5,6,7 | 15/13,14/12,13 | Jab, MonPowerStrike, MonIceSpear | rest-4 |
| 37 | `SkeletonBow` | `005F6070` | 11 | 170-174 sk_archer1..sk_archer5, 575-579 sk_archer6..sk_archer10, 726 sk_archer11 | P | 1,2,3,4,5 | 15/14/13 | SkeletonRaise | rest-4 |
| 38 | `MaggotLarva` | `005F6220` | 6 | 180-184 maggotbaby1..maggotbaby5, 680 maggotbaby6 | · | 1,2,3,4,5 | 15/14/13 | — | rest-4 |
| 39 | `PinHead` | `005F6340` | 6 | 186-189 blunderbore1..blunderbore4, 618-619 blunderbore5..blunderbore6 | P | 1,2,3,4,5 | 15/13,14/12,13 | Smite | rest-4 |
| 40 | `MaggotEgg` | `005F6530` | 6 | 190-194 maggotegg1..maggotegg5, 681 maggotegg6 | · | 1,2 | 15/14,15/13,15 | MaggotEgg | rest-5 |
| 41 | `Towner` | `005E7540` | 6 | 195-197 act2male..act2child, 203 act2guard1, 294 act3male, 296 act3female | · | — | 15/15/15 | — | rest-5 |
| 42 | `Vendor` | `005E9E00` | 2 | 204-205 act2vendor1..act2vendor2 | · | — | 15/15/15 | — | rest-5 |
| 43 | `FoulCrowNest` | `005F6650` | 4 | 206-209 crownest1..crownest4 | P | 1,3 | 15/15/15 | Nest | rest-5 |
| 44 | `Duriel` | `005F67B0` | 2 | 211 duriel, 708 uberduriel | · | 1,2,3 | 15/15/15 | Charge, Jab, Smite, Holy Freeze | bosses |
| 45 | `Sarcophagus` | `005F6A10` | 1 | 228 sarcophagus | · | 1,3 | 15/15/15 | Nest | rest-5 |
| 46 | `ElementalBeast` | `005F6B70` | 4 | 230-233 firebeast..poisonorb | · | 1,2,3 | 15/15/15 | — | rest-5 |
| 47 | `FlyingScimitar` | `005F6CA0` | 1 | 234 flyingscimitar | · | 1,2,3,4 | 15/13/10 | Charge | rest-5 |
| 48 | `ZakarumZealot` | `005F6E60` | 5 | 235-237 zealot1..zealot3, 671-672 zealot4..zealot5 | P | 1,2,3,4 | 15/14/13 | — | rest-5 |
| 49 | `ZakarumPriest` | `005F72D0` | 6 | 238-241 cantor1..cantor4, 673-674 cantor5..cantor6 | P | 1,2,3,4,5,6 | 15/14/13 | ZakarumHeal, ZakarumLightning, MonTeleport, MonBlizzard | rest-5 |
| 50 | `Mephisto` | `005F78B0` | 1 | 242 mephisto | · | 1,2,3 | 15/10/6 | PrimeLightning, PrimeBolt, PrimePoisonNova, MephistoMissile, MephFrostNova, Blizzard | bosses |
| 51 | `Diablo` | `005E9170` | 2 | 243 diablo, 333 diabloclone | · | — | 15/13/12 | DiabLight, DiabCold, DiabFire, DiabWall, DiabRun, PrimeFirewall, DiabPrison, Diablogeddon | bosses |
| 52 | `FrogDemon` | `005F8260` | 3 | 247-249 frogdemon1..frogdemon3 | P | 1,2,3,4,5,6,7,8 | 15/14/13 | Submerge, Emerge | rest-5 |
| 53 | `Summoner` | `005F85C0` | 1 | 250 summoner | U | 1,2,3,4,5,6,7,8 | 15/13/10 | Glacial Spike, Frost Nova, Fire Ball, VampireFirewall, Weaken | bosses |
| 54 | `NpcStationary` | `005E73A0` | 4 | 251 tyrael1, 367 tyrael2, 406 izualghost, 521 tyrael3 | · | — | 15/15/15 | — | rest-5 |
| 55 | `Izual` | `005F89B0` | 1 | 256 izual | · | 1,2,3,4,5,6 | 15/12/8 | Frost Nova | bosses |
| 56 | `Tentacle` | `005F8F80` | 3 | 258-260 tentacle1..tentacle3 | · | 1,2,3,4,5,6 | 15/15/15 | Submerge, Emerge | rest-5 |
| 57 | `TentacleHead` | `005F9270` | 3 | 261-263 tentaclehead1..tentaclehead3 | · | 1,2,3,4,5,6 | 15/15/15 | Submerge, Emerge | rest-5 |
| 58 | `Navi` | `005E7E20` | 1 | 266 navi | · | — | 15/15/15 | — | rest-5 |
| 59 | `BloodRaven` | `005E6320` | 1 | 267 bloodraven | · | — | 15/13/10 | Nest, Quick Strike | bosses |
| 60 | `GoodNpcRanged` | `005E7AC0` | 1 | 270 rogue2 | · | — | 15/15/15 | — | rest-5 |
| 61 | `Hireable` | `005E52D0` | 5 | 271 roguehire, 338 act2hire, 359 act3hire, 560-561 act5hire1..act5hire2 | SH | 1 | 1/1/1 | RogueMissile, Jab | hirelings |
| 62 | `TownRogue` | `005E7D60` | 1 | 272 rogue3 | · | — | 15/15/15 | — | rest-5 |
| 63 | `GargoyleTrap` | `005F9490` | 1 | 273 gargoyletrap | · | 1,2,3,4 | 15/15/15 | GargoyleTrap | rest-5 |
| 64 | `SkeletonMage` | `005F96C0` | 27 | 274-277 skmage_pois1..skmage_pois4, 379-390 skmage_cold1..skmage_ltng4, 620-626 skmage_fire5..skmage_pois6, 727-730 skmage_fire7..skmage_pois7 | PU | 1,2,3,4,5,6,7,8 | 15/13,15/12,15 | SkeletonRaise | rest-5 |
| 65 | `FetishShaman` | `005F9A80` | 8 | 278-282 fetishshaman1..fetishshaman5, 662-664 fetishshaman6..fetishshaman8 | PU | 1,2,3,4,5 | 15/14/13 | FetishInferno, FetishAura, Resurrect2 | rest-6 |
| 66 | `SandMaggotQueen` | `005F9CF0` | 5 | 284-288 maggotqueen1..maggotqueen5 | U | 1,2 | 15/15/15 | MagottUp, MagottDown, MagottLay, QueenDeath | rest-6 |
| 67 | `NecroPet` | `005E4CF0` | 9 | 289-292 claygolem..firegolem, 357 valkyrie, 363-364 necroskeleton..necromage, 430-431 wolf..bear | S | 1,2,3,4 | 6,15/6,15/6,15 | BloodGolem, NecromageMissile | summons |
| 68 | `VileMother` | `005FA010` | 5 | 298-300 vilemother1..vilemother3, 675-676 vilemother4..vilemother5 | PU | 1,2,3,4,5,6,7 | 15/14/13 | Nest | rest-6 |
| 69 | `VileDog` | `005FA280` | 10 | 301-303 vilechild1..vilechild3, 551-555 painworm1..painworm5, 677-678 vilechild4..vilechild5 | · | 1,2,3 | 15/14/13 | — | rest-6 |
| 70 | `FingerMage` | `005FA380` | 5 | 304-306 fingermage1..fingermage3, 692-693 fingermage4..fingermage5 | PU | 1,2,3,4,5,6,7,8 | 15/14/13 | FingerMageSpider | rest-6 |
| 71 | `Regurgitator` | `005FA710` | 4 | 307-309 regurgitator1..regurgitator3, 694 regurgitator4 | PU | 1,2,3,4,5,6 | 15/14/13 | RegurgitatorEat | rest-6 |
| 72 | `DoomKnight` | `005FAA90` | 3 | 310 doomknight1, 699-700 dkfig1..dkfig2 | P | 1,2,3,4 | 15/14/13 | — | rest-6 |
| 73 | `AbyssKnight` | `005FAB80` | 1 | 311 doomknight2 | P | 1,2,3,4,5,6,7,8 | 15/14/13 | DoomKnightMissile, MonBoneArmor, MonBoneSpirit | rest-6 |
| 74 | `OblivionKnight` | `005FAF00` | 4 | 312 doomknight3, 701-702 dkmag1..dkmag2, 713 dkmag3 | PU | 1,2,3,4,5,6,7,8 | 15/14/13 | DoomKnightMissile, MonBoneArmor, MonBoneSpirit, Decrepify, Bestow, MonCurseCast | rest-6 |
| 75 | `QuillMother` | `005FB2A0` | 5 | 313-317 quillbear1..quillbear5 | · | 1,2,3,4 | 15/15/15 | — | rest-6 |
| 76 | `EvilHole` | `005FB410` | 6 | 321-325 evilhole1..evilhole5, 711 demonhole | · | 1,2 | 15/15/15 | Nest | rest-6 |
| 77 | `Trap-Missile` | `005FB5B0` | 2 | 326 trap-firebolt, 330 trap-lightning | · | 1,2,3 | 15/15/15 | — | rest-6 |
| 78 | `Trap-RightArrow` | `005FB6C0` | 1 | 327 trap-horzmissile | · | 1,2,3,4 | 15/15/15 | PoisonBallTrap, CursedBallTrapRight | rest-6 |
| 79 | `Trap-LeftArrow` | `005FB7E0` | 1 | 328 trap-vertmissile | · | 1,2,3,4 | 15/15/15 | PoisonBallTrap, CursedBallTrapLeft | rest-6 |
| 80 | `Trap-Poison` | `005FB900` | 1 | 329 trap-poisoncloud | · | 1,2,3 | 15/15/15 | PrimePoisonNova | rest-6 |
| 81 | `JarJar` | `005E7590` | 1 | 331 act2guard2 | · | — | 15/15/15 | — | rest-6 |
| 82 | `InvisoSpawner` | `005E0160` | 1 | 332 invisospawner | · | 1,2,3 | 15/15/15 | — | rest-6 |
| 83 | `MosquitoNest` | `005E0260` | 4 | 334-337 suckernest1..suckernest4 | · | 1,2,3 | 15/15/15 | Nest | rest-6 |
| 84 | `BoneWall` | `005E0400` | 1 | 344 bonewall | S | — | 15/15/15 | Bone Wall | summons |
| 85 | `HighPriest` | `005E0490` | 4 | 345-347 councilmember1..councilmember3, 557 baalhighpriest | U | 1,2,3,4,5,6,7,8 | 15/13,14/12,13 | Hydra, ZakarumHeal | rest-7 |
| 86 | `Hydra` | `005E9E60` | 3 | 351-353 hydra1..hydra3 | S | — | 15/15/15 | HydraMissile | summons |
| 87 | `Trap-Melee` | `005FBA60` | 1 | 354 trap-melee | · | 1,2 | 15/15/15 | — | rest-7 |
| 88 | `7TIllusion` | `005EA080` | 1 | 355 seventombs | · | — | 15/15/15 | — | rest-7 |
| 89 | `Megademon` | `005E0C80` | 7 | 360-362 megademon1..megademon3, 558 venomlord, 686-687 megademon4..megademon5, 712 megademon6 | PU | 1,2,3,4,5,6 | 15/13,14/11,13 | MegademonInferno | rest-7 |
| 90 | `Griswold` | `005E5AC0` | 1 | 365 griswold | U | — | 15/13/10 | — | bosses |
| 91 | `DarkWanderer` | `005EA130` | 1 | 368 darkwanderer | · | — | 15/15/15 | — | rest-7 |
| 92 | `Trap-Nova` | `005FB9B0` | 1 | 369 trap-nova | · | 1,2,3 | 15/15/15 | Trap Nova | rest-7 |
| 93 | `ArcaneTower` | `005E0F60` | 1 | 371 lightningspire | · | 1,2,3,4,5,6 | 15/15/15 | ArcaneTower, Lightning | rest-7 |
| 94 | `DesertTurret` | `005E0980` | 4 | 348-350 turret1..turret3, 372 firetower | · | 1,2,3,4,5 | 15/15/15 | DesertTurret | rest-7 |
| 95 | `PantherJavelin` | `005E1080` | 9 | 373-376 slinger1..slinger4, 394-395 slinger5..slinger6, 610-612 slinger7..slinger9 | P | 1,2,3,4,5,6 | 15/13,14/12,13 | — | rest-7 |
| 96 | `FetishBlowgun` | `005E1250` | 8 | 396-400 fetishblow1..fetishblow5, 659-661 fetishblow6..fetishblow8 | P | 1,2 | 15/14/13 | SkeletonRaise | rest-7 |
| 97 | `Spirit` | `005E3840` | 1 | 401 mephistospirit | · | — | 15/15/15 | — | rest-7 |
| 98 | `Smith` | `005E3890` | 2 | 402 smith, 409 hephasto | U | — | 15/13/12 | — | rest-7 |
| 99 | `TrappedSoul` | `005E9F10` | 2 | 403-404 trappedsoul1..trappedsoul2 | · | — | 15/15/15 | — | rest-7 |
| 100 | `Buffy` | `005E7F50` | 1 | 408 malachai | · | — | 15/15/15 | — | rest-7 |
| 101 | `AssassinSentry` | `005EA3D0` | 4 | 410-412 wakeofdestruction..lightningsentry, 415 infernosentry | S | 1,2,3,4 | 15/15/15 | Wake Of Destruction Sentry, BoltSentry, Shock Field, sentry lightning, mon inferno sentry, Wake of Fire Sentry | summons |
| 102 | `BladeCreeper` | `005EA540` | 1 | 413 bladecreeper | S | — | 15/15/15 | Blade Sentinel | summons |
| 103 | `InvisoPet` | `005EA7A0` | 1 | 414 invisopet | · | 1,2 | 15/15/15 | — | rest-7 |
| 104 | `DeathSentry` | `005EA980` | 1 | 416 deathsentry | S | 1,3,4 | 15/15/15 | mon death sentry, death sentry ltng | summons |
| 105 | `ShadowWarrior` | `005EAFA0` | 1 | 417 shadowwarrior | S | 1,2,3,4,8 | 15/15/15 | Fists of Fire, Blade Fury, Blades of Ice, Dragon Claw, Dragon Flight, Claws of Thunder, Attack | summons |
| 106 | `ShadowMaster` | `005EB970` | 1 | 418 shadowmaster | S | 1,2,3,8 | 15/15/15 | Fists of Fire, Blade Fury, Blades of Ice, Dragon Claw, Dragon Flight, Claws of Thunder, Attack | summons |
| 107 | `Raven` | `005ECC10` | 1 | 419 druidhawk | S | 1,2,3,4,5 | 15/15/15 | Raven | summons |
| 108 | `DruidWolf` | `005ED710` | 2 | 420-421 spiritwolf..fenris | S | 1,2,3,4,5 | 15/15/15 | Teleport 2, fenris rage | summons |
| 109 | `Totem` | `005ED9E0` | 3 | 422-424 spiritofbarbs..oaksage | S | 1,2,3,4 | 15/15/15 | — | summons |
| 110 | `Vines` | `005EC6C0` | 1 | 425 plaguepoppy | S | 1,2,3,4,5 | 15/15/15 | Vine Attack | summons |
| 111 | `CycleOfLife` | `005EC8C0` | 2 | 426-427 cycleoflife..vinecreature | S | 1,2,3,4,5 | 15/15/15 | CorpseCycler, VineCycler | summons |
| 112 | `DruidBear` | `005ED730` | 1 | 428 druidbear | S | 1,2,3 | 15/15/15 | BearSmite | summons |
| 113 | `SiegeTower` | `005E1860` | 1 | 435 barricadetower | · | 1 | 15/15/15 | — | rest-7 |
| 114 | `ReanimatedHorde` | `005E1540` | 6 | 436-440 reanimatedhorde1..reanimatedhorde5, 698 reanimatedhorde6 | PU | 1,2,3,4,5,6,7,8 | 15/14/13 | Self-resurrect, Charge | rest-7 |
| 115 | `SiegeBeast` | `005E1900` | 5 | 441-445 siegebeast1..siegebeast5 | PU | 1,2,3,4,5,6,7 | 15/14/13 | Siege Beast Stomp, Charge | rest-7 |
| 116 | `Minion` | `005E1B60` | 11 | 453-460 minion1..minion8, 682-684 minion9..minion11 | PU | 1,2,3,4,5 | 15/14/13 | — | rest-8 |
| 117 | `SuicideMinion` | `005E1D30` | 8 | 461-468 suicideminion1..suicideminion8 | P | 1,2,3,4 | 15/14/13 | — | rest-8 |
| 118 | `Succubus` | `005E1E00` | 8 | 469-473 succubus1..succubus5, 634-635 succubus6..succubus7, 719 succubus8 | PU | 1,2,3,4,5,6,7,8 | 15/14/13 | Defense Curse, Blood Mana, SuccubusBolt | rest-8 |
| 119 | `SuccubusWitch` | `005E2120` | 9 | 474-478 succubuswitch1..succubuswitch5, 636-638 succubuswitch6..succubuswitch8, 720 succubuswitch9 | PU | 1,2,3,4,5,6,7,8 | 15/14/13 | Amplify Damage, Weaken, Defense Curse, Blood Mana, SuccubusBolt | rest-8 |
| 120 | `Overseer` | `005E27A0` | 6 | 479-483 overseer1..overseer5, 724 overseer6 | PU | 1,2,3,4,5,6,7 | 15/14/13 | Cry Help, Healing Vortex, Overseer Whip, Smite | rest-8 |
| 121 | `MinionSpawner` | `005E2BD0` | 9 | 484-491 minionspawner1..minionspawner8, 710 demonspawner | · | 1,2,3,4,5 | 15/15/15 | MinionSpawner | rest-8 |
| 122 | `Imp` | `005E2FF0` | 8 | 492-496 imp1..imp5, 688-689 imp6..imp7, 714 imp8 | PU | 1,2,3,4 | 15/14/13 | Imp Teleport, ImpBolt, Imp Fireball, Imp Fire Missile, Imp Inferno, Imp Fire Missile Ex | rest-8 |
| 123 | `Catapult` | `005E34C0` | 4 | 497-500 catapult1..catapult4 | · | 1 | 15/15/15 | — | rest-8 |
| 124 | `FrozenHorror` | `005E3530` | 5 | 501-505 frozenhorror1..frozenhorror5 | PU | 1,2,3,4 | 15/14/13 | Horror Arctic Blast | rest-8 |
| 125 | `BloodLord` | `005E36F0` | 7 | 506-510 bloodlord1..bloodlord5, 652-653 bloodlord6..bloodlord7 | PU | 1,2,3,4 | 15/14/13 | BloodLordFrenzy | rest-8 |
| 126 | `CatapultSpotter` | `005EE040` | 4 | 516-519 catapultspotter1..catapultspotter4 | · | 1,2,3,4,5 | 15/15/15 | Catapult Charged Ball, Catapult Spike Ball, CatapultBlizzard, CatapultPlague, CatapultMeteor | rest-8 |
| 127 | `NpcBarb` | `005EDC50` | 2 | 522-523 act5barb1..act5barb2 | · | 1,2,3 | 15/15/15 | — | rest-9 |
| 128 | `Nihlathak` | `005EE5D0` | 1 | 526 nihlathakboss | U | 1,2,3,4,5 | 15/15/15 | Imp Teleport, Overseer Whip, NihlathakCorpseExplosion, Horror Arctic Blast, MinionSpawner | bosses |
| 129 | `GenericSpawner` | `005E61B0` | 1 | 528 evilhut | · | 1,3 | 15/15/15 | Nest | rest-9 |
| 130 | `DeathMauler` | `005EE260` | 6 | 529-533 deathmauler1..deathmauler5, 604 deathmauler6 | PU | 1,2,3,4 | 15/15/15 | DeathMaul | rest-9 |
| 131 | `Wussie` | `005EE3C0` | 1 | 534 act5pow | · | — | 15/15/15 | — | rest-9 |
| 132 | `AncientStatue` | `005EEAA0` | 3 | 537-539 ancientstatue1..ancientstatue3 | · | — | 15/15/15 | MinionSpawner | rest-9 |
| 133 | `Ancient` | `005EF1A0` | 3 | 540-542 ancientbarb1..ancientbarb3 | PU | 1,2,3,4,5 | 15/13/11 | Whirlwind, Shout, Leap Attack | rest-9 |
| 134 | `BaalThrone` | `005EF320` | 1 | 543 baalthrone | · | 1 | 15/15/15 | Decrepify, Baal Corpse Explode, Defense Curse, Blood Mana | rest-9 |
| 135 | `BaalCrab` | `005FCFE0` | 1 | 544 baalcrab | · | — | 15/13/12 | Baal Nova, Baal Inferno, Baal Tentacle, Baal Cold Missiles, Baal Teleport, Defense Curse, Blood Mana | bosses |
| 136 | `BaalTaunt` | `005EF710` | 1 | 545 baaltaunt | P | 1,2,3 | 15/15/15 | Baal Taunt | rest-9 |
| 137 | `PutridDefiler` | `005EFA90` | 5 | 546-550 putriddefiler1..putriddefiler5 | P | 1,2 | 15/15/15 | Impregnate | rest-9 |
| 138 | `BaalToStairs` | `005EF620` | 1 | 559 baalcrabstairs | · | 1 | 15/15/15 | — | bosses |
| 139 | `BaalTentacle` | `005EF820` | 5 | 562-566 baaltentacle1..baaltentacle5 | · | 1,2,3 | 15/15/15 | — | rest-9 |
| 140 | `BaalCrabClone` | `005FD210` | 1 | 570 baalclone | · | — | 15/14/12 | Baal Nova, Baal Inferno, Baal Tentacle, Baal Cold Missiles, Baal Clone Teleport, Defense Curse, Blood Mana | bosses |
| 141 | `BaalMinion` | `005EF910` | 3 | 571-573 baalminion1..baalminion3 | U | 1,2,3,4 | 15/14/13 | Smite | rest-9 |
| 142 | `ClawViperEx` | `005F1DE0` | 5 | 594-598 clawviper6..clawviper10 | P | 1,2,3,4,5,6,7,8 | 15/14/13 | Charge | rest-9 |
| 143 | `ShadowMasterNoInit` | `005EB970` | 0 | — | **none** | — | — | — | summons |
| 144 | `UberIzual` | `005F8C80` | 1 | 706 uberizual | · | 1,2,3,4,5,6 | 15/12/8 | Frost Nova, Chilling Armor, MonTeleport | bosses |
| 145 | `UberBaal` | `005FD200` | 1 | 709 uberbaal | · | — | 15/13/12 | Baal Nova, Baal Inferno, Baal Tentacle, Baal Cold Missiles, Baal Teleport, Defense Curse, Blood Mana, Chilling Armor | bosses |
| 146 | `UberMephisto` | `005F81C0` | 1 | 704 ubermephisto | · | 1,2,3 | 15/10/6 | PrimeLightning, PrimeBolt, PrimePoisonNova, MephistoMissile, MephFrostNova, Blizzard | bosses |
| 147 | `UberDiablo` | `005E9DF0` | 1 | 705 uberdiablo | · | — | 15/13/12 | DiabLight, DiabCold, DiabFire, DiabWall, DiabRun, PrimeFirewall, DiabPrison, Diablogeddon | bosses |
<!-- ai_survey.py md: end -->

`[C]` Counts (keys of the `ai` survey): **148 rows; 146 named by at least one stock MonStats record; 2 named by none**,
rows 0 `None` and 143 `ShadowMasterNoInit` (`ai_used=146`, `ai_unused=2`). By reach: 63 rows have a pool class (365
records), 44 a superunique's class (62 records), 16 a summon (32 records), 1 a hireling class (`Hireable`, 4
records), and 60 rows have records but none of the four marks. 47 rows have one record; the most is 61 (`Idle`).

- `[C]` **Summons.** The 16 rows with S: 1 `Idle` (`dopplezon` 356 from Dopplezon, `boneprison1` 340 from
  DiabPrison), 61 `Hireable` (PetType `hireable`'s `mclass` 338, 359, 561), 67 `NecroPet` (the four golems 289–292,
  `valkyrie` 357, `necroskeleton` 363, `necromage` 364), 84 `BoneWall`, 86 `Hydra` (`hydra1` 351), 101
  `AssassinSentry` (four sentries), 102 `BladeCreeper`, 104 `DeathSentry`, 105 `ShadowWarrior`, 106 `ShadowMaster`,
  107 `Raven`, 108 `DruidWolf` (`spiritwolf`, `fenris`), 109 `Totem` (the three spirits), 110 `Vines` (`plaguepoppy`),
  111 `CycleOfLife` (`cycleoflife`, `vinecreature`), 112 `DruidBear`. Per PetType row: [PetType § AI of the
  summons](PetType.md#ai-of-the-summons-plan-0052-phase-0). (tbl:PetType.txt:mclass1, tbl:Skills.txt:summon)
- `[C]` Two summoning Skills rows have no `pettype` and so no S mark: 295 Overseer Whip (`suicideminion1`, AI 117
  `SuicideMinion`) and 300 Impregnate (`painworm1`, AI 69 `VileDog`). 95 Revive has a `pettype` (6 `revive`) and no
  `summon`: a revived monster is any class, so no AI row is marked for it. (tbl:Skills.txt:pettype)
- `[C]` **Hirelings.** All four Hireling classes (271 `roguehire`, 338 `act2hire`, 359 `act3hire`, 561 `act5hire2`)
  use row 61 `Hireable`, and so does 560 `act5hire1`, which has no Hireling row ([Hireling § AI of the
  hirelings](Hireling.md#ai-of-the-hirelings-plan-0052-phase-0)). (tbl:Hireling.txt:Class)
- `[C]` The 60 rows with records and no mark (`ai_reach_none_of_push=60`): 31–34, 38, 40–42, 44–47, 50, 51, 54–60,
  62, 63, 69, 75–83, 87, 88, 91–94, 97, 99, 100, 103, 113, 121, 123, 126, 127, 129, 131, 132, 134, 135, 138–140,
  144–147: the town and npc AIs, the act bosses and Uber rows, the traps, spawners, eggs and nests, and the siege and
  Baal set pieces. The other links that name a class (presets, `minion1/2`, `spawn`, skill and AI spawns) are not
  marked here. (tbl:MonStats.txt:minion1, tbl:MonStats.txt:spawn)

## Batches

`[C]` as data, by the rule `BATCH_RULE` of `tools/ai_survey.py` (`python3 -I tools/ai_survey.py batches <excel-dir>`):
a **proposal by record count**, as plan 0052 Phase 0 asks until P1.1 names shared code. Every one of the 148 rows is in
exactly one batch (`batch_rows=148`; the test `test_batches_cover_each_row_once`).

| Batch | AI rows | Records | Rows |
|---|---:|---:|---|
| machinery (with P1.1) | 2 | 61 | 0 `None` (no record), 1 `Idle` |
| rest-1 | 9 | 74 | 2–10 (`Skeleton` … `CorruptRogue`) |
| rest-2 | 11 | 78 | 11–21 (`Baboon` … `Mummy`) |
| rest-3 | 10 | 73 | 22–31 (`GreaterMummy` … `NpcOutOfTown`) |
| rest-4 | 7 | 76 | 32, 33, 35–39 (`Npc` … `PinHead`) |
| rest-5 | 18 | 79 | 40–43, 45–49, 52, 54, 56–58, 60, 62–64 (`MaggotEgg` … `SkeletonMage`) |
| rest-6 | 18 | 67 | 65, 66, 68–83 (`FetishShaman` … `MosquitoNest`) |
| rest-7 | 18 | 56 | 85, 87–89, 91–100, 103, 113–115 (`HighPriest` … `SiegeBeast`) |
| rest-8 | 11 | 79 | 116–126 (`Minion` … `CatapultSpotter`) |
| rest-9 | 12 | 36 | 127, 129–134, 136, 137, 139, 141, 142 (`NpcBarb` … `ClawViperEx`) |
| bosses | 16 | 19 | 34, 44, 50, 51, 53, 55, 59, 90, 128, 135, 138, 140, 144–147 |
| summons | 15 | 31 | 67, 84, 86, 101, 102, 104–112, 143 `ShadowMasterNoInit` (no record) |
| hirelings | 1 | 5 | 61 `Hireable` (with `MERCAI_PickSkill`, fn:MERCAI_PickSkill@0x005E4D30) |

- The rule: rows 0 and 1 go with P1.1 (their `+8` words lie apart from every other row's); summons are the other rows
  with an S record and no H, P or U record, plus row 143 (its `+8` word is row 106's); hirelings the rows with an H
  record and the AI of `act5hire1`; bosses the other rows with a `boss` or `primeevil` record and no P record; the rest
  in table order, cut at 80 records or 18 AI rows. Thirteen batches against the plan's estimate of eight to twelve: the
  whole-table coverage (question 8) adds the unreferenced and the many one-record AIs; P1.1 regroups by shared code.
- Hydra (86) is in summons although `hydra2` and `hydra3` carry no S mark: only `hydra1` is a Skills `summon`.

## AI columns of MonStats

The AI-relevant MonStats columns, per AI: `python3 -I tools/ai_survey.py rows <excel-dir> [<AI>]` prints every record
with `aidel`, `aidist`, `aip1..8` (n/N/H), `Skill1..8` with `Sk<k>mode` and `Sk<k>lvl`. Their layout and observed
ranges are in [MonStats § AI columns](MonStats.md#ai-columns-plan-0052-phase-0). `[C]` from the survey: 588 records
set an `aip` slot, 497 of them with a value that differs between difficulties; in 13 AI rows the records disagree on
which slots they set (`ai_aip_slots_differ=13`, for example 30 `Fetish`, 122 `Imp`, 133 `Ancient`); 393 records name a
skill (775 cells) in 97 AI rows.

## Leads

- `[L]` **The comment columns `*aip1..8`.** 95 rows label one or more slots. They are editor notes, not compiled; they
  are leads for what a slot is, never for how it is used. 25 rows set a slot in their records and label none (for
  example 50 `Mephisto`, 61 `Hireable`, 67 `NecroPet`, the druid and assassin summon AIs, the Baal AIs), and 5 rows set
  slots past their last label (6 `Fallen`, 36 `CorruptLancer`, 117 `SuicideMinion`, 118 `Succubus`, 122 `Imp`). Row
  143 `ShadowMasterNoInit` labels slots 1–3 and 8 (`approach dist/melee bonus/progressive bonus`, `random pick/ignore
  range`, `attack chance`, `summoning skill`) and has no record; `shadowmaster` (418, AI 106) sets `aip8` = 279 in
  Normal, the Skills row of Shadow Master. (tbl:MonAI.txt:AI)
- `[L]` **`Aiparms.txt`** (shipped, 7 359 bytes, sha256 `739620e34282567d322fb63a7ed3c342ec7382bdbf123dd1b2eaffdcff3ffdf5`)
  has no loader ([data/excel B1](../specs/data/excel.md); data/0001 § 3). `python3 -I tools/ai_survey.py aiparms
  <excel-dir>` splits it into 19 sections of prose (titles, then `P1`..`P5` lines, 78 in all, and `Missiles:` /
  `Skills:` lines). 16 sections match an AI row by a title: 14 by the AI's name (`Corrupt Rogue` → 10, `"Brute" Ai` → 7
  and `Thorn Hulk` → 27 in one section, …) and 2 by a MonStats display name (`Spike Fiend` → 14 `QuillRat`, `Sand Maggot
  Egg` → 40 `MaggotEgg`); `"Conservative" Ai`, `Serpent Demon` and `Sand Maggot Baby` match none. The file names four or
  five parameters per AI where 1.14d records set up to eight, and lists `Thorn Hulk` under the `Brute` AI where 1.14d gives
  it its own row 27: it describes an earlier build. A lead for parameter names only; Phase 1 reads the slots from the
  code.

## Open questions

- `[L]` What the `+0`, `+4` and `+C` words of a `g_MonAiTable` row are, and whether row 143 is ever installed on a unit
  (its name and its `+4` word against row 106's). Owner: reverser, plan 0052 P1.1 (the machinery) and the summons batch.
- `[L]` What each `aip<k>` slot means per AI. Owner: reverser, plan 0052 P1 (each catalogue batch).
- `[L]` Whether any path sets a unit's AI to a row other than its MonStats record's (a hireling, a revived or
  converted monster, row 143). Owner: reverser, plan 0052 P1.1.
