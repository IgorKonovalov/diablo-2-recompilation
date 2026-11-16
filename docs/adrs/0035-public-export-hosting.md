# ADR-0035 — The public export's hosting: a separate repository under the owner's GitHub account, a Starlight site on GitHub Pages (amends 0009)

> **Status:** accepted (owner, 2026-11-16, with plan 0070's answers: "1 b / 2 keep / 3 github pages, similar to
> @../Ritmolux/ documentation / 4 yes / 5 go as recommended"; on the account: "My account, like Ritmolux"); amended by [ADR-0036](0036-schematic-illustrations-in-the-export.md) (the cut may hold marked schematic illustrations, served as static files)
> **Date:** 2026-11-16
> **Related plan(s):** [0070-redacted-public-export](../plans/0070-redacted-public-export.md)

## Context

[ADR-0009](0009-public-documentation-site.md) deferred publication to a separate, heavily redacted export. It ruled
that the export carries no reference to the working repository: "no repository URL or owner name, no paths into
`docs/` or `re/`, no finding ids, and no links to unpublished files". It left the host open.
[Plan 0070](../plans/0070-redacted-public-export.md) proposed the redaction and the publish check, and asked the
owner five questions. One of them was the host, another whether to keep the no-tie rule.

The owner answered on 2026-11-16. Scope (b): the wiki and the glossary first, then the redacted specs. Keep the
`[C]`/`[I]` tags without anchors. Host on GitHub Pages, "similar to" the owner's other project's documentation. Keep
the no-tie rule. Re-cut on request. Asked which account owns the export repository, the owner answered "My account,
like Ritmolux".

That other project's documentation is an Astro Starlight site in a `site/` folder of its repository. A `pages.yml`
workflow has two jobs. The build job runs on every push and every pull request and is the guard: it renders Mermaid at
build time with a headless browser, then runs a link check. The deploy job runs only from `main`. The base path is the
repository's name as spelled. A queued deployment waits instead of cancelling (`cancel-in-progress: false`). The npm
dependencies are pinned to exact versions, and CI installs them from a committed lockfile.

Two answers pull against each other. The owner's account puts the owner's name in the export's URL
(`<account>.github.io/<repository>/`) and on every commit. The working repository is public under the same account.
ADR-0009's rule barred the owner name. Keeping the rule as written would mean a second account, which the owner did
not choose.

## Decision

**The export is a separate repository under the owner's own GitHub account, published as an Astro Starlight site on
GitHub Pages.** It is set up like the owner's other documentation site: a `site/` project with exact-pinned npm
dependencies and a committed lockfile, and a `pages.yml` workflow whose build job (install, Mermaid drawn at build time,
build, link check) runs on every push and pull request, and whose deploy job runs only from `main`. The base path is the
export repository's name as spelled. Deployments queue and never cancel.

**ADR-0009's no-tie rule is relaxed for the owner's account and name only.** The owner's name may appear where the
host puts it: the account in the URL, the commit author, a "GitHub" link to the export repository itself. The rest of
the rule stands. The export carries no link to the working repository, no repository paths, no finding or run ids,
no plan, ADR or lane names, and no commit hashes. The export repository's name is neutral: it is not the working
repository's name, and it uses no trademark.

**What the export repository holds.** Only three things: the redacted Markdown cut, the Starlight site project, and
its workflow, with a README and a LICENSE. Never game data, never `docs/findings/`, never `re/`, never this
repository's history. Each cut is copied into the export repository's content folder by hand. It is never a clone,
fork or subtree of this repository.

**Who does what.** Agents never create the export repository, never push to it, and never enable its Pages. The owner
does all three. Agents prepare files under `workspace/` and stop there.

**Dependencies.** The npm dependencies live only in the export repository. This repository's `tools/` stays
standard-library Python, as before (ADR-0005, ADR-0034). `tools/export_build.py` writes a Markdown tree shaped for
Starlight's content collection, not HTML.

**Two guards.** `tools/export_check.py` runs here, on the cut and on the export repository's files, and must be green
before the owner copies anything over. The export repository's CI build and link check are the second guard. A green
CI run does not replace the check here: it knows nothing of the redaction.

**Licence and footer.** The export repository's LICENSE is CC BY 4.0 for our text. The owner may change it before the
first push. Every page carries ADR-0009's footer: unofficial, non-commercial, not affiliated with or endorsed by
Blizzard Entertainment, the trademark notice, no game files, art, text dumps or code. The footer is a Starlight
component override, so no page can be built without it.

## Consequences

### Positive
- The host is one the owner already runs. The stack, the workflow and the guard pattern are known to work.
- A pull request to the export repository is built and link-checked before anything is served.
- Mermaid is drawn in CI, so the cut holds only Markdown and no generated images.
- This repository gains no npm dependency and no JavaScript toolchain.

### Negative
- **The export and the working repository are tied by name.** Both sit under one account. Anyone can find the
  working repository, and with it `docs/findings/` and `re/`, from the export's URL. ADR-0009's no-tie rule now bars
  only the direct links. It no longer hides the connection. The owner accepted this by choosing the account, and
  had already ruled that the working repository stays public.
- **Starlight's output is not the plain HTML plan 0070 first described.** It ships scripts (search, theme toggle).
  The publish check can no longer bar every script. It scans the Markdown cut and the site project's files instead,
  and the export's own CI is trusted for the build.
- **A second repository to keep.** Its dependency pins age. A Starlight or Astro upgrade is the owner's work there,
  not a lane's here.
- **Takedowns reach the owner's account.** A DMCA notice against the export lands on the same account as the working
  repository. This isn't legal advice (ADR-0009).

### Neutral
- The redaction depth, the allowlist and the publish check stay plan 0070's. ADR-0009's ban on documenting copy
  protection, the CD key, Battle.net authentication and Warden is unchanged.
- The local site of ADR-0034 is unchanged. It is not the export and is never pushed.

## Alternatives considered

### A second GitHub account under a neutral identity
It keeps ADR-0009's rule whole. It lost because the owner chose their own account, and because the working
repository is public anyway: a reader who connects the two by content sees both.

### Render the export here with `tools/site_build.py` and push plain HTML
No npm and no second toolchain. It lost because the owner asked for the setup of their other documentation site, and
because a CI build on the export repository gives a second guard for free.

### Keep the Starlight project in this repository
One place for everything. It lost because it would bring npm into this repository, and because a site project here
would sit one directory from `docs/findings/`.
