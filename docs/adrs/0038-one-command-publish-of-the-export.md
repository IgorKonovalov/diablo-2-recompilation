# ADR-0038 — One-command publish of the export: a script copies each cut, the owner's run pushes it (amends 0035)

> **Status:** accepted (owner, 2026-11-17: asked to "make it so update of this repo will automatically publish site,
> as done in" the owner's other project; offered a local command, CI in this repository, or a git hook, the owner
> chose "One local command")
> **Date:** 2026-11-17
> **Related plan(s):** [0070-redacted-public-export](../plans/0070-redacted-public-export.md)

## Context

The owner's other project deploys its site on every push, because the site lives in the same repository. Here the
site is a separate, redacted export ([ADR-0035](0035-public-export-hosting.md)): `tools/export_build.py` cuts it from
the manifest, `tools/export_check.py` guards it, and each cut is then copied into the export repository by hand, built,
link-checked, committed and pushed by the owner. Plan 0070's first two cuts took about ten manual steps each.

Three facts rule out a copy of the other project's setup. The illustrations are rendered from game files in
`workspace/`, which a CI runner never sees, so a build in this repository's CI would freeze them. Agents never push
(a hook blocks it), and ADR-0035 says the owner does. And every cut that adds pages has had a redaction review
(plan 0070 Phases 6 and 9); the check is a backstop, not a reader.

## Decision

`tools/export_publish.py` does every step of a cut in one run: it rebuilds the cut into `workspace/export`, runs the
check with `--repo workspace/export-repo/` and stops on any failure, refuses a cut whose manifest names a page that
`docs/export/reviewed-pages.txt` does not list, copies the export repository's project files from
`workspace/export-repo/` and the cut's content, illustrations and `cut.json` into the export repository's checkout
(`~/Work/arpg-1-14d-notes` by default), builds the site and runs its link check, and commits on that checkout's
`main` when anything changed. With `--push`, run by the owner in their own terminal, it then pushes `main`, and the
export repository's workflow deploys it. The script refuses `--push` inside an agent session. ADR-0035's "copied by
hand" becomes "copied by this script"; the rest of ADR-0035 stands. **The review stays where a cut adds pages:** the
architect adds a page to `reviewed-pages.txt` only in a redaction review; changes to pages already listed go out on
the check alone.

## Consequences

### Positive
- A cut is one command, so a merged spec or wiki fix can reach the site the same day.
- The illustrations stay current: the script runs where the game files are.
- The two guards remain: the check here, and the export repository's CI build and link check.

### Negative
- Edits to listed pages are published without anyone reading the cut; the check's text rules are the only guard
  for them. A wrong word that the rules don't know (a new tool name, a new kind of record) can go out. The redaction
  review of each new page and the check's own tests are what keep this narrow.
- Commits land on the export repository's `main` directly, with no pull request to read first; the owner reads the
  local build, or runs without `--push` and looks before pushing.

### Neutral
- Agents may run the script without `--push`; it then stops after the commit and prints the push command.
- The export repository's project files now follow `workspace/export-repo/` on every run, so a hand edit made only
  in the export repository's checkout is overwritten; make such changes in `workspace/export-repo/`.

## Alternatives considered

**A workflow in this repository that builds and pushes the export on every push to `main`.** It lost on the
illustrations (no game files on a runner, so they would freeze) and on review: nobody would read any cut.

**A git hook that commits a cut into the export repository whenever `main` moves.** It lost on noise: every lane
merge, most of which change no exported page, would run a build and might add an export commit.
