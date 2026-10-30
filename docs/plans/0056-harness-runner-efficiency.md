# 0056 — Harness runner efficiency: one shared runner library, and several cases per game launch

> **Status:** draft (architect, `lane/plans56`, 2026-10-30), for the owner's approval
> **Created:** 2026-10-30
> **Owner skill(s):** reverser (phases 1–3), architect (phase 4)
> **Related ADRs:** 0003-runtime-experiments, 0011-harness-slots, 0014-scope-game-simulation, 0022-scope-server-frame

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
