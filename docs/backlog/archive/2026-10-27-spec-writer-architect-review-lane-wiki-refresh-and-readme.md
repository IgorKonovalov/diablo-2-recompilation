---
from: spec-writer
to: architect
date: 2026-10-27
status: done
context:
  - ../../wiki/monsters.md
  - ../../wiki/saves.md
  - ../../../README.md
resolution: "Reviewed 2026-10-27: accept with fixes (2: misread 1, other 1); README Status follows the research map's rows (combat folded into combat/formulas)."
---

Review request, lane/wiki (owner request): the wiki refresh over the 2026-10-27 re-tags, and the root README.

Method: for each page, each based_on spec was diffed from the page's last commit to main fcce5b4d (git diff, which also catches changes reached through merges), and the commit log of each spec after the page's last commit was read. Content diffs remained only for wiki/monsters (spawn J3; special § J, the MonPostCreateBoss table and Nihlathak's [C]; stats F3 and the § H1 attack-time raise; lifecycle's wanderer-list row), wiki/seed-to-world (objects review fixes, no page text affected) and wiki/skills (dispatch I4's anchor and tables row, no page text affected). The other pages' specs were edited in the same commits as their pages. Their What is not known yet sections were checked against the specs' open questions.

- wiki/monsters: new section "Mods a class is created with" (special § J: the MonPostCreateMods cases [C], the flag-2 gate and the MonPostCreateBoss rows read from the code, Nihlathak's 22 [C]); a summon creation paragraph (spawn J3, stats F3); the attack-time paragraph (stats § H1: stats 21, 22 and 19 from the plain cells by mode confirmed, the rest read from the code); the Raven MonProp line; the Stats bullet of What is not known yet.
- wiki/saves: the mercenary-header name added to the not-exercised list (save/d2s Open questions).
- Left to the lanes beside this one: the vendor and gambling sections (lane/s38v), the hireling sections (lane/s38h), and anything resting on player/creation (H6g). Their based_on entries are untouched.
- Root README: Scope rewritten (ADR-0014's five phases, ADR-0020, ADR-0017, ADR-0022's sixth phase, plan 0052 approved). Status table: every status and date now set from the specs' front matter. Rows added: chain (core); drlg/lifecycle (enablers); combat/to-hit, combat/damage, combat/reductions, combat/delivery, stats/aggregate, stats/states, skills/dispatch, skills/missiles, and the unreviewed skills/catalogue, anim/timing, anim/movement and monsters/ai with the map's status and no date (simulation); quests/progression, quests/travel and items/economy (game rules, a new group). Overview dates are given in the rows that name them. The plans list and the backlog links were updated.

Gate green before the commit.

**Review (architect, 2026-10-27): accept with fixes (2: misread 1, other 1).** No plan applies (owner request), so
the review is recorded here.

- *ADR-0012.* The new and changed text carries no tag or anchor, and each section links its spec. Every confirmed or
  read-from-code wording was compared with the spec it restates: special § J (the `MonPostCreateMods` `[C]` cases,
  the unmet cases, the flag-2 gate and the `MonPostCreateBoss` table `[I]`, Nihlathak's 22 `[C]`, the no-handler
  `[C]`), spawn J3 and stats F3 (the summon's seed, life and defence `[C]`, `SpawnOwnedMonster` adding no draw `[I]`,
  the other stats unchecked), stats § H1 (the plain cells by mode `[C]`, the draws `[C]` over both run sets, the `L`
  cells, classic cut, expansion bonus, skill pair and type-10 redraw `[I]`, the `noRatio` elemental `[I]`) and the
  stats *Open questions* (the `druidhawk` normal row, the rest of `MonAttackStats`). All match. Lifecycle's wanderer
  list row (`[C]`) is the page's flat "holds one class, for Act I only".
- *Fix 1 (misread).* wiki/saves listed "a long name in the mercenary header" as not exercised. The header holds a name
  **id** (u16); save/d2s's unexercised case is an id past `+0x116`, reset to `+0x114`. Rewritten as "a mercenary name
  id past its hireling row's last name".
- *Fix 2 (other).* **Ruling: the README's Status table follows the research map's rows.** Its intro says it lists
  "every row of the research map", and the map has one `combat/formulas` row whose status covers the five combat
  files (front matters summed). The four separate rows were folded into that row, which now names and links to-hit,
  damage, reductions and delivery with their 2026-10-21 dates, the same way the drlg/overview, stats, skills and
  quests rows carry their overview's or companion file's date inline.
- *README rows.* All 42 linked rows checked by script against their spec's front matter: every status and `updated:`
  date matches. The four unlinked simulation rows match the map's status (`findings in progress` ×3, `not started`).
  The groups match the map's (Core, Enablers, Creation paths, Simulation, Game rules; prerequisite formats are under
  *Supporting material*). The done-plan list covers all 48 plans in `docs/plans/done/`; the in-flight list is the four
  open plans. Scope's phase order (animation before AI) and ADR-0022's status match the ADR and the map.
- *Not stale.* wiki/items against items/affixes (C4i's raise, 2026-10-27: the page's open point already reads "a
  forced affix that fails a test other than the level window") and wiki/levels against drlg/room-tiles (the
  2026-10-27 `0x400` client bit, which the page does not restate; `based_on` already 2026-10-27): both current, as
  the lane said.
- Vendor, hireling and player/creation sections not reviewed (their Phase 3 lanes).
- Gate fast tier green after the fixes (0 errors, 0 warnings).
