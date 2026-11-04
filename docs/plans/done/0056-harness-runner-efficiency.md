# 0056 — Harness runner efficiency: one shared runner library, and several cases per game launch

> **Status:** done (closed 2026-11-03, `lane/c56`; ADR-0028 proposed, for the owner); approved by the owner 2026-10-30 ("as recommended": questions 1–7); drafted by the architect (`lane/plans56`, 2026-10-30)
> **Created:** 2026-10-30
> **Owner skill(s):** reverser (phases 1–3), architect (phase 4)
> **Related ADRs:** 0028-case-and-process-in-experiment-records (proposed), 0003-runtime-experiments, 0011-harness-slots, 0014-scope-game-simulation, 0022-scope-server-frame

## TL;DR

How do harness lanes spend less wall time and fewer tokens per kept session, without losing what makes a log
evidence? Two changes. (a) **One shared runner library**, `tools/harness_runner.py`, holding launch, the readiness
wait on an explicit logger ready line, save install, stop, case marks, and a background batch with one wait. It
replaces the per-lane copies (31 `tools/*_sessions.py`, 11 684 lines), and each runner migrates **when its plan next
uses it**, not all at once. (b) **Several cases per game launch**: return to the menu or warp between cases instead of
relaunching, with a written rule for when a case needs a fresh process. Once the plan is done, the library and its
no-game tests exist, the fresh-process rule is in `harness-play.md`, one pilot batch has measured the gain against the
baseline below, and an ADR records what a session and a process mean for a log's provenance.

## Context

The owner approved this work on 2026-10-30, after an analysis of 17 harness lane transcripts:

- about **45%** of wall time was blocked on sessions, about **30%** was model generation, and the gate took about **6%**;
- about **25%** of launches were dev runs or reruns (a broken readiness wait, a crash, a wrong install);
- the boot to a playable game (wine, menu steps, gdb attach) is **about 60 s**, so roughly **25%** of a session's time.

**Quick fixes already in flight, not repeated here.** These are being done now on `lane/hx`: the readiness-wait bug in
the h1a and h1c runners, the unattended-batch rule and the smoke-test rule. This plan starts after `lane/hx` merges.
The library implements those rules (Phase 1) but does not restate them; `harness-play.md` stays their home.

**What the runners share today.** Every runner restores the slot's aside and installs a save (`tools/saves.py`), starts
`tools/d2run.py` (seed, gdb file, steps, `--after`, `--install`, `--log`), polls the log for a substring until it
appears (`"PLR "` in `tools/h6g_sessions.py`, 180 s, every 3 s), hides the window, then runs its own commands
(`d2pilot.py`, `xdrive.py`, `quest_sessions.py act`, waits on a line count) and stops the slot (`tools/slots.py stop`).
`run_session` is written 24 times, `sh` 24 times, `hide_window` 16 times. The game-specific parts are the session
table and the command kinds. The launch skeleton is the same in every runner.

**What a second game in one process carries.** This is already recorded, and it is why some cases need a fresh process:
- `g_HitClassCounter` is process-wide and never reset (frame/0001 § 6, data:g_HitClassCounter@0x0088CAD0). Plan 0055
  Phase 2b requires a fresh single-player process per session for this reason, and **that requirement stays**.
- `/players` survives *Save and Exit* (monsters/experiments.md, run h4b session 5).
- On a second game, `tools/drlg.py` fails because the DT1 lists are those already loaded, and `parse_log` refuses a log
  that holds a second game (monsters/experiments.md, the h4b deviations). The split logs `…-game1.log` / `…-game2.log`
  are the precedent for cutting a log at the second game's start.
- Whether `-seed N` also sets the map seed of a second game in the same process has not been measured. Phase 2 does.

**Baseline** (ledger rows; wall per kept session = lane wall / kept sessions, tokens likewise):

| Lane | Plan batch | Kept sessions | Wall / kept (min) | Tokens / kept |
|---|---|---|---|---|
| `lane/h1c` | 0038 H1c | 7 | 7.4 | 39k |
| `lane/h6g` | 0038 H6g | 8 | 13.3 | 67k |
| `lane/p50e` + `lane/p50f` | 0050 P2 parts 1–2 (four rows) | about 80 | 5.6 | 21k |
| `lane/h6c` | 0038 H6c | 6 | 21.5 | 101k |
| **Mean of the four** | | | **11.95** | **57k** |

## Phases

### Phase 1 — The library and its no-game tests
- **Owner skill:** reverser (tools; no Ghidra; **one slot** from 1–2, given in the prompt, for the smoke sessions only)
- **Starts when:** `lane/hx` is merged and this plan is approved.
- **What:** `tools/harness_runner.py`, which keeps the steps every runner shares and leaves the session tables and the
  command kinds to the runners:
  - `launch(slot, seed, gdb, steps, install, log, after, game_args)`: wraps `d2run.py` with the slot's memory limit
    (`MEM_MAX`, 4G) and a new session group, and records the start;
  - `wait_ready(log, ready, timeout)`: waits for an **explicit ready line** that the logger prints once the character
    is in game. The line is a fixed tag in the gdb file (for example `RDY`); a runner that still uses a substring
    (`"PLR "`) passes it explicitly. The wait reports *ready*, *timeout* or *game gone*, never a silent pass;
  - `install(slot, tag, saves)`: the `restore`/`aside`/`install` sequence of `harness-play.md`, checked;
  - `stop(slot)`: `slots.py stop`, confirmed by `slots.py status`;
  - `mark(stem, case, event)`: a sidecar `<stem>.marks.tsv` with the case name, the event (start, ready, end, fail), the
    wall time and the log's line count at that moment; and `split(log, marks)`, which cuts a multi-case log into
    per-case logs at the game-start lines, the way the h4b `-game1`/`-game2` split was cut;
  - `batch(cases, …)`: runs a list of cases in the background and writes one status file at the end (kept, failed,
    rerun, wall per case). The lane starts it once and waits once, following the unattended-batch rule from `lane/hx`.
  - `tools/test_harness_runner.py`: no-game tests with fake logs and fake processes for the ready wait (ready, timeout,
    game gone), the marks, the split and the batch status.
  - One runner is migrated as a worked example, chosen by the plan the pilot uses (Phase 3), and its documentation
    goes in `tooling.md` § Runtime harness.
- **Outputs:** `tools/harness_runner.py`, `tools/test_harness_runner.py`, the migrated example runner,
  `.claude/skills/reverser/references/tooling.md` (a section on the library), `harness-play.md` (the migration rule).
- **Done when:** the tests pass with `python3 -I`. Two smoke sessions on the assigned slot, one through the migrated
  runner and one through its pre-migration copy on the same save and seed, give logs that the plan's checker reads with
  the same result. The **migration rule** is written in `harness-play.md`: a runner moves to the library when its plan
  next uses it; a runner is never deleted while a kept log's record cites it; a new runner is written on the library.

### Phase 2 — Several cases per launch, and the fresh-process rule
- **Owner skill:** reverser (harness; **one slot** from 1–2, given in the prompt)
- **Starts when:** Phase 1 is accepted.
- **What:** two ways to switch cases in one process, both measured. The **menu return** is *Save and Exit* (the
  `d2pilot.py join leave` click), then installing the next case's save, then `enter-sp.steps`. The **in-game switch** is
  a waypoint, `-act`, or a scripted walk between cases that share a save. A short probe answers four questions:
  1. does `-seed N` set the map seed of the second and later games in one process (the log's seed lines say)?
  2. does a save installed while the process sits at the menu load in the next game?
  3. which process state carries across games? Start from the list in Context, and look for more;
  4. what does a case switch cost in wall time, compared with a ~60 s boot?
- **Outputs:** the probe's record in `docs/findings/harness/` (or the plan's implementation log when no finding
  directory fits), `harness_runner.py` gains `next_case` (menu return) and the case loop, and `harness-play.md` gains
  **§ Fresh process**.
- **Done when:** each of the four questions has a measured answer from at least three case switches. § Fresh process
  names when a case **must** start a fresh process: it is the first case of a batch; its checker models process state
  (`g_HitClassCounter`, DRLG tile lists, `/players`, or any state the probe finds); its plan says so (0055·P2b); the
  map seed is not controlled for a later game (if question 1 says so); or the previous case in the process failed or
  timed out. **Every other case may share a process.** A per-launch cap on cases and on wall time is set from the
  probe's memory readings and stays inside the 4G limit.

### Phase 3 — Pilot on the next harness batch that needs it
- **Owner skill:** reverser (harness; **one slot**, given in the prompt; inside the batch's own lane, not a separate slot)
- **Starts when:** Phase 2 is accepted, and the pilot batch's own gates are met.
- **What:** the next batch that needs a harness runs on the library. The recommended pilot is **0052·P2**'s first batch
  (AI decisions; its checker models no DRLG state, so cases may share a process unless § Fresh process says otherwise),
  on a new `tools/ai_sessions.py` written on the library. **0055·P2b**'s pilot window uses the library with one fresh
  process per session, as that plan requires, and measures the library alone. Whichever comes first is the pilot; the
  second, when it runs, is recorded as well.
- **Outputs:** the pilot lane's usual outputs. Its implementation-log entry also gives launches, kept sessions, kept
  cases, dev or rerun launches, and wall and tokens per kept session, and its ledger row carries them in the Slot cell.
- **Done when** (measured on the pilot lane against the baseline):
  - **wall per kept session ≤ 9.0 min** and **tokens per kept session ≤ 43k**, both 25% under the four-lane mean
    (11.95 min, 57k). The stretch target is under `lane/h1c`'s 7.4 min and 39k;
  - **dev or rerun launches ≤ 10%** of launches (about 25% in the analysed transcripts);
  - on a multi-case pilot, **launches per kept case ≤ 0.5**, and every case log produced by `split` checks the same
    as a fresh-process log would. At least two cases are re-run in a fresh process for comparison, with 0 mismatches.
  A pilot that misses a target says why: the batch kind, survivability, crashes, or the model's generation time. For
  generation time, the analysis's 30% is the reference.

### Phase 4 — Evaluate and record
- **Owner skill:** architect
- **What:** compare the pilot with the baseline. Then propose an ADR that amends ADR-0003's notion of a session: a
  *case* is the unit an experiment record cites, a *process* may hold several cases under § Fresh process, and the
  marks file and the split are part of a log's provenance. Settle the per-launch cap.
- **Outputs:** an ADR (proposed, for the owner), and the plan closed in `done/`.
- **Done when:** the entry gives the pilot's numbers next to the baseline table. Each target is marked met or missed,
  with the reason for a miss. The ADR is proposed and the migration rule is confirmed or changed.

## Resources and limits

- **Harness:** at most **two harness lanes** at once, on **slots 1 and 2** (slot 0 is the owner's). Phase 1 takes one
  slot for two smoke sessions; Phase 2 takes one slot for the probe, which is about one lane run; Phase 3 runs inside
  the pilot batch's lane and its slot. This plan never adds a third harness lane.
- **Memory:** every run stays under `d2run.py`'s `MemoryMax=4G` scope. Multi-case launches are capped (Phase 2) so that
  a long-lived process stays inside it. No Ghidra in any phase, so the two-Ghidra limit is untouched.
- **Rotation:** lanes past about 4 h checkpoint, write a resume note and stop.
- **Estimate** (not measured): P1 one lane run; P2 one; P3 no extra lane (it is part of the pilot batch); P4 one
  architect run.

## Owner questions (recommendations)

1. **Migration: incremental or all at once?** *Recommendation: incremental.* A runner moves when its plan next uses
   it, every new runner is written on the library, and old runners stay as long as a kept record cites them. Migrating
   all 31 now would cost lane runs, and runners nobody reruns would gain nothing.
2. **Multi-case: default or opt-in?** *Recommendation: opt-in per batch.* The lane's prompt says whether a batch may
   share a process, and § Fresh process always wins. This makes 0055·P2b's fresh-process sessions the plain default.
3. **Pilot batch.** *Recommendation: 0052·P2's first batch* for the full pilot (library plus multi-case), and
   0055·P2b's pilot window for the library alone (one fresh process per session, unchanged). **0050·P2 part 3 is not
   held for this plan:** it takes the next free slot on `tools/anim_sessions.py` as it stands.
4. **Slot order for Phase 2.** *Recommendation:* the probe takes the next free slot **after** 0050·P2 part 3 and does
   not take a slot from 0038, 0046 or 0050. If 0052·P2 is ready first, the probe runs as the opening sessions of that
   lane, in the same slot.
5. **If `-seed` does not hold for a second game.** *Recommendation:* keep the in-game switch (waypoint or walk inside
   one game, one seed) for cases that share a save, and give every seed-dependent case a fresh process. Do not patch
   the seed in memory to force it; that would be a new evidence form and would need its own ADR.
6. **An ADR for case and process.** *Recommendation: yes, at Phase 4* (architect, proposed for the owner), because
   experiment records start citing cases inside a shared process. That changes how a log's provenance reads, and the
   change would be costly to reverse.
7. **Lane models.** *Recommendation:* Opus for Phase 1, because 31 runners will adopt the API it designs; Sonnet for
   Phase 2's probe and for the pilot's harness sessions, following the lane-models rule.

## Open questions

- Whether the 30% spent on model generation can be cut by the runner at all: shorter status files, and one wait in
  place of polls. The pilot measures it, but it is not a target.
- Whether `split` can cut on a ready line instead of a game-start line for loggers that print no game-start tag.

## Implementation log

_(lanes append dated entries as phases land)_
- **2026-10-30 — Approved (owner; recorded by the architect, `lane/plans57`).** "As recommended": all seven owner
  questions answered as the plan recommends. Q1 incremental migration; Q2 several cases per launch opt-in per batch, §
  Fresh process wins; Q3 the full pilot is 0052·P2's first batch, 0055·P2b's pilot window tests the library only, and
  0050·P2 part 3 does not wait; Q4 the Phase 2 probe takes the next free slot after 0050·P2 part 3; Q5 if `-seed` does
  not hold, cases switch inside one game, no in-memory seed patching; Q6 the case-and-process ADR is proposed at Phase
  4; Q7 Opus for Phase 1, Sonnet for the probe and pilot sessions. **Phase 1 starts after `lane/hx` merges.**
- **2026-10-30 — Phase 1, no-game part landed (`bef3f51d`); smoke sessions pending a slot (reverser, `lane/p56a`, from `main`
  `b75144a9`; no slot, no Ghidra).**
  - **Library:** `tools/harness_runner.py`: `new_stem`, `install` (restore when aside, aside, install; each return
    code checked), `launch` (`d2run.py` in a new session group, `--mem-max 4G` explicit, a `launch` mark), `wait_ready`
    (the first line tagged `ready`, or starting with it when it holds a space; outcomes `ready`, `timeout`, `gone`, the
    log read incrementally), `wait_count`, `mark` (`<stem>.marks.tsv`: case, event ∈ launch/ready/start/end/fail, wall
    time, line count, note), `split` (one log per `start` mark, optional `--at TAG` snap to a game-start line before
    the next mark, the header repeated with a `# split` line), `stop` (`slots.py stop N`, then `slots.busy(N)` empty
    within 30 s), `batch` (one JSON status file at the end, also when interrupted: kept, failed, rerun, wall per case),
    `bg` (detached start, one `tail --pid` wait). Documented in tooling.md § The runner library.
  - **Tests:** `python3 -I tools/test_harness_runner.py`: 44 tests, OK (fake logs, fake and short real child processes,
    fake clocks; the worked example's session end to end on fakes). `tools/test_h1_ready.py` (9) OK; its source check
    now looks for the library call in h1a.
  - **Worked example: `tools/h1a_sessions.py`** (the pilot's own runner, `tools/ai_sessions.py` for 0052·P2, does not
    exist yet and is written on the library under the migration rule; H1a is the deterministic, several-loads-per-
    process runner whose checker `tools/sweep_h1a.py` gives a comparable result). Session table, clicks and sleeps
    unchanged; it still writes `<stem>.marks.jsonl` for the checker, plus the library's `.marks.tsv`; `run` is one
    `batch` with `workspace/logs/h1a/<RUN>-s<N>.status.json`. `tools/h1c_sessions.py` is untouched and still imports
    h1a's bool `wait_ready`. `tools/anim_sessions.py`, `tools/skills_sessions.py` and their loggers are untouched.
  - **Migration rule:** harness-play.md § Runners and the library.
  - **Resume note: the two smoke sessions (Done when), on the slot N the next prompt gives (1 or 2).** Same save
    (`workspace/runtime/h1a`, the 38 kept H1a case directories, already built) and same seed (session `order`, 27204),
    two of its loads (`hdrshort`: a menu load refused with a code; `param`: a load that passes, then Save and Exit):
    1. `python3 -I tools/slots.py status` shows slot N with no game, driver or aside left; nothing else of another
       lane is touched.
    2. **Pre-migration copy**: `tools/h1a_sessions.py` at `efac8f91`. Check that the main checkout still holds it
       (`git -C /home/igor/Work/recompilcation-project diff --quiet efac8f91 -- tools/h1a_sessions.py` exits 0 while
       this lane is unmerged); otherwise `git worktree add --detach <scratch>/pre efac8f91` with a `workspace` symlink
       to the main `workspace/`, and run from there. Command (run from that checkout):
       `python3 -I tools/h1a_sessions.py run --slot N --tag p56a --cases workspace/runtime/h1a --run dev-p56a-pre --only hdrshort,param order`
    3. **Migrated runner**, from this worktree:
       `python3 -I tools/h1a_sessions.py run --slot N --tag p56a --cases workspace/runtime/h1a --run dev-p56a-lib --only hdrshort,param order`
       Run 2 then 3 as one background command with output to the lane's scratch, and wait once (`tail --pid`); about
       3 min each.
    4. Cleanup: `python3 -I tools/slots.py stop N`, `python3 -I tools/saves.py --slot N restore p56a`, `saves.py --slot N
       status` (no aside), `slots.py status`.
    5. Check both with the plan's checker, output to files:
       `python3 -I tools/sweep_h1a.py check workspace/merged/data/global/excel workspace/runtime/h1a workspace/logs/h1a/dev-p56a-pre-sN-27204-order.log`
       and the same for `dev-p56a-lib-…`. Done when both give the same comparison count and 0 failing, and the
       per-case lines are equal once the log names are replaced. Also on the lib log: `harness_runner.py marks`
       (launch, ready, two start/end pairs; the `.marks.tsv` start lines equal the `.marks.jsonl` lines),
       `harness_runner.py split` (two pieces), `harness_runner.py status workspace/logs/h1a/dev-p56a-lib-sN.status.json`
       (kept 1). Both are dev logs (`dev-` names, outside the H1a kept glob): write
       `workspace/logs/h1a/p56a-manifest-dev.sha256` for both logs, their marks, status and check outputs, passing
       `sha256sum -c` from `workspace/logs/h1a`. Then file the Phase 1 review request.
  - **Next:** a slot for the two smoke sessions, then the Phase 1 review.
- **2026-10-30 — Phase 1, smoke sessions run (reverser, `lane/p56a`, slot 2).** Main merged into the lane first (ledger
  conflict kept both). Same save and seed (27204), cases `hdrshort,param`: pre-migration runner (`efac8f91`) and the
  migrated runner each give `TOTAL H1A 19 comparisons, 0 failing; d2sio logs failing 0` (hdrshort 7, param 12); the
  per-case lines are equal; only the `d2sio WRITE` sha differs (the saved file carries a time stamp). Each session 60 s
  wall; migrated: launch to `ready` 6.6 s (the new `RDY` line, smoke OK), to first case start 14.6 s. `marks` (launch,
  ready, two start/end pairs; starts equal the `.marks.jsonl` lines), `split` (2 pieces), `status` (kept 1) read right.
  Manifest `workspace/logs/h1a/p56a-manifest-dev.sha256`. Slot 2 stopped, saves restored. Review request filed.
- **2026-10-30 — Phase 1 lane check (lane/p56a, Tier B, architect): accept with fixes (2); Phase 2 (the probe) released.**
  Tests re-run: `test_harness_runner.py` 44 OK, `test_h1_ready.py` 9 OK, `test_slots.py` 33 OK; `sha256sum -c` of
  `p56a-manifest-dev.sha256` OK (all lines); gate green. API read against tooling.md § The runner library and
  harness-play.md § Runners and the library: matches. Rules kept: `--mem-max 4G` is in every launch command line (and
  tested), `launch`, `launch_argv` and `stop` refuse slot 0 (tested), `stop` returns True only once `slots.busy(N)` is
  empty and h1a turns a busy slot into a failed session. The migrated h1a keeps its steps, clicks and sleeps; `h1c`'s
  import of the bool `wait_ready` still works. Fixes: the table's `stop` signature omitted `timeout`/`out`; `lines()`
  now matches the first word (a bare tag line counts) and the table now says so; the plans index still read "P1
  starts after `lane/hx` merges". The ledger row set to 226 708 tokens, 80 calls, 15 min. Phase 2 may start; it takes
  the next free slot after 0050·P2 part 3 (Q4).
- **2026-10-30 — Phase 2 probe (lane/p56b, reverser, slot 2): several games in one process; `-seed` holds; § Fresh process written.**
  Tools: `harness_runner.next_case` (the menu return, 3 tests added, 47 OK), `tools/probe0056.py`, logger
  `tools/gdb/probe-0056.gdb` (= `mon-special.gdb` + `tools/gdb/probe-state.py`: `PST` g_HitClassCounter `0x0088CAD0` and
  g_PlayersOverride `0x00883D70` once a second on the `PLR` hook, `HCP` at `HitClassPick` `0x0057CE30`). Smoke: dev1
  (1 switch), dev2 (2 switches, 2 fights), dev3 (the `start` mark placement and `split`); dev logs `dev-dev*-s2-4801-probe.*`
  apart from the kept run, `workspace/logs/p56b/run:2026-10-30-multicase-probe-s2-4801-probe.log` (47 653 lines, 8.7 MB,
  sha256 `f3bf2381b4d042f5…`), seed 4801, expansion normal, UniqNova / ProbeB (a tool-built copy of the recipe under another
  name) alternating, `/players 5` in game 0, Nova fights (City of the Damned) in games 0, 2, 4; 292 s for five games.
  Marks of the kept run were written by the first revision of `next_case` (`start` after the load); the numbers below
  are cut by the `end` marks, and dev3 shows the final placement splits exactly at each game's first `WND` line.
  1. **Does `-seed N` set the map seed of the second and later games? Yes `[C]`.** The `LC0` level seed of every level id
     is the same in all five games (103 to 108: `75e10186:0000029a` … `75e1018b:0000029a`, `base` 1977680159), with two
     different characters alternating and in all three dev runs. The game seed `gs` of the `RW` lines is not constant (it
     is drawn from) and is not the test.
  2. **Does a save installed at the menu load? Yes `[C]`.** Four of four switches: the file copied over the same name in
     the slot's saves directory while the game sat at the menu (`saves.py` refuses while the slot is busy, so a plain copy),
     SINGLE PLAYER, OK, the difficulty box, and a new `PLR` within 90 s each time (plus 5 more in the dev runs).
  3. **What carries over `[C]`:** `g_HitClassCounter` (0..3 in game 0, the first pick of game 2 read 3, then 6 in game 4;
     games 1 and 3 had no hits), `g_PlayersOverride` (0 then 5 in game 0, 5 in games 1 to 4), the DT1 tile lists
     (`TL` lines 634 in game 0, 143 in game 2, none in games 1, 3, 4; `TINIT` 97, 25, 109, 21, 106), and, from earlier
     records (`docs/findings/monsters/experiments.md` h4b session 5, `tools/drlg.py` `parse_log`), `/players` through Save and Exit
     and the DRLG failure on a second game; the `parse_log` refusal itself does not fire on this probe's log (one `WNDARM`
     line with `levels`). Not carried: the level seeds
     (question 1) and the character (the save). No other state was looked for beyond these.
  4. **Cost.** Switch (Escape to the next `PLR`): 18.5, 19.5, 19.4, 19.5 s, about 15.5 s of it the runner's fixed
     sleeps (1.5 + 8 + 1 + 3 + 2) and about 4 s the game's own load. Launch to the first `PLR` (install, launch, the
     steps' clicks): 20.1, 20.6, 20.9, 21.2 s on this logger. The 60 s of the baseline therefore is not the game's boot
     here `[I]`: by subtraction it would be the sum of stop, restore, aside, install and the ready wait around it, which
     this probe did not time (lane check ruling 2). The saving per case is that
     bookkeeping, and the switch's sleeps could be cut (`menu_wait` 8 s was not tuned). Memory: the game's scope held
     203 to 227 MB (peak 227.5 MB) across the five games; gdb 66 MB; no trend.
  The in-game switch (waypoint or walk) was not measured: question 1 came out so that the menu return keeps the seed,
  and the seed-dependent cases take a fresh process by rule. § Fresh process in harness-play.md names the five conditions
  and the cap (8 games or 40 min per launch, `[I]` beyond the five measured). Slot 2 stopped, saves restored (no aside).
- **2026-10-30 — Phase 2 lane check (lane/p56b, Tier B, architect): accept with fixes (4); Phase 3 may start.**
  Recounted from the kept log with `tools/probe0056_check.py` (new; output `...probe.check.txt`, manifest
  `workspace/logs/p56b/manifest-run-multicase-probe.sha256`, dev files in `manifest-dev.sha256`, both `sha256sum -c` OK;
  47 tests OK, gate green): `LC0` one (seed, base) pair per level id 103 to 108 over the five games; `PST`/`HCP` counter
  0..3, 3..6, 6..9 with picks 0,1,2 / 3,4,5 / 6,7,8 in games 0, 2, 4; `g_PlayersOverride` 0 then 5, then 5; `TL` 634, 0,
  143, 0, 0; `TINIT` 97, 25, 109, 21, 106; switches from the marks 18.5, 19.5, 19.4, 19.5 s. All four answers stand `[C]`
  (answer 1 for seed 4801 and Act IV only). Rulings:
  1. **Cap 8 games / 40 min stays `[I]`**; the memory readings (203 to 227 MB, peak 227.5 MB) show no trend over five games.
  2. **The "~60 s boot" is not the game's boot on this logger (launch to first `PLR` about 21 s), but "it was runner
     bookkeeping" is `[I]`**: stop, restore, aside and install were not timed. **Phase 3 still makes sense**, with a
     smaller prize: a switch (19.5 s) saves about 1.5 s against a launch to `PLR` (21 s) plus the bookkeeping, so the
     multi-case target ("launches per kept case <= 0.5") is reachable but its wall saving is the bookkeeping only, and
     the `<= 9.0 min` per kept session has to come from the library, fewer dev launches and shorter waits. Phase 3 times
     stop, restore, aside and install per fresh case and the sleeps of `next_case` (15.5 s of the 19.5; `menu_wait` 8 s
     untuned), and reports both against the baseline.
  3. **Fresh-process rule against the owner's answers:** 0055 P2b (condition 3) and seed (condition 4) match; Q2's opt-in was
     missing from § Fresh process and is added. The in-game switch of the Phase 2 text was not measured; owner Q5 needed it
     only if `-seed` failed, so the omission is within scope.
  4. **Not caught by `parse_log`:** a `split` piece of a later game holds no `WNDARM` with `levels`, so `tools/drlg.py` runs
     on it unchecked; § Fresh process rule 2 is the only guard. Noted for Phase 3's checkers (tools/drlg.py is the
     archivist/static lane's; no backlog entry, the rule already covers it).
- **2026-11-03 — Phase 3 pilot ran on plan 0052·P2's first lane run (`lane/p52a`, slot 2, `tools/ai_sessions.py` on the
  library).** Figures in [0052's log](0052-monster-ai.md) and [ai/experiments.md run:2026-11-03-ai](../../findings/ai/experiments.md):
  19 launches (10 kept-batch, 9 development; one kept-batch launch was a rerun), 31 kept sessions = 31 kept cases,
  launches per kept case 0.32 (target ≤ 0.5: met; 0.61 counting development), dev or rerun launches 10 of 19 = 53 % (63 % with the two fresh comparison launches counted as reruns)
  (target ≤ 10 %: **missed**, the logger and the waypoint staging were new; two of the comparison launches are by
  design), harness wall 3.6 min per kept session (withdrawn by the Phase 4 entry below: 4.5 against the target, 3.0 and 3.5 harness; target ≤ 9.0: met; the stretch 7.4: met), tokens about 17 k (measured) per kept
  session (target ≤ 43 k: met, provisional until the ledger row), two cases re-run in a fresh process, 0 mismatches
  (met). A case switch by menu return took 18.7 s; the shared-process cases checked like the fresh ones (the checker
  models no process state); the lane's prompt supplied the per-batch opt-in (owner answer 2); Phase 3 names this batch as the pilot. The
  library needed nothing new; a runner-side staged-level check (a case that never left its start level is failed and
  re-run in a fresh process) is in `tools/ai_sessions.py`, not in the library.
- **2026-11-03 — Phase 4, evaluated and closed (architect, `lane/c56`).** Recount: `tools/pilot0056_recount.py`, output
  `workspace/logs/p56/phase4-recount.txt`; `d2run-<pid>` scope lines of the journal, matched to the marks' pids, kept as
  `phase4-scope-peaks.txt`; `manifest-phase4.sha256`, `sha256sum -c` OK. The pilot beside the baseline (wall and tokens as the
  baseline counts them: lane wall and lane tokens over kept sessions, here 139 min and 530 967 over 31 kept cases):

  | Lane | Plan batch | Kept sessions | Wall / kept (min) | Tokens / kept |
  |---|---|---|---|---|
  | `lane/h1c` | 0038 H1c | 7 | 7.4 | 39k |
  | `lane/h6g` | 0038 H6g | 8 | 13.3 | 67k |
  | `lane/p50e` + `lane/p50f` | 0050 P2 parts 1–2 | about 80 | 5.6 | 21k |
  | `lane/h6c` | 0038 H6c | 6 | 21.5 | 101k |
  | Mean of the four | | | 11.95 | 57k |
  | **`lane/p52a` (pilot)** | 0052 P2 first run | 31 cases in 9 kept launches | **4.5** | **17.1k** |

  | Target | Limit | Pilot | Verdict |
  |---|---|---|---|
  | Wall per kept session | ≤ 9.0 min (stretch < 7.4) | 4.5 min | **met**, stretch met |
  | Tokens per kept session | ≤ 43k (stretch < 39k) | 17.1k | **met**, stretch met |
  | Dev or rerun launches | ≤ 10 % | 10 of 19 = 53 % (63 % with the two fresh comparison launches) | **missed** |
  | Launches per kept case | ≤ 0.5 | 10/31 = 0.32 (0.61 with development) | **met**, reading below |
  | Fresh comparison | at least 2 cases, 0 mismatches | `a1-jail` 385, `a2-halls` 522 decisions, 0 mismatches | **met**, weak test below |

  **The miss.** The cause is the batch kind: a new logger and new waypoint staging. The 9 development launches were the first
  logger, a wrong click point, rev 1's missing argument read, `PathPlan`'s late returns and the Necromancer smoke; the rerun
  was a waypoint list that did not open. None was a readiness wait, a crash or a wrong install, the classes the library was
  written against. Two things make the percentage look worse than the cost. Development took 15.9 of the 108.1 harness minutes
  (15 %, 16 % with the failed try), and sharing shrinks the denominator: counted per case run, 13 of 44 were development or
  not kept, 30 %, against about 25 % in the analysed transcripts. So the pilot does **not** show fewer dev runs. That the
  logger's newness explains the miss stays `[I]`.

  **Wall figure.** "3.6 min per kept session" **does not stand**; it is withdrawn here and in 0052's log. The kept launches
  sum to 91.15 min (2.94 per case), the four batches to 92.26 min (2.98; 91.15 plus the failed try and the runner's seams), all
  19 launches to 108.07 min (3.49). The "about 110 min" was probably that last sum rounded up, and 110/31 gives 3.55, not 3.6;
  the first launch to the last end is 118.89 min (3.84). No record gives 3.6. **The figure against the target is 4.5**, because
  the baseline divides lane wall. The harness figures are **3.0** (kept batches) and **3.5** (with development). The ledger row's
  Slot cell still says 3.6; the ledger takes appends only, so this review's row states the correction.

  **What gave the gain. Not the shared process.** Phase 2's lane check (ruling 2) asked Phase 3 to time the bookkeeping; the lane
  did not, and the marks give it. A fresh process costs 0.49 to 0.66 s from one launch's end to the next (stop, restore,
  aside, install; 6 gaps; not separated further) plus 18.1 to 19.1 s to ready (10 launches, mean 18.6). A switch costs 18.2 to 20.4 s
  (24 switches, mean 18.8). The saving is about 0.4 s per case, about 10 s of 92 min. The bookkeeping reading of the "60 s" boot is
  **refuted on this logger**, and the origin of the 60 s stays unknown. The launches-per-case target is met and buys almost
  nothing. The sleeps of `next_case` (about 15 s, untuned) are the only visible room, and nobody has measured a tuned switch. The
  gain must come from the library's one-wait batch and from the case kind; one lane cannot separate those.

  **Fairness.** One lane. Its cases are unattended: a clvl 85 Sorceress, a waypoint and a Nova sweep of 130 to 300 s, no route
  to find, no survivability risk, no owner step. That is the cheapest kind of log. The 62 % and 70 % under the mean compare it
  with vendor and route work (`lane/h6c`, `lane/h6g`) and are not a fair measure of the library. The nearest baseline kind is
  `lane/p50e` + `lane/p50f`: **20 % under on wall and 18 % on tokens**, and even that is not controlled. Counted per kept process
  (9), the lane is 15.4 min and 59k, so the verdicts rest on a case counting as a session. The record shows that was the plan's
  intent (Phase 3 asks for both), but the two units are not the same work. Against the analysis's reference, non-harness wall
  was 30.9 of 139 min (22 %, against 30 % generation); that is not a generation measure.

  **Launches per kept case.** The target is about sharing inside a batch, and development has its own target, so 0.32 is the
  reading; 0.61 is stated beside it.

  **Fresh comparison.** Met, and weak. The repeats ran under other seeds (5203, 5204), so the logs differ. Each decision's
  inputs come from its own log, and the checker models no process state. It shows the checker's result does not depend on
  sharing, not that the process is unaffected.

  **Rule 5 ruling.** Launch 5202 ran `a5-glacial`, `a1-cloister`, `a1-catacombs` and `a3-durance` after `a4-cotd` and `a5-crystal`
  had stayed in the town. The runner of that batch had no stage check and reported both as kept; they were found afterwards.
  Against the rule's text this is outside its list; against its reason (a process whose state is not known) it is a deviation.
  The record did not state it, and now does. Ruling: **the rule stands and is widened.** (a) A stage not reached is a failure.
  (b) A batch that shares a process checks each case's stage before the switch; the check is only in `tools/ai_sessions.py`, so
  [a backlog entry](../../backlog/2026-11-03-architect-reverser-plan-0056-p4-stage-check-in-the-library.md) moves it to the
  library. Once it existed the rule worked: 5401's failure sent the batch to a fresh 5402. (c) A failure found only afterwards
  leaves the later cases of that process named in the record, kept only if their checker reads no carried state and the
  record gives the result without them. **The four cases stay.** Without them: 27 logs, 13 355 decisions, 11 472 compared, 0
  mismatches, every tier AI still at least 50 (Andariel 60, BloodLord 55, Wraith 68). The switches after the town cases took a
  normal 18.2 and 18.7 s. No conclusion leans on the four. harness-play.md § Fresh process holds the new text.

  **Evidence cost.** The weak separation is real, but the data do not lay it mainly on session length. Each of the rows with one
  logged first boundary showed it at the first decision and never another, up to 5 697 decisions (Hireable), 1 393 (Fallen). Long
  and short cases agree on three pairs (`a4-cotd` Megademon 90 and 8 decisions, one boundary each; `a2-halls` Mummy 81 and 36, five
  each; thin, and the per-game cap of 200 clips Hireable). The same rows show 2 to 22 distinct logged call sequences of up to
  eight boundaries (SkeletonMage 22, Vampire 19, SkeletonBow 12; FallenShaman, with two first boundaries, 35), which the checker does not compare. So most
  of the cost is **depth** (the claim stops at the first boundary) and **breadth** (one character, Normal, no curse, `AiCtl.state` 0
  at all 32 324 events), and neither is bought back by longer sessions. **Length does cost** where a row was still finding outcomes:
  BloodLord's last new boundary came at decision 52 of 55, in its one log. (Scarab's count mixes logger revisions, so it is no test.) The speed therefore cost little evidence in
  itself, but **the efficiency target is blind to it**: `a1-cloister` (60 decisions, 30 s) and `a1-andariel` (518, 636 s) each count as
  one kept case, and 39 % of all decisions are one Hireable outcome. The `[C]` is correctly scoped to first boundaries and
  stands. Lane speed should be read beside separation, not alone: ADR-0028 item 7, [the checker's line](../../backlog/archive/2026-11-03-architect-reverser-plan-0056-p4-separation-line-in-tools-ai.md),
  and the resume note of 0052 (a resumable model, state-control windows) are the remedy.

  **Cap settled: 8 games or 40 minutes.** Peaks of the kept scopes: 269.8 MB (8 games, 19.9 min), 270.3 (8, 26.2 min), 277.4 (7, 12.7 min), 351.4 (5,
  18.9 min), and one-game launches 254.6 to 620.7 MB; swap peak at most 140.8 MB. The game count does not drive the peak and the 4G
  limit is not close. The 40 minutes was never reached, so it stays `[I]`. Nothing measured favours raising the cap: fewer launches
  buy nothing.

  **Migration rule confirmed unchanged:** h1a migrated with an equal check, `tools/ai_sessions.py` was written on the library, and
  the library needed nothing new but the stage gate above. No runner was deleted.

  **`lane/p52b` is not counted before closing.** Done-when does not ask for it, and no verdict or ADR item would flip: wall and tokens
  are far inside their limits and the sharing arithmetic would come out the same on the same logger. It is useful as the only test of
  the `[I]` above, because it reuses this staging and changes the logger less. Its ledger row should carry the same figures in the
  Slot cell, and 0052's log the reading. If its dev share again sits far over 10 %, the attribution is wrong, and that goes to a
  backlog entry, not back to this plan. 0055·P2b's library-only window is recorded the same way when it runs (Phase 3).

  **Open questions, at close.** Generation time: not separable here (22 % non-harness wall). A `split` cut on a ready line: not needed
  by this pilot, left open. **ADR-0028 is proposed, not accepted; the owner decides.** The plan closes on Done-when, which asks
  for the ADR to be proposed; items 1 to 7 of the ADR do not reopen this plan.
