# ADR-0012 — A human wiki: explanatory pages over the reviewed specs, no claims of their own, not published

> **Status:** accepted (owner request, 2026-10-15)
> **Date:** 2026-10-15
> **Related plan(s):** 0036-human-wiki-readme

## Context

The specs are written for a reimplementer and for agents. They carry anchors, confidence tags, exact RNG call
order and pseudocode, and a person who wants to know "how does an item drop?" has to read several of them, in
dependency order, to get an answer. On 2026-10-15 the owner asked for a **human wiki**: pages a person reads to
understand the game's systems. It is not to be published.

There are two risks. First, a second account of the same behaviour can drift from the specs, or quietly add claims
that no finding stands behind. Second, a wiki looks like something to publish, and ADR-0009 settled that nothing is
published now. Any later export is a separate, redacted artifact.

## Decision

The wiki lives in **`docs/wiki/`** as Markdown, one page per topic plus an index (`docs/wiki/README.md`). Its rules:
- **It makes no claims of its own.** Every statement in it restates a reviewed spec, and every section links the spec
  section(s) it explains (relative links, checked by the gate's E8). Where the two disagree, the spec wins, and the
  wiki page is fixed.
- **It is prose for people.** It has no confidence tags, no `fn:`/`data:`/`tbl:` anchors, no addresses, and no
  decompile-shaped code. It may use small worked numbers, tables of a few rows, and Mermaid diagrams (`E9` applies).
  A spec's `[I]` point or open question is said in words ("not yet confirmed by a run", "unknown"), never hidden.
- **It covers reviewed specs only.** A topic whose spec is not `reviewed` gets no page, or a stub that says so. The
  one exception is a page on how the project itself works (evidence tags, runs, reviews). It restates ADRs and the
  evidence rules instead of specs, and it is marked `based_on: [process]`.
- **Each page records what it is based on.** Its front matter lists `based_on:` spec paths with each spec's `updated:`
  date at the time of writing. A gate warning flags a page whose spec has a newer `updated:` date.
- **The `spec-writer` lane owns it**, and the architect reviews it like a spec. When a plan changes a spec that a
  wiki page is based on, the plan's spec phase updates the page or leaves the staleness warning for a later sweep.
- **It is not published.** It is no site, no Artifact and no export. The repository is public and the wiki is part of
  it, exactly as the specs are (ADR-0009, *Negative*). A publication remains ADR-0009's separate export.

## Consequences

### Positive
- A reader can understand a system from one page and follow links to the exact spec text when they need precision.
- The evidence trail is unchanged: the wiki adds no claims, so it adds no evidence obligations.
- The future redacted export (ADR-0009) has a natural starting text, since the wiki already avoids addresses and
  code-shaped content.

### Negative
- It is a second text to keep in step. The `based_on:` check catches stale pages, but not a wrong paraphrase; that
  is left to review.
- Writing for people takes judgement about what to leave out. A simplified sentence can be read as a stronger claim
  than the spec makes. The review checks that the hedges survive.
- It costs spec-writer time that does not advance the research map.

### Neutral
- The glossary stays where it is; wiki pages link it.
- The main `README.md` stays the project's front page and links the wiki index.

## Alternatives considered

**Summaries at the top of each spec.** Specs already have a *Purpose* section. Growing it into a tutorial would mix
two audiences in one file and inflate the gate-checked, tagged text with untagged prose.

**A rendered site kept local** (a static site generator under `workspace/`). It would add a toolchain and make the
pages harder to review in diffs. ADR-0009 also makes any rendered form a publication question. Markdown in the repo
needs neither.
