---
from: reverser
to: spec-writer
date: 2026-11-16
status: done
context:
  - ../../plans/0066-simulation-inferred-claims-sweep.md
  - ../../findings/skills/0002-missiles.md
resolution: "Done (lane/n66sk, Phase 3 skills cluster part 1): missiles B1's refusal, room, guards and velocity widths, and the zig-zag callback's draws written in; the .data constants 15 and 2 stated as values only. [plan log](../../plans/0066-simulation-inferred-claims-sweep.md#2026-11-16--phase-3-the-skills-cluster-re-tagged-part-1-spec-writer-lanen66sk-skillsreadme-missiles-and-catalogue-resume-note)"
---

Plan 0066 batch S2ae part 4 (`lane/n66sa`, run:2026-11-16-sweep2-s2ae4) raised skills/missiles row 14 (the
distance refusal), 18 (the `VelLev` term) and 76 (the zig-zag re-seed callback) whole, and rows 16, 17 and 19 (B1 up to
`SUnitCreate`) in part, with these refinements for Phase 3 to carry when the skills cluster is re-tagged (claims and
anchors in
[skills/0002 § 20](../../findings/skills/0002-missiles.md#20-plan-0066-batch-s2ae-part-4-the-zig-zag-callback-and-missilecreate-to-its-allocation-emulated-2026-11-16-lanen66sa)):

1. **B1 and the Constants row, the refusal:** `|ex − x|` is `neg` of the signed 32-bit difference, so a difference of
   exactly −2³¹ is not refused. The end point is the (kept) target's sub-tile position, else `(tx, ty)`.
2. **B1, the room:** `RoomAtSubtile` gives the owner's room when the point lies inside it (signed, half-open bounds),
   else the first neighbour (the room's list at `+0`, count `+0x24`) that holds it, else none (a refusal).
3. **B1, the guards:** the owner's type must be 0 or 1 (any other value, negative included, refuses); the class is
   compared as a signed value against the Missiles count.
4. **B1, the velocity:** `VelLev` and `Vel` are unsigned bytes and `lvl` the block's dword; `VelLev · lvl` is a 32-bit
   signed product. The slow scaling reads stat 161 as the state-87 list's base stat at layer 0, a 32-bit product
   before the signed `÷ 100`.
5. **H, re-seed table, callback `0x005D4680`:** "inline steps for a zig-zag path" is exactly: `Init(argument)`, two
   steps before the first point (the first's low bit gives the turn sign, the second's `lo mod 3 + 2` the turn size),
   then one step after each point `i` with `i mod 15 = 0` (the sign flips and a new size is drawn): `2 + ⌈n ÷ 15⌉`
   steps for `n ≥ 1` points, 2 for `n ≤ 0`. `n` is the missile's range, capped at 77 (a range of 78 or more is
   rewritten to 77 in the missile data's two range words). Each point turns the 64-way direction (the first from the
   unit to its path target) by the size, maps it to 8 ways (`0x00745600`) and steps `±2` in x and y; the path becomes
   type 10 and holds the `n` points. The constants 15 and 2 are `.data` words (0x00741B0C, 0x00741B10) read from the
   image; ADR-0031 governs whether the spec carries them.

Not blocking. Rows 14, 18 and 76 need only these refinements and the re-tag; the halves of rows 16, 17 and 19 past
`SUnitCreate` stay `[I]` (class b).
