---
from: spec-writer
to: architect
date: 2026-10-27
status: open
context:
  - ../wiki/monsters.md
  - ../wiki/saves.md
  - ../../README.md
resolution: ""
---

Review request, lane/wiki (owner request): the wiki refresh over the 2026-10-27 re-tags, and the root README.

Method: for each page, each based_on spec was diffed from the page's last commit to main fcce5b4d (git diff, which also catches changes reached through merges), and the commit log of each spec after the page's last commit was read. Content diffs remained only for wiki/monsters (spawn J3; special § J, the MonPostCreateBoss table and Nihlathak's [C]; stats F3 and the § H1 attack-time raise; lifecycle's wanderer-list row), wiki/seed-to-world (objects review fixes, no page text affected) and wiki/skills (dispatch I4's anchor and tables row, no page text affected). The other pages' specs were edited in the same commits as their pages. Their What is not known yet sections were checked against the specs' open questions.

- wiki/monsters: new section "Mods a class is created with" (special § J: the MonPostCreateMods cases [C], the flag-2 gate and the MonPostCreateBoss rows read from the code, Nihlathak's 22 [C]); a summon creation paragraph (spawn J3, stats F3); the attack-time paragraph (stats § H1: stats 21, 22 and 19 from the plain cells by mode confirmed, the rest read from the code); the Raven MonProp line; the Stats bullet of What is not known yet.
- wiki/saves: the mercenary-header name added to the not-exercised list (save/d2s Open questions).
- Left to the lanes beside this one: the vendor and gambling sections (lane/s38v), the hireling sections (lane/s38h), and anything resting on player/creation (H6g). Their based_on entries are untouched.
- Root README: Scope rewritten (ADR-0014's five phases, ADR-0020, ADR-0017, ADR-0022's sixth phase, plan 0052 approved). Status table: every status and date now set from the specs' front matter. Rows added: chain (core); drlg/lifecycle (enablers); combat/to-hit, combat/damage, combat/reductions, combat/delivery, stats/aggregate, stats/states, skills/dispatch, skills/missiles, and the unreviewed skills/catalogue, anim/timing, anim/movement and monsters/ai with the map's status and no date (simulation); quests/progression, quests/travel and items/economy (game rules, a new group). Overview dates are given in the rows that name them. The plans list and the backlog links were updated.

Gate green before the commit.
