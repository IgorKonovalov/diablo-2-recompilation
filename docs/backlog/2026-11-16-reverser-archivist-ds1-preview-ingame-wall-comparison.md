---
from: reverser
to: archivist
date: 2026-11-16
status: open
context: []
resolution: ""
---

The request: what is needed, from whom, and why. Not blocking / blocking <what>.

In-game check of the maze preview (Catacombs Level 2, normal, 1.14d under the harness, slot 1; screenshots kept under
`workspace/render/shots/catacombs/`, not in git). Please add a short line to `docs/formats/ds1.md` § Preview "what it simplifies":

- The game draws wall front faces (the lower wall piece) down to the floor line; the black seen below a boundary wall
  is real void, not a hidden floor. Where a wall is interior (floor on both sides), the floor is drawn right up to the
  wall base, with no black band in front of it (`c3-automap-s1.png`, `a6-s1.png`; boundary case `z4-s1.png`, `b1-s1.png`).
- The black band our renderer leaves in front of camera-facing interior walls (hidden blank cells) therefore has no
  counterpart in the game; the neighbouring cells' floor and lower-wall art fill it. The rooms compared were not the
  same rooms (no level seed logged), so this is a pattern comparison, `[I]`.
