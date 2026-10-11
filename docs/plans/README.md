# Plans index

Next free number: **0008**

| # | Title | Status | Current phase |
|---|---|---|---|
| [0001](done/0001-bootstrap.md) | Bootstrap: extract, inventory, load the binary, first spec (RNG) | done | — (closed 2026-10-11; MPQ precedence `[L]` → reverser backlog) |
| [0002](done/0002-excel-foundation.md) | Excel foundation: which data the game actually reads | done | — (closed 2026-10-11; `data/excel` reviewed, small spec fixes → backlog) |
| [0003](done/0003-seed-tree-runtime-harness.md) | Seed tree to reviewed, and the first runtime harness | done | — (closed 2026-10-11; `rng/seeds` reviewed, small spec fixes → backlog; harness method → ADR-0003) |
| [0004](0004-items-treasure-classes.md) | Items: treasure class resolution | in-progress | Phase 1 done; Phase 1b (reverser) next, then Phase 2 (amended: quality roll as oracle, ADR-0004) |
| [0005](0005-prerequisite-formats.md) | Prerequisite formats: DS1, DT1, TBL, D2S | in-progress | Phases 1–2 accepted with fixes (2026-10-11); Phase 4 (D2S) next, then Phase 3 |
| [0006](0006-asset-rendering.md) | Asset rendering: palettes, DT1 tiles, DC6, DCC (tools-only, ADR-0005) | in-progress | Phases 1–2 accepted with fixes (2026-10-11); Phase 3 done, awaiting architect review; later phases yield to 0005·P4 |
| [0007](0007-docs-gate.md) | Docs gate: mechanical checks for anchors, tags, links and parser surveys (ADR-0006) | in-progress | Phase 1 (fast tier) next; after 0005·P4 |

Suggested order per lane: **archivist** 0005·P1–2 review fixes (backlog) → 0006·P1 (small) → 0005·P4 (D2S, on the 0003 harness) → 0007·P1–3 (docs gate) → 0005·P3 (TBL) → 0006·P2–5;
**reverser** 0004·P1b → 0004·P2 (runtime runs per ADR-0003, quality roll as oracle per ADR-0004); **spec-writer** follows each plan's
reverser phases. Next in line after these (not yet planned): `items/quality`, `drlg/overview` (plan 0008 once the reverser is past 0004·P2),
`monsters/pool`.
