---
from: architect
to: reverser
date: 2026-10-25
status: open
context:
  - ../findings/monsters/experiments.md#run2026-10-21-sweep-monsters-a
  - ../plans/0038-inventory/README.md#26-moves-made-by-the-batch-reviews
resolution: ""
---

From the lane/h4a review (plan 0038 H4a, 2026-10-25). The chained models that tools/monstats.py check runs first (tools/monspawn.py, the DRLG and collision models) disagree with three kept H4a logs (workspace/logs/h4a/check/monstats-h4a.txt, hashed in h4a-manifest.sha256); the earlier --no-chain check had hidden them. None is on a tag the H4a rows rest on, but each is a model the specs' [C] rows lean on, so each needs its cause found and, if a spec claim is contradicted, routed. (1) council (h4a-s1-4905-council): 3 DRLG room-tile mismatches (CB W entries of DRLG room 02e58d00, 68 logged and 68 model, first difference at entry 18, [6, 0, 33797, 1], flags 0x8005 'built'), reported by monspawn.py as its 1. Check against drlg/room-tiles. (2) nihl2 (h4a-s1-4910-nihl2:31107): Nihlathak (class 526, record 60) leaves SpecialMonPlace with mods [22] (SMPX) and SU1 [22, 30]; the model's post-create table has no entry for 526 and gives [30]. Find what writes mod 22 before the superunique path and whether monsters/special § J (post-create mods) misses it. (3) chaos7 (h4a-s1-4907-chaos7:34913, :50798): CollisionTest at the Infector's and the Vizier's placement points returned 4097 and 4096, the collision model 1 and 0 (bit 0x1000, the unit mark of drlg/collision row 12, set in the game only), and the creation marks of five units next to them follow (10 collision mismatches). A lead to test first: a unit the model does not mark (the player beside the seal, or a seal-spawned unit). Not blocking for plan 0038; a reverser static or harness lane may take it, plan 0051 or later.
