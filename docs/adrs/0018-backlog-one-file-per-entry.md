# ADR-0018 — The backlog as one file per entry

> **Status:** proposed
> **Date:** 2026-10-17
> **Related plan(s):** none (process); the [lane run ledger](../plans/metrics.md) records the merges that motivated it

## Context

`docs/backlog.md` is one file of 730 lines holding 519 entries, 464 of them struck. Every lane adds its
entries at the end of the file, and several lanes run in parallel (up to two static, two harness, the
archivist, the spec-writer and the architect's reviews). On 2026-10-16/17 about 170 entries were added
(119 and 51) and almost every lane merge conflicted in this file. Each conflict was resolved by hand:
keep both sides, then dedupe by entry text. Keeping both sides duplicated entries whenever one side had
struck or annotated an entry and the other had not. The reviews of S2b, S4b, H4b, `lane/p38s3` and S1e
(plan 0038 log) each record such a dedupe.

The file is not append-only. Entries are edited in place: struck when answered, and annotated with
"Narrowed", "Update", "Plan" or "Done" paragraphs by later lanes. Over those two days the commits that
touched the file added 1 279 lines and deleted 478, and the deletions are mostly these in-place edits.
201 lines are continuations of multi-line entries.

The gate (ADR-0006) checks nothing in the backlog except E8 (relative links resolve), which applies to
every tracked `.md` file. 31 tracked files link to `docs/backlog.md`, none with a fragment. Plans and
reviews name entries by prose ("the S2a tc 64 entry", "backlog entry (h)"), because entries have no id.
Lanes use the file three ways: file a request to another lane, file a review request to the architect,
and strike or annotate an entry they answered. The orchestrator reads it to find open review requests.

## Decision

New backlog entries become one file each under `docs/backlog/`, named
`YYYY-MM-DD-<from>-<to>-<slug>.md`, with front matter `from`, `to`, `date`, `status`
(`open | done | moved | dropped`), `context` (links) and, once closed, `resolution` (one line with a link).
The body is the request. Later lanes add dated annotations under it instead of editing the request. To
strike an entry, set `status` and `resolution`; nothing is deleted. `docs/backlog.md` is frozen as the
archive of entries filed before the switch. Its open entries move to files by a one-time script, each
leaving a struck line in the archive pointing to its new file, so existing links keep resolving. The
gate gains backlog checks: front matter well formed, `from` and `to` in the lane list (plus `human`),
`status` in the enum, the date matching the filename, `resolution` present when the status is not
`open`, and no unstruck entry in the archive dated after the freeze. A small tool, `tools/backlog.py`,
lists entries by `to` and `status` (the orchestrator's "open review requests" query). No committed index
is generated, because a shared index would bring back the hot spot.

## Consequences

### Positive

- Two lanes that file entries never touch the same file, so filing no longer conflicts. A conflict now
  means two lanes edited the same entry, which is a real conflict that a person should see.
- Struck and unstruck twins can no longer arise from a merge: an entry exists once, and its status is one
  front-matter field.
- Entries get stable paths. Plans, reviews and findings can link the exact entry, and the gate can check
  those links (E8).
- The orchestrator's queries ("open, to architect") become a tool call instead of a read of a 730-line
  file.

### Negative

- Many small files: about 80 a day at the 2026-10-16/17 rate, thousands within weeks. `ls` stops being a
  way to read the backlog; the tool, or grep on `status: open`, replaces it.
- Every lane changes a habit. The four SKILL.md files, the finding, spec and table-doc templates
  and `evidence-rules.md` mention `docs/backlog.md` and must be updated in the same change. Lanes in flight at
  the switch append to the archive once more; the gate's freeze check catches that, and the merge moves
  the entry by hand.
- One-time work: the migration script (archivist, `tools/`), the gate checks with tests (`test_gate.py`),
  and the skill edits. The 464 struck entries do not move.
- Two lanes picking the same slug for different requests on the same day, between the same lanes, would
  collide. It is rare, and git reports it as an add/add conflict, not a silent merge.
- Annotations by two lanes on one entry still conflict. This is rare and visible.

### Neutral

- The archive keeps its path, so the 31 links resolve and history stays readable in place.
- The backlog stays outside the evidence rules: entries make no claims and carry no tags.

## Alternatives considered

**(b) `merge=union` on `docs/backlog.md`, plus a gate check for duplicate text and struck/unstruck
twins.** Union merge suits a file whose lines are only ever appended. This file is edited in place, so a
union merge keeps both the old and the new version of every edited line. That makes the twin problem
automatic and silent. The gate check would flag the twins after the merge, and someone still has to
dedupe them by hand. It moves the work from the conflict to the gate; it does not remove it. Union merge
also interleaves the continuation lines of multi-line entries when both sides append. It lost because the
file is not append-only.

**(c) Per-lane backlog files** (`docs/backlog/reverser.md`, … by addressee, or by author). Parallel lanes
of one kind (two static reverser lanes, two harness lanes, a wiki and a spec lane) still append to the end
of the same file, and the other side of each entry (the addressee who strikes it, or the author who files
it) still edits a file it does not own. It reduces conflicts but keeps both failure modes.

**(d) Fragments folded by the orchestrator.** Lanes write new entries as fragment files in
`docs/backlog/inbox/`, and the orchestrator folds them into `docs/backlog.md` when it merges. New entries
stop conflicting, at a lower migration cost than (a). But the fold is an extra manual step at every
merge, an entry has two homes during its life (fragment, then the file), and a strike made by a lane
before the fold lands in a fragment that moves. In-place edits in the shared file can still conflict
when they are close together. It lost to (a), which reaches the same end without a fold step.

**(e) An append-only event log with ids and `merge=union`.** Entries get ids, and status changes are
appended as separate event lines (`- done B0123: …`), so no line is ever edited and a union merge is
safe. A gate check validates the ids and events. It removes the conflicts with one file, but the status
of an entry is no longer next to its text, so reading the backlog needs a tool, and id allocation across
parallel lanes needs a rule (date plus lane plus counter). It lost to (a), whose files are readable as
they are and need no id scheme beyond the filename.

**Keep the file and dedupe by hand.** This is the status quo. Each merge costs a hand dedupe, and the
dedupe has already gone wrong both ways (stale copies kept, struck copies dropped). It lost because the
merges are the orchestrator's routine work, and lanes are getting more parallel, not less.

## Recommendation to the owner

Accept (a) as decided above. Migrate between two batches of lanes, when no lane is in flight, as one
change so the gate is never red: the archivist's script, the gate checks and their tests, the skill and
template edits, and the move of the 55 open entries. If the owner prefers a smaller first
step, (d) is the fallback. It needs no gate change, and it can be turned into (a) later by not folding.
