---
from: spec-writer
to: architect
date: 2026-10-19
status: open
context:
  - ../plans/0042-quests-travel.md
resolution: ""
---

Plan 0042 Phase 3 (quests specs) on `lane/p42s` (spec-writer), **ready for review**: the drafts of 2026-10-19 are
re-tagged from Phase 2 part 3's reviewed raises (`lane/p42r` review, 2026-10-20), `main` `d331763` merged in. Blocking
the plan's close.

**Files** (all `status: draft`; counts recounted by the gate):
- [quests/README](../specs/quests/README.md): C 11 / I 5 / L 2 (was 9 / 5 / 2).
- [quests/progression](../specs/quests/progression.md): C 114 / I 315 / L 6 (was 84 / 327 / 7).
- [quests/travel](../specs/quests/travel.md): C 68 / I 79 / L 4 (was 55 / 80 / 4).
- [save/d2s](../specs/save/d2s.md) (reviewed spec, one edit allowed by the E1 entry): C 91 / I 149 / L 3 (was 90 / 150 / 3).

**Re-tagged to `[C]`** (each against quests/0001 § 17, quests/0002 § 14 and the section each corrects, with
run:2026-10-19-quests3): progression § E1–E3 (registration, the 20-frame pass, first run at `tick = due + 1`, one-shots;
E4 re-arm and wrap `[I]`); W4 (the order on the `bkd ` use, classes in fill order, the `0x00544840` dispatch as W4a; the
stone-operate trigger W4b `[I]`); W11/W11a (the arm for level 44, period `15 + (low & 1)`, once per game by the state;
level 45 and b3/b4 `[I]`); word 4's "Cain lost" by `TownLevelLeave` (the e3 and Warriv paths `[I]`); word 12 b8, b7 on
entering 50; word 9's `ass ` use; W32 (8-try branch; 7-try `[I]`); W37 Anya's reward in three difficulties, b9/b10, the
reward-second b0/b1 row, b3 at 113, b14 at 123 (the NPC 513-second row, 114, 121/122/124 and 109 `[I]`); word 37's `tr2 `
use; word 40's 0x4ED0 → b9, 0x4ED3 → b6; the Harrogath portal note; the § G draws table and G4a. Travel A3 (Meshif's
stepping type 5; Harrogath's n = 0 exit), E1 (NPC 367's menu **for the logged state only**; "never offered" and the
branch's unreachability `[I]`), E2 (264, 175), E4 (packet 0x48's clear branch, one case per travel word; returns 3/2
`[I]`), E5 (`0x00597310` on arrival in 40), § F Harrogath portal row, G1 (refused in town; level 136 `[I]`), I1 (the
move and the draw; the writes `[I]`), the draws-by-event table; README status paragraph and two bullets.

**Settled points of the first request:** (2) save/d2s E1 restated `[C]` (and the wiki saves paragraph, `based_on`
bumped on saves and characters); (3) quests/0002's summary fixed by the reviewer; (4) cairn order in fill order `[C]`,
the *Open question* on the other reading dropped (progression L 7 → 6); (5) eclipse period `15 + (low & 1)`, never 17.

**Stay `[I]`**: the Zoo (object 567 placed by no stock DS1; note added under W40), mode-0 waypoint activation and the
`Sync` 0 draw (travel C1, plus a C2 note on `wpmodes`, not raised), the unreached e3 rows, the 7-try branch, timer
re-arm and wrap, NPC 367's travel branch.

**Points for the review.**
1. Mixed blocks carry the scope on the tag line ("[C] for …") and an untagged "not reached" comment on the unreached
   lines, the `[I]` stated in the step notes (progression E1, E2/E4, W11, W32; travel E1, E4, I1). Check none overreaches.
2. Travel E1: the "Meshif's Act III menu" sentence is `[C]` from the screenshot named in quests/0002 § 5; check that a
   screenshot is enough for the tag.
3. The packet 0x48 *Open question* `[L]` stays (the client's trigger was not logged); its "part 3 logs it" was removed.
4. Tag scoping from the first request (point 1: travel C1, E3, G2, G2a, H2; progression W12, W18, W29) still stands.

**Research map** (`docs/specs/README.md`, architect's): rows `quests/progression` and `quests/travel` can read
"draft · [quests/progression](../specs/quests/progression.md) / [quests/travel](../specs/quests/travel.md), overview
[quests](../specs/quests/README.md); re-tagged from part 3, review requested".

**Backlog closed by this lane:** the part 3 inputs entry, the part 2 inputs entry, the save/d2s E1 entry.

Gate green at the lane's last commit.
