# ADR-0019 — Closed backlog entries move to `docs/backlog/archive/`

> **Status:** accepted (owner, 2026-10-20). Amends [ADR-0018](0018-backlog-one-file-per-entry.md).
> **Date:** 2026-10-20
> **Related plan(s):** none (process)

## Context

ADR-0018 put one file per entry in `docs/backlog/` and closed an entry by setting `status` and
`resolution` in place. Three days later the folder held 55 open and 80 closed entries (580 KB). The
closed share grows with every review, and new entries arrive at about 80 a day. A lane or the orchestrator
looking for open work (`ls docs/backlog/`, `grep`, an editor's file tree) has to wade through closed
entries. On 2026-10-20 the owner asked for closed entries to be taken out of the backlog and put in an
archive, because the backlog "is getting large".

Two constraints come from the way lanes run. Several lanes run in parallel on branches cut before any
change lands, so they will keep closing entries in place in `docs/backlog/` for a while, and merges must
stay green. And entries are linked: from plans, findings, other entries, the frozen `docs/backlog.md`
pointer lines, and entry `context` fields. About 90 links pointed at the 80 closed entries. Gate E8
fails on any of them that breaks.

## Decision

Open entries live in `docs/backlog/`, closed ones (`done`, `moved`, `dropped`) in
`docs/backlog/archive/`, with the same file name and format. Nothing is deleted: entries move with
`git mv`. `tools/backlog.py close` sets the status and resolution, then moves the file. A new idempotent
`tools/backlog.py archive` command runs `migrate`, then moves every closed entry left in `docs/backlog/`
into `archive/` (and an open entry found in `archive/` back out), and rewrites every relative link that
the moves broke: inbound links from `.md` files under `docs/`, `re/`, `.claude/` and the repository root,
`context` items, and the moved entries' own links, which gain or lose one `../`. After each lane merge
the orchestrator runs `python3 -I tools/backlog.py archive` and commits the result. The gate checks
entries in both folders (E13), reports an open entry in `archive/` as an E13 error, and warns (new W6)
on a closed entry outside `archive/`. A warning, not an error, so that a lane merged from an older branch
leaves `main` green until the sweep. `list` reads both folders. The frozen `docs/backlog.md` stays where
it is as the pre-2026-10-17 archive. It no longer grows, and ADRs (append-only) link it.

## Consequences

### Positive

- `docs/backlog/` lists only open work: 55 files instead of 135 at the switch.
- The merge flow stays one command. `archive` includes `migrate`, both are idempotent, and on a tree
  with nothing to do it changes nothing.
- Lanes keep their habit: they still run `close`. A lane on an old branch that closes in place is
  swept after its merge, and the gate tells the orchestrator when that is pending (W6).

### Negative

- An entry changes path when it closes, so a link to an open entry goes stale at the close. The tool
  rewrites the links it can see in the tree, but a link added on a branch that has not merged yet still
  names the old path. The post-merge `archive` repairs it (it maps any link to an entry's old place to
  its current one, and heals an archived entry's own links written as if it still sat in
  `docs/backlog/`), but only after the merge, so a merge can leave E8 red until the sweep runs. The
  orchestrator therefore merges with `--no-commit`, runs `archive`, stages its changes, and then commits
  the merge, so the gate sees the repaired tree.
- A lane that annotates an entry another lane has since closed edits a file that moved. Git follows the
  rename in most merges; when it does not, the conflict is a modify/delete that a person resolves by
  applying the annotation to the archived file.
- A `close` rewrites links in other files (plans, other entries), so a close touches more than the entry.
  The lane stages each file the tool changed.
- Links in `resolution` lines are written relative to `docs/backlog/` (where the entry sits when it is
  closed); the tool rebases them on the move. A resolution written by hand in an already archived entry
  must be relative to `archive/`.

### Neutral

- The entry format, the file names and the gate's E13 rules are unchanged.
- History stays readable: `git log --follow` traces an entry across the move.

## Alternatives considered

**Keep closed entries in place and filter with the tool.** `backlog.py list` already shows open entries
only. It lost because the request is about the folder itself, which people and agents read with `ls`
and editors, not only through the tool.

**Delete closed entries (git history is the archive).** Smallest folder, but resolutions stop being
readable in the tree and every inbound link breaks with nothing to point to. It lost to ADR-0018's
"nothing is deleted".

**Append closed entries to a second frozen Markdown file.** It brings back the shared hot file that
ADR-0018 removed, and every close would edit it.

**Archive by date bucket (`archive/2026-10/`).** It splits a folder that is not yet large, and adds a
second path component to compute on every move. One flat `archive/` can be split later the same way, by
the same tool.
