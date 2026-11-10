# Plan 0066 inventory: stats/aggregate

- **Spec:** [stats/aggregate](../../specs/stats/aggregate.md), read at `main` `b5999f5e`.
- **Front matter `I`:** 42; the *Count* column sums to 42.
- Classes, batches and conventions as in [the inventory README](README.md#conventions).

| # | Line | Section | Claim (excerpt) | Anchor | Class | Route or reason | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | 50 | Entry points | The maxima are read | `fn:sub_00625D10_UnitGetMaxHp@0x00625D10` | ? | ? | ? | 1 |
| 2 | 51 | Entry points | An item is equipped or unequipped | `fn:ITEMS_AttachToOwner@0x0055C2C0` | ? | ? | ? | 1 |
| 3 | 82 | Runtime state | parent list, linked unit — +, + | `struct:StatList+0x34` | ? | ? | ? | 1 |
| 4 | 90 | Constants: list flags |  — timed (an end frame at +) | `fn:STATE_ApplyTimed@0x0056E970` | ? | ? | ? | 1 |
| 5 | 91 | Constants: list flags |  — dropped on a mode change | `fn:sub_006272E0_StatListsDropOnMode@0x006272E0` | ? | ? | ? | 1 |
| 6 | 92 | Constants: list flags |  — the state's aura bit | `fn:STATE_ApplyTimed@0x0056E970` | ? | ? | ? | 1 |
| 7 | 93 | Constants: list flags |  — a curse | `fn:STATE_ApplyTimed@0x0056E970` | ? | ? | ? | 1 |
| 8 | 94 | Constants: list flags |  — an item's property list | `fn:STATLIST_Alloc@0x006251F0` | ? | ? | ? | 1 |
| 9 | 95 | Constants: list flags |  — the state's exp bit | `fn:STATE_ApplyTimed@0x0056E970` | ? | ? | ? | 1 |
| 10 | 122 | A. The list tree | A plain list holds the unit it is linked to (+), the type and guid … | – | ? | ? | ? | 1 |
| 11 | 128 | A. The list tree | Entries are {key, value}, key = stat << 16 / param, sorted ascending (binary search). … | – | ? | ? | ? | 1 |
| 12 | 133 | A. The list tree | An extended list's active array is its cache (+); a plain list's is its own … | – | ? | ? | ? | 1 |
| 13 | 163 | B. Link, unlink, toggle | sub_00627910_StatListLinkOwner(unit, item, withDamage): an item in locations 11 and 12 (item data | – | ? | ? | ? | 1 |
| 14 | 210 | C. Propagation and the cache | C5. Takes(list, s, k) by ISC[s].op (class table ): | `0x006267AD` | ? | ? | ? | 1 |
| 15 | 298 | D. The evaluation: op 1–13 | Ops 3, 6, 7, 10 and 12 were not reached: op 3 and op 10 … | – | ? | ? | ? | 1 |
| 16 | 301 | D. The evaluation: op 1–13 | b0 starts as the own-plus-children sum and only ops 1 and 13 on an item … | – | ? | ? | ? | 1 |
| 17 | 306 | D. The evaluation: op 1–13 | op 8/9 add only full − own of the source on the list being evaluated. … | – | ? | ? | ? | 1 |
| 18 | 310 | D. The evaluation: op 1–13 | ByTime(p) (op 6/7). The source is Encode 4: bits 0–1 a period q, bits 2–11 … | – | ? | ? | ? | 1 |
| 19 | 325 | E. The op graph the loader builds | The op stat cells are honoured as written, with no check against the row's name: … | – | ? | ? | ? | 1 |
| 20 | 338 | F. Reads | Both readers floor the value at MinAccr << ValShift when the stat has fMin and … | – | ? | ? | ? | 1 |
| 21 | 363 | G. The maxima, the rescale and the stat callback | , ) The getters' own bodies are read from the code. | tbl:CharStats.txt:LifePerVitality | ? | ? | ? | 1 |
| 22 | 369 | G. The maxima, the rescale and the stat callback | For a monster with a MonStats DamageRegen factor the callback also sets stat 74 from … | – | ? | ? | ? | 1 |
| 23 | 372 | G. The maxima, the rescale and the stat callback | The callback's other cases: it (re)registers a stat's item events (itemevent1/2) when the value goes … | – | ? | ? | ? | 1 |
| 24 | 377 | G. The maxima, the rescale and the stat callback | UNIT_ClampVitals (when ITEMS_DetachFromOwner is asked to clamp): stamina, mana and life, in that order, | – | ? | ? | ? | 1 |
| 25 | 383 | H. Items: equip, requirements, the refresh, broken, per-leve | H1. ITEMS_AttachToOwner(owner, item): | `fn:ITEMS_AttachToOwner@0x0055C2C0` | ? | ? | ? | 1 |
| 26 | 389 | H. Items: equip, requirements, the refresh, broken, per-leve | H2. ITEMS_DetachFromOwner(owner, force, clamp): | `fn:ITEMS_DetachFromOwner@0x0055C730` | ? | ? | ? | 1 |
| 27 | 414 | H. Items: equip, requirements, the refresh, broken, per-leve | The item_req_percent term changed no outcome in its 814 checks (a reading without it predicts … | – | ? | ? | ? | 1 |
| 28 | 421 | H. Items: equip, requirements, the refresh, broken, per-leve | Step (2) runs once, so an unlink that breaks another item's requirement (strength from another … | – | ? | ? | ? | 1 |
| 29 | 425 | H. Items: equip, requirements, the refresh, broken, per-leve | The refresh also runs every 136 frames with no player action: the commonest gap between … | – | ? | ? | ? | 1 |
| 30 | 428 | H. Items: equip, requirements, the refresh, broken, per-leve | Broken. sub_0055F850_ItemBreak sets , unlinks an equipped item, sets durability (72) to 0 and | – | ? | ? | ? | 1 |
| 31 | 431 | H. Items: equip, requirements, the refresh, broken, per-leve | Ethereal and sockets change only the item's own lists (items/properties § F), | – | ? | ? | ? | 1 |
| 32 | 438 | H. Items: equip, requirements, the refresh, broken, per-leve | So the item's value catches up at its next link: for a set item at … | – | ? | ? | ? | 1 |
| 33 | 446 | I. Dual wield and the weapon switch | UNIT_CanDualWield answers yes for player classes 4 and 6 (Barbarian, Assassin) and monster classes 417 | – | ? | ? | ? | 1 |
| 34 | 448 | I. Dual wield and the weapon switch | The weapon switch (sub_005616A0_PlayerSwapWeapons, from sub_0054CE70_SwapWeaponsReq) detaches both | – | ? | ? | ? | 1 |
| 35 | 509 | J. Set bonuses | A set whose last member is broken (flag ) was not reached, so its full … | – | ? | ? | ? | 1 |
| 36 | 511 | J. Set bonuses | The aprop lists are the item's own lists of states 165..169 (flags , made at … | – | ? | ? | ? | 1 |
| 37 | 516 | J. Set bonuses | Stat 71 sums. The marker stat 71 (value) is an ordinary entry, so the wearer's … | – | ? | ? | ? | 1 |
| 38 | 520 | J. Set bonuses | A Sets param naming a skill, a montype or a state is compiled to the … | – | ? | ? | ? | 1 |
| 39 | 532 | K. Passive stat lists | The list is rebuilt only when 351 differs from the skill's current level (with bonuses), … | – | ? | ? | ? | 1 |
| 40 | 536 | K. Passive stat lists | The masteries 127–129 carry the aura bit with no aurastate; no code read gives the … | – | ? | ? | ? | 1 |
| 41 | 544 | Draw order | The requirement refresh, the set activation and the passive refresh run inside those events; no … | – | ? | ? | ? | 1 |
| 42 | 593 | Reimplementation notes | … refresh in step (2); the refresh runs every 136 frames on its own as well. | – | ? | ? | ? | 1 |
