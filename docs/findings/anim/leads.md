# anim — community claims staged for the Phase 1b cross-check (plan 0050)

> **Question:** what do the community breakpoint tables and formulas claim about attack, cast, hit-recovery and
> block frames, skill delays against the animation, and walk, run and Charge speed, so that each claim can get one
> verdict against the P1.2 and P1.3 findings?
> **Status:** staged, no verdicts (plan 0050 Phase 1b part 1, `lane/p50c`, 2026-10-27). Part 2 gives each claim one
> verdict (`held` / `held with refinement` / `contradicted` / `not covered`) against P1.2 (`anim/0002-rates`) and
> P1.3 (`anim/0003-movement-gates`) after P1.3's review, and moves the verdicts into those findings' *Leads used*.
> **Blind rule:** this file is leads only. Every claim here is `[L]` and stays `[L]`: agreement promotes nothing
> (reverser skill, step 7). A lane running P1.2 or P1.3 does not read the claims of its batch here before its own
> behavioural claims are written from the code (step 2, blind first); it may read § 1 to learn which sources exist.
> No claim here was compared with our binary: this lane opened no Ghidra, ran no harness and read no P1 work.

## 1. Sources and the versions they describe

| Source | Version it describes | Read |
|---|---|---|
| `src:maxroll-d2r-breakpoints` | Diablo II: Resurrected, patch 2.4 and later (page 2026-02-10) | in full |
| `src:maxroll-d2r-attack-speed` | Diablo II: Resurrected, patch 2.4 and later (page 2026-02-10) | in full |
| `src:basin-wiki-animation` | LoD 1.10 and later, D2R differences marked inline (revisions 2012–2026) | the nine pages named in the registry |
| `src:basin-runwalk-thread` | before 1.10 (posts of February 2003, 1.09 era), tested on modded CharStats | in full |
| `src:basin-movement-clarification` | 1.13 era (2012), video-timed tests on stock data | in full |
| `src:pd-breakpoints` | no patch named (page 2022), classic-era tables | in full |

Not read: `src:lurker-movement-thread`, `src:gustafsson-movement-speed` (fetch refused; registered so a later lane does not
search for them again). No community source was found for **monster** frame counts, monster rates or the `fast`
mod's timing, for object operate frames or for `monseq` sequences: those parts of P1.2 and P1.3 have no claim to
compare, and part 2 records them as having no lead. No page that reproduces game code was met. The animation-data
format guides (`animdata.d2`) are left to the archivist's Phase 0 (plan 0050 P0 owns the format).

Since 1.14d is neither 1.09 nor D2R, a claim from a D2R or a pre-1.10 source that the code contradicts is a
version difference until shown otherwise. Part 2 says so in the verdict and does not file it as a community error.

## 2. How a claim is written

One row per claim that a code reading can decide. **Id** is stable (part 2 cites it). **Batch** is where the
claim is decided: P1.2 (rates), P1.3 (movement and the gates), or P0 (a table or `animdata.d2` value the archivist's
survey prints, which part 2 reads from the P0 docs). **Verdict** is empty until part 2. A formula is copied as the
source writes it; `[x]` is floor and `{x}` is ceiling in the Maxroll pages, written here as `floor()` and `ceil()`.
Where two sources disagree, both readings are one row each and the conflict is named in both.

The breakpoint tables are not copied: each table claim names its source table, and the consistency of the tables
with their own formula is checked by `tools/anim_leads_check.py` (§ 9). That check compares two community claims with
each other; it is not a check of the game.

## 3. Rates shared by every mode (R)

| Id | Claim | Source | Batch | Tag | Verdict |
|---|---|---|---|---|---|
| R1 | The game runs 25 frames per second; every mode length is a whole number of frames; a rate gain shows only when it removes a whole frame (hence breakpoints). | `src:maxroll-d2r-breakpoints`, `src:pd-breakpoints` | P1.2 | `[L]` | |
| R2 | A breakpoint is met at the listed value or above ("values must meet or exceed"). | `src:pd-breakpoints` | P1.2 | `[L]` | |
| R3 | Item IAS, FCR, FHR and FBR are each diminished as `E = floor(120·x/(120 + x))` before use. | `src:maxroll-d2r-breakpoints`, `src:maxroll-d2r-attack-speed`, `src:basin-wiki-animation` (Attack speed) | P1.2 | `[L]` | |
| R4 | EFCR is capped at 75, so FCR above 200 has no effect. (`E(200) = 75` exactly.) | `src:maxroll-d2r-breakpoints` | P1.2 | `[L]` | |
| R5 | No cap is stated for EFHR, EFBR or EIAS; the FHR and FBR tables of `src:pd-breakpoints` list rows up to 600. | `src:maxroll-d2r-breakpoints`, `src:pd-breakpoints` | P1.2 | `[L]` | |

## 4. Attack (A)

| Id | Claim | Source | Batch | Tag | Verdict |
|---|---|---|---|---|---|
| A1 | Attack frames = `ceil(AnimLength·256 / floor(AnimSpeed·(AnimRate + SIAS + EIAS − WSM)/100)) − 1`, with `AnimRate` = 100 and `AnimSpeed` 256 for a player; the `− 1` is because the first and last frame are the same. Example: an Amazon's 12-frame unarmed attack takes 11 frames at no IAS. | `src:maxroll-d2r-attack-speed` | P1.2 | `[L]` | |
| A2 | Attack frames = `ceil((FramesPerDirection − 1 − StartingFrame)·256 / AnimRate)`, `AnimRate = AnimationSpeed·(100 + percentage modifiers)/100`. Conflicts with A1 in where the `− 1` sits (inside or outside the ceiling) whenever the rate is not 256; both match at no IAS. | `src:basin-wiki-animation` (Attack speed) | P1.2 | `[L]` | |
| A3 | `StartingFrame` skips the first frames of an animation: 1 or 2 for the Amazon's and Sorceress's melee A1 classes, 0 elsewhere. | `src:basin-wiki-animation` (Attack speed) | P0, P1.2 | `[L]` | |
| A4 | Per class, mode A1 and weapon class, the animation has the frames per direction, speed (256ths of a frame), starting frame and action frame of the Basin table: 10 Assassin rows, 8 Amazon, 12 Barbarian (with `1JS`, `1JT`, `1SS`, `1ST`), 8 each for Druid, Necromancer, Paladin and Sorceress, and 7 kick (`KK`) rows. Illustrative rows: `AM A1 HTH 13 256 1 8`, `AI A1 HT1 11 208 0 6`, `BA A1 2HS 18 256 0 8`. Part 2 re-fetches the page and compares it row by row with the P0 `animdata.d2` survey. | `src:basin-wiki-animation` (Attack speed) | P0, P1.2 | `[L]` | |
| A5 | When dual wielding, only the primary weapon's IAS counts towards EIAS. | `src:maxroll-d2r-attack-speed`, `src:basin-wiki-animation` (Attack speed) | P1.2 | `[L]` | |
| A6 | Dual-wield WSM: `(L + R)/2` when the left-slot weapon is primary; `(L + R)/2 − L + R` when the right-slot weapon is primary. | `src:maxroll-d2r-attack-speed`, `src:basin-wiki-animation` (Attack speed) | P1.2 | `[L]` | |
| A7 | WSM is a per-base-item value from −60 to 20, positive slower, subtracted from the rate; the Basin's per-base lists (for example Axe 10, Hand Axe 0, Military Pick −10) are the Weapons `speed` column. | `src:maxroll-d2r-attack-speed`, `src:basin-wiki-animation` (Weapon speed) | P0, P1.2 | `[L]` | |
| A8 | SIAS (skill IAS) is added undiminished: Burst of Speed, Fanaticism, Werewolf and Frenzy raise it; Decrepify, Holy Freeze, cold length and Slows Target lower it; the slow on a character is capped at 50 %. The Basin's "required EIAS = target − skill EIAS − chill − Slows Target + WSM" says the same. | `src:maxroll-d2r-attack-speed`, `src:basin-wiki-animation` (IAS intro) | P1.2 | `[L]` | |
| A9 | Throwing a throwing weapon with a throw skill costs a flat 30 off the rate, except for the Barbarian. | `src:maxroll-d2r-attack-speed` | P1.2 | `[L]` | |
| A10 | Sequence skills (Blades of Ice, Charge, Claws of Thunder, Fists of Fire, Impale, Jab, Leap Attack) use `ceil(AnimLength·256 / floor(AnimSpeed·(AnimRate + SIAS + EIAS − (WSM + 30))/100))`: no `− 1` and WSM + 30. Leap Attack and Charge ignore WSM. | `src:maxroll-d2r-attack-speed` | P1.2 | `[L]` | |
| A11 | Rollback skills (Dragon Talon, Fend, Fury, Strafe, Zeal) give each hit of a sequence its own length (first and last full, middle ones partial). Fend: one target, one attack of normal length; two targets, the first-frame plus last-frame lengths; 3–12 targets, the follow-up lengths. | `src:maxroll-d2r-attack-speed`, `src:basin-wiki-animation` (Amazon attack speed, Fend) | P1.2 | `[L]` | |
| A12 | Double Throw: `Vinc = 70 + (WSM1 + WSM2)/2 + SIAS + EIAS`, `fpa = ceil(256·12 / floor(256·Vinc/100)) / 2`. Double Swing: `Vinc = 120 + …`, 17 frames. `Vinc` is clamped to 15–175. | `src:maxroll-d2r-attack-speed` | P1.2 | `[L]` | |
| A13 | Frenzy: `Vinc1 = 70 + SIAS + EIAS − WSM1st`, `Vinc2 = 70 + SIAS + EIAS − WSM2nd`, `WSM1st = P + S − (P + S)/2`, `WSM2nd = 2S − (P + S)/2`; `fpa1 = ceil(256·9 / floor(256·Vinc1/100)) − 1`, `fpa2 = ceil(256·17 / floor(256·Vinc2/100))`. If the first swing misses, the second swing uses the first weapon's speed. | `src:maxroll-d2r-attack-speed` | P1.2 | `[L]` | |
| A14 | Werewolf and Werebear: `AnimSpeed = floor(256·FramesNeutral / Delay)`, `Delay = floor(256·FramesChar / floor((100 + WIAS − WSM)·CharSpeed/100))` with `FramesNeutral` 13 (wolf) or 12 (bear), `FramesChar` 15, `CharSpeed` 256, weapon IAS undiminished, then A1. The "faster of this and A1" rule is patch 2.4 (D2R only). | `src:maxroll-d2r-attack-speed` | P1.2 | `[L]` | |
| A15 | Trang-Oul's vampire form attacks with `AnimLength` 14 and `AnimSpeed` 176; Delirium's fetish form with 12 and 256. | `src:maxroll-d2r-attack-speed` | P0, P1.2 | `[L]` | |

## 5. Cast (C)

| Id | Claim | Source | Batch | Tag | Verdict |
|---|---|---|---|---|---|
| C1 | Cast frames = `ceil(256·Base / floor(Speed·(100 + EFCR)/100) − 1)`; Lightning and Chain Lightning drop the `− 1`. | `src:maxroll-d2r-breakpoints` | P1.2 | `[L]` | |
| C2 | Casting base and speed: Amazon 20/256, Assassin 17/256, Barbarian 14/256, Druid 16/208, werewolf 16/229, werebear 16/228, Necromancer 15/256, vampire form 15/160, Paladin 16/256, Sorceress 14/256, Lightning and Chain Lightning 19/256, Act 3 mercenary 18/256. | `src:maxroll-d2r-breakpoints` | P0, P1.2 | `[L]` | |
| C3 | The FCR tables of both sources (12 per source: Amazon, Assassin, Barbarian, Druid human, wolf and bear, Necromancer human and vampire, Paladin, Sorceress other spells and Lightning, Act 3 mercenary) agree with each other. With C1 and C2 they reproduce 8 of the 12; the Druid's three forms are reproduced only with base 15, the Necromancer's only with base 16 (§ 9). C2's Druid and Necromancer rows and the tables cannot both hold. | `src:maxroll-d2r-breakpoints`, `src:pd-breakpoints` | P1.2 | `[L]` | |
| C4 | Cast action frame = `ceil(BaseActionFlag·256 / floor(Speed·(100 + EFCR)/100))`; bases: Amazon with a bow 10, no weapon 11, crossbow or two-handed sword 12, two-handed staff, hammer, axe, polearm, spear, knife or javelin 13; Assassin 9; Barbarian 9; Druid 10, werewolf 8, werebear 9; Necromancer 8, vampire form 5; Paladin 9; Sorceress 7; Act 3 mercenary 7. | `src:maxroll-d2r-breakpoints` | P1.2, P1.3 | `[L]` | |
| C5 | The Amazon's cast length does not depend on her weapon (19 frames at 0 FCR with any weapon); only her action frame does (C4). | `src:maxroll-d2r-breakpoints` | P1.2 | `[L]` | |
| C6 | A cast is interrupted by hit recovery, by a stun and by a block. | `src:maxroll-d2r-breakpoints` | P1.3 | `[L]` | |
| C7 | The Act 1 mercenary's Inner Sight runs on her attack rate; FCR has no effect on it. | `src:maxroll-d2r-breakpoints` | P1.2 | `[L]` | |

## 6. Skill delays against the animation (D)

| Id | Claim | Source | Batch | Tag | Verdict |
|---|---|---|---|---|---|
| D1 | A skill's delay starts at the action frame, so the interval between casts is the action frame plus the delay; Immolation Arrow fired continuously repeats at its 25-frame delay plus the action frame. | `src:maxroll-d2r-breakpoints`, `src:basin-wiki-animation` (Cast rate; Amazon attack speed) | P1.3 | `[L]` | |
| D2 | The delay runs after the whole cast: a 1-second delay on an 11-frame cast gives 36 frames per use (11 + 25). Conflicts with D1. | `src:pd-breakpoints` | P1.3 | `[L]` | |
| D3 | In LoD every delay is global: while any delay runs, no skill with a delay can be used (local delays are D2R patch 2.4). | `src:basin-wiki-animation` (Cast rate) | P1.3 | `[L]` | |
| D4 | LoD delays in seconds: Poison Javelin 0.6, Plague Javelin 4, Immolation Arrow 1, Valkyrie 6; Shock Web 0.6, Blade Sentinel 2, Shadow Warrior 6, Dragon Flight 1, Shadow Master 6; Werewolf 1, Firestorm 0.6, Werebear 1, Molten Boulder 2, Fissure 2, Volcano 4, Armageddon 6, Hurricane 6; Fist of the Heavens 1; Fire Wall 1.4, Meteor 1.2, Blizzard 1.8, Hydra 1.6, Frozen Orb 1. Nothing shortens a delay. | `src:basin-wiki-animation` (Cast rate) | P0, P1.3 | `[L]` | |
| D5 | A delay skill cast by a chance-to-cast item sets no skill delay, but an 11-frame delay from the action frame during which no active skill can be used (belt scrolls still can); it does not interrupt an attack sequence, and the last chance-to-cast in a sequence sets it. | `src:basin-wiki-animation` (Cast rate, citing forum tests) | P1.3 | `[L]` | |

## 7. Hit recovery, stun and knockback (H)

| Id | Claim | Source | Batch | Tag | Verdict |
|---|---|---|---|---|---|
| H1 | Hit-recovery frames = `ceil(256·Base / floor(Speed·(50 + EFHR)/100) − 1)`. | `src:maxroll-d2r-breakpoints` | P1.2 | `[L]` | |
| H2 | Hit base and speed: Amazon 6/256, Assassin 5/256, Barbarian 5/256, Druid with a one-handed swinging weapon 7/248, Druid otherwise 7/256, werewolf 4/256, werebear 5/184, Necromancer 7/256, vampire form 4/136, Paladin with a spear or staff 5/192, Paladin otherwise 5/256, Sorceress 8/256, mercenaries Act 1 6, Act 2 8, Act 3 9, Act 5 5 (all 256). | `src:maxroll-d2r-breakpoints` | P0, P1.2 | `[L]` | |
| H3 | The FHR tables of both sources (16 cases) are reproduced by H1 and H2 up to each table's last row (§ 9); `src:pd-breakpoints` lists further rows (for example Amazon 600 → 3 frames). | `src:maxroll-d2r-breakpoints`, `src:pd-breakpoints` | P1.2 | `[L]` | |
| H4 | Which weapons count as "one-handed swinging" for the Druid's FHR and the Amazon's FBR: axes, clubs, maces, scepters, swords, throwing axes and wands (Maxroll FHR); the same with hammers and without wands (Maxroll FBR note); one-handed axes, clubs, one-handed maces, orbs, scepters, one-handed swords, two-handed swords held in one hand, throwing axes and wands (PureDiablo). The three lists differ; the weapon classes the code tests decide. | `src:maxroll-d2r-breakpoints`, `src:pd-breakpoints` | P1.2 | `[L]` | |
| H5 | Hit recovery is not entered when the damage kills, the target is frozen, the damage is poison only, or the damage is below 1. Otherwise `T = maxLife / divisor`, the divisor by the attack's hit class (2, 6, 10, 11 → 8; 4, 8 → 32; 5 → 64; otherwise 16, the hit class "in Missile.txt"): damage below T, none; below 2T, a 1-in-2 roll then a 3-in-4 roll; below 4T, a 3-in-4 roll; 4T and above, always. Some units are immune. (The page writes the last test both as "> 4T" and "≥ 4T".) | `src:maxroll-d2r-breakpoints` | P1.3 | `[L]` | |
| H6 | Hit recovery is triggered by any hit that takes more than 1/12 of the character's maximum life. Conflicts with H5. | `src:pd-breakpoints` | P1.3 | `[L]` | |
| H7 | Hit recovery interrupts a cast, an attack, walking, running and standing; the unit can act on nothing until it ends, and it can be re-entered with no cooldown ("stun lock"). | `src:maxroll-d2r-breakpoints`, `src:pd-breakpoints` | P1.3 | `[L]` | |
| H8 | A stunned player is not incapacitated but enters hit recovery on every hit while the stun lasts, even with no damage. | `src:basin-wiki-animation` (Stun length) | P1.3 | `[L]` | |
| H9 | Stun length has a 10-second ceiling and no penalties; the most recent stun replaces the running one (a 2-second stun 2 s into a 10-second one gives 4 s in all). Champions, uniques and superuniques are stunned only 1 time in 10; bosses and a list of static units never. | `src:basin-wiki-animation` (Stun length) | P1.3 | `[L]` | |
| H10 | Knockback moves the target up to three sub-tiles from the attacker (sometimes one, two or none) and puts it into hit recovery; not when the target is frozen or killed; it needs a knockback mode on the target, and the chance depends on its size. | `src:basin-wiki-animation` (Knockback) | P1.3 | `[L]` | |

## 8. Block (B)

| Id | Claim | Source | Batch | Tag | Verdict |
|---|---|---|---|---|---|
| B1 | Block frames = `ceil(256·Base / floor(Speed·(50 + EFBR)/100) − 1)`; Holy Shield adds 50 to EFBR. | `src:maxroll-d2r-breakpoints` | P1.2 | `[L]` | |
| B2 | Block base and speed: Amazon 3/256, Amazon with a one-handed swinging weapon 3/88, Assassin 3/256, Barbarian 4/256, Druid 6/256, werewolf 5/256, werebear 5/200, Necromancer 6/256, Paladin 3/256, Sorceress 5/256. | `src:maxroll-d2r-breakpoints` | P0, P1.2 | `[L]` | |
| B3 | The FBR tables of both sources (11 cases) are reproduced by B1 and B2 up to each table's last row (§ 9). | `src:maxroll-d2r-breakpoints`, `src:pd-breakpoints` | P1.2 | `[L]` | |
| B4 | The Assassin's Weapon Block uses the block mode and the same FBR values as a shield block. | `src:maxroll-d2r-breakpoints`, `src:pd-breakpoints` | P1.3 | `[L]` | |
| B5 | A block is possible only in melee combat or while walking, not while running; the unit can do nothing during the block, and blocks repeat with no cooldown. | `src:pd-breakpoints`, `src:maxroll-d2r-breakpoints` | P1.3 | `[L]` | |

## 9. The tables against their own formulas (kept check)

`tools/anim_leads_check.py` (sha256 `331eb0f0…`) holds the 39 table cases of `src:maxroll-d2r-breakpoints` and
`src:pd-breakpoints` as transcribed in this session and the formulas C1, H1 and B1 with the bases of C2, H2 and B2.
Output `workspace/logs/anim-leads/p50c-leads-check.txt` (`b185e780…`, manifest `workspace/logs/anim-leads/manifest.sha256`):

```
SUMMARY anim_leads cases=39 agree=70 differ=8 alt_base_found=8
```

78 comparisons (39 cases × 2 sources): 70 agree, 8 differ. The 8 are the FCR tables of the Druid (human, wolf,
bear) and the Necromancer (human) in both sources; each is reproduced with another base (15 and 16, the `ALT` lines).
This is C3. It says nothing about the game: part 2 decides C2 and C3 against the P1.2 reading and the P0 data.

## 10. Movement (M)

| Id | Claim | Source | Batch | Tag | Verdict |
|---|---|---|---|---|---|
| M1 | Every class has CharStats `WalkVelocity` 6 and `RunVelocity` 9. | `src:basin-runwalk-thread`, `src:basin-wiki-animation` (Walk/run speed) | P0 | `[L]` | |
| M2 | Walk speed = `max(WB·(100 + Speed)/100, WB/4)`; run speed = `max(RB + WB·Speed/100, WB/4)`, so the run gains only the walk's share of a bonus (+100 % adds 6 to the run's 9). | `src:basin-wiki-animation` (Walk/run speed), `src:basin-runwalk-thread`, `src:basin-movement-clarification` | P1.3 | `[L]` | |
| M3 | The velocities are per second: 6 and 9 "tile units" (sub-tiles) per second (2003 tests); 6 and 9 yards per second, a yard being a sub-tile corner to corner, 32 × 16 pixels (2012 tests over 25 frames). Part 2 compares only the per-frame step in the code's units; the unit naming is the sources'. | `src:basin-runwalk-thread`, `src:basin-movement-clarification`, `src:basin-wiki-animation` (Walk/run speed) | P1.3 | `[L]` | |
| M4 | Item FR/W is diminished as `EFRW = floor(150·FRW/(150 + FRW))` (rounded down, 2003); skill bonuses, slows and the armour penalty are added undiminished. | `src:basin-wiki-animation` (Faster Run/Walk), `src:basin-runwalk-thread` | P1.3 | `[L]` | |
| M5 | `Speed` is the sum of: EFRW; Burst of Speed, Frenzy, Increased Speed, Feral Rage, Vigor (each `min(a + floor(b·floor(110·lvl/(lvl + 6))/100), cap)`); body armour and shield speed 0/−5/−10 each (the Armor `speed` column); cold length −50 for a player (monsters by their own value); Holy Freeze; Decrepify −50; Slows Target. | `src:basin-wiki-animation` (Walk/run speed), `src:basin-runwalk-thread` | P1.3 | `[L]` | |
| M6 | Slows Target lowers a player's speed by its percentage, capped at −50 (a 2012 run used ST 25 % as −25). | `src:basin-wiki-animation` (Walk/run speed, Slows Target), `src:basin-movement-clarification` | P1.3 | `[L]` | |
| M7 | Slows Target of any percentage gives −100 % to walk and run (1.09-era test). Conflicts with M6; a version difference is possible. | `src:basin-runwalk-thread` | P1.3 | `[L]` | |
| M8 | Slows Target caps: 90 % on normal and minion monsters and pets, 50 % on players, mercenaries, champions, uniques, superuniques and bosses; with cold, Decrepify and Holy Freeze no unit falls below 15 % attack rate or 25 % velocity. It lasts about 30 s; from separate units the first percentage sets velocity and the most recent sets attack rate. | `src:basin-wiki-animation` (Slows Target) | P1.2, P1.3 | `[L]` | |
| M9 | The final speed keeps its fraction (not rounded to a whole number per second). | `src:basin-runwalk-thread` | P1.3 | `[L]` | |
| M10 | With `WalkVelocity` 0 a character never moves; negative values walk backwards (modded data, not stock-reachable). | `src:basin-runwalk-thread` | P1.3 | `[L]` | |
| M11 | `effective rw = skill FRW + EFRW + RunVelocity·100/WalkVelocity − 100 − armour speed`, floored at 15; `velocity1 = effective rw · factor / 100` with factor 213 for walk and town walk and 65 for run; `velocity2 = WalkVelocity·256·effective rw / 100` (Hammerman, 1.09; how either is used "I don't know"). | `src:basin-runwalk-thread` | P1.3 | `[L]` | |
| M12 | Charge: speed `RB·(1 + skill bonus + armour)·150 %`, item FR/W not applied (2003). | `src:basin-runwalk-thread` | P1.3 | `[L]` | |
| M13 | Charge: speed `RB·(1 + skill bonus + armour) + 1.5·RB` (22.5 yards per second at base), item FR/W not applied, the bonus floored at −50 % at the start, normal run speed when a slow lands during the charge; 8–9 frames between consecutive charges. Conflicts with M12. | `src:basin-movement-clarification`, `src:basin-wiki-animation` (Walk/run speed: FR/W not on Charge) | P1.3 | `[L]` | |
| M14 | Shape and state base speeds: Delirium's fetish walks and runs at 6, Trang-Oul's vampire form at 9 (minimum 2.25), werewolf and werebear at the class's 6 and 9. | `src:basin-wiki-animation` (Walk/run speed) | P0, P1.3 | `[L]` | |

## 11. Counts

61 claims: R 5, A 15, C 7, D 5, H 10, B 5, M 14, counted with
`grep -cE '^\| [RACDHBM][0-9]+ \|' docs/findings/anim/leads.md` (61; per letter with `^\| R[0-9]+ \|` and so on).
None for monster or object timing (§ 1). Conflicts named in the rows: A1/A2, C2 against C3 (bases against tables),
D1/D2, H4 (three weapon lists), H5/H6, M6/M7, M12/M13.
