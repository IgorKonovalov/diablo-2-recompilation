# 0020 — Owner-played Duriel and The Countess: C10's melee choice, state 13's first logged decisions, what a late attach cannot test

> **Subsystem:** monsters/ai
> **Question:** does Duriel's melee choice follow three fresh draws (33 : 33.5 : 33.5) or the community page's 33 : 50 : 17, and does row 44 meet the promotion rule; when does a unit hold state 13, and does S13's block give its 160 logged decisions; what can logs attached late not test?
> **Date:** 2026-11-04   **Plan:** [0052](../../plans/done/0052-monster-ai.md) (closed; owner-played cases P1b-1 and the Countess)   **Status:** answered, for review (`lane/r72`)

Record: [run:2026-11-04-r72](experiments.md#run2026-11-04-r72), owner-played. Kept outputs under `workspace/logs/ai/r72/`, manifest `workspace/logs/ai/manifest-r72.sha256` (22 lines, passes from `workspace/logs/ai`). Tools: `tools/ai_duriel_c10.py`, `tools/ai_s13_check.py`, `tools/ai_s13_census.py`, `tools/ai_owner_fields.py` at `a2a78e7c`; `tools/ai.py`, `tools/ai_resume.py`, `tools/ai_resume_flip.py` unchanged. No game was run by this lane.

## Answer (summary)

- [C] **C10, the tally.** Duriel, Normal, 308 melee decisions in two processes (9 against the mercenary, 299 against the player): Smite 102, Jab 116, plain attack (A1) 90. Exact 95 % intervals: Smite 27.9–38.7 %, Jab 32.2–43.3 %, A1 24.2–34.6 %. The page's 50 and 17 fall outside theirs (exact tests p = 1.76 × 10⁻⁵ and 1.17 × 10⁻⁷; exact multinomial p = 7.1 × 10⁻⁸); the code's 33 : 33.5 : 33.5 falls inside all three (multinomial p = 0.193). A2 and any other first command: 0. (run:2026-11-04-r72, fn:sub_005F67B0_AiDuriel@0x005F67B0, `c10-run.txt`)
- [C] **What the 300 separates.** At the entry's floor of 300, on the A1 count: an exact 5 % test rejects the page with probability 0.999998 when the code holds, and the code with probability 0.999999 when the page holds; the one cut A1 ≥ 74 errs with 0.000476 and 0.000357. Smite cannot separate them: both give 33. It separates those two distributions and nothing about how the draws are made. A single roll cut at 33 and 67 gives the code's frequencies, and no frequency test can tell it. (run:2026-11-04-r72, `c10-run.txt`)
- [C] **The draws, by replay.** From the unit seed on each decision's AID line, the three steps' low words mod 100 predict the arm of all 308 and the seed at the logged call and at AIX of all 308. Every other way of making the choice fails: the page as one roll 206, the page as fresh draws 90, one draw tested three times 206, the third draw left out 90 (right call, wrong seed: only the seed tells that `draw < 0` still steps), Jab's test first 234, the code's own frequencies from one roll 206. This is predicted from the logged seed at the think call; a seed from one decision to the next is not chained (one drawing pair, § 1.4). (run:2026-11-04-r72, 0x005F6861, 0x005F68D4, 0x005F693F)
- [C] **Row 44 meets the promotion rule** (`lane/p52c` review, as in ai/0018 § 4): 309 resumed, 0 mismatches, 619 boundary calls matched, 310 past the first, 309 of 309 with no unknown-value branch, every call one offer, 3 of 3 two-way sites failing alone. H1's sentence holds for these 309, on the logged paths, Normal, record 211. (run:2026-11-04-r72, 0x005B186F, `resume-44.txt`, `flip-44.txt`)
- [I] **The frequencies 33 : 33.5 : 33.5** stay arithmetic on that map; the logged counts agree and do not prove them. **C11** is not run: no decision of record 708 is logged, and Nightmare and Hell are not logged for record 211. The aura grant, the Charge test's true side and A2 are not reached (§ 1.5). (fn:sub_005F67B0_AiDuriel@0x005F67B0)
- [C] **State 13 is held by a unit, not reached by one.** 160 decisions, all by one class 45 unit per process (id 307, frames 2743–2774; id 213, frames 2083–6350), the only class 45 units with a home record at AiCtl `+0x20`. The 7 other class 45 units in those processes (ids 308–313 and 217) hold state 0 for all their 49 decisions. **No unit in any log holds two states**, so no 0 → 13 is logged: state 0 before state 13 in a process is another unit. (run:2026-11-04-r72, `s13-check.txt` `STATES`, 0x005B186F)
- [I] **What that says of the setter.** Nothing observes the call. At her first logged decision she already has `v14` 3, `v18` 2712 (L1) and `v14` 4, `v18` 1855 (L3): the think had already fired before the first logged frame of those processes, 2726 and 2070. The reading that `SuperUniqueSpawn` sets it at spawn, 0x005A4C1A for record word 6 alone, is unchanged and untested. **"No setter" for states 2, 3, 8, 9, 14, 17 stays `[I]`:** this window holds states 0 and 13 only, 626 AID and 769 AIN lines, and the plan's live-control window (10, 11, 12 and 13 together) is still not one window. (0x005A4C1A, fn:sub_005B0E00_MonAiInit@0x005B0E00, `fields.txt`)
- [C] **S13's block, on the arms reached, by `tools/ai_s13_check.py`:** 160 of 160, 0 mismatches, every boundary call, the seed at each call and at AIX, `v14`, `v18` at each call and chained across the unit's 158 pairs. Arms reached: fire 21, reset 5, melee A1 97, melee idle 8, far run 28, far idle 5, target's region differs and RunHome 1. Controls fail where arms are reached (§ 2.3); two cannot and say so. (run:2026-11-04-r72, fn:sub_005E5C50_AiSt13@0x005E5C50, fn:sub_005E5B70_AiPathSkillStep@0x005E5B70)
- [C] **Her path is the preset's.** The four fire points, in `v14` order, equal the one path of `cryptcountess1.ds1` at the offset (12500, 11000): a source the logger does not read. Five rounds of index 0 to 3 are logged, each after a reset. So the list's count is 4 from the file, not only from the fires. (run:2026-11-04-r72, `s13-census.txt`, 0x005E5C02)
- [C] **The promotion rule, state 13: not met by the stock tool, met with three words given.** `tools/ai_resume_flip.py` as it stands has 1 of 160 fork-free, on four sites inside `AiPathSkillStep`'s gate, whose words the logger does not record. Given the list's count (the file), the MonStats base (logged, one value per process) and the Skills count (357, skills.bin), `tools/ai_s13_census.py` has 160 of 160 fork-free, 1 148 calls with one offer each, 988 past the first, 7 of 7 two-way sites failing alone. Stated as that, for the review to rule on; not added to H1's table here. (run:2026-11-04-r72, `s13-census.txt`, `flip-10.txt`)
- [I] **Row 10's own think (state 0):** R10's block gives its 49 decisions, 0 mismatches, one control failing 28; short of the rule (49 of 50, 0 fork-free: `MonPlayerBonus`'s block is unknown to the model). It raises no block tag. (0x005F0B00, `r10-check.txt`, `flip-10.txt`)
- [C] **The logger wrote nothing** (rule 17): the source scan finds no write in `tools/gdb/ai.py`, `ai-g4.py`, `ai.gdb`, `ai-g4.gdb` or `pilot.py`; its one hit is a comment. (run:2026-11-04-r72, `fields.txt` `SCAN`)

## Leads used

- [L] src:arreat-summit-boss-pages: C10, Duriel "17 % Melee Attack 1, 33 % Smite, 50 % Jab". **contradicted**, now by the required case of [ai/0014](0014-community-cross-check.md). Detail: Jab 37.7 % and A1 29.2 % over 308 decisions, and the seed replay's 308 of 308; 33 and 50 are the `aip` values, marginal only for the first (fn:sub_005F67B0_AiDuriel@0x005F67B0, 0x005F6861, 0x005F68D4, run:2026-11-04-r72).
- [L] src:arreat-summit-boss-pages: C11, the same for Über Duriel. **contradicted**, unchanged: same think and `aip` values as data, no decision of record 708 logged (0x005F67B0).

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x005F67B0` | `sub_005F67B0_AiDuriel` | row 44 think; logged `th` on 309 decisions, compared call by call | C |
| `0x005E5C50` | `sub_005E5C50_AiSt13` | state row 13 think; logged `th` on 160 decisions of state 13, compared call by call | C |
| `0x005E5B70` | `sub_005E5B70_AiPathSkillStep` | `Skill1` at the next DS1 path point; 21 calls of its `UseSkill` compared, the points against the file | C |
| `0x005F0B00` | `sub_005F0B00_AiCorruptRogue` | row 10 think; logged `th` on 49 decisions, compared call by call | C |

A symbol's tag is its role. The blocks' tags are as stated above and in the routed entry.

## 1. Duriel

### 1.1 The cases

Owner-played, one case in each process (ADR-0028). L1: seed 3364, save `AiDur.d2s` with a mercenary, who killed Duriel: 9 decisions, all melee, target class 561 (type 1). L2: seed 3364, the no-mercenary save, recipe `tools/d2s_recipes/ai-dur-nomerc.json`: 300 decisions, 299 melee, target the player. The count recounted from the logs differs from the running note: 308 melee decisions, not 302, and 9 in L1, not 8. The kept tally is 308, `c10-run.txt`.

### 1.2 The tally

The first command of each melee decision, from its last boundary call, MSM0's mode and the skill the call carries:

| Arm | Call | MSM0 mode | Skill | n | L1 | L2 |
|---|---|---|---|---:|---:|---:|
| Smite | 0x005DEAD0@0x005F6884 | 14 | 97 | 102 | 3 | 99 |
| Jab | 0x005DEAD0@0x005F68F7 | 14 | 10 | 116 | 5 | 111 |
| A1 | 0x005DDF90@0x005F6964 | 4 | | 90 | 1 | 89 |
| A2 | 0x005DDF90@0x005F694E | | | 0 | | |

- [C] Smite and Jab are mode 14 (`Sk3mode`, `Sk2mode` of record 211), so **MSM0 alone cannot tell them**: the skill word does. ai/0014's "mode 5 with Skill3, mode 5 with Skill2" as the line needed was the expected form and is not what the data gives; the entry's mode is the record's. (0x005F687A, 0x005F68ED, run:2026-11-04-r72)

Among not-Smite, Jab is 116 of 206, 56.3 %, exact interval 49.2–63.2 %: the code's 50 % inside, the page's 74.6 % outside. ln(L_code / L_page) = 14.6.

### 1.3 The replay

`draw` is `(seed step).low % 100` by the inlined step and the `0x51EB851F` divide, read at 0x005F6824–0x005F6858, 0x005F6897–0x005F68CB and 0x005F6900–0x005F6936; `cmp` against `aip` at signed s16. For each melee decision, each reading gives an arm and a number of steps:

| Reading | ok | wrong call | right call, wrong seed |
|---|---:|---:|---:|
| `code`: three fresh draws | 308 | 0 | 0 |
| `page-one`: one roll, 33, 83 | 102 | 86 | 120 |
| `page-fresh`: fresh draws, 33, then 75 of the rest | 218 | 47 | 43 |
| `reused`: one draw against `aip2`, `aip3`, `aip4` | 102 | 102 | 104 |
| `two-draws`: `aip4`'s draw left out | 218 | 0 | 90 |
| `swapped`: Jab's test first | 74 | 204 | 30 |
| `one-cum`: one roll, 33, 67 | 102 | 98 | 108 |

`page-one` and `page-fresh` are this lane's renderings of a page that gives percentages, not draws. Equality at a test, a `<` against `≤`: 3 at draw 1 = 33, 2 at draw 2 = 50, 0 at draw 3 = 0; the emulated run:2026-10-30-ai-cat-emu-6 meets each.

### 1.4 What the seed is

The AID `s` word is the unit seed at the think call, not `-seed` (3364 fixes the levels only). Replay starts there. **Chaining between decisions is not tested:** `check-duriel.txt` has one drawing pair for row 44, short of the floor of 20; why so few pairs qualify is not examined. Decision to skill start: 218 inside, 218 with the event exit seed, 0 steps.

### 1.5 What row 44's rule does not reach

Sites reversed alone, `flip-44.txt`. Two-way: 0x005F6814 (`melee`), 0x005F6861 (Smite's draw), 0x005F68D4 (Jab's draw). One-way, the other side not compared: 0x005F67D7, 0x005F67E1, 0x005F6822, 0x005F6895, 0x005F693F (A2's draw, `aip4` 0), 0x005F6975, 0x005F69B2 (Charge's draw, `aip5` 0).

- [I] **The aura grant:** `GetRightSkill` returned non-zero in all 309, so `UnitSkillAdd` and `PlayerSetSkill` are not logged. He held the skill by his first logged decision. (0x005F67E3, 0x005F680B)
- [I] **Not melee:** one decision, L2 frame 1080, distance 6: `Ovr` 0x005DE190@0x005F69EE, `Walk` 0x005DEC80@0x005F69FD, MSM0 mode 2. One case carries that arm. (0x005F69B2)
- [I] **The first boundary** is one outcome in `check-duriel.txt`'s `MIX` line (`GetRightSkill`, 309): `tools/ai.py`'s 0 mismatches there test nothing about the choice. The replay and the resume do. (run:2026-11-04-r72, 0x005F67DF)

## 2. State 13

### 2.1 The first decisions

| Log | Unit | Class | State | Frames | Decisions | First `v14`, `v18` |
|---|---|---:|---:|---|---:|---|
| L1 | 307 | 45 | 13 | 2743–2774 | 2 | 3, 2712 |
| L1 | 308–313 | 45 | 0 | 2726–2781 | 23 | |
| L3 | 213 | 45 | 13 | 2083–6350 | 158 | 4, 1855 |
| L3 | 217 | 45 | 0 | 2070–2473 | 26 | |

L1's first state 13 decision: frame 2743, distance 18, not melee, fires index 3. L3's: frame 2083, distance 2, melee, A1. L2 holds no class 45 decision (lag stopped the owner short). AIN lines for these units: 0.

- [C] Same class, same process, different state, and no unit with two: `units_with_two_states=0` over L1's 11 units and L3's 2, AID and AIN lines. The state is not the class's. (run:2026-11-04-r72, `s13-check.txt`)
- [I] She is taken as The Countess from the owner's report (killed in L1) and from the state; no logged word carries the superunique's index. (run:2026-11-04-r72, 0x005A4BFE)
- [C] The static side, recounted: 33 direct calls of `MonAiInit`, one with an immediate 13, 0x005A4C1A; of the switch's 57 cases at 0x005A4BF7, only record word 6 reaches 0x005A4BFE. (`fields.txt` `SETTERS`, `SWITCH`, 0x005A4C1A)

### 2.2 Arms reached, by distance

`dist` is AiCtx `+0x14`, the bins the first tally's (117, 19, 3, 9, 4, 1, 7), which these rows sum to:

| Arm | 0–4 | 5–9 | 10–14 | 15–19 | 20–24 | 25–29 | 30+ | n | MSM0 mode / path |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| fire, `AiPathSkillStep` | 11 | 1 | 0 | 3 | 2 | 1 | 3 | 21 | 4 / 100 |
| melee, A1 | 97 | | | | | | | 97 | 4 / 100 |
| melee, idle | 8 | | | | | | | 8 | none |
| far, run | 1 | 14 | 2 | 6 | 2 | 0 | 3 | 28 | 15 / 101 |
| far, idle | 0 | 3 | 1 | 0 | 0 | 0 | 1 | 5 | none |
| step 4, RunHome | 0 | 1 | | | | | | 1 | 15 / 101 |

Reset (no call; `v14` ← 0 and the same decision goes on to its draw): 5, all at distance 0–4. Of the 117 at distance 0–4, 11 fire and 1 runs: the fire comes before the melee test, and the melee word is its own, not the distance (that far run).

**Not reached by any log, stay `[I]`:** `M` = 0 and no room (0x005E5C6B, 0x005E5C7C); the home record's push (0x005E5CA6) and a zero word's refill (0x005E5CE1, 0x005E5CE7); step 3's RunHome (0x005E5DBB); step 4 with the unit at home: `dist < 25`, the skill step, `Idle(10)` (0x005E5E8E, 0x005E5E9A, 0x005E5EC2); step 5's RunHome (0x005E5F22: the largest home distance logged is 29); every RunHome's refused side, `CancelEvents(2, 0)` and the fall-through (0x005E5E01, 0x005E5F0C, 0x005E5F65); `AiPathSkillStep`'s no list and out-of-range returns (0x005E5B88, 0x005E5B9B–0x005E5BE0); Nightmare and Hell (`aip` columns); any target but the player.

- [I] **For the block:** a refused RunHome does not return. 0x005E5E06 jumps to 0x005E5E0B and the other two fall to 0x005E5F11 and 0x005E5F6A, so the next step runs. S13's `RunHome` line leaves that to the reader. (0x005E5E06, 0x005E5F0C, 0x005E5F65)

### 2.3 Controls

Each changes one rule; kept in `s13-check.txt`:

| Control | Fails | Says |
|---|---:|---|
| `no-ten`: `r < aip(3)` | 14 | the 10 is added |
| `melee-swap` | 138 | |
| `no-reset` | 5 | the reset exists |
| `reset-1400` | 5 | |
| `no-v18` | 0, 21 by the chain | `v18` written at a fire, seen only at the next AID |
| `draw-first` | 21 | the fire comes before the draw |
| `idle-aip1` | 13 | Idle's word is `aip(2)` |
| `no-step4` | 1 | one decision carries the target's region test |
| `no-step3` | 160 | the home's region is compared |
| `limit-0`, `limit-20`, `limit-28` | 156, 90, 20 | the limit is above 28 |
| `limit-29` | **0** | cannot fail: the largest home distance is 29, so 30 to 40 is read, not separated |
| `ovr-byte`: `Ovr(13, 100, 0)` | 28 | the 0 |
| `mode-sk1` | **0** | cannot fail: class 45's `Sk1mode` is 4, so "the pushed 4, not `Sk1mode`" stays read |

The reset's threshold: resets at gaps 704, 705, 723, 725, 730, none up to a gap of 699. So it lies in 699 to 703; 700 and `>` are read (`cmp edi, 0x2BC; jle`, 0x005E5C29, 0x005E5C2F). Row 10's two-way site 0x005E5C2F fails alone in 138 decisions.

### 2.4 The count, and why the stock census does not meet the rule

`ai_resume_flip`'s row 10 over L1 and L3: 209 resumed, 0 mismatches, 1 fork-free. 159 of state 13 fork at 0x005E5B93, 0x005E5BC8, 0x005E5BD3, 0x005E5BE0 (`flip-10.txt`), the 49 of state 0 at 0x005F0B47 and 0x005F0B80. The one fork-free state 13 decision is the step 4 RunHome, which never calls the skill step.

The S13 check takes the count per unit from the fires, so by itself `v14 < count` is fitted. `tools/ai_s13_census.py` replaces that with sources the decision's calls do not hold: the file's 4 points, the base from `ms − class × 0x1A8` (1 value per log) and the 357 of [Skills](../../tables/Skills.md). Reversing 0x005E5B93 then fails 159. A reversal there tests the word's use, not the file. The 14 sites failing none are one-way: 13 are the position getters and their callers' unit-type tests, and 0x005E5E8E is step 4's at-home test on its one decision.

## 3. What a late attach cannot test

The logger was attached by `d2run --attach-file` in all five: at the orifice for Duriel, on arrival on Tower Cellar Level 5 for L1 and L2, after the level was cleared for L3. Sound on (`--sound`, no `-ns`), `--fullscreen`.

- [I] **No `AGM` line** in any of the five. It costs the game pointer's line and the caps' per-game restart, no field: `g`, `diff` and `fr` come from the event's own `ECX` at 0x005B1740. (tools/gdb/ai.py `on_entry`, 0x005B1740)
- [I] **No `AIN` before the attach**, and none at all for row 44 or for the state 13 unit: whether their pre-checks ended events earlier is not logged. (run:2026-11-04-r72, 0x005B1740)
- [I] **Earlier state:** `MonAiInit`'s calls, the grant of Duriel's aura, her first fires (`v14` from 0 at the start), her home's push, the first frame of any unit's life. So the setter of § 2.1 is not observable in these logs: a log that attaches before she is created and a read-only break at 0x005B0E00 would give it.
- [C] **`t` and `pl`:** no checker in `tools/ai.py` or `tools/ai_resume.py` reads `pl`; `t` goes into their models. `tools/ai_owner_fields.py`: `t` null exactly when `ctx[2]` is, all 626; a player target's `t` position equals `pl` in all 597; `pl` against the last PLR line, largest difference 1 sub-tile (8 lines of L3), else 0. L1's 20 row 61 lines and Duriel's 9 have no player target; 16 of those 20 follow a PLR line, all within 20 and equal, and the other 4 are unchecked. Both are this logger's reads of one unit, so that is consistency, not a second source; S13's region call carries `t`'s position as logged arguments in all 160, which is. (run:2026-11-04-r72, `fields.txt`, 0x005E5E76)
- [C] CAP 0, AIL 0, LOGERR 0 in all five. (run:2026-11-04-r72, `fields.txt`)
- [C] The reruns of `tools/ai.py check` equal the first checks kept in `owner-dur-check/`, byte for byte. (run:2026-11-04-r72, `check-duriel.txt`, `check-countess.txt`)

## Data touched

`tbl:MonStats.txt:aip1`..`aip5`, `tbl:MonStats.txt:Skill1`..`Skill4`, `tbl:MonStats.txt:Sk1mode`..; `data/global/tiles/act1/crypt/cryptcountess1.ds1`'s path list (sha256 in `s13-census.txt`); `struct:AiCtl` `+0x14`, `+0x18`, `+0x38`; the AiCtl `+0x20` record `+0x0C`, `+0x10`.

## Dead ends

The first count's "302 melee decisions" and "8 in L1" were running notes; § 1.1. "State 0 then 13" reads so by process and not by unit; § 2.1.

## Open questions

- [L] **The setter, observed.** Break at 0x005B0E00 read-only, attached before her level is entered. It needs an owner's walk under the debugger, or a recipe that starts next to the level.
- [L] **C11, row 44's record 708:** with the Uber shorts of [ai/0016](0016-uber-event.md), owner's.
- [L] **Whether a fork-free census with given words counts as the rule** is the review's: § 2.4.
- [L] **The reset gaps run 4 to 30 past 700.** A reset can only be met at a decision, which would explain it; not measured against the unit's event times.
