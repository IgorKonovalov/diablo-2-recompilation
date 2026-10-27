# 0002 — Rates: the animation rate of each mode, its stat terms, caps and floors, and when a rate change applies

> **Subsystem:** anim/timing
> **Question:** how does `UNIT_AnimSetRate` compute a unit's animation rate (`Unit+0x4C`, and the sequence step
> `Unit+0x3C`) for each mode from the record, the stats and the weapon; what caps and floors it applies; which code
> calls it again when a stat changes; and does a rate change apply to a mode already in progress?
> **Date:** 2026-10-27   **Plan:** 0050 (Phase 1, batch P1.2)   **Status:** open (P1.3 movement and the gates
> follows; the velocity and path speed that the moving branch passes on are P1.3's)

Static reading of the pinned `Game.exe` in Ghidra (project copy `workspace/ghidra-p50b`) and objdump, with two
emulated families (ADR-0015). The image tables, the call sites and the `UpdateAnimRate` readers come from
`tools/anim_rates.py`; the derived breakpoint function and its brute-force check from the same tool's `bp` section.
All outputs are kept under `workspace/logs/anim/` (`p50b-manifest.sha256`, one path base: `p50b-tables.txt`,
`p50b-calls.txt`, `p50b-uar.txt`, `p50b-data.txt`, `p50b-bp.txt`, `p50b-setrate.asm`, `p50b-setrate-callees.txt`,
`p50b-setrate-xrefs.txt`, `p50b-anim-rows.txt` (anim/0001 § 10's re-read), `p50b-emu/` and `p50b-commands.txt` with the command lines and tool hashes). Unit fields as
in `re/types/game.h`, the animation records as in `re/types/anim.h`. "Display" type, class and mode are the values
after `UNIT_AnimTransform` ([anim/0001 § 2](0001-modes-frames.md#2-records-the-token-the-lookup-and-the-fallback)).
`spd` is the record's speed (`AnimDataRec+0x0C`, u32). 8.8 means frames × 256.

## Answer (summary)

- [I] **One function, nine branches.** `UNIT_AnimSetRate(unit)` returns at once for a null unit or a type ≥ 4; it
  takes the display type, class and mode, sets the record (`UNIT_AnimSetRecord`), and then takes the first branch that
  matches: cast, block, get-hit, knockback, moving, attack, fixed, default. Each writes `+0x4C`; only cast and attack
  also write the sequence step `+0x3C`; knockback and moving also set the path speed. Every result is floored at 0
  (`≤ 0` signed → 0) and capped at `0x7FFF`. (fn:UNIT_AnimSetRate@0x00623F50, `p50b-setrate.asm`)
- [I] **The formulas** (`B_i` the rate bonus below, `/100` truncating):
  cast `r = spd · min(100 + B_FCR, 175) / 100` (unsigned divide; no lower bound on the factor);
  block `r = max(1, spd · (B_FBR + 50) / 100)`, 100 instead of 50 under state 101 (`holyshield`), no cap on the factor;
  get-hit `r = spd · (B_FHR + 50) / 100`;
  attack `r = base · clamp(B_IAS + stat 68 [+ dual-wield term] [− 30 in a player sequence], 15, 175) / 100`, `base` = `spd`
  except in a shapeshift form (below); moving `r = vbase · max(B_FRW + stat 67, 25) / 100` (signed divide);
  knockback `r = vbase`; fixed (death modes) `r = spd`; default (every other mode) `r = spd · clamp(stat 69, 15, 175) / 100`.
  (fn:UNIT_AnimSetRate@0x00623F50, 0x00623FCB–0x0062438B, tbl:ItemStatCost.txt:Stat)
- [C] **The rate bonus** `B_i = k · s / (k + s)` (signed 32-bit `imul`, `idiv` truncating toward zero) when `s ≠ 0`,
  else 0, with `s` = `sub_00625500_UnitGetStat(unit, stat, 0)` (that this is the unit's full stat is the § 2 reading,
  `[I]`) and `(k, stat)` = (120, 93 `item_fasterattackrate`), (120, 99
  `item_fastergethitrate`), (120, 105 `item_fastercastrate`), (120, 102 `item_fasterblockrate`), (150, 96
  `item_fastermovevelocity`) from the image table `g_AnimRateBonus`. As a map (ADR-0015): 3 413 emulated cases over
  the six entries, `s` from −119 to 65 535 and 240 random 32-bit values, 0 mismatches, 0 stops, no read outside the
  declared set. (fn:sub_00621740_AnimRateBonus@0x00621740, data:g_AnimRateBonus@0x006E8E24,
  run:2026-10-27-anim-rates-emu `bonus`)
- [I] **Which branch a mode takes** is the image's mode-class tables (`g_PlrModeRateClass`, `g_MonModeRateClass` for a
  monster class below 410, `g_MonXModeRateClass` from 410): player A1, A2, TH, KK attack; SC cast (and SQ when the
  skill's `seqtrans` is SC); BL block; GH get-hit; KB knockback; WL, RN, TW moving; DT and DD fixed; S1–S4 and SQ
  moving with a move-first skill, attack with Skills `UseAttackRate`, else default; NU and TN default. Monster A1, A2
  attack; SC cast; BL block; GH get-hit; KB knockback; WL, RN moving; DT, DD fixed; S1–S4 **always moving for a
  class below 410**, and like the player's S1–S4 from 410; SQ like the player's SQ; an `npc` row is moving only in WL
  and RN. (fn:sub_006214A0_AnimRateIsMove@0x006214A0, fn:sub_00621580_AnimRateIsAttack@0x00621580,
  data:g_PlrModeRateClass@0x006E8A00, `p50b-tables.txt` `MCLS`, tbl:Skills.txt:UseAttackRate, tbl:MonStats.txt:npc)
- [I] **Where the stat terms come from** (read here only as far as the rate needs them): stats 67, 68, 69 are 100 on
  a new player and 75, 100, 100 on a new monster; a weapon carries 68 = −`speed`; the unit's 68 and 93 are
  `damagerelated`, so after `WeaponListsRelink2(unit, 1)` only the weapon the attack uses counts, and a dual-wielder
  with two weapons gets the average of the two hands' 68 in place of the right hand's; champions and the `fast` and
  `fanatic` mods add to 67 only; skills reach the rate through stat lists (`aurastat*`, `passivestat*`, the start-32
  list's 68, chill's 67/68/69). No difficulty, player-count or game field is read. (fn:PLAYER_InitBaseStats@0x005706D0,
  fn:sub_00573CB0_MonStatsInit@0x00573CB0, fn:sub_00623C80_WeaponListsRelink2@0x00623C80, 0x00624211–0x0062428E,
  tbl:ItemStatCost.txt:damagerelated)
- [C] **`UNIT_AnimAdvance` takes the rate at each call** (ADR-0015 map): 1 200 emulated pairs of consecutive advances, the second with a new rate, 0 mismatches over 2 400 calls;
  1 114 of the 1 120 pairs whose rate changed would mismatch had the advance kept the old rate. (fn:UNIT_AnimAdvance@0x00623E00,
  run:2026-10-27-anim-rates-emu `advance`) [I] So an every-frame monster's next advance after a re-call runs at the new
  rate (that the every-frame modes call it once per frame is anim/0001 § 10's reading). A scheduled mode keeps its
  queued events: `UNIT_AnimSetRate` calls
  neither the event queue nor the cancel (its 19 direct callees, `p50b-setrate-callees.txt`), so a re-call moves no
  frame event and no mode end; only the § 7.1 reschedules of anim/0001 rebuild them, from the rate at their call.
- [I] **Who re-computes the rate.** 31 call sites: 24 server (the mode inits, equip, the aura, curse, chill, slow,
  state-end and skill stat-list functions, the monster's mode-command velocity) and 7 client. No stat write hooks it:
  the ItemStatCost `UpdateAnimRate` bit is tested by the server only in four curse and Taunt paths, which set a flag
  their apply callback reads before calling it; every other caller calls it unconditionally. (`p50b-calls.txt`,
  `p50b-uar.txt`, fn:sub_005C35C0_CurseApplyCb@0x005C35C0, tbl:ItemStatCost.txt:UpdateAnimRate)
- [I] **Breakpoints as a function.** For a scheduled mode of `F` frames, start `S` and rate `r > 0`, the mode lasts
  `n(r) = max(2, ⌈256 (F − S) / r⌉)` game frames and frame `f` fires at `T + max(1, ⌈256 (f − S) / r⌉)` when that is at
  most `⌈256 (F − S) / r⌉ − 1`. With `r = ⌊spd · X / 100⌋`, the least factor that gives a length ≤ `m` is
  `X = ⌈100 · ⌈256 (F − S) / m⌉ / spd⌉`, and the least item stat that gives a bonus ≥ `y < k` is `⌈k y / (k − y)⌉`.
  Checked against brute force over every stock (frames, speed) pair (166 957 cases, 66 096 least-X cases, 254
  least-stat cases, 0 mismatches; a model check, not of the game). (fn:SUNIT_ScheduleModeEvents@0x005539B0,
  `p50b-bp.txt` `CHECK`)

## Leads used

No lead was used to locate or read this code, and [anim/leads](leads.md) was read only in its § 1 (sources and
versions) before filing ("leads not read before filing"; plan 0050, `lane/p50c` review ruling (b)).
*2026-10-27 (plan 0050 Phase 1b part 2, `lane/p50v`):* the verdicts on the 29 rate, attack, cast, hit-recovery and
block rows, against this finding, anim/0001 and the P0 `animdata.d2` survey; agreement promotes nothing, and a
`contradicted` row is a required Phase 2 case ([backlog](../../backlog/2026-10-27-reverser-reverser-plan-0050-p1b-contradicted-cases.md),
cases P1b-1 … P1b-15; `(version: …)` marks a row whose only source describes D2R or 1.09, not a community error). The
table and record comparisons come from `tools/anim_leads_check.py code` (`workspace/logs/anim-leads/p50v-code.txt`
`99e7b983…`, `p50v-manifest.sha256`): the code's length `n` from `sched_len` and the rates of `tools/anim_rates.py`
over the records the code looks up.

- [L] src:pd-breakpoints: R2, a breakpoint is met at the listed value or above. **held**
  Detail: § 7's least factor and least item stat are lower bounds (`X ≥ X_m`, `s ≥ ⌈k y / (k − y)⌉`); the code's change
  points equal both sources' 39 tables (`TAB … thresholds_equal=1` ×78).
- [L] src:maxroll-d2r-breakpoints, src:maxroll-d2r-attack-speed, src:basin-wiki-animation: R3, item IAS, FCR, FHR and
  FBR are diminished as `⌊120 x / (120 + x)⌋`. **held with refinement**
  Detail: `B = k s / (k + s)` with `k` 120 for stats 93, 99, 102, 105 (§ 2, fn:sub_00621740_AnimRateBonus@0x00621740),
  truncated toward zero (the floor for the stock `s ≥ 3`), `s` the unit's stat; FR/W is the same with `k` 150.
- [L] src:maxroll-d2r-breakpoints: R4, EFCR is capped at 75. **held**
  Detail: the cast factor `min(100 + B_FCR, 175)` (§ 3.1, 0x00623FDA–0x00623FE1).
- [L] src:maxroll-d2r-breakpoints, src:pd-breakpoints: R5, no cap for EFHR, EFBR or EIAS. **contradicted**
  ([P1b-2](../../backlog/2026-10-27-reverser-reverser-plan-0050-p1b-contradicted-cases.md))
  Detail: get-hit and block have no upper bound on their factor (§ 3.2), but the attack factor `B_IAS + stat 68 (+
  terms)` is clamped to 15..175 (§ 3.6, fn:UNIT_AnimSetRate@0x00623F50), so EIAS with the skill and weapon terms is
  capped; reachable with Fanaticism or Burst of Speed and a fast weapon.
- [L] src:maxroll-d2r-attack-speed: A1, attack frames `⌈256 L / ⌊256 (100 + SIAS + EIAS − WSM) / 100⌋⌉ − 1`.
  **contradicted (version: D2R)** ([P1b-1](../../backlog/2026-10-27-reverser-reverser-plan-0050-p1b-contradicted-cases.md))
  Detail: the rate agrees (`r = ⌊spd · X / 100⌋`, `X = B_IAS + stat 68` with 68 = 100 + skill terms − `speed`, § 3.6),
  but the scheduled mode ends at `T + max(2, ⌈256 (F − S) / r⌉)` with no `− 1` (§ 7, fn:SUNIT_ScheduleModeEvents@0x005539B0):
  the source's 11-frame Amazon unarmed attack is 12 in the code (`AMA1HTH` 13 frames, start 1). `PlrModeLeaveOk` lets
  A1, A2, SC and TH be left for a new request while the end is queued (anim/0003 § 6.2), so the interval between two
  attacks is the run's to log.
- [L] src:basin-wiki-animation: A2, attack frames `⌈256 (F − 1 − S) / r⌉`. **contradicted**
  ([P1b-1](../../backlog/2026-10-27-reverser-reverser-plan-0050-p1b-contradicted-cases.md))
  Detail: the code's `⌈256 (F − S) / r⌉` (§ 7) is one more than the Basin cycle column in all 69 rows at factor 100
  (`BASIN … cycle=… n_at_x100=…`); at `r > 256` the two can coincide, so the case takes two or more rates.
- [L] src:maxroll-d2r-attack-speed, src:basin-wiki-animation: A5, with two weapons only the primary weapon's IAS
  counts. **held**
  Detail: stats 68 and 93 are `damagerelated`; `WeaponListsRelink2(unit, 1)` links only the weapon the attack uses
  with damage (§ 3.6, fn:sub_00623C80_WeaponListsRelink2@0x00623C80).
- [L] src:maxroll-d2r-attack-speed, src:basin-wiki-animation: A6, dual-wield WSM `(L + R)/2` with the left-slot weapon
  primary, `(L + R)/2 − L + R` with the right-slot one. **held with refinement**
  Detail: the term `(68(R) + 68(L))/2 − 68(R)` (body locations 4 and 5, `cdq; sub; sar 1`) gives `(R + L)/2` when the
  location-4 weapon is linked and `(R + L)/2 − R + L` when the location-5 one is (§ 3.6, 0x00624211–0x0062428E): the
  two formulas, with the source's left slot as body location 4 (the slot naming is the source's); only when the unit
  can dual-wield and both hands hold a usable `weap`.
- [L] src:maxroll-d2r-attack-speed, src:basin-wiki-animation: A7, WSM is the Weapons `speed` (−60 to 20, positive
  slower), subtracted from the rate. **held with refinement**
  Detail: a weapon's stat 68 is `−speed` (items/properties A4, fn:sub_005563D0_ItemSetBaseDamage@0x005563D0), added
  into `X` (§ 3.6); stock `speed` −60..20 over 306 rows, Axe 10, Hand Axe 0, Military Pick −10 (`WSM` lines).
- [L] src:maxroll-d2r-attack-speed, src:basin-wiki-animation: A8, skill IAS is added undiminished; Burst of Speed,
  Fanaticism, Werewolf and Frenzy raise it; Decrepify, Holy Freeze, cold and Slows Target lower it; the slow on a
  character is capped at 50 %. **held with refinement**
  Detail: stat 68 enters `X` raw (§ 3.6); chill's 68 is the cold effect and Slows Target's state sets 68 and 69 to
  `−v`, `v` capped at 50 for players (skills/0003 handler 19, fn:sub_005C0310_StatEv19Slow@0x005C0310); the other
  skills reach 68 through their stat lists (§ 4), whose values are not read here; the factor's floor 15 also bounds a
  slow.
- [L] src:maxroll-d2r-attack-speed: A9, a throw with a throwing weapon costs 30 off the rate, except for the
  Barbarian. **contradicted (version: D2R)** ([P1b-3](../../backlog/2026-10-27-reverser-reverser-plan-0050-p1b-contradicted-cases.md))
  Detail: the only `− 30` is for a player whose real mode is 18 (a sequence), for every class (0x00624290–0x0062429B);
  the throw mode TH (11) takes the attack branch without it (§ 3.6).
- [L] src:maxroll-d2r-attack-speed: A10, sequence skills use `⌈256 L / ⌊256 (100 + SIAS + EIAS − (WSM + 30)) / 100⌋⌉`
  with no `− 1`; Leap Attack and Charge ignore WSM. **contradicted (version: D2R)**
  ([P1b-4](../../backlog/2026-10-27-reverser-reverser-plan-0050-p1b-contradicted-cases.md))
  Detail: for the five with `UseAttackRate` (Jab, Impale, Fists of Fire, Claws of Thunder, Blades of Ice) the attack
  branch with `X − 30` and the sequence length `L` with no `− 1` agree (§§ 3.6, 7), the speed being the mode-18 record's,
  whose token is `GH` (anim/0001 § 2); Charge and Leap Attack have no `UseAttackRate`, so they take the moving or the
  default branch (§ 1), item IAS does not enter, and their sequence step stays 0x100 (§ 3.8).
- [L] src:maxroll-d2r-attack-speed, src:basin-wiki-animation: A11, rollback skills give each hit of a sequence its own
  length; Fend's lengths by target count. **not covered**
  Detail: Dragon Talon (do 42), Strafe (12) and Fend (13) rebuild their schedule through
  fn:sub_00553B10_RescheduleFromPct@0x00553B10 (anim/0001 § 7.1), whose percentage is a catalogue value (plan 0046);
  Zeal and Fury are not among the reschedule callers read; the per-hit lengths are not decided here.
- [L] src:maxroll-d2r-attack-speed: A12, Double Throw `Vinc = 70 + (WSM1 + WSM2)/2 + SIAS + EIAS`, `fpa = ⌈256·12/⌊256
  Vinc/100⌋⌉ / 2`; Double Swing `Vinc = 120 + …`, 17 frames; `Vinc` clamped 15–175. **contradicted (version: D2R)**
  ([P1b-5](../../backlog/2026-10-27-reverser-reverser-plan-0050-p1b-contradicted-cases.md))
  Detail: both are real-mode-18 attack-rate sequences, so `X = B_IAS + stat 68 + dual term − 30`, clamped 15..175
  (§ 3.6): base 70 for both, not 120 for Double Swing; the hands' mean is subtracted (stat 68 = −`speed`), where the
  row writes `+`; one schedule per sequence, 12 frames (sequence 15) and 17 (sequence 11) (`SEQ` lines, anim/0001 § 5).
- [L] src:maxroll-d2r-attack-speed: A13, Frenzy's two swings at two factors (`WSM1st`, `WSM2nd`), `fpa1 = ⌈256·9/…⌉ −
  1`, `fpa2 = ⌈256·17/…⌉`; after a missed first swing the second uses the first weapon's speed.
  **contradicted (version: D2R)** ([P1b-5](../../backlog/2026-10-27-reverser-reverser-plan-0050-p1b-contradicted-cases.md))
  Detail: the 17-frame sequence 11 is scheduled once at the start's rate (anim/0001 § 7), one factor for both swings,
  with the base 70 and the dual term of A6; Frenzy is not among the reschedule callers of anim/0001 § 7.1.
- [L] src:maxroll-d2r-attack-speed: A14, werewolf and werebear `AnimSpeed = ⌊256·FramesNeutral/Delay⌋`, `Delay =
  ⌊256·FramesChar/⌊(100 + WIAS − WSM)·CharSpeed/100⌋⌋`, FramesNeutral the NU length 13 or 12, FramesChar 15, then A1;
  the faster of this and A1 from patch 2.4. **contradicted (version: D2R)**
  ([P1b-6](../../backlog/2026-10-27-reverser-reverser-plan-0050-p1b-contradicted-cases.md))
  Detail: the shape agrees: `w = (+0x48 & ~0xFF) / D`, `D` from the weapon's IAS and `speed` undiminished, then the
  attack factor (fn:sub_00646170_WereformAttackBase@0x00646170, § 3.6). But `+0x48` is the form's current record
  (A1 at `SUNIT_AnimInit`'s call: `40A1HTH` 13, `TGA1HTH` 12 frames; the NU records have 9 and 10), and `D` uses the
  human A1 record of the weapon's class (`DZA1*` 16–23 frames) or 19 with no weapon (fn:sub_0062A710_HumanAttackFrames@0x0062A710),
  not 15; no "faster of the two" test.
- [L] src:maxroll-d2r-attack-speed: A15, Trang-Oul's vampire form attacks with length 14 and speed 176, Delirium's
  fetish with 12 and 256. **held with refinement**
  Detail: the display records `VAA1HTH` (14, 176) and `FKA11HS` (12, 256) by States `gfxclass` (anim/0001 § 2,
  fn:UNIT_AnimTransform@0x00645270); neither state has `meleeonly`, so the base is the record's speed (§ 3.6).
- [L] src:maxroll-d2r-breakpoints: C1, cast frames `⌈256 B / ⌊S (100 + EFCR) / 100⌋ − 1⌉`, Lightning and Chain
  Lightning without the `− 1`. **contradicted (version: D2R)**
  ([P1b-1](../../backlog/2026-10-27-reverser-reverser-plan-0050-p1b-contradicted-cases.md))
  Detail: the cast rate agrees (§ 3.1) and the change points of all 24 FCR tables equal the code's, but the code's
  length is the table's + 1 in every row of the eleven record casts (`table_minus_n=[-1]`); the Lightning tables equal the
  code's `n` exactly (`table_minus_n=[0]`: sequence 12, 19 frames, at the cast rate, § 3.1).
- [L] src:maxroll-d2r-breakpoints: C2, cast bases and speeds per class and form. **contradicted (version: D2R)**
  ([P1b-7](../../backlog/2026-10-27-reverser-reverser-plan-0050-p1b-contradicted-cases.md))
  Detail: the records agree for the Amazon (20/256, all weapon classes), Assassin 17, Barbarian 14, Paladin 16,
  Sorceress 14, the vampire (15/160), Lightning (19) and the Act 3 mercenary (18), and differ for the Druid (`DZSC*` 15
  frames, speed 208; the row 16), the Necromancer (`NESC*` 16; the row 15), the werewolf (`40SCHTH` 11/168; the row
  16/229) and the werebear (`TGSCHTH` 10/152; the row 16/228) (`CAST` lines; fn:ANIMDATA_Lookup@0x0066A9B0).
- [L] src:maxroll-d2r-breakpoints, src:pd-breakpoints: C3, the two sources' FCR tables agree with each other; with C1
  and C2 they reproduce 8 of 12, the Druid's only with base 15 and the Necromancer's only with base 16. **held with
  refinement**
  Detail: the records give exactly those bases (C2 above), and with them the code's change points equal all 24 FCR
  tables (`TAB fcr …`); the frame counts are C1's, one below the code's.
- [L] src:maxroll-d2r-breakpoints: C5, the Amazon's cast length does not depend on her weapon, only her action frame
  does. **held with refinement**
  Detail: the eight `AMSC*` records are 20 frames at 256 with first events at 10–13 (`CAST`); the "19 frames at 0 FCR"
  is C1's count, 20 in the code.
- [L] src:maxroll-d2r-breakpoints: C7, the Act 1 mercenary's Inner Sight runs on the attack rate; FCR has no effect.
  **held with refinement**
  Detail: the Rogue's Inner Sight is Hireling `Mode1` 4 (A1), and a monster's A1 takes the attack branch (§ 1); the
  mode choice is the AI's (plan 0052), tbl:Hireling.txt:Mode1.
- [L] src:maxroll-d2r-breakpoints: H1, hit-recovery frames `⌈256 B / ⌊S (50 + EFHR) / 100⌋ − 1⌉`.
  **contradicted (version: D2R)** ([P1b-1](../../backlog/2026-10-27-reverser-reverser-plan-0050-p1b-contradicted-cases.md))
  Detail: the get-hit rate agrees (§ 3.2) and the 32 FHR tables' change points equal the code's, but the code's
  length is the table's + 1 in every row (`TAB fhr … table_minus_n=[-1]`); get-hit cannot be left before its end
  (anim/0003 § 6.2).
- [L] src:maxroll-d2r-breakpoints: H2, hit bases and speeds per class, form, weapon and mercenary. **held with
  refinement**
  Detail: the `GH` records agree row for row (`TAB fhr` `F=`, `spd=`); the Paladin's 5/192 records are `PAGHSTF` and
  `PAGH2HT`, so the weapon classes `stf` (staves, polearms, two-handed axes and hammers) and `2ht` (spears) take it;
  the Druid's 248 is `DZGH1HS` only (H4).
- [L] src:maxroll-d2r-breakpoints, src:pd-breakpoints: H3, the FHR tables are reproduced by H1 and H2. **held with
  refinement**
  Detail: with the records' frames and speeds the code's change points equal all 32 FHR tables up to their last rows,
  `src:pd-breakpoints`'s further rows included; the counts are H1's, one below the code's.
- [L] src:maxroll-d2r-breakpoints, src:pd-breakpoints: H4, the "one-handed swinging" weapons of the Druid's FHR and the
  Amazon's FBR (three lists). **contradicted**
  ([P1b-8](../../backlog/2026-10-27-reverser-reverser-plan-0050-p1b-contradicted-cases.md))
  Detail: the record is chosen by the weapon class (anim/0001 § 2, fn:COMPOSIT_WeaponClass@0x0064F060), and the
  248 and 88 records are `DZGH1HS` and `AMBL1HS`: the types whose Weapons `wclass` is `1hs` held one-handed (axes,
  clubs, hammers, maces, orbs, scepters, swords, throwing axes, wands; `WSM wclass_1hs_types`). Maxroll's FHR list
  lacks hammers and orbs, its FBR note lacks wands, PureDiablo's lacks hammers; a two-handed axe is `stf` and a
  two-handed sword held in two hands `2hs`.
- [L] src:maxroll-d2r-breakpoints: B1, block frames `⌈256 B / ⌊S (50 + EFBR) / 100⌋ − 1⌉`, Holy Shield + 50 to EFBR.
  **contradicted (version: D2R)** ([P1b-1](../../backlog/2026-10-27-reverser-reverser-plan-0050-p1b-contradicted-cases.md))
  Detail: the block rate and Holy Shield's 100 for 50 agree (§ 3.2), the 22 FBR tables' change points equal the code's,
  and the code's length is the table's + 1 in every row (`TAB fbr … table_minus_n=[-1]`).
- [L] src:maxroll-d2r-breakpoints: B2, block bases and speeds per class and form. **held with refinement**
  Detail: the `BL` records agree (`TAB fbr`); the Amazon's 88 is `AMBL1HS` only (H4); `PABL2HS` (speed 168) exists but
  a two-handed sword leaves no shield.
- [L] src:maxroll-d2r-breakpoints, src:pd-breakpoints: B3, the FBR tables are reproduced by B1 and B2. **held with
  refinement**
  Detail: the code's change points equal all 22 FBR tables, Holy Shield's included; the counts are B1's.

No lead was found for monster rates, the `fast` and champion terms, or the shapeshift's rate re-call (part 1, anim/leads
§ 1): "no lead; derived from code".

## Functions

New names (subsystem `anim/timing`) and the existing ones this finding reads; all new rows are I except where a
family checks the function's map.

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x00623F50` | `UNIT_AnimSetRate` | the rate (§ 2); unchanged name | I |
| `0x00621740` | `sub_00621740_AnimRateBonus` | `B_i` from `g_AnimRateBonus[i]` (EAX `i`, ECX unit) | I (its map checked by the `bonus` family; an ADR-0015 map raises no symbol row) |
| `0x006216E0` | `sub_006216E0_AnimRateIsCast` | the cast test (EAX type, EDX mode, ECX unit) | I |
| `0x006214A0` | `sub_006214A0_AnimRateIsMove` | the moving test (ECX type, EDX mode, ESI class) | I |
| `0x00621580` | `sub_00621580_AnimRateIsAttack` | the attack test (ECX mode, EDX type, stack class) | I |
| `0x00621630` | `sub_00621630_AnimRateIsFixed` | the fixed test (EAX type, ECX mode, stack class) | I |
| `0x006213D0` | `sub_006213D0_AnimMoveBaseRate` | `vbase`: player 0x65 (run) / 0xD5; monster MonStats `+0x36` / `+0x38` (RN) | I |
| `0x00621360` | `sub_00621360_AnimPathBaseSpeed` | the path speed base: CharStats `+0x040` `<< 8` / MonStats `+0x032` `<< 8` | I |
| `0x00646170` | `sub_00646170_WereformAttackBase` | `(+0x48 & ~0xFF) / D` for a transformed player (§ 3.6) | I |
| `0x0062A710` | `sub_0062A710_HumanAttackFrames` | `D`: the human A1 length in game frames with this weapon | I |
| `0x0066AA80` | `sub_0066AA80_AnimDataInfo` | frames, speed and first event frame of a named record | I |
| `0x00628500` | `sub_00628500_ItemWClass` | Items `+0xC0` (the weapon class code) | I |
| `0x0062A4E0` | `sub_0062A4E0_ItemNotDisabled` | not an item, or an item without flags `0x100`, `0x4000` | I |
| `0x0063A400` | `sub_0063A400_UnitTransformFlag` | `Unit+0xC8` bit 3 | I |
| `0x005A6380` | `sub_005A6380_MonModeVelocity` | stat 67 ← the mode command block's `+0x10` in a `0x4000` list, then the rate | I |
| `0x0056B6C0` | `sub_0056B6C0_ClampVitalsSetRate` | life, mana, stamina clamped to their maxima, then the rate | I |
| `0x0057AD80` | `sub_0057AD80_ColdEndCb` | chill (state 11) end callback, then the rate | I |
| `0x005C6DC0` | `sub_005C6DC0_SkillPassiveStatList` | a skill's `passivestat1..5` into a list (68 also into 69), then the rate | I |
| `0x005D8EF0` | `sub_005D8EF0_SkillSt38EndCb` | Whirlwind start's state end callback, then the rate | I |
| `0x00650F00` | `sub_00650F00_MonStatsSpeeds` | MonStats `+0x36`, `+0x38` at load (§ 3.5); unchanged name | I |

Data: `g_AnimRateBonus` `0x006E8E24` (6 × 12 B: type, k, stat), `g_PlrModeRateClass` `0x006E8A00` (20 × 20 B),
`g_MonModeRateClass` `0x006E8B90` (16 × 20 B), `g_MonXModeRateClass` `0x006E8CD0` (16 × 20 B); the 20-byte entry is
`{skillMove, move, skillAttack, attack, fixed}` (`re/types/anim.h` `ModeRateClass`).

## Walkthrough

### 1. Entry, the record and the order of the tests

```c
// fn:UNIT_AnimSetRate@0x00623F50 (stack: unit, source file, line; ret 0xC), trimmed
if (!unit || unit->type >= 4) return;                 // items (4) and above: nothing
type = unit->type; cls = unit->class; mode = unit->mode;
UNIT_AnimTransform(unit, &type, &cls, &mode);          // display values (anim/0001 § 2)
UNIT_AnimSetRecord(unit, type, cls, mode);             // +0x50
rec = unit->pAnimData;  spd = rec->speed;
if      (IsCast(unit, type, mode))            { cast;      +0x4C = +0x3C = r; }
else if (type,mode in {(0,9),(1,6)})          { block;     +0x4C = r; }
else if (type,mode in {(0,4),(1,3)})          { get-hit;   +0x4C = r; }
else if (type,mode in {(0,19),(1,13)})        { knockback; +0x4C = r; PathSetSpeed(path, 0x1000); }
else if (IsMove(unit, type, mode, cls))       { if (!path) return; moving; +0x4C = r; PathSetSpeed(path, …); }
else if (IsAttack(unit, type, mode, cls))     { attack;    +0x4C = +0x3C = r; }
else if (IsFixed(type, mode, cls))            { +0x4C = r = spd; }
else                                          { default;   +0x4C = r; }
```

- [I] The second and third stack arguments (a source path and a line) are not read; every call site pushes them
  (`p50b-calls.txt` `file=`). (0x00623F56–0x0062401D)
- [I] **The record is set again at every call**, so a re-call in the middle of a mode can change `+0x50` (for example
  after a weapon swap changes the weapon class, anim/0001 § 2) but never `+0x48` (the length), which only the mode
  inits write. (0x00623FAF, fn:UNIT_AnimSetRecord@0x00620F00)
- [I] **Objects and missiles** (types 2 and 3) pass the type test and reach `AnimRateIsMove`, which fails an assert
  for a type other than 0 or 1 (0x006214C5–0x006214DF); in the code read, `UNIT_AnimInit`'s object and missile
  branches do not call `UNIT_AnimSetRate` (anim/0001 § 3), and no caller in `p50b-calls.txt` passes one.
  (fn:sub_006214A0_AnimRateIsMove@0x006214A0)
- [I] **Floor and cap.** Every branch ends `q ≤ 0 (signed) → 0; q ≥ 0x7FFF → 0x7FFF` (`test; setle; sub 1;
  and; cmp 0x7FFF; jl`) and stores the low word in `+0x4C`, block after its `q < 1 → 1` (it joins the default
  branch's floor at 0x00624369; *2026-10-27, `lane/p50b` review:* "every branch but block" corrected); cast and attack store the sign-extended word in `+0x3C`
  too. (0x00623FF6–0x00624016, 0x006242E2–0x00624302, 0x00624369–0x00624381)

### 2. The rate bonus

```c
// fn:sub_00621740_AnimRateBonus@0x00621740 (EAX i, ECX unit)
s = sub_00625500_UnitGetStat(unit, g_AnimRateBonus[i].stat, 0);
if (g_AnimRateBonus[i].type == 1 && s != 0) return (k * s) / (k + s);   // imul, cdq, idiv: truncation
return s;
```

| `i` | type | `k` | stat | used by |
|---:|---:|---:|---|---|
| 0 | 1 | 120 | 93 `item_fasterattackrate` | attack |
| 1 | 1 | 120 | 99 `item_fastergethitrate` | get-hit |
| 2 | 1 | 120 | 105 `item_fastercastrate` | cast |
| 3 | 1 | 120 | 102 `item_fasterblockrate` | block |
| 4 | 1 | 150 | 96 `item_fastermovevelocity` | moving |
| 5 | 1 | 1 | 0 `strength` | no caller in `UNIT_AnimSetRate` |

(`p50b-tables.txt` `BONUS`)

- [C] (ADR-0015) The map above, for all six entries: the emulated `bonus` family writes the unit's stat list (one
  entry for the stat at layer 0, decoys at other stats and layers, the stat absent in one case per entry), the
  DataTables ItemStatCost pointer and count and the record's `+0x05` byte (fMin clear, as in the `.txt` for every
  rate stat, `p50b-data.txt` `ISC`); 3 413 cases (positive 2 569, negative 832, zero 12), 0 mismatches, 0 stops, every
  read inside the declared set (the table and the fMin mask byte `0x006CE270`). Not covered: `s = −k`, a divide fault
  that SLEIGH does not model. (run:2026-10-27-anim-rates-emu `bonus`, `p50b-emu/check.txt`)
- [I] **Range.** For `s ≥ 0` the bonus rises from 0 toward `k` and never reaches it (`k − 1` at `s ≥ k (k − 1)`); for
  `−k < s < 0` it is negative and unbounded below (−14 280 at `s = −119` for `k` 120); `s = −k` divides by zero
  (`idiv`, a fault); for `s < −k` it is positive and above `k` (14 520 at `s = −121`). (0x00621769–0x00621777,
  `p50b-bp.txt` `EDGE bonus`)

### 3. The branches

#### 3.1 Cast

- [I] `AnimRateIsCast(unit, type, mode)` is true for (0, 10 SC), (1, 7 SC), and (0, 18 SQ) when the used skill's
  Skills `seqtrans` byte (`+0x012`) is 10 (SC). Then `X = 100 + B_FCR`, capped at 175 and not floored; `r = (spd ·
  X) mod 2³² / 100` unsigned; `+0x4C` and `+0x3C` = `r`. (fn:sub_006216E0_AnimRateIsCast@0x006216E0, 0x00623FCB–0x00624016,
  tbl:Skills.txt:seqtrans)
- [I] A negative `X` (an FCR stat from −119 to −55) wraps the product to a large unsigned value and gives the cap
  `0x7FFF`, not a slow cast: the least such stat is −55 (`B = −101`). (0x00623FE9–0x00624007, `p50b-bp.txt` `EDGE
  cast_factor_negative`)
- [I] No `MinimumCastingDelay` enters: this `charstats.txt` has no such column
  ([CharStats](../../tables/CharStats.md)), and `UNIT_AnimSetRate` reads no delay (`p50b-setrate-callees.txt`,
  fn:UNIT_AnimSetRate@0x00623F50). The skill `delay` is P1.3's.

#### 3.2 Block and get-hit

- [I] Block, (0, 9) or (1, 6): `X = B_FBR + 50`, or `+ 100` under state 101 (`holyshield`, `UNIT_HasState`); `q =
  (spd · X) mod 2³² / 100`; `q < 1 → 1` (`cmp 1; jae`), then the floor and cap. No upper bound on `X`. (0x0062403D–0x00624084,
  fn:UNIT_HasState@0x00639DF0)
- [I] Get-hit, (0, 4) or (1, 3): `X = B_FHR + 50`, the same divide, floor and cap. A negative `X` (FHR from −119 to
  −36) gives the cap, as in § 3.1; so does a block factor below 0 (FBR from −119 to −36; under state 101 `X = B_FBR + 100`,
  so from −119 to −55, as for cast).
  (0x0062409F–0x006240B1, 0x0062435C–0x00624381, `p50b-bp.txt` `EDGE gethit_factor_negative`, `block_factor_negative`)

#### 3.3 Knockback

- [I] (0, 19) or (1, 13): `r = vbase(type, cls, mode)` floored and capped, then `PathSetSpeed(+0x2C, 0x1000)`. For a
  player in mode 19 `vbase` is 0xD5; for a monster it is MonStats `+0x36` (the derived walk rate, § 3.5).
  (0x006240CC–0x00624110, fn:sub_006213D0_AnimMoveBaseRate@0x006213D0)

#### 3.4 Moving

- [I] `AnimRateIsMove(unit; ECX type, EDX mode, ESI class)`: a monster whose MonStats `npc` bit (`+0x00D` bit 0) is set →
  true only for modes 2 and 15; else the entry of the mode in the player table, or the monster table by class (< 410,
  ≥ 410): `move` set → true; `skillMove` set and a used skill whose entry flags (`SkillEntry+0x0C`) have bit 0 (move
  to the target first) and not bit 12 → true. (fn:sub_006214A0_AnimRateIsMove@0x006214A0, `p50b-tables.txt` `MCLS`)
- [I] With no path (`+0x2C` = 0) the function returns and `+0x4C` keeps its value. Else `X = max(B_FRW + stat 67,
  25)` (no cap); `r = (vbase · X) / 100` **signed** (`imul`, `sar 5` with the sign fix) floored and capped; then
  `PathSetSpeed(path, (pbase · X) / 100)` signed, `pbase` = CharStats `+0x040` `<< 8` (player) or MonStats `+0x032`
  `<< 8` (monster) (fn:sub_00621360_AnimPathBaseSpeed@0x00621360). (0x00624128–0x006241D4)
- [I] `vbase` for a player: `(mode == 3) ? 0x65 : 0xD5` (`sub eax, 3; neg; sbb; and 0x70; add 0x65`,
  `p50b-tables.txt` `PLRV`); for a monster MonStats `+0x38` in mode 15 (RN), else `+0x36`.
  (fn:sub_006213D0_AnimMoveBaseRate@0x006213D0, 0x0062140E–0x0062141B)
- [I] **Wrap bound.** `vbase · X` is a 32-bit `imul`; with `vbase ≤ 0x7FFF` it fits for `X ≤ 65 538`
  (`32 767 × 65 538 = 2 147 483 646`) and wraps from `X = 65 539` (`2 147 516 413`) (`p50b-bp.txt` `EDGE
  move_product`, 0x0062416A). The velocity and the path step themselves are P1.3's.

#### 3.5 The monster walk and run base (`MonStatsSpeeds`, at load)

- [I] For each MonStats row `i` with base row `b` = `BaseId` (`+0x002`; out of range → `i`): walk `+0x36` = the
  record `(type 1, class b, mode 2 WL)`'s speed, scaled by `Velocity(i) / Velocity(b)` (`(s16 Velocity(i) × speed) /
  Velocity(b)` unsigned) when `b ≠ i` and `Velocity(b) > 0`; run `+0x38` = row `b`'s `+0x36 / 2` (signed) for `i <
  410`, else the record `(1, b, 15 RN)`'s speed, then scaled the same way by `Run`; each capped at `0x7FFF`. No stock
  row's base comes after it (`p50b-data.txt` `MONSTATS base_later=0`), so row `b`'s `+0x36` is always computed first.
  (fn:sub_00650F00_MonStatsSpeeds@0x00650F00, 0x00650F3E–0x00651015, tbl:MonStats.txt:BaseId, tbl:MonStats.txt:Velocity,
  tbl:MonStats.txt:Run)

#### 3.6 Attack

```c
// 0x006241EF–0x0062430A, trimmed
WeaponListsRelink2(unit, 1);
X = B_IAS + STATS_GetUnitStat(unit, 68);
if (UNIT_CanDualWield(unit)) {
    R = usable(InvGetBodyLocItem(inv, 4));  Lh = usable(InvGetBodyLocItem(inv, 5));
    if (IsType(R, 45) && IsType(Lh, 45)) X += (stat68(R) + stat68(Lh)) / 2 - stat68(R);   // cdq; sub; sar 1
}
if (unit->type == 0 && unit->mode == 18) X -= 30;       // the real type and mode, not the display ones
X = clamp(X, 15, 175);
base = (UNIT_HasStateFlag(unit, 38) && (w = WereformAttackBase(unit))) ? w : spd;
r = (base * X) mod 2^32 / 100;                          // unsigned
```

- [I] `AnimRateIsAttack(unit; ECX mode, EDX type, stack class)`: the mode entry's `attack` set → true; `skillAttack`
  set and a used skill with Skills `UseAttackRate` (`+0x006` bit 3) → true. (fn:sub_00621580_AnimRateIsAttack@0x00621580,
  tbl:Skills.txt:UseAttackRate)
- [I] **The weapons.** `usable` is `sub_0062A4E0_ItemNotDisabled` (an item with flag `0x100`, broken in
  [stats/0001 § 6](../stats/0001-aggregate.md#6-items-equip-requirements-broken-ethereal-sockets), or `0x4000` counts
  as absent). Stats 68 and 93 are `damagerelated` (`p50b-data.txt` `ISC`), so the unit's values hold only the lists
  linked with damage; `WeaponListsRelink2(unit, 1)` links the weapon `SkillSrcDamWeapon(unit, 1)` returns with damage
  and the other hand without (fn:sub_00623C80_WeaponListsRelink2@0x00623C80). The dual-wield term then replaces the
  right hand's 68 by the two hands' mean, also when the linked weapon is the left one (the term subtracts the right
  hand's 68 whichever hand is linked). (0x00624211–0x0062428E, fn:UNIT_CanDualWield@0x006235A0)
- [I] **The sequence term.** A player whose real mode is 18 (a sequence skill with `UseAttackRate`) gets `X − 30`
  before the clamp. (0x00624290–0x0062429B)
- [I] **Shapeshift base.** With state flag 38 (`meleeonly`) on the unit and `w ≠ 0`, `base = w =
  sub_00646170_WereformAttackBase(unit)`: 0 unless the unit is a player with `Unit+0xC8` bit 3 (the transform flag);
  then `D` = 19 without a weapon, else `sub_0062A710_HumanAttackFrames(unit, weapon)` (`D ≤ 0` → `w = 0`), and
  `w = (+0x48 & ~0xFF) / D` signed. `HumanAttackFrames` builds the player's own (not the display) A1 record name with
  the weapon's class code (Items `+0xC0`), takes its frames `F_h` and speed `spd_h` (45 when the name has no record),
  and returns `(F_h << 8) / ((spd_h · (100 + stat93(weapon) + stat68(weapon))) / 100)` (signed, truncating; a zero
  divisor faults). So a shapeshifted attack starts from the speed that makes the form's record last as many frames
  as the human attack with that weapon, before `X` applies. (fn:sub_00646170_WereformAttackBase@0x00646170,
  fn:sub_0062A710_HumanAttackFrames@0x0062A710, 0x0062A7EB–0x0062A822, tbl:States.txt:meleeonly)
- [I] `+0x48` at the call is the current record's length: at a mode start `UNIT_AnimInit` calls the rate before it
  writes `+0x48` (0x0062445D–0x00624473), so its call reads the previous mode's length, but `SUNIT_AnimInit` (every
  server player and monster mode start that schedules) calls it again after `UNIT_AnimInit` has written the new one.
  (fn:UNIT_AnimInit@0x00624390, fn:SUNIT_AnimInit@0x005533D0)
- [I] **Wrap bound.** `base · X` with `X ≤ 175` fits 32 bits for `base ≤ 24 542 670` (`2³² ÷ 175`); the stock speed is
  at most 512 (`p50b-data.txt` `ANIM speed_max=512`, `p50b-bp.txt` `EDGE attack_product`, 0x006242D5). A shapeshift `w` is bounded by `+0x48 ≤ 0x7FFF00`.

#### 3.7 Fixed and default

- [I] `AnimRateIsFixed(EAX type, ECX mode, stack class)` reads the mode entry's `fixed` word: player DT, DD; monster
  DT, DD. `r = spd` floored and capped. (fn:sub_00621630_AnimRateIsFixed@0x00621630, 0x00624320–0x00624332)
- [I] Default (player NU, TN; monster NU; S1–S4 and SQ without a move-first or `UseAttackRate` skill, monsters from
  class 410 for S1–S4): `X = clamp(stat 69, 15, 175)`, `r = (spd · X) / 100` unsigned. (0x00624334–0x00624381)

#### 3.8 The sequence step

- [I] Only cast and attack write `+0x3C`. A sequence in any other branch keeps the step `UNIT_SeqInit` set (0x100), so
  for a monster sequence (mode 14, advanced by `UNIT_AnimAdvance` with `+0x3C`) without `UseAttackRate` the stats do
  not change its pace, and a player sequence (mode 18, scheduled with `+0x3C`) is paced by the rate only through the
  cast or attack branch. (0x00624016, 0x006242FF, fn:UNIT_SeqInit@0x00621260; anim/0001 §§ 7–8)

### 4. Where the stat terms come from

Read only to the depth the rate needs; the writers are other findings' or specs'.

- [I] Base values: a new player `68 ← 100; 67 ← 100; 69 ← 100` ([player/creation](../../specs/player/creation.md),
  fn:PLAYER_InitBaseStats@0x005706D0); a new monster `68 ← 100; 67 ← 75; 69 ← 100` with no difficulty term
  ([monsters/stats](../../specs/monsters/stats.md) B5, fn:sub_00573CB0_MonStatsInit@0x00573CB0); a weapon `68 ← −speed`
  ([items/properties](../../specs/items/properties.md) A4, fn:sub_005563D0_ItemSetBaseDamage@0x005563D0).
- [I] Monster mods: `champion` and `possessed` +20 to 67, `fast` and `fanatic` `clamp(2048 ÷ Velocity − 128, 10, 100)`
  to 67 ([monsters/stats](../../specs/monsters/stats.md) G3, fn:sub_005A1910_UModFast@0x005A1910). They change only
  the moving branch (and, through it, a classic monster's S1–S4).
- [I] Skills and states: through stat lists the aggregate holds — the `aurastat*`/`passivestat*` cells that name 67,
  68, 69 or `item_slow` ([Skills § Timing](../../tables/Skills.md#timing-plan-0050-phase-0)); start 32's list with
  68 = `calc3` (fn:sub_0056E520_SkillAttackRateList@0x0056E520); `SkillPassiveStatList`, which copies a 68 value into
  69 as well (0x005C6E76–0x005C6E81; callers 0x005C9580, 0x005C9CF0, 0x005D9221); chill (state 11) 67, 68, 69 = the cold effect
  (fn:COMBAT_ApplyCold@0x0057AF80, combat/0001). A monster's mode command can also carry a velocity: `MonSetMode`
  calls `sub_005A6380_MonModeVelocity` after `SUNIT_AnimInit` when `MonsterData+0x2C` is set, which writes that
  block's `+0x10` as stat 67 into the unit's `0x4000` list and re-runs the rate (0x005A7DB6–0x005A7DBF,
  fn:sub_005A6380_MonModeVelocity@0x005A6380); the block is the AI's (phase (5)).
- [I] `UNIT_AnimSetRate` takes no game pointer and reads no difficulty, expansion or player-count field: its inputs
  are the unit, its stat lists, its items, its states, the record and the image tables (`p50b-setrate-callees.txt`,
  fn:UNIT_AnimSetRate@0x00623F50).

### 5. Who calls it, and the `UpdateAnimRate` bit

| Site(s) | In | Source path pushed | When |
|---|---|---|---|
| 0x0062443F, 0x00624464, 0x006244C0, 0x006244DE | `UNIT_AnimInit` | `Units.cpp` | every mode change |
| 0x00553435, 0x0055345B | `SUNIT_AnimInit` | `SUnit.cpp` | server mode starts (after `+0x48` is set) |
| 0x0055C454 | `ITEMS_AttachToOwner` | `ItemMode.cpp` | equip |
| 0x005735DB | `MonInitMode` | `Monster.cpp` | a new monster |
| 0x005A63DE | `MonModeVelocity` | `MonsterMode.cpp` | a monster mode command with a velocity |
| 0x0056E56A, 0x005C6EAF | `SkillAttackRateList`, `SkillPassiveStatList` | `Skills.cpp`, `SkillDruid.cpp` | skill stat lists |
| 0x005C6DAF, 0x005CEFAB | `SKILLS_ApplyAuraStats`, `AURA_ApplyToTarget` (0x005CEE4A) | `SkillDruid.cpp`, `SkilPal.cpp` | aura stats |
| 0x005C372C, 0x005C3ED0 | `CurseApplyCb`, `ConfuseApplyCb` | `SkillNec.cpp` | curses (gated, below) |
| 0x005C044F, 0x005C6850 | `StatEv19Slow`, `StatEv27ClayGolemSlow` | `SkillItem.cpp`, `SkillNec.cpp` | slows |
| 0x0057B0CF, 0x0057ADC2 | `COMBAT_ApplyCold`, `ColdEndCb` | `SUnitDmg.cpp` | chill on and off |
| 0x0056E941, 0x005C9461, 0x005D07B2, 0x005D8F31 | `STATE_DefaultRemoveCB`, `SkillDo18RemoveCb`, `HolyFreezeRemoveCb`, `SkillSt38EndCb` | `Skills.cpp`, `SkillSor.cpp`, `SkilPal.cpp`, `SkillBar.cpp` | a state ends |
| 0x0056B732 | `ClampVitalsSetRate` (called from 0x005CEC7B) | `Skills.cpp` | after a vitals clamp |
| 0x00466177, 0x004662DA, 0x004B0D7A, 0x004C21D7, 0x004C7C2A, 0x004D9D57, 0x004D9E47 | client functions | `CUnit.cpp`, `Monster.cpp`, `Item.cpp`, `Skills.cpp`, `PlrSkills.cpp` (all `.\UNIT\` or client `SKILLS`) | client |

(`p50b-calls.txt`: 31 sites; enclosing functions from the padding scan and `re/symbols.csv`, the two without a Ghidra
function, 0x0057AD80 and 0x005D8EF0, being the callbacks that `COMBAT_ApplyCold` pushes at 0x0057B08C and Whirlwind's
start stores at 0x005D91EC)

- [I] **No stat write calls it.** `ITEMS_DetachFromOwner` is not a caller, so unequipping an item leaves the rate
  until the next call (a mode start, typically). (`p50b-calls.txt`; fn:ITEMS_DetachFromOwner@0x0055C730)
- [I] **A second `+0x4C` writer.** `0x00621780(unit, q)` (stdcall, unnamed) stores `q` floored at 0 and capped at
  `0x7FFF` into `+0x4C`, with no record and no stat read (0x00621783–0x006217B1). Its 17 call sites are 16 client
  (`0x004C5662` … `0x004F1827`) and one server, in `sub_005CC2E0_InfernoMissileRange` at `0x005CC387`, on the unit in
  `EBX` whose range `MISSDATA_SetRange` sets next (`0x005CC38E`), a missile. So the only server write outside
  `UNIT_AnimSetRate` and `UNIT_AnimInit` that this scan finds is a missile's. (*2026-10-27, `lane/p50b` review:*
  added; objdump `call 0x621780` over `.text`, 17 sites.)
- [I] **`UpdateAnimRate`** (ItemStatCost `+0x005` bit 1, mask byte `0x006CE26C`) is tested on an ItemStatCost record
  at 5 sites, 4 server: do 30 (`0x005C38F4`) and its per-target helper `0x005C39C0` (`0x005C3A8D`), do 61
  (`0x005C403B`), do 71 Taunt (`0x005D868A`); each sets a word of the state block when any of the row's stats has the
  bit, and the apply callback calls the rate only then (`CurseApplyCb` tests `block+0x0C` at 0x005C371B); the fifth
  is client (`0x004D9E32`). The other 9 loads of that mask byte followed by a `+0x5` test are on 2 MonStats2, 2
  Missiles and 2 Skills records, 1 local record in `sub_00573CB0_MonStatsInit` (`0x00574141`), and 2 client records
  the scan does not identify (`0x004AEB4E`, `0x004AF024`) (`p50b-uar.txt`, `SCAN uar sites=14 -=2 ItemStatCost=5
  Missiles=2 MonStats2=2 Skills=2 local=1`; *2026-10-27, `lane/p50b` review:* breakdown corrected). (fn:sub_005C37C0_SkillDo30Curse@0x005C37C0,
  fn:sub_005C3F20_SkillDo61Confuse@0x005C3F20, fn:sub_005D8570_SkillDo71Taunt@0x005D8570)

### 6. Does a rate change apply to a mode in progress? (P1.1 review ruling (a))

- [I] **Scheduled modes keep their events.** The frame events and the mode end are queued once by
  `SUNIT_ScheduleModeEvents` at the start, from `r` at that moment (anim/0001 § 7). `UNIT_AnimSetRate`'s 19 direct
  callees include neither `UnitQueueEvent` (0x005417D0) nor `SUNIT_CancelModeEvents` (0x00553990), and the helpers
  read in § 3 queue nothing; so a re-call (equip, an aura, a curse, chill) during a scheduled attack, cast, get-hit or
  block changes `+0x4C` but moves no queued event. Only the § 7.1 reschedules of anim/0001 rebuild the list, reading
  `+0x4C` at their call. (`p50b-setrate-callees.txt`, fn:SUNIT_ScheduleModeEvents@0x005539B0)
- [C] (ADR-0015) **The advance reads the rate at its call.** The `advance` family runs
  `UNIT_AnimAdvance` on a monster unit (type 1, no sequence, a record with random event bytes or none) twice per pair,
  the second call on the first's resulting frame with a different rate: 2 400 calls, 0 mismatches (frame `+0x44`, event
  byte `+0x4E`, length `+0x48` unchanged), 0 stops, no read outside the case memory; 490 calls wrap the length; event
  bytes 1–4 taken 205 times; of the 1 120 pairs whose rate changed, 1 114 would mismatch under the old rate. Not
  covered: the sequence branch (`+0x30` ≠ 0, which steps by `+0x3C`), and a player or a start frame other than 0.
  (fn:UNIT_AnimAdvance@0x00623E00, run:2026-10-27-anim-rates-emu `advance`, `p50b-emu/check.txt`)
- [I] Hence the second case of ruling (a): an every-frame monster (anim/0001 § 10: walk, run, knockback, sequence,
  and the `*mv` attack and skill modes) re-computed in the middle of its mode advances at the new rate from the next
  frame on. (fn:UNIT_AnimAdvance@0x00623E00, fn:sub_005A6B10_MonModeEveryFrame@0x005A6B10)
- [I] The length does not follow: `+0x48` stays the start's, so a faster rate ends an every-frame mode in fewer
  advances only through the frame position, as the advance's `UNIT_AnimAtEnd` test reads it
  (fn:UNIT_AnimAtEnd@0x006217C0).

### 7. The breakpoint function (derived, not copied)

- [I] From anim/0001 § 7 (`T` the start frame, `L = 256 F`, steps `256 S + k r < L`): `n(r) = max(2, ⌈256 (F − S) /
  r⌉)` for `F > S` (`T + 2` otherwise); frame `f ≥ S` fires at `T + k_f`, `k_f = max(1, ⌈256 (f − S) / r⌉)`, only if
  `k_f ≤ N = ⌈256 (F − S) / r⌉ − 1`. When the first step already reaches `L` (`r ≥ 256 (F − S)`), no frame event fires,
  not even frame `S`'s. (fn:SUNIT_ScheduleModeEvents@0x005539B0, 0x00553A0C–0x00553AF1)
- [I] With `r = ⌊spd · X / 100⌋` (every branch but moving and knockback; block's minimum 1 aside), `n ≤ m ⇔ r ≥ R_m =
  ⌈256 (F − S) / m⌉ ⇔ X ≥ ⌈100 R_m / spd⌉`; so the breakpoints of a record are the least factors
  `X_m = ⌈100 ⌈256 (F − S) / m⌉ / spd⌉`, for each length `m` that `[X_lo, X_hi]` reaches (15..175 for attack and
  default; 100.. 175 for cast with a non-negative FCR; 50 upward for get-hit and block, 100 upward under Holy Shield).
  The item stat for a bonus `y = X − base` (`base` 100 cast, 50 get-hit and block, 100 under Holy Shield) is the least
  `s` with `⌊k s / (k + s)⌋ ≥ y`, i.e. `s = ⌈k y / (k − y)⌉` for `0 < y < k`. For attack the factor is `B_IAS + stat
  68 (+ terms)`, so the IAS needed is the least `s` with `⌊120 s / (120 + s)⌋ ≥ X_m − stat 68 (− terms)`.
  (fn:UNIT_AnimSetRate@0x00623F50, fn:sub_00621740_AnimRateBonus@0x00621740)
- [I] `tools/anim_rates.py bp` checks these closed forms against the loop over all 350 stock (frames, speed) pairs
  with `S` 0, 1, 2 and `X` 15..175, and against brute-force minima (`CHECK … bad=0` ×3); this checks the algebra, not
  the game. Worked examples (stock records, `p50b-bp.txt` `EX`, `EXBP`, `EXSTAT`): `SOSCHTH` (14 frames, speed 256,
  event at frame 7): FCR 0, 9, 20, 37, 63, 105, 200 give lengths 14, 13, 12, 11, 10, 9, 8 (the last at the cap 175, any FCR
  ≥ 200 the same); `PAGHHTH` (5 frames): FHR 0, 7, 15, 27, 48, 86, 200 give 10, 9, 8, 7, 6, 5, 4; `AMA11HS` (16 frames, start 2,
  event at 10) at `X` 100 lasts 14 frames with its event at `T + 8`. (fn:SUNIT_ScheduleModeEvents@0x005539B0,
  `p50b-bp.txt`)

## Draws

- [I] None. `UNIT_AnimSetRate` and its helpers read in § 3 call no RNG function (`p50b-setrate-callees.txt`; the
  helpers' decompiles); the rate is a pure function of the unit's state. The chaining reading of anim/0001 § 11
  stands: a rate change is an event kind with no draw. (fn:UNIT_AnimSetRate@0x00623F50)

## Event kind: rate change (ADR-0014)

- [I] Inputs: the unit's display type, class and mode, its record, stats 67, 68, 69, 93, 96, 99, 102, 105 (full
  values), the two hands' items, states 101 and flag 38, the used skill's `seqtrans`, `UseAttackRate` and move-first
  flag, the path. Outputs: `+0x50`, `+0x4C`, `+0x3C` (cast, attack), the path speed (moving, knockback). No draw, no
  queued event. Phase 2 logs it at `UNIT_AnimSetRate`'s exit (unit, branch, `+0x4C`, `+0x3C`) at each of the 24 server
  sites, and compares the next schedule or advance. (fn:UNIT_AnimSetRate@0x00623F50)

## Data touched

- Tables: tbl:ItemStatCost.txt:Stat, tbl:ItemStatCost.txt:UpdateAnimRate, tbl:ItemStatCost.txt:damagerelated,
  tbl:ItemStatCost.txt:fMin, tbl:Skills.txt:seqtrans, tbl:Skills.txt:UseAttackRate, tbl:Skills.txt:passivestat1,
  tbl:MonStats.txt:npc, tbl:MonStats.txt:BaseId, tbl:MonStats.txt:Velocity, tbl:MonStats.txt:Run,
  tbl:CharStats.txt:WalkVelocity, tbl:States.txt:meleeonly, tbl:Weapons.txt:speed; `animdata.d2` (`+0x08` frames,
  `+0x0C` speed, `+0x10` events).
- Unit: struct:Unit+0x2C, struct:Unit+0x3C, struct:Unit+0x48, struct:Unit+0x4C, struct:Unit+0x50,
  struct:Unit+0x60, struct:Unit+0xC8 (bit 3); `SkillEntry+0x0C` (bits 0, 12).

## Dead ends

- Ghidra shows the helpers with no parameters (register arguments); the argument registers above are from objdump at
  each call (0x00623FBD, 0x00624113, 0x006241D7, 0x0062430D, 0x00624158, 0x006241A7).
- Ghidra's decompile of `sub_0062A710_HumanAttackFrames` drops the return value into the stack-cookie call; the
  division is at 0x0062A81E–0x0062A822.
- A whole-function emulation of `UNIT_AnimSetRate` is not possible with EmuTrace: `UNIT_AnimSetRecord` reaches
  `wsprintfA` (an import) through `COMPOSIT_BuildCofName`; only the bonus and the advance are emulated.

## Open questions

- [L] `SkillEntry+0x0C` bit 12 (`0x1000`), which turns a move-first skill's mode back to the default branch, is not
  named by the code read.
- [L] Item flag `0x4000` (`ItemData+0x18`), which makes a hand count as empty for the dual-wield term, is not named.
- ~~[L] Whether any stock property or state gives a rate stat a value at or below −36 (the wrap of § 3.1–3.2) or −120
  (the divide fault of § 2); not surveyed here.~~ *2026-10-27 (plan 0050 P1.3, `lane/p50d`):* closed by
  [ItemStatCost § Timing](../../tables/ItemStatCost.md#timing-plan-0050-phase-0) (`lane/a50t`): the 353 stock property
  blocks that write stats 93, 96, 99, 102 or 105 all have `min`/`max` ≥ 3, and no Skills, States, Misc or `op stat`
  cell names one of them, so no stock source makes a rate-bonus stat negative; the wraps of §§ 3.1–3.2 and the
  divide fault of § 2 are not reached by stock data.
- [L] The caller of `ClampVitalsSetRate` at 0x005CEC7B lies after `sub_005CE9F0_SkillDo150Smite` in the image and its
  own function is not delimited; not read.
- [L] What the client does with its seven calls (the displayed animation) is presentation (plan 0050 § Open questions).
