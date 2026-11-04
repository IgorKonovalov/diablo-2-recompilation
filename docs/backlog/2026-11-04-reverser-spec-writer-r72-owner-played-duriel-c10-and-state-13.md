---
from: reverser
to: spec-writer
date: 2026-11-04
status: open
context:
  - ../findings/ai/0020-owner-played-duriel-countess.md
  - ../findings/ai/experiments.md
  - ../specs/monsters/ai/README.md
  - ../specs/monsters/ai/catalogue.md
resolution: ""
---

[2026-11-04] from reverser (`lane/r72`) → spec-writer: carry [ai/0020](../findings/ai/0020-owner-played-duriel-countess.md) into monsters/ai, after its review. Not blocking. Tags and sentences as below; a review change to the finding wins. Numbers are from `workspace/logs/ai/r72/`. Anchors as written.

**One call is the review's and shapes two items below:** whether state 13's census with three given words counts as the promotion rule (ai/0020 § 2.4). The S13d sentence below does not depend on it; the H1 table takes row 44 only unless the review rules otherwise.

## README, Open questions

Replace the `[L]` **State 13** bullet with:

> - [I] **States 2, 3, 8, 9, 14 and 17.** They stay E7's reading and are not called dead. The owner-played window holds states 0 and 13 only (626 AID and 769 AIN lines, Normal), and states 10, 11, 12 and 13 have not been live in one window. (run:2026-11-04-r72, ai/0020 (link it from the spec))
> - [L] **State 13's setter, observed.** 0x005A4C1A at spawn is a reading: every owner log attached after she was created. A read-only break at 0x005B0E00, attached before her level is entered, would give it. (fn:sub_005B0E00_MonAiInit@0x005B0E00)

Replace the `[L]` **P1b-1, Duriel** bullet, the `[C]` **The code's side of C10** and the `[I]` **Its frequencies** with:

> - [C] **C10, settled for record 211, Normal.** Of 308 logged melee decisions, Smite 102, Jab 116, A1 90; exact 95 % intervals 27.9–38.7, 32.2–43.3, 24.2–34.6 %, excluding src:arreat-summit-boss-pages's 50 and 17. Each decision's arm and seed follow from its logged seed by the three draws, 308 of 308; other ways of making the choice fail 90 to 234. (run:2026-11-04-r72, fn:sub_005F67B0_AiDuriel@0x005F67B0, ai/0020 (link it from the spec))
> - [I] **Its frequencies** are arithmetic on that map with `aip2..4` 33, 50, 0: Smite 33 %, Jab 33.5 %, A1 33.5 %; the counts agree and do not prove them. (fn:sub_005F67B0_AiDuriel@0x005F67B0)
> - [L] **C11, Über Duriel:** the page's same 17/33/50. Same think and `aip` values as data, no decision of record 708 logged; open with the Uber cases. (fn:sub_005F67B0_AiDuriel@0x005F67B0, ai/0014 (link it from the spec))

## README, H1's table

Add, and extend the sentence's anchors with run:2026-11-04-r72 (the row is not a tier AI; say so if the column's heading needs it):

> | 44 | Duriel | 309 | 310 | 3 of 3 | rev 6, owner-played | Normal, record 211; 1 decision not melee |

## Catalogue R44

- R44a: leave `[I]`; replace "a community disagreement that is under Open questions" with "against the community page's 33 : 50 : 17, settled in the README's Open questions".
- R44b: delete "as do the walks after `Ovr`" only if the review accepts one logged case; otherwise leave it. Keep the rest.
- Replace R44l with:

> - R44l. [C] Logged: 309 decisions, 308 melee, Normal, record 211, owner-played; H1's sentence holds for them. The three draws of steps 3 to 5 follow from the logged seed in all 308, and the third draw is told only by the seed (90 decisions), since `aip4` is 0. (run:2026-11-04-r72, 0x005F6861, 0x005F68D4, 0x005F693F)
> - R44m. [I] Not reached: step 1's grant (`UNIT_GetRightSkill` non-zero in all 309), A2 and `Charge`'s true sides. Step 2's walk is one decision. Smite and Jab both command mode 14, so a command's mode does not tell them. Nightmare, Hell and record 708 are not logged; a seed is not chained between decisions (1 pair). (0x005F67E3, 0x005F69B2, run:2026-11-04-r72)

- In the catalogue's Open questions, replace **Row 44, Duriel: a community disagreement, open** with the C11 sentence above, and in the `src:arreat-summit-boss-pages` list add to C10 "settled, run:2026-11-04-r72".

## Catalogue S13

- Add to the block's `RunHome` line: "; a refused run does not return: the next step runs" `[I]` (0x005E5E06, 0x005E5F0C, 0x005E5F65).
- S13a: keep `[I]` for the block's unreached arms and drop the sentence "`CountessFirewall` runs along her preset's DS1 path, once per point, again after 700 frames.", which moves to S13e.
- Replace S13c with:

> - S13c. [C] State 13 is held by one class 45 unit per process, the only one with a home record; 7 others of the class in those processes hold state 0, and no unit in the logs holds two states. So no 0 → 13 is logged. (run:2026-11-04-r72, 0x005B186F)
> - S13d. [C] The block on the arms the logs reach: 160 decisions, 0 mismatches, every boundary call, the seed at each and at the exit, `v14`, `v18`, also across 158 consecutive pairs. Fire 21, reset 5, melee A1 97, melee idle 8, far run 28, far idle 5, step 4's RunHome 1. Normal, the player as target. (run:2026-11-04-r72, fn:sub_005E5C50_AiSt13@0x005E5C50, fn:sub_005E5B70_AiPathSkillStep@0x005E5B70)
> - S13e. [C] `CountessFirewall` fires at the four points of `cryptcountess1.ds1`'s one path, in file order, at offset (12500, 11000), one per decision, and starts again once 704 to 730 frames have passed since the last; none restarted at a gap up to 699. (run:2026-11-04-r72, 0x005E5C02, 0x005E5C2F)
> - S13f. [I] Read, not reached: steps 1, 2's push and refill, 3, 4 at home, 5 (home distances reach 29, so 30 to 40 is not separated), every refused RunHome, `AiPathSkillStep`'s early returns, the mode as the pushed 4 (class 45's `Sk1mode` is also 4), the threshold's exact 700 and `>`, and Nightmare and Hell. The setter too: first logged decisions already have `v14` 3 and 4. (0x005E5F22, 0x005E5E8E, 0x005A4C1A)

The stock census has 1 of 160 fork-free, so S13 stays out of H1's table unless the review rules on § 2.4.

## Catalogue R10

- R10b: keep.
- Replace R10l with:

> - R10l. [I] Logged: 209 decisions of class 45, 160 of them state 13 (S13) and 49 this think. The block gives the 49 with 0 mismatches: melee A1 14, near idle 7, near run 11, near walk 17; one control fails 28. 0 are fork-free, as `MonPlayerBonus`'s block is unknown to the model, and the far run and melee idle are not reached, so the block stays a reading. (run:2026-11-04-r72, 0x005F0B47)

## Elsewhere

The catalogue's census of `l` lines and its totals in *How to read an entry* move with R44l and R10l; the map row and [wiki/monster-ai](../wiki/monster-ai.md)'s Duriel and state 13 statements move with these. Symbols `AiDuriel`, `AiSt13`, `AiPathSkillStep` and `AiCorruptRogue` are `C` for their role, not their blocks.
