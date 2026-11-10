---
from: architect
to: archivist
date: 2026-11-10
status: done
context:
  - ../../findings/data/0006-loaded-tables-and-bundles.md
  - ../../plans/done/0068-game-files-coverage.md
resolution: "Done in plan 0068 Phase 3 (lane/n68f): Sounds, MonItemPercent, Events, SkillDesc, Arena, Overlay, Composit, MonSounds, AutoMap, BodyLocs and PlayerClass docs carry data/0006's answers [log](../../plans/done/0068-game-files-coverage.md)"
---

**Table docs that data/0006 answers or narrows (Phase 3).** docs/tables/Sounds.md L16 and L35 (the '[L] which call loads sounds.bin' question and the H3b 'loads in every run' sentence): answered by data/0006 § 2.4, no stock run loads sounds.bin. docs/tables/MonItemPercent.md L29 and L35 (layout, 'every reader'): data/0006 § 1.5 gives the descriptor layout (four u8, type 4) and § 1 'no reader' at [I]. Also Events, SkillDesc, Arena, Overlay, Composit, MonSounds, AutoMap, BodyLocs, PlayerClass per the plan 0068 log's Phase 3 list.
