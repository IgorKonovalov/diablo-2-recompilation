# ADR-0026 — The in-game message layer enters scope; the transport and everything outside a game stay out

> **Status:** accepted (owner, 2026-10-30, with the approval of plan 0061 "as recommended")
> **Date:** 2026-10-30
> **Amends:** [ADR-0002](0002-scope-creation-paths-and-enablers.md) and [ADR-0014](0014-scope-game-simulation.md) (both list "the network protocol" as out of scope); consistent with [ADR-0022](0022-scope-server-frame.md) (message arrival stays out)
> **Related plan(s):** [0061-message-catalogue](../plans/0061-message-catalogue.md)

## Context

ADR-0002 and ADR-0014 put "the network protocol" out of scope as a whole, and ADR-0022 keeps the wall-clock arrival of
client messages out of the frame phase. The specs have nonetheless grown entry points that are client messages: the
skill request (skills/dispatch), the cube button `0x4F` and socket insertion `0x28` (items/0008), the move request
(plan 0054), and plan 0055's drain, which reads the two queues before `GameTick`. The dispatch
`sub_0054D750_SrvPacketDispatch` and its table `g_SrvPacketTable` (`0x006E0D18`, 8-byte {handler, flag} entries,
opcodes 1..0x66) are `[C]` by H6a; the send side (`ClientQueuePacket` `0x0053B280`, `ClientFlushPackets` `0x0052E320`,
several builders) is named at `[I]` in `re/symbols.csv`.

For a reimplementer the client-to-server table is the server's whole input space, and the server-to-client side is
what a compatible client or a replay tool must decode. Neither needs the layers below a message: how bytes cross the
wire, the compression, the encryption, or the Battle.net, realm and pre-game handshake traffic, which carry no game
rule. Plan 0061's question 1 asks for this ADR.

## Decision

The **in-game message layer** enters scope: every message a game client sends the server and the server sends a
client once the game is joined, each with its opcode, length rule, fields and their widths, its validation and
refusals, and its handler (client to server) or its send sites and the condition that sends it (server to client),
linked to the spec section that owns its effect. **Both directions** are in, **client to server first** (it is the
server's input and touches the reviewed specs), server to client after. Out of scope stay the transport (sockets,
framing below a message, timing of delivery), compression, encryption, Battle.net and realm traffic, and the pre-game
and join handshake beyond the game's own messages; message arrival order stays out as ADR-0022 says, each received
message being a logged input. Runtime evidence is **gdb capture** under ADR-0003 (breakpoints on the dispatch and the
queue functions in a short session); **no injected logger** is introduced, since the injected-logger triggers
(plan 0055 question 2, under ADR-0022) are not met by this work. The research-map row is `net/messages` under Simulation (plan 0061), whose static phase starts after
plan 0055's spec (0055·P3).

## Consequences

### Positive

- Every request handler becomes a named entry point into an existing spec, and opcodes with no owning spec become a
  listed gap instead of an invisible one.
- A replay tool or compatible client can be written from the spec, and `tools/netmsg.py` decodes the harness's own
  captures, which helps every later harness phase.
- The layer is small and mostly static: one table of 0x66 entries and the callers of a few queue functions.

### Negative

- **Scope grows again**, and part of it (the server-to-client side) serves a client, not the server the specs
  describe; the three priority areas gain nothing directly.
- **Large surface for one row.** About 100 client and 150–180 server opcodes; some server messages may be built only by
  the local-server path (game modes 0 and 1), and plan 0061 must say which.
- **gdb capture may perturb timing** (ADR-0003 § Negative). Sessions are short and claims are layouts and conditions,
  not timing, so this matters little; if a capture cannot be logged whole, the layouts it misses stay `[I]`.
- **Community message lists are plentiful** and must be treated as leads under ADR-0001 and ADR-0007, compared field
  by field with a verdict each; agreement alone raises nothing.

### Neutral

- Evidence rules and tags are unchanged; ADR-0022's frame phase keeps the drain's place and order, and this layer adds
  only what a message contains and who builds or handles it.
- ADR-0008's two-client harness is the capture setting when both slots are free; nothing in it changes.

## Alternatives considered

**Keep the whole protocol out.** The handlers would stay named one by one as each spec meets them. It lost because the
gap is the list itself: a reimplementer cannot know which server inputs exist, and several reviewed specs already
depend on handlers no spec catalogues.

**Bring in the full protocol, transport and handshake included.** It would allow a networked reimplementation to talk
to a stock client, but the transport, compression, encryption and Battle.net layers carry no game rule, are large, and
are the part community documentation and other tools already cover; it lost on cost for no gain to the deliverable.

**An injected logger for capture.** It would log every message without breakpoint overhead, but the logger ADR is reserved
for plan 0055's question-2 triggers (ADR-0022), none of which this plan meets; gdb on two functions suffices for short sessions.
