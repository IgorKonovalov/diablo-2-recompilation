---
from: spec-writer
to: architect
date: 2026-10-17
status: done
context:
  - ../plans/done/0041-stats-and-states.md
resolution: "Reviewed 2026-10-17: accept with fixes (15: overclaim 3, misread 7, omission 5), applied on lane/wiki7; research-map rows link the page; verdict in plan 0041's log."
---

[2026-10-17] from spec-writer → architect: review `lane/wiki7` (from `main` `a3a5abe`), the wiki work of
[plan 0041](../plans/done/0041-stats-and-states.md#implementation-log) owed by the closed entry
[plan-0041-wiki-after-review](2026-10-17-spec-writer-spec-writer-plan-0041-wiki-after-review.md). Not blocking.

- **New page [wiki/stats-and-states](../wiki/stats-and-states.md)**, `based_on` stats/README, stats/aggregate and
  stats/states (all 2026-10-17). Sections: the big picture (list tree diagram, the cache, no draw but the aura hit);
  derived stats (the op table: 1, 2, 4, 5, 8, 9, 11, 13 confirmed, 3, 6, 7, 10, 12 read from the code; the non-base
  energy and vitality, the chain, the hidden per-level source and the strength quirk; level-up); maxima and the
  rescale (diagram); requirements, ethereal −10, the refresh steps, the 136-frame refresh (read from the code and the
  run's timing), per-level item values not refreshed on level-up; dual wield and the weapon switch; set bonuses
  (diagram; partial pairs, full, `add func`, the full Trang-Oul's lists as logged); passives; timed states (state
  diagram; refresh, refuse, replace confirmed; curses, curse resistance, Attract read from the code); how a state
  ends; group clears; regeneration (life, stamina, mana, poison); auras (the grid, `perdelay + 1`, two casters,
  Sanctuary's draw); shrines and wells (all read from the code; shrine states count as curses); worked examples
  (six, from the two specs' examples); what is not known yet; where to read more.
- **[wiki/README](../wiki/README.md):** a row 10 for the page (Saves now 11); *What the wiki does not cover* names
  stats and states as the second simulation row, drops the 0041 bullet from the open plans, and says skills and
  missiles have no research-map row yet.
- **[wiki/combat](../wiki/combat.md):** *What the model takes as given* links the page and keeps the combat run's
  stats as inputs (combat README open question); the player's life tick under poison confirmed, its floor read from
  the code; the *not known* bullets rewritten (the inputs; the floor instead of the tick); a related-page link.
- **[wiki/characters](../wiki/characters.md):** the level-up maxima sentence links the page (the run's values stay
  given); the struck *not known* bullet removed; a *Where to read more* link.
- **Please check:** each hedge against its spec tag, above all the op table, the take-test paragraph, the stamina
  modes (no mode names in the spec, so none on the page), the shrine and well section, and the 136-frame wording.
  Not touched (architect's): the research-map rows still say "wiki page to follow".
