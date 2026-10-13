# ADR-0009 — Public documentation: deferred; a later, heavily redacted export with no tie to the repository

> **Status:** proposed (owner decided 2026-10-13: no site now)
> **Date:** 2026-10-13
> **Related plan(s):** none; a plan is written only when publication is taken up again

## Context

The owner considered publishing the documentation as a static site (GitHub Pages or similar), for
people to read rather than as Markdown in a repository. Most of what we write is safe to publish. Copyright protects
expression, not methods, algorithms, facts or data formats (US 17 USC §102(b); EU Software
Directive 2009/24/EC Art. 1(2); *SAS Institute v World Programming*, CJEU C-406/10, 2012, on
functionality and data file formats). A spec in our own pseudocode, with our own prose and tables of
column meanings, describes how the game works. It is not Blizzard's code. Community write-ups of D2
mechanics have been public for over twenty years.

The risk is in specific kinds of content, not in publishing as such. (1) **Contract and
anti-circumvention.** The game's EULA forbids reverse engineering, and a public site shows that we
did it. In *Davidson & Associates v. Jung* (8th Cir. 2005, the bnetd case) Blizzard won on both an
EULA reverse-engineering ban and DMCA §1201, in a project that emulated Battle.net's CD-key check.
The EU's interoperability exception (Directive Art. 6) can't be overridden by contract, but it is
narrow. (2) **Code-shaped excerpts.** Findings quote decompiled routines as C-like listings
("trimmed, our names", e.g. [items/0002](../findings/items/0002-quality-roll.md)). Renamed variables
don't stop such a listing from being argued a derivative of the binary's code. `docs/findings/` holds
dozens of these blocks, and `re/symbols.csv` plus `re/types/` map the binary's functions and structs.
(3) **Data.** The EU has a sui generis database right (Directive 96/9/EC). A full dump of a table is
more exposed than a column schema. Item names and flavour strings are creative expression. ADR-0001
and CLAUDE.md already keep game data out of git; what is in `docs/tables/` today is schema,
semantics and short illustrative rows. (4) **Trademarks.** "Diablo" and "Blizzard" may be used to
name the game (nominative use), not as branding. (5) **Third-party text.** Entries in
`docs/sources.md` are other people's writing, under their own terms.

**The repository is already public** (`origin` on GitHub, visibility PUBLIC, checked 2026-10-13).
So everything above, findings and `re/` included, is published today. A site that leaves out
findings while the repository serves them, or links back to it, excludes nothing. Faced with this,
the owner chose on 2026-10-13 not to publish a site now, and to publish later only a heavily
redacted form with no tie to the repository.

Specs and table docs cite findings heavily: 118 relative links from `docs/specs/` into
`docs/findings/`, from 44 files across specs, tables and formats (counted 2026-10-13). The evidence
trail is the point of the project, and it can't be cut silently.

## Decision

We **don't publish a documentation site now.** When publication is taken up again, it is a
**separate, heavily redacted export** of the deliverable, made for that purpose. It is not a render of
this repository. The export carries **no reference to the working repository**: no repository URL
or owner name, no paths into `docs/` or `re/`, no finding ids, and no links to unpublished files. How
deep the redaction goes (addresses, anchors, evidence tags, code-shaped pseudocode) is decided by
the plan that builds the export, against the five risk kinds above. That plan also builds a
mechanical publish check (decompiler-like code blocks, game-data tables over 20 rows, leftover
repository references) that must be green before any export leaves the machine, and adds a footer:
an unofficial, non-commercial preservation project, not affiliated with or endorsed by Blizzard
Entertainment; no game files, art, text dumps or code included; no logos or game art. **One rule
takes effect now, in every lane, published or not: the project never documents copy protection, the
CD key, Battle.net authentication or Warden** beyond a one-line "out of scope" note. The owner runs
any publish. This ADR doesn't decide the repository's own visibility (see Consequences).

## Consequences

### Positive
- Nothing new is exposed, and the lanes keep working as they do now, with full evidence.
- A purpose-built export can be redacted as far as needed, without the working docs having to stay
  publishable.
- Banning protection and auth topics now closes the door the closest precedent (bnetd) went through,
  before anything is written there.

### Negative
- **The working repository is still public.** The decision not to publish a site doesn't change
  that `docs/findings/` (code-shaped listings) and `re/` (the binary's symbol map) are served by
  GitHub today. That exposure is larger than any site would add, and it is the owner's call,
  outside this ADR. Making the repository private later doesn't unpublish existing clones or forks.
- **A redacted export with no tie to the repository can't show its evidence.** Readers have to take
  the tags on trust, or check against their own binary if addresses survive the redaction.
- **Two forms of the docs** once the export exists: the redaction has to be redone, or rechecked,
  each time it is cut.
- This isn't legal advice. If the owner wants certainty, it takes a lawyer in their jurisdiction.

### Neutral
- The lanes, evidence rules and docs gate don't change.

## Alternatives considered

### A curated site now, built from a private working repository
The first draft of this ADR. It lost because the owner prefers to publish later, heavily redacted,
with no tie to the repository at all. A site built from the repository would keep that tie.

### A site built from the public repository as it is
Simplest. It lost because findings and `re/` would be one link away from every page.

### Never publish
No exposure. It lost because a preservation spec that nobody can read preserves less. The owner
keeps publication as a later step.
