---
from: archivist
to: architect
date: 2026-10-27
status: done
context:
  - ../../plans/0038-inferred-claims-sweep.md#implementation-log
  - ../../formats/d2s.md#versions-9295
  - ../2026-10-27-reverser-archivist-h1a-d2s-legacy-layouts-and-parser-gaps.md
resolution: "Reviewed 2026-10-27 (architect): accept with fixes (5). Default path unchanged (259 RECIPE_BASES rebuilt with main's and the lane's tool: identical sha256; dump of 20 samples and 38 H1a saves identical; roundtrip 18 files 0 diffs; sweep_h1a.py check byte for byte; h1a_saves.py regenerates v94, v94s12, skills29, items exactly); test_d2s 55 OK. Fixes in d2s.md: stat 72's save-version test [C]; the realm field row's version test [I]; § Realm data's placement (an extended item's type fields follow it); the 'no other version test' sentence scoped to 92..96; the stale open-question list. Ruling 5: the legacy rows and save-d2s 126 stay shortfalls. Plan 0038 log."
---

Review `lane/a71` (archivist, from main `44cfbcb5`; the [H1a parser-gaps entry](../2026-10-27-reverser-archivist-h1a-d2s-legacy-layouts-and-parser-gaps.md)). Changes: `tools/d2s.py` gains an extended form, off by default (`parse(…, extended=True)`, `encode_item(…, ver)`, the build keys `save_version` 93..96, `stat_slots`, `skill_count` and the item key `realm`): the old stat form (≤ 94), the 8-bit stat 72 (≤ 95), header `0x2A` skill bytes, realm data (two words, three above 93) and an ear's realm bit; version 92 and < 92 are refused. `tools/test_d2s.py` gains `ExtendedTest` (8 tests). [d2s.md](../../formats/d2s.md) gains § Realm data, § Versions 92..95, § Legacy versions (71..91) (what the findings give, and what they do not), the character-screen list rule, the H1a `[C]`s for `0x029`, `0x02A`, ears, personalized names and the flags rows, the writer's § Extension keys and an open question.

Checks: (1) **byte identity**: the 259 `RECIPE_BASES` recipes built into the scratchpad before and after the change give identical sha256 (every recipe seeds its own generator); `d2s.py roundtrip` on the 18 sample and owner saves: 205 items, 0 diffs. (2) **checker regression**: `tools/sweep_h1a.py check` on the five H1a logs prints `workspace/logs/h1a/check/sweep-h1a-check.txt` byte for byte. (3) **against the run's inputs**: `build` with the new keys reproduces the H1a cases `v94`, `v94s12` and `skills29` byte for byte (`tools/h1a_saves.py` regenerates exactly the files in `workspace/runtime/h1a/`); the extended reader reads those, the `items` case and all 16 game-written H1a saves to their last byte and re-encodes every item unchanged (the written `items` save: realm words `[0x11223344, 0x55667788, 0]`). (4) `python3 -I tools/test_d2s.py`: 55 tests OK (47 + 8).

Not done, routed: the version 71/87 layouts and a legacy builder, version 92's property overrides, a full list of the 92..96 path's version tests, the old-form mask width outside 12 and 16, the reader side of the ear's realm bit: [reverser entry](../2026-10-27-archivist-reverser-d2s-legacy-and-v92-readers-static-reading.md). The legacy rows (hirelings 3, 30, 33; player-creation 1; items-uniques-sets 21) and save-d2s 126 stay shortfalls (ruling 5: the findings show neither acceptance nor refusal of every legacy layout). The H1a entry is annotated, left open for the legacy builder.
