# Animation experiments

Runtime records for [anim/0001](0001-modes-frames.md) and the later animation findings (plan 0050 Phase 2). Harness
and evidence rules: ADR-0003, ADR-0004, ADR-0011, ADR-0013, ADR-0014, ADR-0015, ADR-0021;
[tooling](../../../.claude/skills/reverser/references/tooling.md),
[harness-play](../../../.claude/skills/reverser/references/harness-play.md).

Harness runs (plan 0050 Phase 2): [run:2026-10-27-anim](#run2026-10-27-anim), closed (two lane runs); [run:2026-10-27-anim-p2](#run2026-10-27-anim-p2), part 2 (in review). Emulated runs
(ADR-0015, no wine, nothing native): [run:2026-10-27-anim-rates-emu](#run2026-10-27-anim-rates-emu).

## run:2026-10-27-anim

**Status: closed.** `lane/p50e`, two lane runs of plan 0050 Phase 2 (the first rotated at its checkpoint, 31
sessions; the second added batch 5, 24 sessions). The findings' run sections ([anim/0001](0001-modes-frames.md#plan-0050-phase-2-run2026-10-27-anim),
[anim/0002](0002-rates.md#plan-0050-phase-2-run2026-10-27-anim), [anim/0003](0003-movement-gates.md#plan-0050-phase-2-run2026-10-27-anim))
cite the closing check (`2026-10-27-anim-check.txt`) and its summary (`2026-10-27-anim-summary.txt`); the
checkpoint numbers are kept below as the first run's.

- **Question:** (plan 0050 Phase 2) Does `tools/anim.py`, the model of [anim/0001](0001-modes-frames.md),
  [anim/0002](0002-rates.md) and [anim/0003](0003-movement-gates.md), reproduce per event, with 0 mismatches: the
  logged record and rate of every server player and monster rate call (`UNIT_AnimSetRate`'s exit: the record name,
  frames and speed, the branch's `+0x4C`, `+0x3C` and path speed), every mode schedule (`SUNIT_ScheduleModeEvents`:
  the start frame and the queued kind-0/1 list), the dispatch of every queued event, the windowed monsters' advance,
  the windowed units' path step, the run drain, `GetHitRoll` with its draws, `PlayerModeAllowed`'s draw, an object's
  animation start with its `Sync` draw, the block gate and the first frame of an every-frame event; and what do the
  P1b-1 back-to-back actions, the P1b-12 delay interval and the P1b-11 block window show?
- **Setup:** agent-driven sessions on harness slot 2 (display `:9`, prefix `workspace/wineprefix-2`), single player,
  pinned `game.exe` in `workspace/runtime/game` (stock data), gdb by `tools/d2run.py` with `-seed` per session, all in
  Normal (batch 5: gh4n in Nightmare, br-hell and br-hell2 in Hell). Logger `tools/gdb/anim.gdb` (`de08f7d2…`) sourcing `tools/gdb/pilot.py` (`1ad48a4c…`, unchanged) and
  `tools/gdb/anim.py` **rev 4** (`c5fa964f…`) for the first 37 logs and **rev 5** (`78cdb2c3…`: states 139 `wolf`
  and 140 `bear` added to `ss`, for the shapeshift display; nothing else changed) for the 18 logs of batches 5f
  and 5g; each kept log's header names its revision (`ANIM logger armed rev N`). Breakpoints
  only read and continue. No gdb conditions are used: a Python `stop()` method runs before gdb tests a condition, so
  every filter is in Python, and the per-frame breakpoints (PathStep's `0x00650899`, the advance `0x00623E00`) log
  only the windowed units. Driver `tools/anim_sessions.py` over `tools/d2pilot.py` (`3ccabe20…`, unchanged) and
  `tools/xdrive.py` (`f263487d…`, its new `rhold`: the right button held beside the player, for back-to-back
  actions): per session `saves.py --slot 2 restore`/`aside p50e`, `d2run.py --install p50e`, the waypoint, then
  `explore --walk --melee --melee-button 3 --curse-keys … --keys-cycle` (the next skill hotkey and a right-click at the
  nearest live monster, `--loot 6` to open containers), held skills, the weapon swap and the run toggle; the monster
  sessions Teleport and cast at the nearest monster. `slots.py stop 2` after each session, `saves.py --slot 2 restore
  p50e` at the end of each batch (slot idle, aside empty). The pilot only decides where to click. Driver revisions:
  the batch gh and 1 sessions ran `0b5149f7…` (commit `ed221fa2`), batches 2 and 3 `be14bf3a…`; the sessions they
  share have the same steps. Batch 5 ran `tools/anim_sessions.py` `889dae99…` (its new session families added
  between the sub-batches, the earlier rows unchanged) and `tools/d2pilot.py` `771856fc…` (commit `e9bbbf84`: its new
  `--drink-in-burst`, the life orb sampled after each click of a burst too, drinking from the non-mana columns).
- **Characters** (ADR-0013 § Neutral: tool-built by `anim_sessions.py build` from `tools/d2s_recipes/anim-*.json` on
  the stock `p0005` base saves; stock magic affixes at their fixed values and plain base items; no test-state key),
  in `workspace/logs/anim/saves-2026-10-27-anim/`. Per class (Amazon `ama` … Assassin `ass`) and tier `Anim<Cls><k>`:
  clvl 25, life 1 500, Dexterity 100; set 1 a one-handed or thrown weapon with a buckler, set 2 another weapon class
  (`jav`/`sbw`, `crs`/`lst`, `wnd`/`scy`, `crs`/`spr`, `tax`/`2hs`, `crs`/`mau`, `ktr`/`tkf`); hotkeys F1 Attack, F2
  the cast skill, F3 Kick, F4 Throw or a second cast, F5 the sequence skill (Jab, Lightning, Sacrifice, Double Swing,
  Arctic Blast, Fists of Fire). Tier items: t0 none; t1 IAS 20 (weapon *of Alacrity*), FCR 20 (two rings *of the
  Apprentice*), FHR 24 (body armour *of Stability*), FBR 15 (buckler *of Blocking*), FRW 20 (boots *of Haste*); t2 IAS
  50 (*of Quickness*, gloves *of Readiness*), FCR 50 (+ amulet *of the Apprentice*, circlet *of the Magus*), FHR 48
  (+ belt *of Stability*), FBR 30 (*of Deflecting*), FRW 30 (*of Speed*); thrown weapons and the bow carry no IAS
  suffix. The `gh/` variants (recipes `anim-<cls>-t<k>-gh`, saves under `gh/`) have life 40, so that Act I hits reach
  `GetHitRoll`'s bands. `AnimSorMon` (`anim-sor-mon`, clvl 80, life 900: Teleport, Frost Nova, Nova, Frozen Orb,
  Lightning) plays the monster sessions.

### Sessions (to the checkpoint)

| batch | sessions | saves | seeds | waypoint (act, row) |
|---|---|---|---|---|
| gh | gh-ama-t0, gh-sor-t0 | `gh/AnimAma0`, `gh/AnimSor0` | 5100, 5110 | 1,2 · 1,3 |
| 1 | ama-t0, sor-t0, nec-t0, pal-t0, bar-t0, dru-t0, ass-t0, mon-1 | `Anim<Cls>0`, `AnimSorMon` | 5100–5160 (step 10), 5200 | Act I 1,2 … 1,5 by class; 5,2 |
| 2 | ama-t1, sor-t1, nec-t1, pal-t1, bar-t1, dru-t1, ass-t1, mon-2, mon-3 | `Anim<Cls>1`, `AnimSorMon` | 5101–5161, 5201, 5202 | Act I; 5,3 · 2,2 |
| 3 | gh-nec-t0, gh-pal-t0, gh-bar-t0, gh-dru-t0, gh-ass-t0 | `gh/Anim<Cls>0` | 5320–5360 | Act I |
| 4 | ama-t2, sor-t2, nec-t2, pal-t2, bar-t2, dru-t2, ass-t2 | `Anim<Cls>2` | 5102–5162 | Act I |

Deaths (the pilot's "life orb is empty"): gh-ama-t0, gh-sor-t0, gh-nec-t0, gh-pal-t0, gh-dru-t0, gh-ass-t0, mon-1 and
bar-t2 (gh-bar-t0 survived); the remaining steps of those sessions ran on a dead character, so no event after the
death is staged, and the logs are kept whole. Logs `workspace/logs/anim/2026-10-27-anim-<session>.log` with `.pilot.txt`,
`-shots/` and the batch outputs `2026-10-27-anim-batch*.out`. Development logs, not cited: `dev-`, `dev2-`, `dev3-`
(smoke sessions, logger rev 1 and its fixes), `dev-r1-` … `dev-r4-` (logger rev 2–4 and the earlier recipes: clvl 80
with life 32–45, Nightmare at clvl 50, a session cut by a recipe change), their saves in `dev-r2-saves/` and
`dev-r3-saves/`.

### Sessions (the second lane run, batch 5)

| batch | sessions | saves (recipe life) | seeds | field |
|---|---|---|---|---|
| 5a | gh2-sor-t1 | `gh2/AnimSorH1` (120) | 5411 | Act III Normal, Spider Forest (3,2) |
| 5c | gh4-sor-t2, gh4-nec-t1 | `gh4/Anim<Cls>M<k>` (80) | 5612, 5621 | Act II Normal, Far Oasis (2,5) |
| 5d | gh4n-pal-t2, gh4n-bar-t1 | `gh4/` (80) | 5732, 5741 | Act I Nightmare, Stony Field (1,3) |
| 5e | bk-ama-t2 | `bk/AnimAmaB2` (1 500) | 5802 | Far Oasis |
| 5f | br-hell, sp-ass-bos, sp-bar-dw, sp-pal-chg, sp-dru-form, p8-dru-1h, p8-dru-2h, bk-sor-t1, bk-nec-t2, bk-pal-t1, bk-bar-t2, bk-dru-t1, bk-ass-t2, mon-4 | `sp/AnimSorBr` (2 500), `sp/AnimAssBos`, `sp/AnimBarDw`, `sp/AnimPalChg`, `sp/AnimDruForm` (1 500), `gh2/AnimDruH2`, `gh2/AnimDruH1` (120), `bk/` (1 500), `AnimSorMon` | 4807, 5480–5483, 5490, 5491, 5811–5862, 5203 | Hell Cold Plains → Burial Grounds; Act I; Spider Forest; Far Oasis; Spider Forest (mon-4) |
| 5g | mon-5, br-hell2, sp-dru-form2, p8-dru-2hs | `AnimSorMon`, `sp/AnimSorBr`, `sp/AnimDruForm2`, `sp/AnimDruH2s` (120) | 5204, 4807, 5485, 5492 | Act I (1,4); Hell; Act I; Spider Forest |

Recipes (tool-built by `anim_sessions.py recipes`, ADR-0013 § Neutral, stock affixes and plain base items, no
test-state key): `anim-<cls>-t<k>-gh2` / `-gh3` / `-gh4` / `-bk` are the tier recipes with life 120 / 60 / 80 /
1 500 and set 1 a throwing axe with a buckler, hotkey F4 Throw (the Amazon a wand with the buckler, for her block with
a wand; the Druid a war hammer, his set 2 a two-handed sword); `anim-ass-bos` (Burst of Speed 20, two katars *of
Quickness*, the t2 items), `anim-bar-dw` (hand axe and scimitar in set 1, hand axe *of Quickness* and falchion *of
Alacrity* in set 2; Double Swing, Frenzy, Leap Attack, Leap), `anim-pal-chg` (Charge 5; a plain crystal sword in set
1, one *of Quickness* in set 2), `anim-dru-form` (Werewolf, Werebear: no weapon in set 1, a war hammer *of Alacrity*
in set 2) and `anim-dru-form2` (a spear in set 1, a short staff in set 2, the t2 items), `anim-dru-2hs` (life 120, a
two-handed sword in set 1), `anim-sor-br` (clvl 80, life 2 500, Nova 20, Teleport). The `bk-` sessions after
`bk-ama-t2` play 10 hops per half instead of 24 (session cap). br-hell2 repeats br-hell's steps.

Deaths: gh2-sor-t1, gh4-sor-t2, gh4-nec-t1, gh4n-pal-t2, gh4n-bar-t1, p8-dru-1h and p8-dru-2h (each after 2–9
get-hits); p8-dru-2h's weapon swap, pressed after the waypoint, did not take (its get-hits are one-handed), so
p8-dru-2hs carries the two-handed sword in set 1. Development logs (`workspace/logs/anim/dev5/`, manifest
`dev-p50e-manifest-2.sha256`, 9 lines, base `workspace/logs/anim/`): dev5-gh3-sor-t2 (life 60 in Act I: 2 of 33
monster attacks landed on the clvl 25 character, the Act I monsters' level being near 5; stopped), dev5-gh4-pal-t2
(stopped after gh4-nec-t1's character died within one click burst in Far Oasis with its belt full), dev5-gh4n-dru-t2
and dev5-bk-sor-t1 (stopped at their launch when a batch was cut; bk-sor-t1 was rerun in 5f), and the cut batch
output dev5-batch5b.out.

- **Procedure** (from the worktree; the checks under a 4 GB scope):
  ```
  python3 -I tools/anim_sessions.py recipes && python3 -I tools/anim_sessions.py build --saves workspace/logs/anim/saves-2026-10-27-anim
  python3 -I tools/anim_sessions.py run --slot 2 --tag p50e --saves workspace/logs/anim/saves-2026-10-27-anim \
      --run 2026-10-27-anim <sessions of the batch>
  python3 -I tools/anim.py check $(cat workspace/logs/anim/2026-10-27-anim-ckpt1.lst) > workspace/logs/anim/2026-10-27-anim-check-ckpt1.txt
  python3 -I tools/anim.py check $(cat workspace/logs/anim/2026-10-27-anim-close.lst) > workspace/logs/anim/2026-10-27-anim-check.txt
  python3 -I tools/anim.py summary workspace/logs/anim/2026-10-27-anim-check.txt > workspace/logs/anim/2026-10-27-anim-summary.txt
  python3 -I tools/anim.py replay-skills workspace/logs/skills/2026-10-25-skills-*.log workspace/logs/skills/2026-10-27-skills-*.log \
      > workspace/logs/anim/2026-10-27-anim-replay-skills.txt
  python3 -I tools/anim.py replay-combat $(cat workspace/logs/combat/c37p2-run.lst) > workspace/logs/anim/2026-10-27-anim-replay-combat.txt
  python3 -I tools/anim.py replay-combat $(cat workspace/logs/combat/p47b-run.lst workspace/logs/combat/p47h-run.lst) \
      > workspace/logs/anim/2026-10-27-anim-replay-combat-p47.txt
  ```
  Manifest `workspace/logs/anim/2026-10-27-anim-manifest-ckpt1.sha256` (`4dd51a04…`, 148 lines, one path base:
  `sha256sum -c` passes from `workspace/logs/anim/`): the 31 logs, their pilot outputs and screenshots, the batch
  outputs, the 43 saves, the list, the check output `2026-10-27-anim-check-ckpt1.txt` (`1bd13a13…`) and the three
  replay outputs. The development files are in `workspace/logs/anim/dev-p50e-manifest.sha256` (70 lines, same base; at the review its 71st line, a hash of the manifest itself that could not match, was removed).
- **Result at the checkpoint** (all 31 sessions above, `2026-10-27-anim-ckpt1.lst`, checker `tools/anim.py`
  `b3fca053…`): `CHECK anim` every kind 0 mismatched (`adv=2507/0 adv-seq=1109/0 block-gate=299/0 dispatch=29182/0
  drain=27919/0 ef-first=7437/0 endpending-E=715/0 fire=29207/0 ghr=4226/0 kb-end=3050/0 name=186016/0 obj=440/0
  pathspeed=75119/0 pathspeed-step=95907/0 pma-seed=19830/0 rate=186016/0 record=186016/0 sched=17896/0
  sched-len=17896/0 sched-rate=17896/0 seqstep=26504/0 startframe=17398/0 step=70019/0 step-point=68327/0`); what the
  counts cover against *Done when* is in the resume note. The oracle replays: plan 0045's skills
  logs, the do frame of 2 436 player skill events predicted from the recipes' items and the record, 2 435 equal and 1
  not (a Bash in `2026-10-25-skills-bar-1`: 14 frames for the model's 7, consistent with a slowed rate the log does not
  carry, `[L]`); three dual-wield logs not modelled. run:2026-10-16-combat (`c37p2-run.lst`) and the plan 0047 runs:
  `GetHitRoll`'s draws on the defender's seed (`GH0`/`GH1`) predicted from the `AD1` packet and the defender's stat 7,
  3 547 of 3 636 and 2 596 of 2 667 equal; every monster attack on a player equal, the misses all on monster
  defenders where the model draws and the log shows none (the freeze and stun states these logs do not carry, `[L]`).
  The get-hit and block lengths of those runs are not replaceable: their logs hold no mode or rate line.
- **Closing result** (all 55 kept sessions, `2026-10-27-anim-close.lst`, checker `tools/anim.py` `4241197a…`,
  output `2026-10-27-anim-check.txt` `2c3a7ddb…`, summary by `tools/anim.py summary` `2026-10-27-anim-summary.txt` `ee3448a3…`):
  `CHECK anim` every kind 0 mismatched (`adv=2927/0 (2 924 under the part 2 checker, anim/0001) adv-seq=1453/0 block-gate=867/0 dispatch=42449/0 drain=37434/0
  ef-first=9682/0 endpending-E=1027/0 fire=42542/0 ghr=7195/0 kb-end=3585/0 name=298373/0 obj=725/0
  pathspeed=127584/0 pathspeed-step=131167/0 pma-seed=26696/0 rate=298373/0 record=298373/0 sched=25848/0
  sched-len=25848/0 sched-rate=25848/0 seqstep=39901/0 startframe=25149/0 step=99241/0 step-point=97139/0`). The
  closing checker differs from the checkpoint's (`b3fca053…`) in: the dual-wield weapon class and attack term
  (anim/0001 § 2, anim/0002 § 3.6; the checkpoint logs have no dual wield); the shapeshift display (`UNIT_AnimTransform`
  with `g_PlrToMonMode` and its fallback, rev 5's form states) and the wereform base, with `+0x48` the previous mode's
  length at `UNIT_AnimInit`'s three calls (returns 0x00624469, 0x006244C5, 0x006244E3, before its writes at 0x00624473
  and 0x006244F4); two classifications of catalogue code (Phase 2's *Boundary*; at the review, uncompared catalogue paths rather
  than ADR-0004 oracles, since neither output is logged): a dispatch after a cancel from skill code (returns
  0x005B0000–0x005EFFFF, e.g. Leap Attack's 0x005DA2AA, each followed at once by the skill's own
  `sub_005417D0_UnitQueueEvent` call, a queue the logger does not read) is not compared (`dispatch-catalogue-queued`
  124: 110 kind 0 and 14 kind 1, 0–4 frames after the unit's latest such cancel, `rv-catq-*` of the review's
  `2026-10-27-anim-check-review.txt`; the checker excuses any later dispatch of that unit, a window part 2 closes by
  logging the queue), and one `PlrModeEndPending` E,
  `endpending-E-after-catalogue`), and a sequence advance's event byte cleared by the do it triggered is not the
  advance's (`adv-seq-do-cleared-4e` 2, sandmaggot's do 87, whose function `sub_005CB3C0_SkillDo87MaggotLay` stores 0
  at `+0x4E`, 0x005CB48E; the other two such stores, 0x005CB989 and 0x005CD51E, in dos 89 and 103); and the path
  speed of a step compared only with the last rate call whose branch writes it (moving, knockback), where the
  checkpoint compared it with any last call (37 Leap Attack steps whose speed the skill had set showed the
  difference). Over the 31 checkpoint logs the closing checker still finds 0 mismatches. The three replays are
  byte-identical under it (`replay-skills`, `replay-combat`, `replay-combat-p47`).
  Manifest `workspace/logs/anim/2026-10-27-anim-manifest.sha256` (`39ba842a…`, 324 lines, one path base:
  `sha256sum -c` passes from `workspace/logs/anim/`): the 55 logs, their pilot outputs and screenshots, the batch
  outputs, all saves, the two lists, both check outputs, the summary and the three replay outputs.
  *Review re-check* (architect, `lane/p50e` review): the manifest passes; `check`, `summary` and the three replays,
  rerun under a 4 GB scope with `tools/anim.py` `4241197a…`, are byte-identical to the kept outputs. The review added
  `check --review` (`tools/anim.py` `c2ef2166…`; without the flag its output is unchanged, byte-identical again):
  `python3 -I tools/anim.py check --review $(cat workspace/logs/anim/2026-10-27-anim-close.lst) >
  workspace/logs/anim/2026-10-27-anim-check-review.txt` (`d08c92a9…`, in
  `2026-10-27-anim-review-manifest.sha256`, same base), the closing check plus the `rv-*` tallies: the catalogue
  cancels by return address and the uncompared dispatches by distance and kind (`rv-catcan-*`, `rv-catq-*`), and
  per player action the first request after the start against the kind-1 end with `PlrModeLeaveOk`'s result, and the
  next action's start against the request's frame (`rv-req-*`).
- **Covers** (against Phase 2's *Done when*; counts from `2026-10-27-anim-check.txt` and its summary; a short item
  keeps its claims inferred, the rare-branch rule):

  | item | minimum | run | |
  |---|---|---|---|
  | player mode events, all seven classes | 1 500 | 7 092 scheduled (A1 2 599, cast 2 223, kick 637, sequence 699, block 567, throw 192, get-hit 84, S2–S4 77, death 14) | met |
  | per class and stageable mode | 30 | A1, cast and kick met for every class; sequence for the six with one (the Necromancer recipe has none); throw met for the Amazon 54, Sorceress 39, Barbarian 42, Assassin 32, short for the Necromancer 22, Paladin 3, Druid 0; block met but the Barbarian 11; get-hit short for all (8, 22, 7, 6, 6, 27, 8) | short in part |
  | attacks: 3 IAS values on two weapon types, per class | 30 each | three rates of 30+ on one record for six classes (`AMA1BOW`, `SOA11HS`, `NEA11HS`, `PAA11HS`, `DZA11HS`, `AIA1HT1`), none for the Barbarian (two rates); the second weapon type short for all | short in part |
  | casts: 3 FCR breakpoints | 30 each | met for the Sorceress, Necromancer, Paladin, Druid; two rates for the Amazon, Barbarian, Assassin | short in part |
  | get-hits: 3 FHR breakpoints | 30 each | no class has a rate with 30 (`RATES` lines); see below | short |
  | blocks: 2 FBR breakpoints | 30 each | met for the Paladin, Druid, Assassin; one rate for the Amazon and Sorceress, none for the Necromancer and Barbarian | short in part |
  | monster mode events | 500, 20 classes | 18 756 over 54 classes; sequence monsters 1 453 advances | met |
  | a `fast` champion | 1 | not reachable as named: MonUMod `fast` (row 6) has an empty `champion` cell (the rows with `champion` 1 are 16 `champion`, 36 `ghostly`, 37 `fanatic`, 38 `possessed` and 39 `berserk`; tbl:MonUMod.txt); the `fast` mod met on superuniques and their minions instead: 9 300 rate calls of units whose `MON` scan carries mod 6 (`sr-m-fastmod-*`; moving 3 519, most at stat 67 175) | met as the mod |
  | ruling (g): classic S1–S4 at the moving rate, two classes, one under a stat-67 change; class ≥ 410 S1–S4 | 30, 30 | 1 818 moving calls over classes 6, 19, 20, 111, 180, 190 (19 under a changed stat 67); the 70 default-branch calls are classes 257 and 405, `npc` rows (moving only in WL and RN, anim/0002 § 3.4); class ≥ 410: 509 attack, 75 default | met |
  | object animation starts, `Sync` draw predicted and chained | 100 | 725 starts, 490 draws, 235 without; chained pairs 0 of 7 (another draw on the object's seed between each) | met but chaining short |
  | movement windows (walk, run per class; monsters walking, running); 50 slowed | 200, 50 | player walk 719, run 2 211, sequence 30, knockback 1; monster walk 2 544, run 164, knockback 449; slowed 212 monster + 9 player | met |
  | chaining, 20 chained pairs per drawing kind | 20 | `GetHitRoll` 102 of 803 consecutive pairs; object starts 0 of 7; `PlayerModeAllowed` never drew (26 696 calls, no state 42) | met for `GetHitRoll` only |
  | oracle replacement | — | as at the checkpoint; byte-identical under the closing checker | met as stated |
  | P1.3: `GetHitRoll` 100 calls, 20 per drawing band, 2+ divisors | 100, 20 | 7 195 calls; bands `half` 605, `quarter` 613; `D` 16 (5 589), 8 (774), 32 (19), 64 (4) | met |
  | P1.3: 30 knockbacks, players and monsters, end predicted | 30 | monsters 541 ends predicted; players 2 mode-19 starts (and P1b-10's 15 knockback results) | short for players |
  | P1.3: run drain, a run turned to a walk at 0 | — | 35 472 run frames; no run reached 0 stamina | short (the turn) |
  | P1.3: every-frame first run at 30+ moving starts | 30 | 9 682 | met |
  | optional: `PlayerModeAllowed` under state 42; object operate ends | 30, 30 | not staged; not checked | short |

  The P1b cases: **P1b-1** (below); **P1b-2** 31 player attack rate calls with the factor above 175 (clamped), 22
  from sp-ass-bos's Burst of Speed (short of 30 attacks); **P1b-3** 96 throws by the Sorceress, Necromancer,
  Paladin and Assassin, no −30 in the model (met); **P1b-4** Charge 156 rate calls at item IAS 0 and 40, Leap Attack
  24 at 0 and 20, all on the default branch (met); **P1b-5** Double Swing 69 and Frenzy 117 rate calls with two
  weapons of different speed (hand axe and scimitar, hand axe and falchion), the dual-wield term in the model (met;
  Frenzy after a missed first swing not separated); **P1b-6** werewolf and werebear attacks with no weapon (78), a war
  hammer (34), a spear (31) and a short staff (92) (met); **P1b-7** `DZSC*` at three FCR values, `NESC*` at three,
  `40SCHTH` at two (11, 5), `TGSCHTH` at two (17, 20), `VASCHTH` not staged; **P1b-8** the Druid's get-hit with the war
  hammer 9 (`DZGH1HS`) and the two-handed sword 4 (`DZGH2HS`), the Amazon's block with a wand 99 (`AMBL1HS`) (met);
  **P1b-9** 64 get-hits in `[hp/16, hp/12)`, 332 refusals above `hp/12` (met); **P1b-10** 15 knockback results
  (`GH` bit `0x8`) on a player, 13 from Blood Raven in Hell (met for 10), of which 12 set the player to neutral in
  the same frame and 1 later, and 2 from class 462 that started mode 19; **P1b-11** 867 block gates (open 618:
  started 567, refused by the mode test 51; shut 249) (met); **P1b-12** 72 casts starting exactly at the delay
  state's end (`DLY` frame + `d`) (met); **P1b-13** not staged (no Slows Target item in the recipes); **P1b-14** no
  moving factor below 25 reached (`sr-*-move-x-lt25` 0), the run at base `0x65` in 2 211 windows; **P1b-15** 91
  Charge starts (sp-pal-chg), its 160 logged player sequence steps at path speed 5 760 (`ps-p-m18-v=5760`), stat 67
  100 at all 156 Charge rate calls (`sr-p-sk107-m18-s67=100`; none at ≤ 50).

  **Why the get-hits are short.** `GetHitRoll` refuses a hit below `maxHP / D` (`D` 16 for nearly every monster hit
  met), so a get-hit needs a hit of a sixteenth of the character's life or more, and each such hit costs that much.
  Every fragile character died after 2–9 get-hits: life 40 in Act I (gh-, first run), 120 in Spider Forest
  (gh2-sor-t1, p8-dru-*), 80 in Far Oasis and Act I Nightmare (gh4-, gh4n-), the belt potions drunk between clicks
  (`--drink-in-burst`) not keeping up with packs; a clvl 25 character with life 60 in Act I Normal is seldom hit at
  all (dev5-gh3-sor-t2), and a life-1 500 character takes no get-hit. The 84 get-hits stay the run's.
- **Readings** (what the logs show; the findings' run sections tag them):
  - **P1b-1, the interval between two actions** (`act-m<mode>-nextact-minus-n`: the next scheduled player mode's
    start `T'` against the kind-1 end `T + n`, within 3 frames; `gap` otherwise). Cast (mode 10):
    `T' = T + n − 1` 448 times, `T + n` 103, earlier (−2, −3) 8, later 175. A1 (7): −1 107, 0 63, −2/−3 15. Throw
    (11): −1 36, 0 2. Kick (12): −1 4, 0 6. Held Lightning (mode 18, skill 49, the control): `T + n` 68, `T + n − 2`
    once, never `T + n − 1`. Get-hit (4) and block (9): never before `T + n` (0: 2 and 21 times; 1–3 later). The 23
    starts before `T + N` are block and get-hit requests. Of the 107 A1 restarts at `n − 1`, 23 have A2's
    `⌈256 (F − 1 − S) / r⌉ ≠ n − 1` (`act-a2-m7-a2ne-n-1-obs-n-1`), so A2's count is not the interval there; the
    other 84 cannot tell them apart. 1 027 `PlrModeEndPending` values equal the queued end while a request comes
    before it. *At the review* (`tools/anim.py check --review`, `2026-10-27-anim-check-review.txt`): the next action
    starts in the frame of its request (after a cast, 1 816 of the 2 084 first action requests, 23 of them two to
    five or more frames before `T + N`), the first action request after a cast comes at `T + N` 451 times and at
    `T + n` 97, and `PlrModeLeaveOk` returned 1 at all 5 633 first requests. So the held normal action's `N` is the
    client's request cadence, not a server gate (anim/0001's run section).
  - **P1b-12, the delay**: Frozen Orb held (mon sessions), of the 73 next casts (mode 10) that start within 3 frames of
    the delay state's end (`delay-next-start-m10-minus-end`), 72 start exactly at the `DLY` frame plus `d` and one 3
    frames later; the `DLY` frame is the do's (`SKILLS_SetDelayState` from `SKILLS_SrvDo`): the delay runs from the do.
  - **P1b-10, a player's knockback**: 15 hits on a player with result bit `0x8`; 12 of Blood Raven's 13 set the
    player's mode to neutral (1) in the hit's own frame (`plr-kb-next=m10-to-1` 8, `m1-to-1` 3, `m9-to-1` 1; one
    later); the two of class 462 started mode 19 (`m1-to-19`).
  - **The first run of an every-frame event** (anim/0003's open question): 9 682 starts, each in the frame it was
    queued when queued before its type's every-frame list ran, else in the next (`ef-first`, 0 mismatched; player
    starts 6 205 all next-frame, monster 3 477).

Emulated runs (ADR-0015, no wine, nothing native):

## run:2026-10-27-anim-rates-emu

- **Question:** (plan 0050 Phase 1, batch P1.2) Does `sub_00621740_AnimRateBonus` map a unit's stat to
  `k s / (k + s)` (truncating) for each entry of `g_AnimRateBonus`, and does `UNIT_AnimAdvance` (a monster, no
  sequence) map frame, length, rate and the record's event bytes to the new frame and event byte as
  [anim/0001 § 8](0001-modes-frames.md#8-the-per-frame-advance) states, taking the rate at each call?
- **Setup:** Ghidra 12.1.2 p-code emulator on the pinned `game.exe` (lane copy `GHIDRA_PROJ_DIR=workspace/ghidra-p50b`,
  heap 3 GB, one instance, each under a 4 GB scope), `re/ghidra_scripts/EmuTrace.java` unchanged (`3255db0c…`). Case
  writers, models and check: `tools/anim_rates.py` `cases`/`check`, every draw from `random.Random("p50b-<family>")`;
  the cases regenerate byte-identical with the tool revision `p50b-commands.txt` names. Families: `bonus` (3 413
  calls, EAX the entry, ECX a scratch unit whose stat list holds the stat with decoys; the DataTables ItemStatCost
  pointer, count and `+0x05` bytes in the spec) and `advance` (1 200 pairs, 2 400 calls, a scratch type-1 unit with
  `+0x30` 0 and a scratch record; the second call of a pair starts from the first's modelled frame with a new rate).
  Guards on the fatal and allocator entries. Files in `workspace/logs/anim/p50b-emu/` and the manifest
  `workspace/logs/anim/p50b-manifest.sha256`; `p50b-emu-dev/` is the development run of an earlier revision, kept,
  not cited.
- **Result:** `check.txt` (`3566d9da…`): `FAMILY bonus cases=3413 bad=0 stops=0 reads_outside=0` (positive 2 569,
  negative 832, zero 12); `FAMILY advance cases=2400 bad=0 stops=0 reads_outside=0` (wraps 490, event bytes 1–4
  taken 205, 1 120 pairs with a changed rate of which 1 114 would mismatch under the old one); `SCAN check bad=0`.
- **Covers:** the two maps above, nothing about what the game stores in those fields or when it calls them
  (ADR-0015). Not covered: `s = −k` (a divide fault), the advance's sequence branch, a player, a start frame other
  than 0. Used by [anim/0002 §§ 2, 6](0002-rates.md).

## run:2026-10-27-anim-p2

**Status: closed for review (`lane/p50f`, three lane runs; the project paused after this roster).** Phase 2 part 2:
get-hits by FHR, blocks, throws, rate tiers, the catalogue queue. 26 kept sessions on harness slot 1 (display `:8`),
Normal sessions for the catalogue and specials, Nightmare for the get-hit route; stock data, single player.

- **Question:** does `tools/anim.py` still reproduce with 0 mismatches over part 2's sessions, and which of part 1's
  *Done when* floors (get-hits and blocks at three FHR/FBR rates of 30 per class, throws 30 per throwing class, a
  second A1 record, a third FCR rate, the catalogue queue) does the run reach?
- **Setup:** logger `tools/gdb/anim.py` rev 6 (`46400bef…`), checker `tools/anim.py` `5be6c31f…` (rev 6 plus the
  restart rule, anim/0001's part 2 section), `tools/anim_sessions.py` `c88ac497…`, `tools/d2pilot.py` `0535411b…`
  (explore `--inv-potions`). Recipes `anim-<cls>-t<k>-gh9`…`-gh10` and the special ones are built by
  `anim_sessions.py build`; saves `saves-2026-10-27-anim-p2/` (manifest below). Sessions: `gh5`–`gh12` (get-hit route
  development, see below), `mon-7`, `sp-pal-chg2`, `sp-ass-bos2`, `sp-pal-slow`, `th-dru`. Batches 10 and 11 of this
  lane run: `gh12-bar-t0 gh12-dru-t0 gh12-ass-t0 th-dru sp-ass-bos2 sp-pal-slow` and `gh12-<bar,dru,ass,pal>-t1`.
- **Deviation from the owner's build (for the review's ruling).** The owner asked for a get-hit build of clvl 60+ and
  life 1 000+. The runs use **clvl 70, life 400, Cold Plains in Nightmare, `/players 2`** (gh10–gh12). The 1 000-life
  build (gh5: life 1 000, Act V Nightmare) died after **6 get-hits**. A get-hit costs a sixth to a quarter of max
  life whatever the hit (`GetHitRoll`'s bands `3/8` in `[hp/16, hp/8)`, `3/4` up to `hp/4`, anim/0003), so the lane
  reads the count as set by the potions the route can drink, not by life. The evidence does not separate that from
  survivability: the deaths came from swarms (up to ~160 damage a second at life 400) faster than the pilot could
  drink, and 40 extra inventory potions (gh9) moved the counts only to 17 and 6. The review rules the floors short and
  *survivability-bound at this build*, not potion-bound. The 400-life, elite-weapon builds gave 6–28
  get-hits a session (gh7–gh12). gh5 and gh6 (480) logs are kept (`…-gh5-sor-t0.log`, `…-gh6-sor-t0.log`).
- **Result** (`2026-10-27-anim-p2-all2.lst` = part 1's close list + `…-p2-ckpt2.lst`, 81 logs; check `--review`
  `2026-10-27-anim-p2-check-ckpt2.txt` `03f83c9d…`; summary `…-summary-ckpt2.txt` `ae27fd27…`): every kind 0
  mismatched (`adv=4110/0 adv-seq=2089/0 block-gate=2309/0 dispatch=56800/0 drain=49914/0 ef-first=12193/0
  endpending-E=1568/0 fire=56941/0 ghr=9858/0 kb-end=5019/0 name=379410/0 obj=955/0 pathspeed=150696/0
  pathspeed-step=164162/0 pma-seed=34743/0 rate=379410/0 record=379410/0 sched=34647/0 sched-len=34647/0
  sched-rate=34647/0 seqstep=62678/0 startframe=33838/0 step=125141/0 step-point=122598/0`). The first check over
  batch 10 had 10 `adv` mismatches: the checker paired two advances across a get-hit restart (anim/0001, part 2
  section); the rule is fixed and part 1's output differs only in `adv` 2 927 → 2 924.
- **Floors reached** (summary, all 81 logs): the catalogue queue (anim/0001); throws Paladin 74, Necromancer 30,
  Barbarian 42, Amazon 54, Assassin 32, Sorceress 39; FBR/blocks at three rates of 30:
  Paladin (`PABL1HS`) and Druid (`DZBL1HS`); one A1 record at 3×30 for every class (the Barbarian's `BAA11HS` is new);
  A1 rates with 30+ on at least 3 rates for all classes; cast rates ≥ 3 for Sorceress, Necromancer,
  Paladin, Druid.
- **Floors short, and why.** (1) Get-hits at three FHR rates of 30: get-hit mode starts total 308 (part 1's 222 plus
  86); per class rates with 30+: Barbarian 128 (61) and 179 (30), Paladin 179 (31), Druid and Assassin and Sorceress
  one rate each, Amazon and Necromancer none (20, 14 starts). Survivability-bound (review ruling; the lane filed it potion-bound): the Sorceress, Amazon and Necromancer die
  within 3–8 hops of Cold Plains; in the t1 sessions the pilot's last half ended in death at hop 1 (Druid,
  Assassin), hop 3 (Paladin) and hop 7 (Barbarian) (`…pilot.txt`; the cause of the early deaths was not examined). The t2 tier (rate 215) was not run in this lane
  run. (2) The Druid's throws: 12 (< 30; `th-dru` died at hop 1; the axes' throw mode is reached 12 times). (3) A second A1 record at 3×30: none (every class has one). The
  third FCR rate: Amazon, Barbarian, Assassin have 2 cast rates of 30. (4) Rare branches not staged: the run's turn to
  a walk (low stamina, `r`), player knockbacks, `VASCHTH` (no stock state transforms a player into the vampire:
  States.txt's transform rows are 63, 93, 101, 119, 139, 140, 176, 177). The Sorceress "sturdier route" (mercenary or
  more Dexterity) was not tried.
- **Kept files:** manifest `2026-10-27-anim-p2-manifest-ckpt2.sha256` (`2801602f…`, 160 lines, base
  `workspace/logs/anim/`, `sha256sum -c` passes): all part 2 logs, pilot outputs, screenshots, batch outputs
  1–11, saves, lists, checks, summaries. The checkpoint manifest `…-manifest-ckpt1.sha256` fails on two lines
  (`…-gh12-bar-t0.log` and its `.pilot.txt`): batch 10 re-ran that session under the aborted run's name and
  overwrote the aborted development log (a review-fix 6 miss of this lane; the session itself is the kept one now,
  `ckpt2` lists it). No claim rested on the aborted log.


## run:2026-10-30-anim-p3

**Status: checkpointed, not closed here; continued by run:2026-10-30-anim-p3b below (`lane/p50g`, one lane run; owner pause at the token budget).** Phase 2 part 3: the
short floors of part 2 with overpowered clvl 99 builds. 33 kept sessions on harness slot 1 (display `:8`), Act I
Nightmare, Cold Plains, `/players 5`; stock data, single player.

- **Question:** does `tools/anim.py` still reproduce with 0 mismatches over parts 1-3, and which get-hit floors do the
  overpowered builds reach?
- **Builds** (`anim_sessions.py` `op_recipe`, recipes `anim-<cls>-op-t<k>`, classes Amazon, Necromancer, Sorceress,
  Druid, Assassin, tiers t0-t2): clvl 99 (experience 3 520 485 254), base life 120 (gear brings the total to about
  300), mana 2 000, Strength 250, Dexterity 150; resistances 65 (t0) or 30 (t1, t2) each from stock uniques at
  `"roll": "max"` in the slots that carry no rate item (Harlequin Crest, Mara's Kaleidoscope, Raven Frost, The Stone of
  Jordan, Magefist, Arachnid Mesh, Skin of the Vipermagi); the FHR tier is the part 1 and 2 items (armour and belt of
  Stability), and `anim_sessions.py oprates` on each save gives FHR 0 / 24 / 48 for every class (Crown of Ages was
  dropped: it carries FHR 30). Clearing skill on F1 at level 20 (Sorceress Blizzard, Necromancer Poison Nova, Druid
  Hurricane, Assassin Lightning Sentry, Amazon Valkyrie; Amazon also a Desert Mercenary Off-Nightmare, Id 11, which the
  pilot did not feed), cast at the character's own position by `d2pilot.py explore` (NovaGate, radius 4), 40 inventory
  rejuvenation potions and the belt, drunk below 0.62 of the orb (`--potion-state` keeps the counts across explores).
  Weapons as gh10 (elite bases, *Ferocious*, the shield set first); the Druid swaps from the hammer to the two-handed sword
  half way (P1b-8).
- **Life sizing (development runs `dev-p3-*`, manifest `dev-p3-manifest.sha256`):** base life 180 (total 342) gave 7
  get-hits in three fields and every hit below `maxHP / 8`; 10 (total 172) died at hop 34 with 3 get-hits; 40 died at hop
  14; skill level 6 and `/players 8` died at hop 14 (3 get-hits). So the clearing skill is the thing that keeps the
  character alive, the band is the thing that limits the count, and a get-hit per session stayed at 2-16.
- **Result** (`2026-10-30-anim-p3-all3.lst` = part 2's `all2.lst` + `2026-10-30-anim-p3.lst`, 114 logs; check `--review`
  `2026-10-30-anim-p3-check.txt`; summary `…-summary.txt`): **0 mismatches**, every kind
  (`adv=4117/0 adv-seq=4133/0 block-gate=2524/0 dispatch=66026/0 drain=77009/0 ef-first=16244/0 endpending-E=1682/0
  fire=66597/0 ghr=13094/0 kb-end=5027/0 name=473502/0 obj=1287/0 pathspeed=185272/0 pathspeed-step=213757/0
  pma-seed=43644/0 rate=473502/0 record=473502/0 sched=43148/0 sched-len=43148/0 sched-rate=43148/0 seqstep=70598/0
  startframe=42339/0 step=162048/0 step-point=158485/0`). The first check had 63 `sched`/`startframe` and 5 `fire`
  mismatches, both fixed in `tools/anim.py` (below).
- **Checker changes found by the run** (`tools/anim.py` `5c3b5852…`): (1) the Valkyrie (monster class 357, 63 schedules in
  the three Amazon sessions) carries a player's record (`AMA12HT`) and its A1 start frame is 2, the logged `s0`: the start
  frame is by display type (anim/0001 § 4), so the model now reads `g_AttackStartFrames[weapon][class]` from a monster
  record's own player token and weapon code `[I]` (121/0 `startframe` over the Amazon t0 log afterwards); (2) 5 dying
  Fallen whose end event fell on the log's last frame (the game was killed in that frame) counted as unfired: the
  excuse now covers `fr == last frame` as its own tally `at-log-end-frame` (5).
- **Floors** (get-hit mode starts per FHR rate, parts 1-3): Sorceress 50 / 35 / 38 and Assassin 40 / 42 / 52 **met**
  (`get-hit rates30` 3); Necromancer 38 / 21 / 42 (2); Amazon 32 / 25 / 25 (1, two rates at 25 and 25); Druid 49 / 24 / 16
  (1; its 179 is the werewolf form of part 1); Paladin and Barbarian unchanged. **Short with counts:** Amazon 179 (25) and
  215 (25), Necromancer 179 (21), Druid 173 (24) and 208 (16). P1b-8: the Druid's hammer and two-handed sword get-hits
  were played in `op2-dru-t1-1`, `op2-dru-t2-1` (swap half way), not counted per weapon here. **Not run:** the Druid's
  throws (12 of 30; `anim-dru-op-th`, session `op-dru-th`, saves built, not played), the knockbacks (`op-br`, `anim-sor-op-br`),
  the run that turns to a walk at 0 stamina (`op-run`, `anim-sor-op-run`), P1b-2, P1b-13/14/15 (Arachnid Mesh's Slows
  Target is on the t0 and t1 belts; the tallies were not read for it), `VASCHTH` (no stock state transforms a player into
  the vampire, part 2's check).
- **Kept files:** manifest `2026-10-30-anim-p3-manifest.sha256` (205 lines, base `workspace/logs/anim/`, passes): logs,
  pilot outputs, potion counts, screenshots, batch outputs 1-2, the saves of `saves-2026-10-30-anim-p3/`, lists, check,
  summary. Tools: `tools/anim.py` `5c3b5852…`, `tools/anim_sessions.py` `bc1fb493…`, `tools/d2pilot.py` `62b6f4f7…`
  (`--potion-state`). Batches: 1 = `op-<cls>-t<k>` (40 hops a field, 12 sessions), 2 = `op2-…` (120 hops, 21 sessions).

## run:2026-10-30-anim-p3b

**Status: closed for review (`lane/p50g`, resumed after the owner pause).** Phase 2 part 3, second half: the short get-hit
floors of [run:2026-10-30-anim-p3](#run2026-10-30-anim-p3) and its unplayed sessions. Harness slot 1 (display `:8`), stock
data, single player, the same saves (`saves-2026-10-30-anim-p3/`, unchanged), `/players 5`.

- **Played (17 kept sessions, logs `2026-10-30-anim-p3b-<session>.log`):** `op2-ama-t1-3`, `op2-ama-t2-3`, `op2-nec-t1-3`,
  `op2-dru-t1-2`, `op2-dru-t1-3`, `op2-dru-t2-2`, `op2-dru-t2-3` (120 hops, the p3 options), `op-dru-th`, `op-br`, `op-br2`,
  `op-br3`, `op-run` and five more run sessions: `op-run2` (without the `r` press, 30 hops), `op-run3` to `op-run6` (200 hops,
  seeds 8512, 8514, 8515, 8516), new session rows in `tools/anim_sessions.py` (additive; the `op2-*` repeat range widened to 1-8).
- **Result** (`2026-10-30-anim-p3b-all4.lst` = p3's `all3.lst` + `2026-10-30-anim-p3b.lst`, 131 logs; check
  `--review` `2026-10-30-anim-p3b-check.txt`; summary `2026-10-30-anim-p3b-summary.txt`): **0 mismatches** over every kind
  (`adv=4117/0 block-gate=2569/0 dispatch=71433/0 drain=88103/0 ef-first=18310/0 fire=72014/0 ghr=13932/0 kb-end=5027/0
  name=541068/0 pathspeed=216788/0 sched=46722/0 startframe=45913/0 step=179727/0 step-point=175511/0` and the rest).
- **Floors** (get-hit starts per FHR rate, parts 1-3 and 3b): Amazon 128:32 179:40 215:33; Necromancer 128:38 179:32
  215:42; Druid 124:49 173:35 208:32 (179:7 is the werewolf form); Sorceress and Assassin as before. **All five short rates
  reached 30** (`get-hit rates30` 3 for the Amazon, Necromancer, Sorceress, Druid and Assassin).
- **Named short, with counts:** the Druid's throws 29 of 30 (`op-dru-th` 17 more, 12 before); player knockbacks 0 new (the
  three Hell sessions `op-br`, `op-br2`, `op-br3` explored 200-220 hops each and the hunt ended "class 267 never seen";
  `kb-end` unchanged at 5027, all monsters); P1b-2, P1b-14, P1b-15 not played; P1b-13: 13 player movement windows under a
  slow (`win-slow-p`) over the 131 logs, from the Slows Target belts (not a 30), 327 for monsters.
- **The run's turn to a walk at 0 stamina (new):** `op-run` held walking all session (`r` toggled the default run off: mode 2
  in every `PS0`); the default is a run (mode 3), so `op-run2` to `op-run6` omit the key. The Sorceress (the run drains stat 10) turned from mode 3 to mode 2 by `MSET` 81 times in the five logs (3, 8, 11, 22, 31 per log;
  75 + 6 as below). 81 events is the count of the checker's tally `ef-first-run-turn`, which pairs the turn's
  `EF` line (queued the same frame as a drain `DR0` line) with the unit's next `PS0`: **offset 0 in 75, offset 1 in 6** `[I]`
  (a measurement; the 6 offset-1 cases are not explained: not every `EF` after a drain is the turn's own, and the tally
  does not separate them). The first check of `op-run2` alone flagged 3 `ef-first` mismatches (the old rule, "an `EF`
  queued in phase 3 runs next frame"): those three are the turn inside the unit's own walk. The rule excludes all 81
  turn pairs from `ef-first` (the 78 that passed the old phase rule included) and counts them in the new tally, so
  `ef-first`'s 0 covers the remaining 18 310 pairs, not the turn.
- **Checker change** (`tools/anim.py` `d05f5354…`): an `EF` for mode 2 in the frame of the unit's own `DR0` is tallied as
  `ef-first-run-turn-offset=N`, not checked against the phase rule. `tools/anim_sessions.py` `e066777b…`.
- **Not done:** the plan's Done-when is met for the get-hit rows; the rest is named short above. Dev logs: none for 3b.
- **Kept files:** manifest `2026-10-30-anim-p3b-manifest.sha256` (122 lines, base `workspace/logs/anim/`, passes): logs,
  pilot outputs, potion counts, screenshots, batch outputs 1-6, lists, check, summary. The p3 manifest still passes.


### Addendum 2026-11-15: plan 0066 batch S6a, new tallies over the 131 kept logs (`lane/n66k`)

- **Question:** (plan 0066 Phase 1, batch S6a) which inferred statements of anim/timing do the kept logs of this run and
  its three predecessors (`2026-10-30-anim-p3b-all4.lst`, 131 logs, revs 4 (37), 5 (18), 6 (76), no `CAP` line) hold
  once a tally reads them, and which need another source?
- **Setup:** no game, no Ghidra. `tools/sweep2_s6ab.py` (`f223ad12…`) parses each log once, runs `tools/anim.py`'s
  `Checker` on it unchanged (the control) and the S6 observers on the same lines; `static` reads the return sites the
  observers classify with r2 and the int3-padding entry next to `re/symbols.csv`, and the raw-byte callers of
  `GetHitRoll`. One kept run each under `systemd-run --user --scope -p MemoryMax=4G` (the logs pass in 50 s):
  `workspace/logs/n66k/check.txt` (`0b8f36b7…`, 52 lines, `S6 total bad=0 control_bad=0`) and `static.txt`
  (`d0e848ac…`, `bad=0`); `manifest.sha256` (`50f61c5e…`, 2 lines) passes from `workspace/logs/n66k`. Development
  outputs under `dev/` with `dev/manifest-dev.sha256` (8 lines, passes from `dev/`); `dev-run5-premature-check.txt` is
  the run before the reschedule model took the weapon class from the last rate call (its only difference: the 893
  reschedules counted "no rows").
- **Procedure:**
  ```
  D=workspace/logs/n66k
  systemd-run --user --scope -p MemoryMax=4G python3 -I tools/sweep2_s6ab.py static > $D/static.txt
  systemd-run --user --scope -p MemoryMax=4G python3 -I tools/sweep2_s6ab.py logs > $D/check.txt
  ```
- **Control:** the run's `CHECK anim …` line equals `2026-10-30-anim-p3b-check.txt`'s byte for byte (`sched=46722/0
  fire=72014/0 dispatch=71433/0 adv=4117/0 ghr=13932/0` and the rest).
- **Static (`static.txt`):** the four `UNIT_AnimSetRate` returns 0x00624444, 0x00624469, 0x006244C5, 0x006244E3 lie in
  `UNIT_AnimInit` (r2: `call 0x623f50` before each, the four calls of the body), 0x0055343A and 0x00553460 in
  `SUNIT_AnimInit` (its two calls), 0x0055399F and 0x005539AC in `SUNIT_CancelModeEvents` (`call 0x540e60`), 0x005A8281
  in `MonModeEndGeneric` (`call 0x624690`); owner by symbol and by padding agree for all 9; `UNIT_AnimInit` ends at
  0x00624690 both ways. `GetHitRoll` 0x0057CB00 has two call sites, 0x0057D0C8 and 0x0057D37A, both in `COMBAT_GetHit`
  (raw bytes; r2 decodes `call 0x57cb00` at each), no abs32 reference. `SOSC1HS` and `SOSCSTF` have `SOSCHTH`'s 14
  frames, speed 256 and event 1 at frame 7; `PAGH1HS` has `PAGHHTH`'s 5 frames and speed 256.
- **Observed** (`check.txt`; counts are lines of the 131 logs):
  - *Mode set → animation start* (`mset-animinit`): every mode set to a new mode is followed, in its frame and before
    the unit's next mode set, by exactly one `UNIT_AnimInit` rate return (players 34 259, monsters 244 552) or one
    object `OA0` (1 481), and that call already sees the new mode; no set to the current mode is (players 12 055,
    monsters 30 130, objects 260). 2 new-mode sets end their log. `[C]` (run:2026-10-30-anim-p3b).
  - *`UNIT_AnimInit`'s branch* (`animinit-branch`): a display type 0 unit (an unshapeshifted player, or a monster whose
    record carries a player token) returns at 0x00624444 in mode 18 (674) and at 0x00624469 otherwise (32 626, of them
    500 monsters in mode 14); a display type 1 unit at 0x006244C5 in mode 14 (4 486) and at 0x006244E3 otherwise
    (238 566). `+0x30` is set at both sequence calls and clear at 0x00624469; at 0x006244E3 it is still set in 4 460
    calls (the monster branch clears it after its call). 1 957 rev-4 calls of a shapeshifted player are not classified
    (no form state in rev 4). `[C]` (run:2026-10-30-anim-p3b).
  - *`SUNIT_AnimInit`* (`sui-branch`, `two-rate-calls`): its rate return is 0x0055343A exactly at a monster mode-14 or
    player mode-18 start with a sequence (5 295) and 0x00553460 otherwise (192 006); all 46 722 schedules follow it, and
    their rate is its rate. 44 415 starts have both calls, `UNIT_AnimInit`'s first; in 168 the two rates differ and the
    schedule takes the second. `[C]` (run:2026-10-30-anim-p3b).
  - *The start order* (`start-sequence`, 140 936 player and monster scheduled or every-frame starts): `SUNIT_AnimInit`'s
    rate, then the two cancels of kinds 0 and 1 from `SUNIT_CancelModeEvents`, then `SUNIT_ScheduleModeEvents` or
    `SUNIT_ModeEveryFrame`, in every one. 88 player starts reschedule (`RSC`) after their schedule, in the same frame.
    `[C]` (run:2026-10-30-anim-p3b).
  - *Two clocks* (`two-clocks`): players schedule modes 0 (41), 4 (756), 7 (4 812), 9 (1 442), 10 (3 186), 11 (300), 12
    (811), 14 (536), 15 (11), 16 (21), 18 (809) and run modes 2 (1 930), 3 (10 722), 19 (2) every frame; 1, 5, 17 queue
    nothing. A monster start through `SUNIT_AnimInit` queues by its resulting mode's record (`g_MonModeRecords` +12) and
    `g_MonModePerFrame` with the MonStats2 `*mv` bit: scheduled 0, 3, 4, 5, 6, 7, 8, 9 (A1 16 283, S1 2 144 …), every
    frame 2, 13, 14, 15 and the `*mv` S1 (127) and S2 (16), nothing for 1, 12; 0 mismatches (one mode-5 start ends the
    log). `[C]` (run:2026-10-30-anim-p3b).
  - *Ends* (`player-mode-end`, `monster-dispatch`): each player kind-1 dispatch is followed in its frame by mode 17 from
    mode 0 (39) and neutral otherwise (10 679), never 5: no end fell in a town. Monster kind-1 ends: DT → 12 (4 520), GH,
    BL, A1, A2, S1, S2 → 1 (2 093, 91, 14 242, 5 233, 1 570, 254). 85 507 arrivals of WL and RN set mode 1 directly
    from 0x005A8281 (74 522 from 2, 10 985 from 15). No monster dispatch carries `fz` 1. `[C]` (run:2026-10-30-anim-p3b).
  - *Neutral and walk by town* (`town-modes`): player sets to 1 fall in the field (20 201), to 5 in a town (131), to 2
    in the field (1 930); no set to 6; runs (3) keep mode 3 in a town (981); 262 sets of each neutral fall between two
    pilot lines of different levels and are not classified. `[C]` (run:2026-10-30-anim-p3b).
  - *`PlrModeLeaveOk`* (`leave-ok`, 26 574 `PL0`/`PL1` pairs): M4's block without the cursor test gives every return;
    781 refusals, all from DT (6), GH (350) and BL (425) for requests outside {0, 1, 5, 17}; every request in A1, cast,
    throw and kick (498, 930, 130, 173) returns 1; no request falls in `(E, E + 5]` (the slack is not separated); 192 SQ
    requests are not modelled. `[C]` for the logged branches (run:2026-10-30-anim-p3b).
  - *Get-hit and block are not left early* (`gh-bl-left`): the next mode set after a player GH (756) or BL (1 442) start
    comes at its end frame (746, 1 436) or is a death before it (10, 5). `[C]` (run:2026-10-30-anim-p3b).
  - *The hit's commands* (`gethit`, `stun-skips-roll`, `stat95`): on a player, get-hit commands mode 4 exactly when
    `GetHitRoll` returned 0 (953) or the defender is stunned (2, no roll), not after a 1 (4 760); knockback requests 19
    (15). On a monster, mode 3 follows exactly after a 0 (3 651; none after 4 566 ones), knockback sets 13 (919, 3
    with no set). The next stat 95 after an open block gate is that frame (1 440, 185 of them after a refused command)
    and after a shut gate unchanged (18 759). 515 monster hits share their segment with `MonKnockbackEnd`, whose command
    is its own. `[C]` (run:2026-10-30-anim-p3b).
  - *`GetHitRoll`* (`ghr-divisor`): divisor 32 at 38 calls, 4 of which a divisor of 16 would answer differently, all as
    32; 64 at 4 calls, none separating; 222 calls on monsters without a GH mode, 28 of which would return 0 without the
    test, all 1. `[C]` for 32 and the mode test, 64 not separated (run:2026-10-30-anim-p3b).
  - *Closed forms* (`k-forms`, 45 913 non-sequence schedules): `+0x48 = frames << 8` at every one; K1's kind-0 list and
    end equal the logged queue at every one (no schedule drops an event past `N`, none has no step); K2's band
    `X_n ≤ X < X_{n−1}` holds at all 39 550 plain-rate schedules (28 922 exactly at `X_n`); K3's stat band at all 3 161
    cast, 5 132 get-hit and 1 626 block schedules (305 at the least stat). `[C]` within those domains (run:2026-10-30-anim-p3b).
  - *Worked records* (`worked`): `SOSC1HS`/`SOSCSTF` at FCR 0, 20, 40, 50: rate 256, 299, 332, 345, length 14, 12, 11, 11,
    the do at `T + 7, 6, 6, 6` (112 casts at FCR 20); `PAGH1HS` at FHR 0, 24, 48: rate 128, 179, 215, length 10, 8, 6;
    `AMA11HS` at factor 80, 130, 147, 160: length 18, 11, 10, 9, the do at `T + 11, 7, 6, 6`. No `SOSCHTH`, `PAGHHTH`,
    factor-100 `AMA11HS` or FHR-7 schedule is logged.
  - *Reschedules* (`reschedule-e3`): all 893 `RSC` lists equal E3's (`RescheduleSkip` 819, `RescheduleAt` 74; every one a
    player sequence); `RescheduleAt` leaves `+0x44 = (T − n) << 8` (74) and `RescheduleSkip` `(T − p) << 8` (819, a value
    the spec does not state). `RescheduleFromPct` is not reached. The catalogue queues kinds 2 (181 836) and 12 (9 206);
    their dispatches are not logged. `[C]` (run:2026-10-30-anim-p3b).
  - *Advances* (`advance`): 9 restarts (a same-mode set, only `SUNIT_AnimInit`'s rate, the first advance from 0);
    `+0x48` equal across all 4 117 windowed pairs, none of which crosses a rate change; 476 pairs below rate `0x100`,
    none where re-scanning the stood frame changes the result; 301 monster sequence starts with `+0x38` 0 and
    `+0x34 = +0x48 = rows << 8`; no sequence step past the user's record. `[C]` for the restarts and the sequence start (run:2026-10-30-anim-p3b).
  - *The plain monster attack* (`mon-attack-frame`, `delivery-frame`): with no used skill, A1's and A2's kind-0 events of
    code 1 are followed in their frame by the attacker's hit (12 973 of 13 344; 5 187 of 5 293); events of code 2 by none
    (A1 2 061, A2 187). 18 168 of 18 347 monster A1/A2 hits fall in a frame of the attacker's kind-0 dispatch.
  - *Objects* (`chest-queue`): 161 object event-1 dispatches, none followed by a mode set or an animation start of that
    object; no `OQ` line is logged at 0x005863B7 (the chest's queue). No chained pair of object start draws (the
    checker's `chain-OA-OA` 0, 8 broken).
  - *Mid-mode rate calls* (`sr-midmode`): the record changes at 52 player calls from `ITEMS_AttachToOwner` and 54 from
    `SKILLS_ApplyAuraStats`, and at 1 390 monster calls (`MonInitMode` 1 363, `AURA_ApplyToTarget` 27), the frames
    with it at 1 355.
  - *Terms* (`rate-terms`): 13 693 monsters' first rate call with no state and no mod flags carries stats 67/68/69 =
    75/100/100, 2 carry 75/95/100; 16 962 of 17 199 plain player calls carry the hands' item stat 93 sum.
- **Conclusion:** the S6a rows are settled in plan 0066's inventory (`anim-timing.md`, each *Route* cell's S6a note).
  **Contradicted in part:** timing § I2 `MonAttackFrame`'s "strikes on each of its scheduled events (any code 1–4)": a
  code-2 event of a no-skill A1 or A2 is followed by no hit in 2 248 of 2 248 dispatches, against 18 160 of 18 637 for
  code 1; which test separates them (`MonEventDispatch`'s kind-0 path or `MON_MeleeHit`) is not read (→ c, S6c). The
  spec's "15 restarts" counts the logs of part 2 by another rule; 9 is this tally's (a same-mode set, then an advance
  of that unit). (run:2026-10-30-anim-p3b)
