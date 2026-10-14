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
  Swap them in and out **only** with `python3 -I tools/saves.py aside <tag>` / `install <tag> <out.d2s>…` /
  `restore <tag>`, which checks the `seedtest` files against their manifest. `restore` at the end of every run.
- Scripted play uses a **Sorceress with Teleport and Nova**: `specnova.json` (expansion), `specclassic.json`
  (classic). Teleport is the left skill, cast with Shift held; Nova the right skill.
- Her belt has **one column of mana potions only**; the pilot drinks from it when the mana orb runs low, as it drinks
  life potions when the life orb runs low. Warmth, enough Energy and mana gear keep casting going.
- For Hell (and `/players 8`), raise damage with the build, stock affixes and ranges only: Nova and Lightning Mastery
  maxed, +skills gear (all skills, sorceress or lightning skills), faster cast rate. If kills stay too slow, lower
  `/players` for the kill and record it; the player count is an input the TC model handles.
- Give her Energy Shield for Hell (`d2pilot.py --es N` casts it every N seconds, on the swap set's right button by default) and a belt of
  rejuvenation potions. Two Hell deaths in run:2026-10-14-mon-special came from a build without it.
- Melee with a low-level character fails in Nightmare and Hell (to-hit, stun-lock). If a run must melee, use a
  clvl 70 save with War Cry on the right button.
- Record which recipe (and which revision of it) each session used.

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
(`wineserver -k`) before a long edit and relaunch after. The other cause seen so far: a driver command that finished its work in seconds
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

The pilot needs the lines that `tools/gdb/mon-special.gdb` writes (`PLR` position, `RL` rooms, `RRESEED`
activation, `CB` collision grids). A logger written for another plan must include them, or load that file too. The
pilot only decides where to click: nothing it computes feeds a model.

## Showing the game to the owner

The owner often watches runs. Xwayland `:7` lives on Hyprland's hidden special workspace `d2harness`, which does not
stay visible to them. To show it, move the `Xwayland on :7` window to a free regular workspace (8 by default) and
follow it:

```bash
hyprctl clients -j | python3 -I -c 'import json,sys; [print(c["address"]) for c in json.load(sys.stdin) if ":7" in c["title"]]'
hyprctl dispatch 'hl.dsp.window.move({ workspace = "8", follow = true, window = "address:0x…" })'
```

Every harness relaunch restarts Xwayland `:7` on the special workspace, so repeat the move with the new address after
each relaunch while the owner is watching. For owner play, also offer `tools/d2hunt.py record` (pointer and
screenshots) so the session can be replayed in the record.

## Cleanup

After the last session: `pkill -f tools/d2run.py` (old driver timers fire `wineserver -k` into a later run),
`WINEPREFIX=$PWD/workspace/wineprefix wineserver -k`, `python3 -I tools/saves.py restore <tag>` and
`saves.py status` (no aside left, harness idle). Only one session may hold `:7` at a time.
