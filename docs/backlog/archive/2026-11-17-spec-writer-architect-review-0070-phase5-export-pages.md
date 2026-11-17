---
from: spec-writer
to: architect
date: 2026-11-17
status: done
context:
  - ../../plans/0070-redacted-public-export.md
resolution: "Tier A review 2026-11-17: accept with fixes (3, wording in reading-the-tags.md); see plan 0070 log"
---

**Tier A review of plan 0070 Phase 5** (lane/x70p): the three export-only pages,
[`export/index.md`](../../export/index.md) (front page: what the project is, what the site holds, where to start, the
manifest's groups as links), [`export/reading-the-tags.md`](../../export/reading-the-tags.md) (`[C]`/`[I]` and the wiki's
words for them, per the evidence rules; leads left out; diagrams carry no tag) and
[`export/about.md`](../../export/about.md) (the footer's statements, the simplified edition, the animations as schematic
drawings of our own per ADR-0036, CC BY 4.0).

Points to read: the tag page names the corroboration kinds in plain words ("the running game", "a rebuild", "another
part of the program", "the game's data") without naming a tool, against the plan's "without naming the method";
the owner's name is not in the page text (ADR-0035 lets it appear only where the host puts it); `tools/export_check.py`
was not on main, so X1–X12 were self-checked by a regex pass over the rules' text (clean; X12 none).

Not blocking any other lane; blocking Phase 5's close.
