# Plan 0066 inventory: stats/aggregate

- **Spec:** [stats/aggregate](../../specs/stats/aggregate.md), read at `main` `b5999f5e`.
- **Front matter `I`:** 42; the *Count* column sums to 42.
- Classes, batches and conventions as in [the inventory README](README.md#conventions).

| # | Line | Section | Claim (excerpt) | Anchor | Class | Route or reason | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | 50 | Entry points | The maxima are read | `fn:sub_00625D10_UnitGetMaxHp@0x00625D10` | c-emu | `UnitGetMaxHp`, `UNIT_GetMaxMana`, `UNIT_GetMaxStamina` emulated (list and CharStats declared) | S4e | 1 |
| 2 | 51 | Entry points | An item is equipped or unequipped | `fn:ITEMS_AttachToOwner@0x0055C2C0` | a-logs | as stats/README row 1: LNK/ULK caller chains from the attach and detach in the s1017 logs | S4d | 1 |
| 3 | 82 | Runtime state | parent list, linked unit — +, + | `struct:StatList+0x34` | a-logs | the TREE dumps of run:2026-10-17-stats: every list's parent and linked unit against the tree the logger walks | S4d | 1 |
| 4 | 90 | Constants: list flags |  — timed (an end frame at +) | `fn:STATE_ApplyTimed@0x0056E970` | a-logs | TREE and STA1 list flags of the s1017 and shortfalls logs: 0x2 on every list with an end frame | S4d | 1 |
| 5 | 91 | Constants: list flags |  — dropped on a mode change | `fn:sub_006272E0_StatListsDropOnMode@0x006272E0` | c | writer and reader pair of flag 0x4 read with a second tool (`StatListsDropOnMode` and the flag's setters) | S4d | 1 |
| 6 | 92 | Constants: list flags |  — the state's aura bit | `fn:STATE_ApplyTimed@0x0056E970` | a-logs | STA1 list flags against the States `aura` bit over the kept aura applies | S4d | 1 |
| 7 | 93 | Constants: list flags |  — a curse | `fn:STATE_ApplyTimed@0x0056E970` | a-run | `stats.gdb` rev 9 with `STATS_MONSTA`, a Necromancer cursing monsters: flag 0x20 on the curse lists | H4e | 1 |
| 8 | 94 | Constants: list flags |  — an item's property list | `fn:STATLIST_Alloc@0x006251F0` | a-logs | TREE dumps: item property lists carry 0x40 (the `ow` owner an item) | S4d | 1 |
| 9 | 95 | Constants: list flags |  — the state's exp bit | `fn:STATE_ApplyTimed@0x0056E970` | a-logs | STA1 list flags against the States `exp` column over the kept applies (a-run if no logged state has it) | S4d | 1 |
| 10 | 122 | A. The list tree | A plain list holds the unit it is linked to (+), the type and guid … | – | a-logs | TREE dumps of run:2026-10-17-stats: the plain-list fields the logger reads | S4d | 1 |
| 11 | 128 | A. The list tree | Entries are {key, value}, key = stat << 16 / param, sorted ascending (binary search). … | – | a-logs | PRP, CA and CW lines of the s1017 logs: add and set semantics and removal at 0, already modelled (a key-order control) | S4d | 1 |
| 12 | 133 | A. The list tree | An extended list's active array is its cache (+); a plain list's is its own … | – | a-logs | the RD reads of the s1017 logs against the extended cache and the plain own entries | S4d | 1 |
| 13 | 163 | B. Link, unlink, toggle | sub_00627910_StatListLinkOwner(unit, item, withDamage): an item in locations 11 and 12 (item data | – | a-logs | LNK and DMG lines of the weapon-switch sessions (StatsBar, StatsBarC): locations 11 and 12, damage toggles | S4d | 1 |
| 14 | 210 | C. Propagation and the cache | C5. Takes(list, s, k) by ISC[s].op (class table ): | `0x006267AD` | c-emu | the take test at 0x006267AD emulated over ops and owner types (extends `sweep_p51s.py`'s `op67` family) | S4e | 1 |
| 15 | 298 | D. The evaluation: op 1–13 | Ops 3, 6, 7, 10 and 12 were not reached: op 3 and op 10 … | – | c-emu | `StatEvaluate` cases 3, 10 and 12 emulated (ops 6 and 7 done by run:2026-10-27-p51s-emu) | S4e | 1 |
| 16 | 301 | D. The evaluation: op 1–13 | b0 starts as the own-plus-children sum and only ops 1 and 13 on an item … | – | a-logs | the 92 op-11 and op-7 writes of the s1017 logs with a control that uses the running total | S4d | 1 |
| 17 | 306 | D. The evaluation: op 1–13 | op 8/9 add only full − own of the source on the list being evaluated. … | – | a-logs | the op-8 and op-9 writes (919, 3 784) with a control that adds the full value | S4d | 1 |
| 18 | 310 | D. The evaluation: op 1–13 | ByTime(p) (op 6/7). The source is Encode 4: bits 0–1 a period q, bits 2–11 … | – | c-emu | `bytime` of run:2026-10-27-p51s-emu covers the formula; extend to `ActTimeOfDay` for the phase | S4e | 1 |
| 19 | 325 | E. The op graph the loader builds | The op stat cells are honoured as written, with no check against the row's name: … | – | a-logs | the ISC lines (loaded `opIn`) of the kept logs against ItemStatCost `op stat` cells, every row (rule 2) | S4d | 1 |
| 20 | 338 | F. Reads | Both readers floor the value at MinAccr << ValShift when the stat has fMin and … | – | c-emu | `StatListGetValue` emulated with values under the floor (fMin, MinAccr, ValShift) | S4e | 1 |
| 21 | 363 | G. The maxima, the rescale and the stat callback | , ) The getters' own bodies are read from the code. | tbl:CharStats.txt:LifePerVitality | c-emu | as row 1 | S4e | 1 |
| 22 | 369 | G. The maxima, the rescale and the stat callback | For a monster with a MonStats DamageRegen factor the callback also sets stat 74 from … | – | b | a monster-side SCB line for a MonStats `DamageRegen` monster (the logger's SCB is player-only) | H4e | 1 |
| 23 | 372 | G. The maxima, the rescale and the stat callback | The callback's other cases: it (re)registers a stat's item events (itemevent1/2) when the value goes … | – | a-logs | SCB lines for keys 83, 97, 107, 126, 127, 188, 204, 151, 98 and the PAS, AU, TGL lines after them in the s1017 logs | S4d | 1 |
| 24 | 377 | G. The maxima, the rescale and the stat callback | UNIT_ClampVitals (when ITEMS_DetachFromOwner is asked to clamp): stamina, mana and life, in that order, | – | a-logs | the vitals' CW writes after a clamping detach in the s1017 logs against the new maxima | S4d | 1 |
| 25 | 383 | H. Items: equip, requirements, the refresh, broken, per-leve | H1. ITEMS_AttachToOwner(owner, item): | `fn:ITEMS_AttachToOwner@0x0055C2C0` | a-logs | UOE, DMG and LNK lines with caller chains of the s1017 logs (the playerbody refusal not met) | S4d | 1 |
| 26 | 389 | H. Items: equip, requirements, the refresh, broken, per-leve | H2. ITEMS_DetachFromOwner(owner, force, clamp): | `fn:ITEMS_DetachFromOwner@0x0055C730` | a-logs | as row 25 for the detach | S4d | 1 |
| 27 | 414 | H. Items: equip, requirements, the refresh, broken, per-leve | The item_req_percent term changed no outcome in its 814 checks (a reading without it predicts … | – | a-run | `stats.gdb` RQ lines on new saves (`d2s.py build`): another class's items, too-high level, `item_req_percent` items | H4e | 1 |
| 28 | 421 | H. Items: equip, requirements, the refresh, broken, per-leve | Step (2) runs once, so an unlink that breaks another item's requirement (strength from another … | – | a-run | `stats.gdb` EQR lines around identify, repair and break events (new saves; Cain or a scroll, Larzuk) | H4e | 1 |
| 29 | 425 | H. Items: equip, requirements, the refresh, broken, per-leve | The refresh also runs every 136 frames with no player action: the commonest gap between … | – | a-logs | all EQR frames of the s1017 logs: the gaps without a player action are 136 (the queue's writer stays a reading) | S4d | 1 |
| 30 | 428 | H. Items: equip, requirements, the refresh, broken, per-leve | Broken. sub_0055F850_ItemBreak sets , unlinks an equipped item, sets durability (72) to 0 and | – | a-run | `stats.gdb` with a tool-built broken set item (`broken` key of `d2s.py build`), equipped then repaired | H4e | 1 |
| 31 | 431 | H. Items: equip, requirements, the refresh, broken, per-leve | Ethereal and sockets change only the item's own lists (items/properties § F), | – | a-logs | TREE dumps of the ethereal War Boots and the socketed items in the s1017 logs | S4d | 1 |
| 32 | 438 | H. Items: equip, requirements, the refresh, broken, per-leve | So the item's value catches up at its next link: for a set item at … | – | a-logs | TREE sequences of the s1017 logs: a worn item's own change reaching the wearer at its next link | S4d | 1 |
| 33 | 446 | I. Dual wield and the weapon switch | UNIT_CanDualWield answers yes for player classes 4 and 6 (Barbarian, Assassin) and monster classes 417 | – | a-run | `stats.gdb` with an Assassin holding two claws (new save) | H4e | 1 |
| 34 | 448 | I. Dual wield and the weapon switch | The weapon switch (sub_005616A0_PlayerSwapWeapons, from sub_0054CE70_SwapWeaponsReq) detaches both | – | c | `PlayerSwapWeapons` read with a second tool against the logged caller chains | S4d | 1 |
| 35 | 509 | J. Set bonuses | A set whose last member is broken (flag ) was not reached, so its full … | – | a-run | as row 30, the set's last member broken | H4e | 1 |
| 36 | 511 | J. Set bonuses | The aprop lists are the item's own lists of states 165..169 (flags , made at … | – | a-logs | the 19 525 aprop toggles by add func of the s1017 logs, with a control swapping funcs 1 and 2 | S4d | 1 |
| 37 | 516 | J. Set bonuses | Stat 71 sums. The marker stat 71 (value) is an ordinary entry, so the wearer's … | – | a-logs | TREE caches of StatsBar (two sets worn): the wearer's stat 71 is the sum of the set ids | S4d | 1 |
| 38 | 520 | J. Set bonuses | A Sets param naming a skill, a montype or a state is compiled to the … | – | c | full-table check of every Sets param name against the skills, montype and states tables (rule 2) | S4d | 1 |
| 39 | 532 | K. Passive stat lists | The list is rebuilt only when 351 differs from the skill's current level (with bonuses), … | – | a-logs | PAS/PAX lines and stat 351 of the s1017 logs: rebuilds only when 351 differs | S4d | 1 |
| 40 | 536 | K. Passive stat lists | The masteries 127–129 carry the aura bit with no aurastate; no code read gives the … | – | c | an exhaustive read scan with a second tool of the skills' `aura` bit readers | S4d | 1 |
| 41 | 544 | Draw order | The requirement refresh, the set activation and the passive refresh run inside those events; no … | – | a-logs | the seed pairs of EQR, SBA and PAS lines in the s1017 logs (draw-freedom tallies by kind) | S4d | 1 |
| 42 | 593 | Reimplementation notes | … refresh in step (2); the refresh runs every 136 frames on its own as well. | – | a-logs | as row 29 | S4d | 1 |

**Totals by class:** a-logs 25, a-run 6, b 1, c 4, c-emu 6 (sum 42).
