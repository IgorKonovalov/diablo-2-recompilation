# Backlog — cross-lane requests and open questions

When a lane needs something it doesn't own, it adds an entry here instead of reaching across.
The owner strikes the entry through and points to the resulting finding, plan or doc.

Format: `- [YYYY-MM-DD] from <lane> → <lane>: <request>. Context: <link>`

- ~~[2026-10-11] from archivist → architect (+human): the Blizzard MPQs in the 1.14d install carry no MPQ signature and include a Russian localisation, so their gameplay content is unverified (`game.exe` is verified unmodified). Get a clean reference before Phase 3 table work?~~ Resolved by comparison with Blizzard's 1.14b installers: every `data/global/` file is byte-identical, and the only gameplay addition (`patch_D2.mpq:…/TreasureClass.txt`) is excluded. See [installer.md § MPQ integrity](formats/installer.md#mpq-integrity-comparison-with-the-114b-reference).
- [2026-10-11] from archivist → architect (+human): is 1.14d's `patch_d2.mpq` content the same as 1.14b's? It needs Blizzard's signed 1.14d patch executable or a Battle.net-updated install. Not blocking: Phase 3 builds `merged/` from the 1.14b reference archives. Context: [installer.md § Open questions](formats/installer.md#open-questions)
- [2026-10-11] from archivist → reverser: (a) does `game.exe` read loose `data/…` files only under `-direct`, or always? (b) what does the 1-byte `data\local\use` file select (`0x00` eng, `0x0B` rus in this install)? Context: [installer.md § Launch path](formats/installer.md#launch-path-in-this-install-not-used-by-us)
