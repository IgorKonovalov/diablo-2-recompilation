# ADR-0001 — Target, toolchain, evidence rules and sources policy

> **Status:** accepted (sources policy amended by ADR-0007)
> **Date:** 2026-10-11
> **Related plan(s):** 0001-bootstrap

## Context

The goal is a specification precise enough to reimplement Diablo II: LoD's item creation, monster
spawning and level generation, with the same outputs for the same seed. The user owns a 1.14d copy,
distributed as an Inno Setup 5.5.6 installer (`workspace/reference/installers/1.14d/`, one `.exe` plus two `.bin`
volumes, 2.6 GB).

D2 is heavily data-driven. Most of "what can drop" and "what spawns where" lives in the excel
tables (`data/global/excel/*`) inside the MPQs. The *algorithms* live in code: the RNG, TC
recursion, quality and affix rolls, DRLG generators, spawn placement. In 1.14d every former DLL
(D2Common, D2Game, D2Client, D2Lang, Storm, Fog…) is statically merged into one `Game.exe`. That
gives one binary to analyse and no exports to anchor on. Community offset lists mostly target
1.10 and 1.13c.

The spec is meant to drive a reimplementation, so it has to stand on its own: no claim can rest
on "the community says so", and nobody should be able to say the text was copied from someone
else's decompiled code.

## Decision

**Target.** We analyse exactly one binary: the `Game.exe` extracted from this installer, pinned by
sha256 in `docs/inventory.md`. Image base `0x400000`; addresses are written `0x00XXXXXX`. Data
comes from the MPQs in the same install. Patch precedence is `patch_d2.mpq` > `d2exp.mpq` > `d2data.mpq`
(to be confirmed by the archivist, see Plan 0001).

**Toolchain.** Ghidra (headless, `analyzeHeadless`) is the primary decompiler. radare2/rizin
handle quick CLI questions such as xrefs, string search and byte patterns. StormLib/`smpq` reads
MPQs, `innoextract` unpacks the installer, wine runs the game for runtime experiments, and our
own Python lives in `tools/`. The Ghidra project is disposable. `re/symbols.csv` is the
single source of truth for names and is replayed into a fresh project by script.

**Evidence rules.** Every behavioural claim carries an anchor and one confidence tag:

- `[C]` **confirmed**: anchored to code we read (`0x00XXXXXX`), *and* independently corroborated
  by a second code path, by observable data-table behaviour, or by a runtime experiment.
- `[I]` **inferred**: anchored to code we read, but not independently corroborated.
- `[L]` **lead**: from an external source, naming, or intuition, with no anchor in our binary
  yet. Leads live in findings and in spec *Open questions*, never in spec body text.

Anchor forms: `0x00XXXXXX` (code/data), `fn:Name@0x00XXXXXX`, `tbl:Levels.txt:MonLvl1`,
`run:<experiment id>`, `src:<docs/sources.md id>` (leads only).

**Sources policy: docs yes, code no.** Community documentation (Phrozen Keep file guides, Amazon
Basin articles, forum posts, offset lists) may be read and used as **leads**. Each one gets an
entry in `docs/sources.md`. Decompiled or reconstructed game source from third parties (D2MOO and
similar) is **not read, not copied, not paraphrased**. Specs are written in our own pseudocode,
not as transliterations of decompiler output.

## Consequences

### Positive
- Each spec statement can be traced to an address in a binary we hold, so it can be re-verified.
- Agents only ever deal with one binary; nothing has to be mapped between DLLs.
- The confidence tags let a reimplementer see at once which parts are solid.

### Negative
- Slower than reading D2MOO. Each claim has to be found in 1.14d from scratch, and 1.14d inlined
  and reshuffled code compared to 1.10.
- Community offset lists for 1.13c don't transfer directly. They can only become leads after
  pattern-matching.
- Upgrading to `[C]` often needs a wine experiment, which needs a harness (save editing, seed control).

### Neutral
- This covers 1.14d only. Version differences (1.09/1.10/1.13) are out of scope unless a later ADR adds them.

## Alternatives considered

### Analyse 1.13c instead
More community offsets, and the DLLs are separate. Rejected because the user's copy is 1.14d, and
pinning to a binary we don't have breaks the anchor rule.

### Use D2MOO as reference
Much faster, but the spec would become derived work of a third-party decompilation, which weakens
the preservation spec's standing. The user chose "docs yes, code no".
