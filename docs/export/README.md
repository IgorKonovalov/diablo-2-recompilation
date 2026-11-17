# The public export's allowlist

This folder holds the allowlist of the public export ([ADR-0009](../adrs/0009-public-documentation-site.md),
[ADR-0035](../adrs/0035-public-export-hosting.md), [plan 0070](../plans/0070-redacted-public-export.md)) and, from
plan 0070 Phase 5, the export-only pages. Nothing here is published by being in this folder. A page reaches the export
only by being named in [`manifest.txt`](manifest.txt), and only through `tools/export_build.py` and a green
`tools/export_check.py` (plan 0070 Phases 2 and 3).

**Ownership.** `manifest.txt` and this README: architect. A change to the manifest is reviewed at the next cut's Tier A
redaction review (plan 0070 § Review). The export-only pages (`index.md`, `reading-the-tags.md`, `about.md`):
spec-writer, reviewed like a wiki page.

## The manifest's format

One entry per line, fields separated by whitespace; `#` starts a comment, blank lines are ignored.

| Line | Fields | Means |
|---|---|---|
| `group` | slug, order, label (the rest of the line) | A sidebar group. Its slug is the route folder of its pages; its order places it in the sidebar. |
| `page` | docs-relative path, group slug or `-`, order | A page in the export. Its route is `<group>/<file stem>`, or `<file stem>` for `-` (top level, before every group); its order is its `sidebar.order` inside its group. `export/index.md` at the top level is the site's front page. |
| `table` | docs-relative path, line of the table's header row, reason | A table over 20 body rows allowed past rule X6. Each one is read in the cut's redaction review. |

Every page path exists, except the export-only pages until Phase 5 writes them. No two pages share a route.

## What never enters the manifest

The exclusions are rules, not a list; a path under one of them may not be added, whatever its content.

- **Evidence trees:** `docs/findings/`, `re/`, `docs/sources.md`, `docs/inventory.md`.
- **The repository's own records:** `docs/plans/`, `docs/adrs/`, `docs/backlog/`, `docs/backlog.md`,
  `docs/specs/README.md` (the research map), every `README.md` index of a docs folder (the wiki's included: it states
  the wiki's working rules and links the plans; the export's front page replaces it), and this folder's README and
  manifest.
- **The method page:** `docs/wiki/how-we-know.md`.
- **Art and data:** every file of game art and every game-art illustration, any file that is not Markdown; table pages
  that list constants of the code image ([ADR-0031](../adrs/0031-constants-of-the-code-image.md)). The one exception
  is a schematic illustration the builder generates from a named page's block
  ([ADR-0036](../adrs/0036-schematic-illustrations-in-the-export.md)); it is never named here.
- **Not before their cut:** `docs/specs/<subsystem>/` enters at the second cut (plan 0070 Phase 9), each spec only
  once a trial cut of it is green; `docs/formats/` and `docs/tables/` are outside the approved scope.

Inside a named page the builder also drops, by rule: front matter, *Open questions* sections, and the targets of links
to pages not in the manifest (their text stays). It runs each ```` ```illustration ```` block in schematic mode and
drops a block whose tool has none. Its simplifier drops any sentence, list item, table row, block or section that
fails the check's text rules, and logs each drop (plan 0070, decision 6). A wiki page's *What is not known
yet* section is kept: it states unknowns in words, holds no lead tag and no source id, and leaving it out would present
the page as complete.

## The hex allowlist

[`allow-hex.txt`](allow-hex.txt) (architect-owned, a reason on every line) names the game-math hex values that pass
the check's X1 and X3: named constants and illustrative seeds by value, and worked-example sections by page and
heading. A `sub_` or `DAT_` name and a `+0x` offset never pass. A value in the code image's range (the pinned
`Game.exe`'s whole mapped image, `0x00400000` to `0x009B9FFF`) passes only by a `pin` line: one value, one page, a
reason, never an address `re/symbols.csv` names. The draw values in a schematic illustration folder's calculation
panels pass by a scoped rule in the check, not by this file (plan 0070, owner decision 2026-11-17; pins and the
range, architect review 2026-11-17).
