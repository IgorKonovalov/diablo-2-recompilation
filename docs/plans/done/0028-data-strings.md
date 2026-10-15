# 0028 — Data: string tables at run time, confirmed and specified

> **Status:** done (approved 2026-10-15, closed 2026-10-15)
> **Created:** 2026-10-15
> **Owner skill(s):** reverser, spec-writer
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0003-runtime-experiments, 0011-harness-slots

## TL;DR

**Question:** given a string index or a string key, which text does the game return, and through which tables,
fallbacks and hash probes? [data/0003](../../findings/data/0003-string-tables.md) reads the code (`[I]`) and confirms
two points (the crc check and the excel 5382 rule, `[C]`). The lookups themselves were never logged. This plan logs
them and checks them against a model of the code, then writes the spec. When it is done:
- `tools/tbl.py` predicts `GetByIndex`, `GetByKey` and `FindInTable` (the probe count included) for any index or key;
- [data/0003](../../findings/data/0003-string-tables.md) has its lookup rules at `[C]` for the cases a run reaches;
- `docs/specs/data/strings.md` is drafted, and monsters/special § I and the later `hirelings` row link it.

## Context

- Research-map row `data/strings`: findings `[I]`, crc `[C]`. Dependency `data/excel` is reviewed. Consumers:
  [monsters/special](../../specs/monsters/special.md) § I (unique names: the row picks are `[C]`, and the text lookup
  points at data/0003 `[I]`), [items/affixes](../../specs/items/affixes.md) § E (rare names stop at the merged id), and
  `hirelings` (not started). Nothing waits on it, but `hirelings` names it as a dependency and it is small.
- Code already named (`re/symbols.csv`, subsystem `data/strings`): `STRTABLE_LoadAll` `0x005259C0`, `LoadFile`
  `0x00525920` (C), `Crc16` `0x00525020` (C), `GetByIndex` `0x00524A30`, `EntryToString` `0x00524930`, `Hash`
  `0x005249E0`, `FindInTable` `0x00524C60`, `GetByKey` `0x00524D30`, `KeyToIndex` `0x006117B0` (C), the not-translated
  placeholder `0x00524AC0`.
- Format: [tbl.md](../../formats/tbl.md) (`[C]` for the bytes); `tools/tbl.py` parses the files.
- Open in data/0003: the classic ≥ 20000 path (expected to become 11078), the entry-500 fallback, and the node offset
  checks have not run. Whether any language byte picks `pol`/`por`/`rus` is not settled.
- No community lead covers the run-time lookup. Phase 1b is not needed: the format is ours, and the hash is
  documented in tbl.md from the data.

## Phases

### Phase 1 — Log the lookups and model them
- **Owner skill:** reverser (agent-driven per [harness-play](../../../.claude/skills/reverser/references/harness-play.md);
  one slot)
- **What:** extend `tools/tbl.py` with a lookup model (`index`, `key`, `probe`), write `tools/gdb/strings.gdb`, and log
  a session of ordinary play. Lookups happen constantly (the UI, item names, monster names), so a short session in
  each mode is enough.
- **Logging:** at `GetByIndex` the index in and the node returned; at `GetByKey` the key, the table searched and the
  index returned; at `FindInTable` the home slot, every slot probed and the result. Rate-limit by distinct
  index or key, so the log stays small.
- **Outputs:** `tools/tbl.py` (lookup model and a `check <log>` command); `tools/gdb/strings.{gdb,py}`;
  `run:YYYY-MM-DD-strings` in a new `docs/findings/data/experiments.md`; data/0003 tags moved.
- **Done when:**
  - `tbl.py check` reproduces every logged lookup, 0 mismatches, in one expansion and one classic session (the
    classic save checked to be classic, harness-play § The character). The record gives the counts of distinct
    indices, distinct keys, and probe chains longer than one;
  - the classic ≥ 20000 path is reached (an expansion item or string requested in a classic game), or it is named as
    unreachable on stock data, with the reason;
  - the entry-500 fallback and the node offset fatals stay `[I]` unless a stock case reaches them. They are not forced:
    a forced path would mean editing a `.tbl` file, and the crc check already makes that a fatal error;
  - the language question is answered statically (what values `data\local\use` can hold in the shipped install, per
    data/0002), and the answer is recorded in data/0003;
  - data/0003's *Open questions* is updated, and every claim the run reproduces is `[C]`, citing it.

### Phase 2 — Spec: data/strings
- **Owner skill:** spec-writer
- **What:** write `docs/specs/data/strings.md` (loading order, index → text, key → index, hash probing, the 5382 rule
  for excel cells, the fallbacks and fatal paths) and link it from monsters/special § I, items/affixes § E and the
  data README.
- **Done when:** the spec follows the template, and every statement is tagged. It has a worked example of a key lookup
  with a probe chain longer than one, taken from the run, and a table of the index bases and fallbacks. It says which
  parts a reimplementation needs (lookup by index for names) and which only guard corrupt files. The architect's
  review passes.

## Open questions

- Fonts, text rendering and the colour codes inside strings are presentation (ADR-0002/0005). The spec stops at the
  UTF-16 string.
- Non-`eng` languages: if the install can't select one, they are named and not tested.

## Implementation log

_(lanes append dated entries as phases land: what was found, the confidence reached, surprises)_

- **2026-10-15 — Drafted and approved.** The owner asked for a queue of plans to run unattended, and approved all of
  them in advance. Written in the architect worktree `lane/plans0028`.
- **2026-10-15 — Phase 1 landed (reverser, harness slot 2; branch `lane/h28p1`).**
  [run:2026-10-15-strings](../../findings/data/experiments.md#run2026-10-15-strings): one expansion and one classic
  session (`UniqNova` / `UniqClassic`, Normal; classic checked by the status byte and the four-tab waypoint hop).
  `tools/tbl.py check` reproduces 336 index lookups (201 distinct indices: 187 expansion, 149 classic) and 3 928 key
  lookups (1 964 distinct keys per session) with 0 mismatches; 885 hits per session after more than one node, the
  longest 5 159 nodes; 2 844 misses per session, each over all `max_probes` nodes. New: `tools/tbl.py` `GameStrings`
  with `index`, `key`, `probe` and `check`; `tools/gdb/strings.{gdb,py}`; `docs/findings/data/experiments.md`.
  [data/0003](../../findings/data/0003-string-tables.md): index → text, key → index, the hash (signed chars, three keys
  with a byte ≥ 0x80), the probe walk, duplicated keys, the placeholder and the UTF-8 → UTF-16 conversion moved to
  `[C]`. Surprises: (1) **`expansionstring.tbl` is loaded whenever `d2exp.mpq` exists, also in a classic game** (the
  load flag is `HasExpansionMpq()`, not the game's mode), so the 11078 path is unreachable on a stock install
  (named, with the reason); (2) the placeholder suffix is `" -not xlated call ken w"` and loses its last character;
  (3) every conversion's limit comes from a character count driven by the font map `default.map`, which matters only
  for placeholders on the shipped `eng` tables. Entry 500 and the fatal checks were not reached and stay `[I]`. The
  language question is answered statically in data/0003 § Language (only `ENG`, and `RUS` through a loose `Use_rus`
  under `-direct`, which would crash). A first logger with a breakpoint per probe was too slow (a miss examines up to
  5 192 nodes); the run's logger reads the probe count at the exits.
- **2026-10-15 — Phase 2 drafted (spec-writer; branch `lane/s28p2`).** [data/strings](../../specs/data/strings.md), status
  `draft`, tags C 59 / I 37 / L 4 (Open questions only): § A loading (`expansionLoad = HasExpansionMpq()`, CRC and
  offset checks, missing file), § B the UTF-8 → UTF-16 conversion and character count, § C index → text, § D key →
  index and the placeholder, § E the signed hash and the probe walk, § F the 5382 rule, § G a table of index bases,
  fallbacks and fatal paths marking which a reimplementation needs and which only guard corrupt files, § H language.
  Worked example `of Amianthus` (run:2026-10-15-strings) plus index rows and a not-found key. Linked from
  monsters/special § I, items/affixes § E, the data README and the glossary. [data/excel § I](../../specs/data/excel.md#i-string-table-keys)
  I3 corrected (`expansionstring` loads whenever `d2exp.mpq` exists). 4 open questions: the unreached fallbacks and
  fatal checks (stay `[I]`), `GEMS_Load`'s keys, other charsets' font maps, the rare-name text (backlog, reverser).
  Awaiting the architect's review.
