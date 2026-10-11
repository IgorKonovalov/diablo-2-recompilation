# ADR-0007 — A lead is a document read in-session, never a recollection

> **Status:** accepted
> **Date:** 2026-10-11
> **Related plan(s):** 0005-prerequisite-formats, 0006-asset-rendering; amends ADR-0001 (sources policy)

## Context

ADR-0001 allows community documentation as a lead and forbids third-party decompiled or reconstructed
code. It assumes a person who knows which page they read. Our lanes are language models, and they
can "remember" a format from training data without knowing where the memory comes from.

That has now happened twice. The plan 0006 Phase 4 review found that the DCC decoder was built from
a write-up the agent "remembered" but never fetched. The registered document (Paul Siramy's "Extracting
Diablo II Animations") turned out to be a user tutorial with no bitstream description at all, and the
registered URL was a C-source download page. The bitstream knowledge therefore came from an
unidentified source, which may have been a prose format doc (allowed) or a C decoder (not allowed).
The code didn't read as transliterated, and bit accounting pins most of it, but four zero-cost rules
had no legitimate lead. `src:siramy-ds1edit` (DS1/DT1) also says its layouts were "recalled from the
editor's documentation".

A recollection can't be checked against the policy, because nobody can show what it was recalled
from. "Docs yes, code no" only works when the doc can be produced.

## Decision

A **lead** is a document that the lane fetched and read in the same session, registered in
`docs/sources.md` *before* use, with a URL that serves that document and a note saying which sections
were used. Knowledge a lane has without such a document (a recollection, "common knowledge", a name it
"knows") is not a lead and may not be cited as `src:`. Where no fetched lead exists, the doc says
"no lead; derived from data" (or "from code"), and the claim stands on its own evidence. A lane that
notices it is relying on recall stops and either fetches a registrable document or re-derives the
claim from data or code. A fetched page that turns out to contain decompiled or decoder source is
registered as `rejected` per ADR-0001, and nothing derived from it may be used. Existing leads that
were recalled rather than fetched (`siramy-ds1edit`, `siramy-dcc`) are re-checked against the
fetched document or downgraded to "no lead". Every `[L]` that cited them either gets the fetched
section or the words "no lead".

## Consequences

### Positive
- The sources policy becomes checkable: a reviewer can open every `src:` URL and find the cited text.
- Contamination by remembered decoder code is cut off at the point of citation rather than discovered
  in review.
- "No lead; derived from data" is honest and pushes work toward the evidence we actually own (byte
  accounting, code anchors, runs).

### Negative
- **It does not stop recall from steering the work.** A model that remembers a decoder may still
  write one shaped by that memory and then "derive" it. Review stays the control: identifiers,
  structure and comments that mirror known decoders are a finding, and any claim that the data can't
  pin and no fetched lead supports stays `[L]`.
- Slower: format work that could lean on memory now has to fetch, register and cite, or re-derive.
- Some community documents are offline or blocked (several returned HTTP 403 during plan 0004 Phase
  1b). A claim whose only source is unreachable gets no lead.

### Neutral
- Tags don't change: a lead never raised a tag before and doesn't now.
- `docs/sources.md` gains a "Used for" note per row naming the sections read.

## Alternatives considered

**Keep ADR-0001 as written and fix the two records.** Lost because the failure is structural: the
next format will invite the same recall, and nothing in the rules would catch it before review.

**Ban community format documents for all format work.** Lost because fetched prose documentation is
exactly what ADR-0001 means to allow, and it saves real time (the D2S README, ds1edit notes).

**Put the rule in evidence-rules.md only, without an ADR.** Lost because it changes ADR-0001's
sources policy, and an ADR is how that policy is changed.
