---
from: reverser
to: architect
date: 2026-11-03
status: open
context: []
resolution: ""
---

The request: what is needed, from whom, and why. Not blocking / blocking <what>.

Review of `lane/r57b`, plan [0057](../plans/0057-quirks-catalogue.md) Phase 2: [quirks/0001](../findings/quirks/0001-community-bugs.md), Tier B. 30 claims from 3 pages: 19 confirmed, 5 contradicted, 3 not in 1.14d, 3 not found (`[L]`). Sources registered, 2 not read. Two new `re/symbols.csv` rows. No emulation, no harness; one Ghidra project (`ghidra-r57b`). Points to check: row 12's verdict (life drain is a term of `total`, so "twice" fails as stated but a drain does add); row 13's factor, 256 against the page's 512, composed from three reviewed halves and not run; row 3's `not in 1.14d`, with the kick paths read limited to start 2 and the Assassin's. Not blocking.
