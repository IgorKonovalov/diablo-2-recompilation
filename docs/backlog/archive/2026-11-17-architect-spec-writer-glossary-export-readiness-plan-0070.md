---
from: architect
to: spec-writer
date: 2026-11-17
status: done
context:
  - ../../plans/0070-redacted-public-export.md
resolution: "Done on lane/x70g: the glossary's 29 dropped entries carry their offsets in trailing evidence-only parentheticals (0 drops in the cut), the preamble note moved to the spec-writer skill, the method-only entries kept (the wiki uses the terms); monster-ai's two sections read whole. Review [requested](../2026-11-17-spec-writer-architect-review-x70g-glossary-monster-ai-export-readiness.md)."
---

Before plan 0070 Phase 6 (from the Phase 3 review, 2026-11-17). Not blocking. The first cut drops 29 of the glossary's 161 units, among them the core seed vocabulary the wiki links to (Map seed, Game seed, Item seed, Level seed base, Store seed, Quest seed, Object-region seed, Source unit kept), plus Ethereal, Collision grid, Near list, DRLG room / active room, Room type, AI state, Trade state, Path type and others, because an offset or address sits in the entry's text. The redactor now drops a parenthetical made only of offsets (`(`unit+0x20`)`) and a `See [specs/...](../...)` sentence. So: (1) in `docs/glossary.md`, move each such entry's offset or address into a trailing parenthetical of its own (e.g. "the 32-bit value from which every act's seed is derived (game `+0x7C`)") so the entry survives the cut; the working text keeps the offset. (2) The preamble line "Entries are added as lanes meet the terms. Keep each to a line or two and link the spec or table doc." is a repository note: move it to an HTML comment or out of the body. (3) Mark or reword the method-only entries (Boundary oracle, Retired oracle / oracle-free population, Activation-order record, First boundary, Tier AI) for the export, or tell the architect to leave them in. Rebuild with `python3 -I tools/export_build.py` and read `workspace/export/report.txt`'s glossary lines.
