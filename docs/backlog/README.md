# Backlog — cross-lane requests and open questions

One file per entry ([ADR-0018](../adrs/0018-backlog-one-file-per-entry.md)), named
`YYYY-MM-DD-<from>-<to>-<slug>.md`. Entries filed before 2026-10-17 are in the frozen
[archive](../backlog.md).

```
python3 -I tools/backlog.py new --from reverser --to spec-writer --slug "p1c answers" --context ../plans/0039-backlog-sweep-4.md
python3 -I tools/backlog.py list [--to LANE] [--from LANE] [--status open|done|moved|dropped|all]
python3 -I tools/backlog.py close docs/backlog/<file>.md [--status done|moved|dropped] --resolution "Done in [x](../findings/x.md)."
```

- **File** a request with `new`, then write the request under the front matter. Front matter: `from`,
  `to` (one lane or several, comma-separated; lanes are `architect`, `archivist`, `reverser`,
  `spec-writer`, `human`), `date`, `status`, `context` (links relative to this folder), `resolution`.
- **Annotate** with a dated paragraph under the request (`*2026-10-18 (reverser):* …`). Don't edit the
  request.
- **Close** with `close`: `status` `done`, `moved` or `dropped`, and a one-line `resolution` with a link.
  Nothing is deleted.

The gate checks every entry (E13) and warns on a live entry in the archive (W5).
