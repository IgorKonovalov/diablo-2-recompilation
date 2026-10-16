# ADR index

Next free number: **0018**

| # | Title | Status |
|---|---|---|
| [0001](0001-target-toolchain-evidence-sources.md) | Target, toolchain, evidence rules and sources policy | accepted (sources policy amended by 0007) |
| [0002](0002-scope-creation-paths-and-enablers.md) | Scope: every item and monster creation path, plus the systems the core depends on | accepted (presentation formats amended by 0005; game simulation amended by 0014) |
| [0003](0003-runtime-experiments.md) | How runtime experiments are run: wine, a subreaper launcher that becomes gdb, logged breakpoints | accepted (emulator scope amended by 0015) |
| [0004](0004-boundary-oracles-in-reproduction.md) | Bit-exact reproduction across an out-of-scope callee: logged boundary oracles | accepted |
| [0005](0005-presentation-formats-tools-only.md) | Presentation formats: tile and sprite decoding, tools-only, output stays in `workspace/` | accepted |
| [0006](0006-docs-gate.md) | A mechanical docs gate: strict checks on what can be checked, review for the rest | accepted |
| [0007](0007-fetched-leads-only.md) | A lead is a document read in-session, never a recollection (amends 0001) | accepted |
| [0008](0008-two-client-harness.md) | Two clients in one game: a second prefix and display, a local TCP/IP game, gdb on the host only | accepted 2026-10-16 (owner's condition: port 4000 closed to non-loopback before hosting; two non-zero slots) |
| [0009](0009-public-documentation-site.md) | Public documentation: deferred; a later, heavily redacted export with no tie to the repository | proposed (no site now) |
| [0010](0010-forced-path-runs.md) | Forced-path runs: an edited decision table may drive a rare stock path | superseded by 0013 |
| [0011](0011-harness-slots.md) | Harness slots: several game copies at once, one per display and prefix | accepted |
| [0012](0012-human-wiki.md) | A human wiki: explanatory pages over the reviewed specs, no claims of their own, not published | accepted |
| [0013](0013-forced-path-runs-cell-level.md) | Forced-path runs: "a table the path reads" is decided cell by cell (supersedes 0010's decision) | accepted |
| [0014](0014-scope-game-simulation.md) | Game simulation enters scope, in five phases, with per-event reproduction as its evidence (amends 0002) | accepted |
| [0015](0015-emulated-reproduction.md) | Emulated reproduction: the binary's own code under the p-code emulator, with a declared memory image (amends 0003) | accepted |
| [0016](0016-pipelined-simulation-phases.md) | Pipelined simulation phases: a phase's table and static work may start once the previous phase's run is accepted (amends 0014) | accepted 2026-10-16 |
| [0017](0017-scope-quests-travel-economy.md) | Quest progression, travel and the item economy enter scope, beside the five simulation phases (amends 0002) | accepted 2026-10-16 |
