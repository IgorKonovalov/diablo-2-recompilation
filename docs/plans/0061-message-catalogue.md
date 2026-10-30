# 0061 — Client–server message catalogue: every in-game message in both directions, its fields and its send condition

> **Status:** draft (architect, `lane/plans57`, 2026-10-30), for the owner's approval; needs a scope ADR (question 1)
> **Created:** 2026-10-30
> **Owner skill(s):** reverser (phases 1, 2), spec-writer (phases 3, 4)
> **Related ADRs:** 0002-scope-creation-paths-and-enablers, 0008-two-client-harness, 0014-scope-game-simulation, 0022-scope-server-frame

## TL;DR

Which messages does a game client send the server and the server send a client, with which bytes, and when? The
client-to-server table is the server's whole input space: each handler is an entry point into specs we already have
(the skill request, the cube button, socket insertion, the move request). The server-to-client side is what a
compatible client or a replay tool must decode. When this plan is done, `docs/specs/net/messages.md` (row
`net/messages`) lists every in-game opcode in both directions with its length, its fields and their widths, its
handler or its send sites and condition, and the spec section that owns its effect.

## Context

- **Scope.** ADR-0002 and ADR-0014 list "the network protocol" as out of scope, and ADR-0022 keeps message arrival
  out. This plan needs a scope ADR that brings in the **in-game message layer** (opcodes, lengths, fields, handlers and
  send conditions) and keeps out the transport, compression and encryption, Battle.net and realm traffic, and the
  join handshake beyond the game's own messages (question 1).
- **Where the pieces live now:** the dispatch `sub_0054D750_SrvPacketDispatch` and `g_SrvPacketTable` (`0x006E0D18`,
  8-byte {handler, flag} entries, opcodes 1..0x66, `[C]` by H6a; items/0008); the `0x4F` button handler and `0x28`
  `SOCK_PacketInsert`; the skill request packet, skills/dispatch; the drain, its two queues and its place before
  `GameTick`, frame/0001 (plan 0055 P1.1, `[I]`); the send side `ClientQueuePacket` `0x0053B280`,
  `ClientFlushPackets` `0x0052E320`, the 6-byte unit packet `0x0053BDA0`, the act clock `0x53` `0x0053C900`, the room
  removals `0x0A` `0x0053A770`, `MonUnitPacketBuild` `0x0053E2E0` (all `[I]`, re/symbols.csv); the two-client harness
  (ADR-0008).
- **Dependencies:** 0055·P1 reviewed (the drain and the queues), so this plan's handler order agrees with the frame
  model. Recommended start after 0055·P3, when static lane B is free.

## Phases

### Phase 1 — Static, in three batches
- **Owner skill:** reverser (static; one headless Ghidra `-Xmx3G`)
- **What:** P1.1 the client-to-server table, every opcode 1..0x66: length rule (the table's flag, fixed or
  variable), field layout, validation and refusals, the handler and the spec section that owns its effect (or "none":
  a gap listed for a later plan); P1.2 the server-to-client builders: every caller of `ClientQueuePacket` and the
  unit-packet helpers, grouped by opcode, with layout and the condition that sends it (which pass, which event); P1.3
  the community message lists (fetched, registered leads) compared field by field, a verdict per message.
- **Outputs:** `docs/findings/net/0001-client-messages.md`, `0002-server-messages.md`; `re/symbols.csv`; a decoder
  `tools/netmsg.py` (layouts as data, no game bytes).
- **Done when:** every client opcode in the table and every server opcode with a send site has a layout `[I]` or
  better, and each P1.3 `contradicted` verdict is resolved or listed.

### Phase 2 — Capture check (one slot)
- **Owner skill:** reverser (harness, one of slots 1–2; gdb on `SrvPacketDispatch` and `ClientQueuePacket`)
- **What:** log the raw messages of a few short sessions (walking, skills, items, a waypoint, a two-client party if
  both slots are free) and decode them with `tools/netmsg.py`.
- **Done when:** every logged message decodes with no unread byte, each opcode met is counted, and the layouts met
  are `[C]`.

### Phase 3 — Spec
- **Owner skill:** spec-writer (Opus)
- **Outputs:** `docs/specs/net/messages.md`, `docs/specs/net/README.md`; row `net/messages`.
- **Done when:** a Tier A review accepts it.

### Phase 4 — Wiki
- **Owner skill:** spec-writer (wiki; Sonnet)
- **Done when:** a wiki page or section over the spec, no claims of its own.

## Resources and limits

- Static lane B after 0055 and 0054, or lane A after 0052's catalogue; one Ghidra. One harness slot for one short
  lane run (two if the two-client part runs).
- **Estimate:** P1 three reverser runs (about 100 client and 150–180 server opcodes); P2 one; P3 one or two; P4 one.

## Owner questions (recommendations)

1. **Scope ADR.** *Recommendation: bring in the in-game message layer only* (opcodes, fields, handlers, send
   conditions); transport, compression, encryption, Battle.net, realm and the pre-game handshake stay out.
2. **Both directions?** *Recommendation: yes*, client-to-server first (it is the server's input and touches the specs),
   server-to-client after.
3. **When.** *Recommendation: after 0055·P3*, so the drain's order is reviewed and lane B is free.
4. **Capture.** *Recommendation: gdb breakpoints in a short session* (no injected logger; ADR-0022's logger triggers
   are not met by this).

## Open questions

- Whether some server messages are built only by the client-side local server path (game modes 0 and 1) and never by
  the open server: answered in P1.2 from the two loops frame/0001 names.

## Implementation log

_(lanes append dated entries as phases land: what was found, the confidence reached, surprises)_

- **2026-10-30 — Drafted (architect, `lane/plans57`).** Status `draft`; rank 5 (needs a scope ADR; after 0055·P3);
  four owner questions.
