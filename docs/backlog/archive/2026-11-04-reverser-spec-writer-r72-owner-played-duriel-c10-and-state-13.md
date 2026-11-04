---
from: reverser
to: spec-writer
date: 2026-11-04
status: done
context:
  - ../../findings/ai/0020-owner-played-duriel-countess.md
  - ../../findings/ai/experiments.md
  - ../../specs/monsters/ai/README.md
  - ../../specs/monsters/ai/catalogue.md
  - ../../wiki/monster-ai.md
resolution: "Carried into monsters/ai by lane/s72: H1's rows and H1b, the Open questions, catalogue R44, S13 and R10, the census, the wiki and the map row [monsters/ai](../../specs/monsters/ai/README.md#open-questions), [catalogue](../../specs/monsters/ai/catalogue.md#how-to-read-an-entry). C11 and the state 13 setter stay open."
---

[2026-11-04] from reverser (`lane/r72`), rewritten at the lane's review (architect) → spec-writer: carry [ai/0020](../../findings/ai/0020-owner-played-duriel-countess.md) into monsters/ai. Not blocking. The review's rulings are already applied below: nothing here waits on a further ruling, and every sentence is meant to go in as written, with "(link it from the spec)" turned into the link. Numbers are from `workspace/logs/ai/r72/` and `r72/review/`.

## README § H

Rename the table's `Tier AI` heading to `Think`. After the table's last row add:

> | 44 | Duriel | 309 | 310 | 3 of 3 | rev 6, owner-played | Normal, record 211; 1 decision not melee, the one case on that side of 0x005F6814 |
> | 10, state 13 | `AiSt13` | 160 | 988 | 7 of 7 | rev 6, owner-played | H1b's three given words; Normal, the player as target, one preset file |

Add run:2026-11-04-r72 to H1's anchors. In H1's sentence, change nothing. After the table, before H2, add:

> - H1b. [C] **State 13's row, three given words.** For that row alone the "logged inputs" include three words the stock model does not load: the list's count at `AiCtl+0x38`, 4, the points of LvlPrest `Def` 159's `File1` path; DataTables `+0xA78`, the logged `ms` minus class × 0x1A8, which is the logger's own read of that word; DataTables `+0xBA0`, 357, the records of skills.bin. They are not unknown: the model does not fork on them, and wrong ones fail, a count of 3 in 6 decisions, a count of 5 in 138, a Skills count of 321 or below in 21. A Skills count above 321 cannot fail, so only that bound is tested. The list's points stay unknown in this census; S13e compares them with the file. Without the words the census has 1 of 160 with no fork. (run:2026-11-04-r72, 0x005E5B93, 0x005E5BC8, 0x005E5BE0)

## README, Open questions

Replace the `[L]` **State 13** bullet with:

> - [I] **States 2, 3, 8, 9, 14 and 17.** They stay E7's reading and are not called dead. The owner-played window holds states 0 and 13 only (626 AID and 769 AIN lines, Normal), and states 10, 11, 12 and 13 have not been live in one window. (run:2026-11-04-r72, ai/0020 (link it from the spec))
> - [L] **State 13's setter, observed.** 0x005A4C1A at spawn is a reading: every owner log attached after she was created. A read-only break at 0x005B0E00, attached before her level is entered, would give it. (fn:sub_005B0E00_MonAiInit@0x005B0E00)
> - [L] **State 13 on her preset's `File2`:** what picks the file, and her fires under it, are not logged. (0x005E5C02, tbl:LvlPrest.txt:File2)

Replace the `[L]` **P1b-1, Duriel** bullet, the `[C]` **The code's side of C10** and the `[I]` **Its frequencies** with:

> - [C] **C10, settled for record 211, Normal.** Of 308 logged melee decisions, Smite 102, Jab 116, A1 90; exact 95 % intervals 27.9–38.7, 32.2–43.3, 24.2–34.6 %, excluding src:arreat-summit-boss-pages's 50 and 17. The 9 with the mercenary as target are counted, as the think only pushes its target; the player alone gives 99, 111, 89 of 299 and excludes them too. Each decision's arm and number of steps follow from its logged seed by the three draws, 308 of 308; six other readings fail 90 to 234. (run:2026-11-04-r72, fn:sub_005F67B0_AiDuriel@0x005F67B0, ai/0020 (link it from the spec))
> - [C] **The code's side, emulated:** `draw < aip2` Skill3, then a fresh `draw < aip3` Skill2, then a fresh `draw < aip4` A2, else A1, to the first callee. (run:2026-10-30-ai-cat-emu-6, fn:sub_005F67B0_AiDuriel@0x005F67B0)
> - [I] **Its frequencies** are arithmetic on that map with `aip2..4` 33, 50, 0: Smite 33 %, Jab 33.5 %, A1 33.5 %; the counts agree and do not prove them. (fn:sub_005F67B0_AiDuriel@0x005F67B0)
> - [L] **C11, Über Duriel:** the page's same 17/33/50. Same think and `aip` values as data, no decision of record 708 logged; open with the Uber cases. (fn:sub_005F67B0_AiDuriel@0x005F67B0, ai/0014 (link it from the spec))

## Catalogue, How to read an entry

In the `l` line's bullet, after "run:2026-11-04-ai-r5," add "and, for rows 10 and 44, run:2026-11-04-r72,".

In the `r` line's bullet, replace "**No entry outside machinery's table is under sentence H1**: nothing past the first boundary of any row here is `[C]`." with:

> **Only R44 and S13 of the entries here are under sentence H1**, on their `r` lines and those of their lines that say so; past the first boundary nothing else here is `[C]`.

Keep "No row's role, symbol or reading is raised by being resumed." In the same bullet's anchors add run:2026-11-04-r72.

In the census bullet: 28 becomes 29, 15 becomes 16, 87 becomes 85; "38 entries have an `r` line" becomes 41, and "4 of them state rows (10, 11, 12, 17)" becomes "5 of them state rows (10, 11, 12, 13, 17)". The new lines below keep the three `grep -cE` patterns true; check them with the greps after the edit.

## Catalogue R44

- R44a: leave `[I]`; replace "a community disagreement that is under Open questions" with "against the community page's 33 : 50 : 17, settled in the README's Open questions".
- R44b: leave as it is. It states the emulation; the one logged walk is in R44n.
- Replace R44l with:

> - R44l. [C] First boundary: 309 decisions compared (309), 0 mismatches, 1 first-call outcome. (run:2026-11-04-r72, 0x005B186F)
> - R44r. [C] Under sentence H1: 309 decisions, 310 calls past the first, 3 of 3 two-way sites failing alone; Normal, record 211, owner-played. (run:2026-11-04-r72, 0x005B186F)
> - R44m. [C] The three draws of steps 3 to 5 give the arm and the number of steps from the logged seed in all 308 melee decisions; the third draw is told only by the seed (90 decisions), since `aip4` is 0. The next decision's seed is 0 to 11 steps past the last exit seed in all 307 pairs; those steps are not attributed. (run:2026-11-04-r72, 0x005F6861, 0x005F68D4, 0x005F693F)
> - R44n. [I] Not reached: step 1's grant (`UNIT_GetRightSkill` non-zero in all 309), A2 and `Charge`'s true sides. Step 2's walk is one decision. Smite and Jab both command mode 14, so a command's mode does not tell them; the skill word does. Nightmare, Hell and record 708 are not logged. (0x005F67E3, 0x005F69B2, run:2026-11-04-r72)

- In the catalogue's Open questions, replace **Row 44, Duriel: a community disagreement, open** with the C11 sentence above, and in the `src:arreat-summit-boss-pages` list add to C10 "settled, run:2026-11-04-r72".

## Catalogue S13

- Add to the block's `RunHome` line: "; a refused run does not return: the next step runs" `[I]` (0x005E5E06, 0x005E5F0C, 0x005E5F65).
- S13a: keep `[I]` for the block's unreached arms and drop the sentence "`CountessFirewall` runs along her preset's DS1 path, once per point, again after 700 frames.", which moves to S13e.
- Replace S13c with:

> - S13c. [C] State 13 is held by one class 45 unit per process, in two processes of one seed, the only one of its class with a home record; 7 others of the class in those processes hold state 0, and no unit in the five logs holds two states. So no 0 → 13 is logged; how she came to hold it lies before each attach. (run:2026-11-04-r72, 0x005B186F)
> - S13r. [C] Under sentence H1 with H1b's three given words: 160 decisions, 988 calls past the first, 7 of 7 two-way sites failing alone; Normal, owner-played. The stock census has 1 of 160. (run:2026-11-04-r72, 0x005E5B93)
> - S13d. [C] The block on the arms the logs reach: 160 decisions, 0 mismatches, every boundary call, the seed at each and at the exit, `v14`, `v18`, also across 158 consecutive pairs. Fire 21, reset 5, melee A1 97, melee idle 8, far run 28, far idle 5, step 4's RunHome 1. Normal, the player as target. (run:2026-11-04-r72, fn:sub_005E5C50_AiSt13@0x005E5C50, fn:sub_005E5B70_AiPathSkillStep@0x005E5B70)
> - S13e. [C] `CountessFirewall` fires at the four points of `cryptcountess1.ds1`'s one path, in file order, one per decision, at the offset (12500, 11000), which equals Levels id 25's `OffsetX`, `OffsetY` times 5. The path's anchor in that file is MonPreset's act 1 row 40, The Countess. It is `File1` of her preset's two, one seed; `File2`'s path matches none of the four. It starts again at a decision whose gap since the last fire is over the limit: restarts are logged at gaps 704 to 730 and none at gaps up to 699. (run:2026-11-04-r72, 0x005E5C02, 0x005E5C2F, tbl:Levels.txt:OffsetX, tbl:LvlPrest.txt:File1, tbl:MonPreset.txt:Place)
> - S13f. [I] Read, not reached: steps 1, 2's push and refill, 3, 4 at home, 5 (home distances reach 29, so 30 to 40 is not separated), every refused RunHome, `AiPathSkillStep`'s early returns and its `neg` for a `T` below `v18`, the mode as the pushed 4 (class 45's `Sk1mode` is also 4), the limit's exact 700 and `>`, and Nightmare and Hell. The setter too: first logged decisions already have `v14` 3 and 4. (0x005E5F22, 0x005E5E8E, 0x005E5C27, 0x005A4C1A)

## Catalogue R10

- R10b: keep.
- Replace R10l with:

> - R10l. [I] Logged, not compared by `tools/ai.py`: 209 decisions (209) of class 45, in a row with no model there, so the first boundary of this row is not raised. 160 are state 13 (S13). (run:2026-11-04-r72, 0x005B186F)
> - R10r. [I] This think's 49, by the block in `tools/ai_s13_check.py --r10`: 0 mismatches, melee A1 14, near idle 7, near run 11, near walk 17; one control fails 28. 0 have no fork, as `MonPlayerBonus`'s block is unknown to the model, and the far run and melee idle are not reached, so the block stays a reading. Not under sentence H1. (run:2026-11-04-r72, 0x005F0B47)

## Wiki and the map

In [wiki/monster-ai](../../wiki/monster-ai.md), in the sentence before the list, change "state 13, Duriel's melee and the Uber forced cases need one played by hand" to "the Uber forced cases need one played by hand"; move its `based_on` date. Replace the two bullets with:

> - **State 13, The Countess's state.** Played by hand: 160 of her decisions follow the catalogue's block on the branches reached, and her Firewall goes through the four points of her preset's path, in the first of its two files. What sets the state was not seen, since the logger attached after she was created. States 2, 3, 8, 9, 14 and 17 are not called dead.
> - **Duriel in melee range.** Played by hand, Normal: 308 decisions, Smite 102, Jab 116, first attack 90, each one's choice following from three fresh draws. The frequencies stay arithmetic on that, **Smite 33 %, Jab 33.5 %, first attack 33.5 %**, and a community page's **17 % first attack, 50 % Jab** fall outside what was measured. Über Duriel, the same think and the same slots, is not played.

Update the map row's counts and date in [the research map](../../specs/README.md) as the gate asks.

Symbols `AiDuriel`, `AiSt13`, `AiPathSkillStep` and `AiCorruptRogue` are `C` for their role, each on the second source ai/0020's Functions table names, not for their blocks and not by the resumed rows.
