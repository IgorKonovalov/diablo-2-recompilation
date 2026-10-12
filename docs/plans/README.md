# Plans index

Next free number: **0014**

| # | Title | Status | Current phase |
|---|---|---|---|
| [0001](done/0001-bootstrap.md) | Bootstrap: extract, inventory, load the binary, first spec (RNG) | done | — (closed 2026-10-11; MPQ precedence `[L]` → reverser backlog) |
| [0002](done/0002-excel-foundation.md) | Excel foundation: which data the game actually reads | done | — (closed 2026-10-11; `data/excel` reviewed, small spec fixes → backlog) |
| [0003](done/0003-seed-tree-runtime-harness.md) | Seed tree to reviewed, and the first runtime harness | done | — (closed 2026-10-11; `rng/seeds` reviewed, small spec fixes → backlog; harness method → ADR-0003) |
| [0004](0004-items-treasure-classes.md) | Items: treasure class resolution | in-progress | Phase 3 accepted with fixes F1–F5 (applied): `specs/items/tc.md` + `README.md` draft; champion and party `[I]` (party blocks `reviewed`, plan 0011) |
| [0005](done/0005-prerequisite-formats.md) | Prerequisite formats: DS1, DT1, TBL, D2S | done | — (closed 2026-10-12; all phases accepted with fixes; run-time `.tbl` use → reverser backlog) |
| [0006](done/0006-asset-rendering.md) | Asset rendering: palettes, DT1 tiles, DC6, DCC (tools-only, ADR-0005) | done | — (closed 2026-10-11; tools-only per ADR-0005; d2char merge → archivist backlog) |
| [0007](done/0007-docs-gate.md) | Docs gate: mechanical checks for anchors, tags, links and parser surveys (ADR-0006) | done | — (closed 2026-10-11; fast + full tier GREEN on `main`, commit hook active) |
| [0008](done/0008-drlg-overview.md) | DRLG overview: generator dispatch, the room-seed chain and the room tile draws (the k of `rng/seeds` step 6) | done | — (closed 2026-10-12; P4 accepted: `drlg/overview` and `drlg/room-tiles` reviewed, `rng/seeds` 6b links k; open points → reverser backlog) |
| [0009](0009-item-art.md) | Item art: classic-class merge, item art index, colour shifts, per-item sheets (tools-only, ADR-0005) | approved | P1–P3 accepted; P4 (per-item sheets, one regenerate command) next |
| [0010](0010-items-quality.md) | Items: the quality roll (oracle of plan 0004 replaced by a model) | in-progress | P0 accepted with fix F1, P1 accepted with fixes F1–F2 (items/0002 `[I]`, `tools/quality.py check` 266/266 at MF 0), P1b accepted (classic rows contradicted → P2 case); P2 reverser next (run: owner may play) |
| [0011](0011-two-client-harness.md) | Two-client harness: the party NoDrop case and a champion kill | approved | P1 reverser (harness), P2 runs (human may play) |
| [0012](0012-monsters-pool.md) | Monsters: the level's monster pool and monster level | in-progress | P0 accepted (MonLvl, MonStats/Levels pool columns, survey); P1 reverser next |
| [0013](0013-save-d2s-code.md) | Save files: the code behind the `.d2s` format | in-progress | P1 accepted (save/0001 `[I]`, 4 `[C]` by earlier runs; data/0003 `.tbl` read alongside); P2 round-trip runs next (reverser) |

Suggested order per lane: **archivist** 0009·P4 (tools only) and its backlog. **reverser** 0010·P2 → 0011 (harness, then the
party and champion runs; unblocks `items/tc` `reviewed`) → 0012·P1 → 0013·P1 (its Phase 2 can reuse the 0010 drop
runs for the saved-item check). **spec-writer** follows each plan's reverser phases (0010·P3 after 0010·P2).
