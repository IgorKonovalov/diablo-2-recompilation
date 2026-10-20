# Backlog — cross-lane requests and open questions

One file per entry ([ADR-0018](../adrs/0018-backlog-one-file-per-entry.md)), named
`YYYY-MM-DD-<from>-<to>-<slug>.md`. This folder holds the **open** entries. Closed ones (`done`, `moved`,
`dropped`) are in `archive/`, same names, same format
([ADR-0019](../adrs/0019-backlog-closed-entries-archive.md)). Entries filed before 2026-10-17 are in
the frozen pre-2026-10-17 [archive](../backlog.md), which no longer grows.

```
python3 -I tools/backlog.py new --from reverser --to spec-writer --slug "p1c answers" --context ../plans/0039-backlog-sweep-4.md
python3 -I tools/backlog.py list [--to LANE] [--from LANE] [--status open|done|moved|dropped|all]
python3 -I tools/backlog.py close docs/backlog/<file>.md [--status done|moved|dropped] --resolution "Done in [x](../findings/x.md)."
python3 -I tools/backlog.py archive [--dry-run]     # after a lane merge: migrate, sweep closed entries, fix links
```

- **File** a request with `new`, then write the request under the front matter. Front matter: `from`,
  `to` (one lane or several, comma-separated; lanes are `architect`, `archivist`, `reverser`,
  `spec-writer`, `human`), `date`, `status`, `context` (links relative to the entry's folder), `resolution`.
- **Annotate** with a dated paragraph under the request (`*2026-10-18 (reverser):* …`). Don't edit the
  request.
- **Close** with `close`: `status` `done`, `moved` or `dropped`, and a one-line `resolution` with a link
  written relative to this folder. `close` moves the entry into `archive/` with `git mv` and rewrites the
  links that pointed at it (and its own links, one `../` deeper); stage every file it changes. Nothing is
  deleted. `list` searches both folders.
- **After a merge**, the orchestrator runs `archive`: it migrates the frozen archive, moves any closed
  entry a lane left here into `archive/` (and an open one found there back), and fixes the links. It is
  idempotent.

The gate checks every entry in both folders (E13, which also rejects an open entry in `archive/`), warns
on a live entry in the frozen archive (W5) and on a closed entry outside `archive/` (W6).
