# Playing the game on the harness

How a run actually gets the character to where the logger needs it: scripted (agent-driven) play, owner play, and
showing the game to the owner. The harness itself (launcher, gdb, `xdrive`, saves) is in
[tooling.md](tooling.md) § Runtime harness. These rules come from the owner watching runs; they are binding for every
harness phase.

## Choosing who plays

| | Scripted (agent-driven) | Owner play |
|---|---|---|
| when | the default for a plan's Phase 2; repeatable; many sessions | rare targets (superuniques, special packs, chests, quest states) that scripted hunting keeps missing |
| launch | `tools/d2run.py --steps <enter-*.steps> --after <s>` then `tools/d2pilot.py explore` | `tools/d2run.py` with **no** `--steps`, a long `--after` (e.g. 7200); `--sound` only if the owner asks |
| record | the pilot's options and the character recipe go in the run record | say "owner-played" in the run record |

An owner session of ten minutes once covered more superuniques, upgrades and chests than an hour of scripted
hunting; ask for one when coverage stalls, don't grind.

## The character

- Build test characters from a recipe in `tools/d2s_recipes/` with `python3 -I tools/d2s.py build <excel-dir> <recipe.json> <in.d2s> <out.d2s>`. Never edit saves by hand.
  Swap them in and out **only** with `python3 -I tools/saves.py [--slot N] aside <tag>` / `install <tag> <out.d2s>…` /
  `restore <tag>`, which checks the `seedtest` files against their manifest. `restore` at the end of every run, on the
  slot the tag was set aside from (each slot has its own asides; see § Slots).
- Scripted play uses a **Sorceress with Teleport and Nova**: `specnova.json` (expansion), `specclassic.json`
  (classic). Teleport is the left skill, cast with Shift held; Nova the right skill.
- **Check a classic character really is classic** before a classic session: the `.d2s` status byte must have bit
  `0x20` (expansion) clear, and the waypoint menu shows four act tabs, not five. One run labelled a session classic
  from an expansion-status save; build classic characters from the recipe on the classic base save.
- Her belt has **one column of mana potions only**; the pilot drinks from it when the mana orb runs low, as it drinks
  life potions when the life orb runs low. Warmth, enough Energy and mana gear keep casting going.
- For Hell (and `/players 8`), raise damage with the build, stock affixes and ranges only: Nova and Lightning Mastery
  maxed, +skills gear (all skills, sorceress or lightning skills), faster cast rate. If kills stay too slow, lower
  `/players` for the kill and record it; the player count is an input the TC model handles.
- Give her Energy Shield for Hell (`d2pilot.py --es N` casts it every N seconds) and a belt of
  rejuvenation potions. Select skills with **skill hotkeys** (F-keys), never by toggling the weapon set: a toggle the game drops leaves the
  character on the wrong set, and every "Nova" after it casts Energy Shield. Press the Nova key before each Nova burst
  and the Energy Shield key only around its cast, so a dropped key heals itself at the next burst. Two Hell deaths in run:2026-10-14-mon-special came from a build without it.
- Melee with a low-level character fails in Nightmare and Hell (to-hit, stun-lock). If a run must melee, use a
  clvl 70 save with War Cry on the right button.
- Record which recipe (and which revision of it) each session used.
- **Every recipe needs `"game"`** (`"classic"` or `"expansion"`): `d2s.py build` refuses a recipe without it, and one
  whose game does not match the base save's status byte (bit `0x20`). Build classic recipes on a classic base save.
- **Reinstall before every launch.** The game rewrites the installed `.d2s` when a session ends, so a loop of games
  passes `tools/d2run.py --install TAG FILE.d2s…` on each launch (TAG set aside on that slot first). `--install`
  copies over a save of the same name but does not empty the directory: with several characters there, the character
  screen preselects one by its own order, not the one just installed. To keep one character per session, run
  `saves.py --slot N restore TAG` then `saves.py --slot N aside TAG` before each `--install` (plan 0029 Phase 2 did).
- Test-state keys of `d2s.py build` (`"identified": false`, `"quality"` on a plain code) build states the game's own
  builders do not make; a run that uses one says so in its record, as a built (forced) state.

## Scripted play rules

**Kill with Nova.** Nova needs no aiming: stand near the pack and cast. Do not use Fire Wall, Blizzard or anything
placed on a target cell; scripted aiming misses and wastes the session. Cast Nova back to back at the
character's cast rate (about 0.3–0.4 s per cast without faster cast rate; give the recipe FCR gear), with no log
polling or screenshots between casts; check the target's state from the log every few casts.

**Skip what Nova can't kill.** Nova is lightning. Before engaging, compute the target's lightning resistance for the
current difficulty: MonStats `ResLi` / `ResLi(N)` / `ResLi(H)` plus whatever its special mods add (lightning
enchanted and the other mods in the handler table of
[monsters/0003](../../../../docs/findings/monsters/0003-special-monsters.md)). At 100 or more the pack is immune:
teleport past it to the next one. As a fallback, abandon a target after a few casts that leave its life unchanged.
A run that needs lightning-immune monsters killed needs a second build (another element) and says so in its plan.

**Teleport only to standable cells.** Every hop targets a cell whose collision value at activation has none of the
player's blocking bits (`0x1C09`, [drlg/0005](../../../../docs/findings/drlg/0005-collision.md)) in a 3×3 square
around it, reached by a path over such cells. Never hop to a wall, water, a cliff edge or void, and never make
near-zero hops (a hop of a cell or two wastes a cast and looks stuck). `tools/d2pilot.py` does this from the live
log; its default hop is 10 sub-tiles.

**Head for unactivated rooms.** The population pass runs when a room activates, so exploration aims at the nearest
DRLG room of the current level that has not activated yet (`d2pilot.py explore`). `--to-pdef DEF` goes to a preset
room (a superunique's lair, a quest room) and stops.

**Stay alive.** The pilot samples the life orb after every hop and drinks a belt potion below `--drink` (a poisoned
orb is green and still counts as life). A death ends the session: note it in the run record and start a new
session rather than continuing a corpse run.

**Check the screen.** Take a screenshot every `--shot-every` hops (`--shots DIR`, under `workspace/logs/`) and look
at it when the log goes quiet: a stuck pilot, a dialog, or a closed game all look like silence.

**Keep menu steps fast.** The waypoint and portal menus open within a frame or two: wait about 0.3–0.5 s between
clicking the waypoint and choosing the destination, not seconds. Long fixed sleeps only slow the session down.

**Watch for stalls.** If neither the log nor the player's position changes for about 20 s, take a screenshot, log
what the pilot was waiting for, and recover: re-click the window, retry the hop, or end the session cleanly. Usual
causes: gdb stopped at a breakpoint or a pager prompt, a slow Python breakpoint handler, the pilot waiting for a log
line that never comes, or the game window losing focus. Never let a session sit idle without a reason in the log. The commonest "stall" is no stall at all: the game
is healthy but nothing drives it while the agent edits code between hops. Don't leave a live session idle; end it
(`python3 -I tools/slots.py stop N`) before a long edit and relaunch after. The other cause seen so far: a driver command that finished its work in seconds
but kept the agent's tool call open for minutes, because a child it started inherited the call's stdout. Start
long-lived helpers detached (`setsid … > log 2>&1 < /dev/null &`, or `start_new_session=True` with redirected
streams), and expect every hop or waypoint command to return within seconds.

**Never use *Save and Exit*** unless the run needs a written save (`d2s-io` runs), and ask the owner not to use it
during owner play. The harness ends a session by killing the game; the installed save stays as built.

## Hunting item drops

For runs that need many unique and set drops (owner guidance, 2026-10-14):

- **Raise magic find first.** Fill the expansion character's inventory with MF charms and wear MF gear, all built
  from recipe items (`tools/d2s.py build`) with stock affixes and ranges. Classic has no charms: use classic MF rings,
  amulets and armour. MF is an input of the quality roll that [items/quality](../../../../docs/specs/items/quality.md)
  models, so it doesn't weaken a reproduction; log the MF value the game uses and record each recipe's total.
- **Farm a fixed superunique.** In Act V, take the second waypoint (Frigid Highlands) and go up from it: Eldritch the
  Rectifier and his pack stand there in every expansion game. Waypoint, a few teleports, Nova, loot, relaunch with
  the next seed. Shenk (Bloody Foothills) is close by. Check lightning immunity for the difficulty first. Don't farm Mephisto: the
  Durance route proved too long and fragile for scripted play.
- **Player count.** Superunique treasure classes (Eldritch and Shenk: `Act 5 (H) Super A`) already have NoDrop 0, so a
  higher `/players` adds no drops there but multiplies monster life by (n+1)/2. Farm them at the lowest count and
  record it. A higher count helps only where NoDrop is non-zero (regular monsters, act bosses).
- **Build notes.** Nova's cast frames drop at 37, 63 and 105 % faster cast rate; aim for at least 63. Spirit and Insight
  are ladder-only in single-player 1.14d, so recipes can't use them. MF beyond about 450–500 adds little to unique
  odds (diminishing returns); more drops matter more than more MF.

## The pilot

```bash
python3 -I tools/d2run.py --seed N --gdb tools/gdb/mon-special.gdb --steps tools/gdb/enter-hell.steps \
    --after 7200 --log workspace/logs/<run>-sK-N-hell.log            # background
python3 -I tools/d2pilot.py where   workspace/logs/<run>-sK-N-hell.log
python3 -I tools/d2pilot.py explore workspace/logs/<run>-sK-N-hell.log --hops 200 --nova 2 --es 30 \
    --shots workspace/logs/<run>-sK
python3 -I tools/d2pilot.py hop     workspace/logs/<run>-sK-N-hell.log <dx> <dy>   # one manual hop
```

For item hunting at a fixed target, `farm` runs one short session: waypoint travel, Energy Shield, then hops
towards the bosses it sees (every hop strictly nearer its target, none while something Nova can hurt is in range)
and Nova bursts until they are down or `--time` runs out:

```bash
python3 -I tools/d2pilot.py farm workspace/logs/<run>.log --wp 5,2 --players 1 --time 90 \
    --nova-key F1 --es-key F2 --es 20 --mana-col 4 --mana-drink 0.3
```

| option | default | meaning |
|---|---|---|
| `--wp TAB,ROW` | | waypoint act tab and row; `--wp-tab-x0/--wp-tab-w` 115/62 (the classic 4-tab menu needs 120/78) |
| `--players N` | | typed by the pilot once the game takes keys (a steps file can type it too early) |
| `--time S` / `--sweep` | 90 / off | session length; after the bosses, keep exploring for more kills |
| `--linger S`, `--chase N`, `--min-hop N` | 2, 8, 5 | stay after a kill; chase radius; shortest hop |
| `--max-res R` | 75 | do not chase a target whose lightning resist is R or more |
| `--nova-hold S` | 1.6 | right button held per burst; the game recasts at its own cast rate |
| `--nova-key`, `--es-key` | | skill hotkeys pressed before each Nova burst / around each Energy Shield |
| `--mana-col C`, `--mana-drink F` | 4, 0.3 | belt column of mana potions; drink below this mana fill |
| `--boss-cls`, `--descend REC` | | restrict the boss classes; take a warp first |

The reference build is the recipe `tools/d2s_recipes/uniqnova.json` (MF 472, FCR 115, hotkeys F1 Nova, F2 Energy
Shield, belt `rvl rvl rvl mp5`); classic uses `uniqclassic.json` (MF 250).

The pilot needs the lines that `tools/gdb/mon-special.gdb` writes (`PLR` position, `RL` rooms, `RRESEED`
activation, `CB` collision grids). A logger written for another plan must include them, or load that file too. The
pilot only decides where to click: nothing it computes feeds a model.

## Slots

Several game copies can run at once, one per **slot** (`tools/slots.py`). Slot 0 is display `:7` with
`workspace/wineprefix` (the historical harness, the default of every tool); slot N ≥ 1 is display `:(7+N)` with
`workspace/wineprefix-N`. `d2run.py`, `d2pilot.py`, `xdrive.py`, `d2hunt.py` and `saves.py` take `--slot N`, which
sets display and prefix together; a `--display` or `--prefix` that contradicts it is refused.

- **Assignment.** A lane is given its slot(s) in its prompt and never touches any other slot: no launch, no
  `xdrive`, no `saves.py`, no `wineserver -k`, no `slots.py stop` on a slot it was not given. Without a slot in the
  prompt, ask; do not take slot 0 because it is the default.
- **One session per slot.** A slot holds one harness session at a time; sessions on different slots run side by side.
- **Make a slot** once: `python3 -I tools/slots.py create N` (a reflink clone of the base prefix with an empty saves
  directory, safe while slot 0 runs). Install its characters with `saves.py --slot N`: `aside <tag>` on the empty
  directory records an empty aside, and `restore <tag>` returns the slot to empty (slot 0 still refuses an empty `aside`).
- **See** what runs where: `python3 -I tools/slots.py status` (display, prefix, game and gdb, driver, saves and asides
  per slot).
- **Budget.** About 3–4 slots at once on this machine (16 cores, ~16 GB free): each copy is one wine session, a game
  process and, when attached, gdb with its logger. Fewer when the loggers are heavy or Ghidra is running.
- Every slot starts `game.exe` in the shared `workspace/runtime/game` (the prefix holds no game files); copies running
  side by side there were first proven by plan 0011's two clients.
- `workspace/wineprefix2` is plan 0011's joiner prefix (ADR-0008). It is not a slot; it used `:8`, which is now slot
  1's display, so a new two-client run uses slot 1 for the joiner instead.

## Showing the game to the owner

The owner often watches runs. Each slot's Xwayland (`:7` for slot 0, `:(7+N)` for slot N) lives on Hyprland's hidden
special workspace `d2harness`, which does not stay visible to them. To show a slot, move **only that slot's**
`Xwayland on :D` window to a free regular workspace (8 by default) and follow it; every other slot stays hidden:

```bash
D=:7   # the display of the slot being shown
hyprctl clients -j | python3 -I -c 'import json,sys; [print(c["address"]) for c in json.load(sys.stdin) if c["title"] == "Xwayland on '$D'"]'
hyprctl dispatch 'hl.dsp.window.move({ workspace = "8", follow = true, window = "address:0x…" })'
```

Every harness relaunch restarts that Xwayland on the special workspace, so repeat the move with the new address after
each relaunch while the owner is watching. For owner play, also offer `tools/d2hunt.py record` (pointer and
screenshots) so the session can be replayed in the record.

## Cleanup

Per slot, and only on your own slot(s). After the last session: `python3 -I tools/slots.py stop N` (kills the slot's
driver from its pidfile, so no old timer fires `wineserver -k` into a later run, then `wineserver -k` on the slot's
prefix only), `python3 -I tools/saves.py --slot N restore <tag>` and `saves.py --slot N status` (no aside left,
harness idle), then `slots.py status` to see the slot empty. Never `pkill -f` a pattern: with several slots it kills
other lanes' sessions. One session per slot at a time.

**Stopping your own loop script.** Not `pkill -f` either, not even with your own script's path: the pattern also
matches the shell running the `pkill` and every other process whose command line holds it (two lanes killed their own
shell this way). Have the loop write its PID at start (`echo $$ > <scratch>/loop.pid`, or `os.getpid()` in Python),
then `kill $(cat <scratch>/loop.pid)` and `slots.py stop N`. To find a stray process, `pgrep -a` with a bracketed
pattern (`pgrep -af '[f]arm2.py'`) and kill by the PID it prints, after checking it is yours.
