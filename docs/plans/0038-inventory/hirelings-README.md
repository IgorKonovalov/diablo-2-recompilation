# Plan 0038 inventory: hirelings/README

- **Spec:** [hirelings/README.md](../../specs/hirelings/README.md), read at `main` `e1c807a` (last change to the spec: `02aa5b0`).
- **Front matter `I`:** 39; the *count* column sums to 39.
- **Finding:** [hirelings/0001](../../findings/hirelings/0001-hirelings.md) (sections given as `§n`; other subsystems' findings named in full).
- **Cluster:** 0c (monsters, hirelings, player). Classes, tiers and batches as in [plan 0038](../0038-inferred-claims-sweep.md#classes).
- Guard rows marked (a-logs) with "0 → d-none" are re-read first: a guard the later logs never took is reclassified d-none by the batch, not raised.

| # | Spec section | Claim | Finding anchor | Class | Route | Tier | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | [Entry points](../../specs/hirelings/README.md#entry-points) | Trade at Asheara builds the table | NPC_OpenStore 0x00578B30 | a-run | H6f: `d2pilot.py npc asheara trade` before any hire interaction | T2 | H6f | 1 |
| 2 | [Entry points](../../specs/hirelings/README.md#entry-points) | Quest gift: free mercenary | HIRE_GiveFreeMerc 0x00579180 | b | new recipe: Act I Burial Grounds quest open, no mercenary; `hunt --mon-cls` Blood Raven, then Kashya | T2 | H6f | 1 |
| 3 | [Entry points](../../specs/hirelings/README.md#entry-points) | Saves older than version 92 | ReadMercOldSave 0x00533C70 | b | old-version save builder (versions 71, 87); save family | T3 | H1a | 1 |
| 4 | [Constants](../../specs/hirelings/README.md#constants) | Hire table 0x450 bytes, 69 entries | HIRE_BuildStock 0x00576070 | a-logs | the 53 logged tables of 69 entries; check the block size against the table pointer reads; addendum | T2 | S3a | 1 |
| 5 | [Constants](../../specs/hirelings/README.md#constants) | List entry level floor 2 | HIRELING_RollEntry 0x006637F0 | b | new recipe: a level 3–6 character opens a list | T2 | H6f | 1 |
| 6 | [Constants](../../specs/hirelings/README.md#constants) | Loaded mercenary level cap 99 | ExpMaxLevel 0x00611830 | b | `merc_saves.py` save with experience past level 99 | T3 | H6f | 1 |
| 7 | [A. Table lookups](../../specs/hirelings/README.md#a-table-lookups) | GetRecord: greatest Level ≤ L | HIRELING_GetRecord 0x006562F0 | c | data behaviour: every Id's rows in Level order in `hireling.txt`; the 72 SetLevel bands agree | T2 | S3b | 1 |
| 8 | [A. Table lookups](../../specs/hirelings/README.md#a-table-lookups) | Loader fills first-by-id and name ranges | HIRELING_LoadTable 0x00655720 | c | second path: HIRELING_GetRecord and HIRE_GetNameRange read the same fields; fatal branches d-edit | T2 | S3b | 1 |
| 9 | [C. When the table is built and rebuilt](../../specs/hirelings/README.md#c-when-the-table-is-built-and-rebuilt) | NPC_OpenStore also builds the table | NPC_OpenStore | a-run | H6f, as the Entry points row | T2 | H6f | 1 |
| 10 | [C. When the table is built and rebuilt](../../specs/hirelings/README.md#c-when-the-table-is-built-and-rebuilt) | Rebuild after a free mercenary | HIRE_GiveFreeMerc | b | as the free-mercenary row | T2 | H6f | 1 |
| 11 | [C. When the table is built and rebuilt](../../specs/hirelings/README.md#c-when-the-table-is-built-and-rebuilt) | Table shared by all players of a game | HIRE_SendList 0x00576770 | d (d-2c) | d-2c | T3 | - | 1 |
| 12 | [D. The stock build](../../specs/hirelings/README.md#d-the-stock-build-hire_buildstock) | Name range of size −1 is fatal | HIRE_GetNameRange 0x00575FF0 | d (d-edit) | d-edit | T3 | - | 1 |
| 13 | [D. The stock build](../../specs/hirelings/README.md#d-the-stock-build-hire_buildstock) | Build with a table present draws nothing | HIRE_BuildStock | d (d-none) | d-none: no path read reaches it | T3 | - | 1 |
| 14 | [E. An entry](../../specs/hirelings/README.md#e-an-entry-hireling_rollentry) | Floor of 2 not reached | HIRELING_RollEntry | b | as the Constants floor row | T2 | H6f | 1 |
| 15 | [E. An entry](../../specs/hirelings/README.md#e-an-entry-hireling_rollentry) | Level-up between list and hire changes the mercenary | HIRELING_RollEntry | b | pilot: open the list, gain a level, hire | T3 | H6f | 1 |
| 16 | [E. An entry](../../specs/hirelings/README.md#e-an-entry-hireling_rollentry) | Client list shows 1057 as 11021 | ClientHireListDraw 0x004B5C60 | b | logger line on the drawn string index; a table holding `Lharhad` | T3 | H6f | 1 |
| 17 | [F. The hire](../../specs/hirelings/README.md#f-the-hire-hire_hire-merc_init) | Qual-Kehk quest gate | HIRE_Hire 0x005770E0 | b | recipe with Act V quest 36 not done | T2 | H6f | 1 |
| 18 | [F. The hire](../../specs/hirelings/README.md#f-the-hire-hire_hire-merc_init) | Kashya level and quest gate | VENDOR_StockLevel 0x00576890 | b | recipe below level 8 with quest 2 open | T2 | H6f | 1 |
| 19 | [F. The hire](../../specs/hirelings/README.md#f-the-hire-hire_hire-merc_init) | Entry index nameIdx − first | 0x005771E8 | a-logs | the 49 hires: MERC_Init {name, seed} = the entry; addendum | T2 | S3a | 1 |
| 20 | [F. The hire](../../specs/hirelings/README.md#f-the-hire-hire_hire-merc_init) | Stash gold covers the rest; refusal when short | PayGold 0x00576D90 | b | recipe with little inventory gold and stash gold | T3 | H6f | 1 |
| 21 | [F. The hire](../../specs/hirelings/README.md#f-the-hire-hire_hire-merc_init) | Gates, refusal and gold check not exercised | HIRE_Hire | b | as the three rows above | T2 | H6f | 1 |
| 22 | [F. The hire](../../specs/hirelings/README.md#f-the-hire-hire_hire-merc_init) | Hire of an unlisted entry would pass | HIRE_Hire | d (d-none) | d-none: the client never sends one | T3 | - | 1 |
| 23 | [F. The hire](../../specs/hirelings/README.md#f-the-hire-hire_hire-merc_init) | Greiz hire; classic lists and hires | HIRE_BuildStock | a-run | H6f `tour --buy greiz:1` and `MercClassic`/VendorNova classic tours | T2 | H6f | 1 |
| 24 | [F. The hire](../../specs/hirelings/README.md#f-the-hire-hire_hire-merc_init) | Saved mercenary header written | D2S_WriteMercHeader 0x00568E60 | a-run | H1b: hire, *Save and Exit*, `d2s-io.gdb` write lines | T2 | H1b | 1 |
| 25 | [G. The stats per level](../../specs/hirelings/README.md#g-the-stats-per-level-merc_setlevel) | MERC_AddExp and the gain cap | MERC_AddExp 0x0057E860 | b | logger lines at MERC_AddExp/MERC_CapExpGain; mercenary kills (the `MercMF` route) | T2 | H6f | 1 |
| 26 | [H. The mercenary from a save](../../specs/hirelings/README.md#h-the-mercenary-from-a-save-d2s_readmercheader-merc_create) | Empty header: no mercenary | D2S_ReadMercHeader 0x0056AA50 | a-logs | assert the empty-header test on the 15 all-zero headers (review recount); checker extension | T2 | S3a | 1 |
| 27 | [H. The mercenary from a save](../../specs/hirelings/README.md#h-the-mercenary-from-a-save-d2s_readmercheader-merc_create) | Name past +0x116 reset | D2S_ReadMercHeader | b | `merc_saves.py` save with an out-of-range name | T3 | H6f | 1 |
| 28 | [H. The mercenary from a save](../../specs/hirelings/README.md#h-the-mercenary-from-a-save-d2s_readmercheader-merc_create) | Dead flag; dead mercenary marked (two lines) | PETS_OnDeath 0x005751A0 | b | `merc_saves.py` save with the dead bit | T2 | H6f | 2 |
| 29 | [H. The mercenary from a save](../../specs/hirelings/README.md#h-the-mercenary-from-a-save-d2s_readmercheader-merc_create) | Loaded mercenary marked hired in an existing table | MERC_Create 0x005774F0 | b | load, then open the seller's list in the same game | T3 | H6f | 1 |
| 30 | [H. The mercenary from a save](../../specs/hirelings/README.md#h-the-mercenary-from-a-save-d2s_readmercheader-merc_create) | id 0xFFFF picks the act's first row | MERC_Create | b | version-71 save; save family | T3 | H1a | 1 |
| 31 | [H. The mercenary from a save](../../specs/hirelings/README.md#h-the-mercenary-from-a-save-d2s_readmercheader-merc_create) | Name, dead mercenary not loaded (note) | D2S_ReadMercHeader | b | as the rows above | T2 | H6f | 1 |
| 32 | [H. The mercenary from a save](../../specs/hirelings/README.md#h-the-mercenary-from-a-save-d2s_readmercheader-merc_create) | Mercenary items read after the header | D2S_ReadMercItems 0x0056AC10 | a-run | H1a: load `MercMF` with `d2s-io.gdb` | T2 | H1a | 1 |
| 33 | [H. The mercenary from a save](../../specs/hirelings/README.md#h-the-mercenary-from-a-save-d2s_readmercheader-merc_create) | Old saves convert experience; v71 has no Id | MercExpFromOldSave 0x00533BF0 | b | old-version save builder; save family | T3 | H1a | 1 |
| 34 | [I. Monster class and the monster level](../../specs/hirelings/README.md#i-monster-class-and-the-monster-level) | Hirelings get no player-count bonus | 0x0057396C | a-run | H4b `/players 8` session with `MercNova` (as monsters/stats § C) | T2 | H4b | 1 |
| 35 | [K. Named only](../../specs/hirelings/README.md#k-named-only) | Free mercenary | HIRE_GiveFreeMerc | b | as the Entry points row | T2 | H6f | 1 |
| 36 | [K. Named only](../../specs/hirelings/README.md#k-named-only) | Resurrection and its price | MERC_Resurrect 0x00579C00 | b | dead-mercenary save, pilot action at the NPC's resurrect line | T2 | H6f | 1 |
| 37 | [K. Named only](../../specs/hirelings/README.md#k-named-only) | Death sets the dead bit | PETS_OnDeath | b | dead-mercenary run or the mercenary dying in play | T2 | H6f | 1 |
| 38 | [K. Named only](../../specs/hirelings/README.md#k-named-only) | Combat skill choice | MERCAI_PickSkill 0x005E4D30 | d (d-sim) | d-sim: AI, later ADR-0014 phase | T3 | - | 1 |

**Totals by class:** a-logs 3, a-run 6, b 23, c 2, d-2c 1, d-edit 1, d-none 2, d-sim 1 (sum 39).
