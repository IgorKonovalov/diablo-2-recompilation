# Animation experiments

Runtime records for [anim/0001](0001-modes-frames.md) and the later animation findings (plan 0050 Phase 2). Harness
and evidence rules: ADR-0003, ADR-0004, ADR-0011, ADR-0013, ADR-0014, ADR-0015, ADR-0021;
[tooling](../../../.claude/skills/reverser/references/tooling.md),
[harness-play](../../../.claude/skills/reverser/references/harness-play.md).

Harness runs (plan 0050 Phase 2): [run:2026-10-27-anim](#run2026-10-27-anim), **in progress**. Emulated runs
(ADR-0015, no wine, nothing native): [run:2026-10-27-anim-rates-emu](#run2026-10-27-anim-rates-emu).

## run:2026-10-27-anim

**Status: in progress.** `lane/p50e`, the first lane run of plan 0050 Phase 2, rotated at its checkpoint; the
sessions still owed are in the resume note of the [plan 0050 log](../../plans/0050-animation-frame-timing.md#implementation-log).
No claim of anim/0001–0003 is raised by this record yet: the findings' run sections are written when the run closes,
against the closing check. The numbers below are the checkpoint check's (`2026-10-27-anim-check-ckpt1.txt`).

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
  Normal. Logger `tools/gdb/anim.gdb` (`de08f7d2…`) sourcing `tools/gdb/pilot.py` (`1ad48a4c…`, unchanged) and
  `tools/gdb/anim.py` **rev 4** (`c5fa964f…`; every kept log's header says `ANIM logger armed rev 4`). Breakpoints
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
  share have the same steps.
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

- **Procedure** (from the worktree; the checks under a 4 GB scope):
  ```
  python3 -I tools/anim_sessions.py recipes && python3 -I tools/anim_sessions.py build --saves workspace/logs/anim/saves-2026-10-27-anim
  python3 -I tools/anim_sessions.py run --slot 2 --tag p50e --saves workspace/logs/anim/saves-2026-10-27-anim \
      --run 2026-10-27-anim <sessions of the batch>
  python3 -I tools/anim.py check $(cat workspace/logs/anim/2026-10-27-anim-ckpt1.lst) > workspace/logs/anim/2026-10-27-anim-check-ckpt1.txt
  python3 -I tools/anim.py replay-skills workspace/logs/skills/2026-10-25-skills-*.log workspace/logs/skills/2026-10-27-skills-*.log \
      > workspace/logs/anim/2026-10-27-anim-replay-skills.txt
  python3 -I tools/anim.py replay-combat $(cat workspace/logs/combat/c37p2-run.lst) > workspace/logs/anim/2026-10-27-anim-replay-combat.txt
  python3 -I tools/anim.py replay-combat $(cat workspace/logs/combat/p47b-run.lst workspace/logs/combat/p47h-run.lst) \
      > workspace/logs/anim/2026-10-27-anim-replay-combat-p47.txt
  ```
  Manifest `workspace/logs/anim/2026-10-27-anim-manifest-ckpt1.sha256` (`4dd51a04…`, 148 lines, one path base:
  `sha256sum -c` passes from `workspace/logs/anim/`): the 31 logs, their pilot outputs and screenshots, the batch
  outputs, the 43 saves, the list, the check output `2026-10-27-anim-check-ckpt1.txt` (`1bd13a13…`) and the three
  replay outputs. The development files are in `workspace/logs/anim/dev-p50e-manifest.sha256` (71 lines, same base).
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
- **Covers so far** (not a closing claim): see the resume note's per-case table.

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
