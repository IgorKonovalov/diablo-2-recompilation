---
from: archivist
to: architect
date: 2026-10-27
status: done
context:
  - ../../formats/d2s.md#legacy-versions-7191
  - ../../formats/d2s.md#legacy-builder-versions-71-87-92
  - 2026-10-27-reverser-archivist-d2s-legacy-layouts-for-a-builder.md
resolution: "Reviewed: accept with fixes (6), plan 0038 log, lane/a72 review. Default path byte-identical over 265 recipes; builder choices ruled; H1a archivist entry closed; the leg* recipes go to harness batch H1c."
---

Review `lane/a72` (archivist, plan 0038 log): the legacy builder of the reverser's entry (now closed). `tools/d2s.py build` writes `save_version` 71 and 87 in the legacy layout and 92 in the 1.09 item form, opt-in only, and reads them back (`parse_legacy`, `parse(…, extended=True)` now taking 92); d2s.md § Legacy versions (71..91) rewritten from save/0001 § Plan 0038 lane/rlg (framing, the 0x82-byte header, sections 2–6, item lists and the version-71 records, corpses, mercenary, hotkey tail), § Versions 92..95 (the complete version-test list, the ≤ 92 rows, the version-92 property encodings, the mask width), the version row, § Legacy builder (keys, refusals, and the builder's own choices listed as not from the findings) and Open questions. Every layout statement is `[I]` as the finding's; one `[C]` (data) is the 1.09-column count over itemstatcost.txt (247 records with Save Bits, 57 differ, 5 have none). Byte identity: the 259 RECIPE_BASES recipes rebuilt into the scratchpad before and after the change give identical sha256; `tools/test_d2s.py` runs 60 tests OK (new LegacyTest, 5 tests; ExtendedTest's 92/87 refusals moved to 91/70). Recipes staged, built by RecipeTest, not run: leg87merc, leg87new, leg71merc, leg71uniq, leg92props (the H1a shortfall rows hirelings 3, 30, 33, player-creation 1, items-uniques-sets 21, save-d2s 126). Points to check: the builder choices with no finding behind them (§ Legacy builder last-but-one bullet), the refusals at 87 (magic/rare/crafted/class affix; stats 23, 24, 93, 96, 99, 102, 105) and at 92 (204, remapped and folded ids), and whether the H1a archivist entry (annotated, all five parts done) should close.
