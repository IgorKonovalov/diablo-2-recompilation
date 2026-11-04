# ADR-0028 — A case is what a record cites, a process may hold several cases, and the marks and the split are provenance (amends 0003)

> **Status:** accepted (owner, 2026-11-04); sharing stays opt-in with a stated reason
> **Date:** 2026-11-03
> **Related plan(s):** [0056-harness-runner-efficiency](../plans/done/0056-harness-runner-efficiency.md) (Phase 4; pilot `lane/p52a`, [run:2026-11-03-ai](../findings/ai/experiments.md))

## Context

ADR-0003 reads as one launch, one session, one raw log: "each experiment's raw log goes to `workspace/logs/`. Its record
names the exact command lines, the `.gdb` and steps files and the checker." Plan 0056 made several games in one game
process routine. [run:2026-11-03-ai](../findings/ai/experiments.md) cites 31 case logs cut from 9 launches, and its `[C]`
statements rest on them. ADR-0003 does not say what such a citation means, what else a cut log depends on, or what the
earlier cases in the process do to a later one. Phase 2 measured that state does carry across games: `g_HitClassCounter`,
`/players`, the DT1 tile lists; the level seeds under `-seed N` do not change.

The pilot also changed the reason for sharing. Phase 2 expected a case switch to save the launch's bookkeeping. From the
pilot's marks, a fresh process costs 0.49 to 0.66 s (stop, restore, aside and install, 6 gaps) plus 18.1 to 19.1 s to ready
(10 launches, mean 18.6); a switch costs 18.2 to 20.4 s (24 switches, mean 18.8). That is about 0.4 s per case, or about
10 s of a 92 min run ([plan 0056's Phase 4 entry](../plans/done/0056-harness-runner-efficiency.md#implementation-log)). 15 s
of the switch are untuned sleeps, so a tuned switch might save more; that is not measured. The lane's large gain over the
baseline did not come from sharing a process. Sharing has a cost in return: launch 5202 ran on for four kept cases after
two cases had failed unnoticed.

Separately, the same run's 12 614 compared decisions hold one predicted first boundary for each of ten tier AIs. A count of
decisions or cases says little about what a comparison tested, and a cheap case makes the count cheaper still.

## Decision

Amending ADR-0003, and leaving the rest of it in force:

1. **Terms.** A **process** is one `tools/d2run.py` launch: one game process, one seed, one raw log `<stem>.log`. A **case**
   is one game inside a process, with its save, its stage and its name. A **case is the unit an experiment record cites**. A
   fresh-process case is a process with one case. The anchor stays `run:<id>`; the record lists each kept case with its
   process (stem and seed) and its position in that process.
2. **A process may hold several cases** under `harness-play.md` § Fresh process, which wins over any batch's opt-in. A shared
   case is valid evidence only for a checker that does not read carried state, or was shown to start from the carried value.
   The record says which, and names at least two cases repeated in a fresh process, except for a batch that repeats a
   comparison already recorded for the same checker.
3. **Provenance.** The raw log, `<stem>.marks.tsv` and every piece `harness_runner.py split` cuts are in the run's manifest.
   The raw log and the marks are the source; a piece is derived and can be cut again from them. The record names the tool
   revision. A case that was run and not kept is named with its reason, and so is any case that followed a failure in its
   process (§ Fresh process rule 5).
4. **Sharing stays opt-in per batch, and the prompt gives the reason.** It is not a default and not a general speed-up: the
   measured wall saving on the pilot's logger is about 0.4 s per case. A lane's prompt opts in when the batch's own launch
   measurably costs more than a switch (a slower logger, a tuned switch), or when carried state is the thing under study.
5. **Cap: 8 games or 40 minutes per launch**, whichever comes first, inside the 4G scope. This is not a memory limit. Peaks
   were 269.8 and 270.3 MB at 8 games (19.9 and 26.2 min), and the largest peak of the kept launches, 620.7 MB, was a
   one-game launch. The 40 minutes was never reached and stays `[I]`. The cap bounds what one failed or stuck case can
   spoil and the size of a log. There is no measured reason to raise it.
6. **Migration rule confirmed unchanged:** a runner moves to the library when its plan next uses it, a new runner is written
   on the library, and a runner is never deleted while a kept log's record cites it.
7. **A comparison record states what it separates.** Next to its decision or case counts, a record that compares a model
   with a log over many cases gives the number of distinct predicted outcomes per row, from the checker's own output. A row
   with one outcome is reported as confirming that outcome, not a branch choice.

## Consequences

### Positive

- `[C]` statements resting on run:2026-11-03-ai get a defined meaning, and a reader can tell a shared case from a fresh one
  and rebuild any piece from its source.
- The rule states what sharing buys, so a lane stops opting in on the assumption that it is faster.
- Item 7 puts the separation in the record, where a large count would otherwise hide it.

### Negative

- **Records get longer**: a case list with position, and a separation line that checkers must print (`tools/ai.py` does
  not yet; [backlog](../backlog/archive/2026-11-03-architect-reverser-plan-0056-p4-separation-line-in-tools-ai.md)).
- **Sharing keeps a machinery with no measured wall gain on the one logger measured**: `next_case`, `split`, the marks, § Fresh
  process and its failure rule. It stays because cases need the definition anyway (31 kept case logs and the h1a and h4b
  precedents) and a tuned switch or a slower logger may change the arithmetic.
- **A shared case is weaker than a fresh one** on any question the checker cannot see: the fresh repeats used other seeds and
  compare checker outcomes, not logs. They show the checker's result does not depend on sharing; they do not show that the
  process is unaffected.
- All of this rests on **one lane, one new logger and one kind of case**. The sharing arithmetic may differ on another logger.

### Neutral

- `run:` anchors, the read-only breakpoint rule and the 4G scope do not change. Records written before this ADR stay valid.
- On acceptance: `references/evidence-rules.md` gains items 1 to 3 and 7, and `harness-play.md` § Fresh process cites this
  ADR and gains item 4's reason. The § Fresh process text on rule 5 and on the measured costs is already in force as the
  plan's ruling; it does not wait for this ADR.

## Alternatives considered

**No ADR: leave it to `harness-play.md`.** A how-to cannot define what an evidence anchor means, and records already cite
cases. Owner answer 6 of plan 0056 also asked for one.

**Retire sharing for new batches, on the measured 0.4 s.** This is the real choice for the owner. It would remove rule 5's
exposure and the split from new runs, and items 1 to 3 would still be needed for kept logs. It lost, narrowly, because one
logger with untuned sleeps is thin evidence for removing a capability that costs nothing until a prompt opts in, and because
a plan studying carried state needs it.

**Make sharing the default, since the pilot's cases checked the same.** The saving does not justify it, and 0055·P2b's fresh
sessions would become the exception.

**Raise the cap to reduce launches.** Memory would allow it, but fewer launches buy nothing measured, and each further case
adds to what one failure can spoil.

**Cite a process and treat cases as an index into it.** The check would still have to be per case, a process-level claim
would hide which game saw what, and a failed case would taint a whole citation.
