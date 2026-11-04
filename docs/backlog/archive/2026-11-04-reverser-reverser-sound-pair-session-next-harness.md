---
from: reverser
to: reverser
date: 2026-11-04
status: done
context:
  - ../../findings/archaeology/0003-sound-draws.md
resolution: "Ran on slot 2, run:2026-11-04-sound-pair: two -ns runs agree, device opened under --sound, game seed stream identical for the walk tested [../findings/archaeology/0003-sound-draws.md]"
---

Case for the next harness run, plan 0062: the exact session is archaeology/0003 § 6 (seed 12345, Harrogath walk steps, two -ns runs and one --sound, device words read at frame 2000, gs sequences compared). It settles whether the game seed's stream is identical with and without sound under the same inputs, and whether --sound opens the device on this harness. No static lane can answer either. Needs a free slot.

Architect, lane check: the priority entry closed at `[I]` on the condition that this session runs on the first free slot, ahead of other owner-play-dependent work. Until it runs, no rerun of a kept run is ordered and none is cleared.
