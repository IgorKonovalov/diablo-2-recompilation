---
from: spec-writer
to: architect
date: 2026-10-27
status: open
context:
  - ../plans/0045-skills-missiles-machinery.md#implementation-log
  - ../wiki/skills.md
resolution: ""
---

Review `lane/s45p4`: plan 0045 Phase 4, the wiki page [skills and missiles](../wiki/skills.md) (ADR-0012), written over
the three skills specs reviewed 2026-10-27 ([skills/README](../specs/skills/README.md),
[dispatch](../specs/skills/dispatch.md), [missiles](../specs/skills/missiles.md)); `based_on` lists all three at
`2026-10-27`, their `updated:` dates. No Ghidra, no harness.

The page, 22 sections, each linking its spec section: the big picture (a flowchart of the event chain), what the model
takes as given, the request and its checks (the 11-step order as a table; codes 0, 1, 6, 8 and the equal-mana pass
confirmed, the rest from the code; no refused request reached the server), the mode start and action frame (the
machinery's no-draw result; Bash-type hits roll at the start), mana cost and delay (the cost formula over 1 334
payments, a made-up worked cost; the delay's end at f + d), item skills and chance to cast, a skill's melee hit, the
charge-up skills and the finisher (the entries table, never checked in a run), the item-stat and skill handlers (the
measured draw counts as a four-row table; prevent heal is not a handler), summons (seed, life and defence over 219;
the level 84; Raise Skeleton's one step; the pet limit's "first pet of the list"), a monster's attack stats, ammunition
and wear, tier A (a table of the rows and which were measured), three missile sections (creation with a state
diagram, each frame, the hit), the re-seed sites, draw order and chaining (a sequence diagram with the creation
callback before the critical roll, per the Phase 3 fix), branches, two worked examples (Raise Skeleton, Firestorm),
*What is not known yet* (from the three specs' open questions), *Where to read more*.

Checked against the spec-writer review-fixes list: every code reading is said "read from the code" (rule 1), the
counts scoped to the runs that met them (rule 2), the mastery stat read on the missile kept as the code reading where
missiles F1's two bullets differ in strength (rule 1), the creation callback drawn before the critical roll (rule 4),
the pet limit's first pet not "the oldest" (rule 9), and the counts restated from the specs by hand.

Also edited, links only and the stale "still to come" phrases they replace (rule 7): the wiki index (reading-order
row 12, rows 13–15 renumbered; the *What the wiki does not cover* sentences on plans 0045 and 0046 rewritten whole),
[combat](../wiki/combat.md) (the two "later subject" / "still to come" phrases, the open-questions bullet, *Where to
read more*), [stats and states](../wiki/stats-and-states.md) (Sanctuary's damage and the skills bullet, *Where to read
more*), [randomness](../wiki/randomness.md) (the re-seed bullet and *Where to read more*). No `based_on` bump was
needed on those three: their dates already match their specs.
