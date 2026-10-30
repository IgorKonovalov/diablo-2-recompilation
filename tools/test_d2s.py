"""Self-test for tools/d2s.py build and tools/excel_edit.py: python3 -I tools/test_d2s.py
(or python3 -I -m unittest discover -s tools -p test_d2s.py).

LayoutTest checks the builder's overlap refusal (d2s.check_layout) on hand-made item lists and needs no game
data. The other tests need workspace/ (the merged excel directory and the base saves) and skip without it;
every output goes to a scratch directory, nothing in workspace/ is written:
- RecipeTest builds every recipe in tools/d2s_recipes/ on its base save and reads it back. Where a run record
  gives the built save's sha256, the build must reproduce it byte for byte.
- KeysTest covers the recipe keys added in plan 0019 Phase 2 (suffix, belt_fill as four columns, hotkeys)
  and the overlap refusal through build and through the command line.
- GameTest (plan 0027 Phase 1) covers the required "game" key: a classic recipe on an expansion base, or the
  reverse, or no key, is refused with nothing written; and a Tome of Town Portal (tbk) in the cube builds, reads
  back and round-trips byte for byte.
- SocketTest (plan 0029 Phase 0) covers "sockets" and "filled": a socketed parent and its socketed items read back
  in order (flags bit 11, socket count, n_filled, location 6, socket index) and round-trip byte for byte; the
  refusals (too many sockets for the base, more filled items than sockets, a filler that is no gem, rune or jewel);
  an equipped socketed weapon moves to the end of the list with its socketed items; and keep_items keeps a socketed
  item (the qitbarb runeword sword) with its runes, byte for byte. Plan 0030 Phase 0: the quality clamp (magic 4,
  rare 2 sockets, items/0007) refuses unless "unclamped_sockets" is true, and rare items ("rare": [name1, name2]).
- ClassicTest (plan 0034 Phase 0) covers `d2s.py classic`: the expansion save the classic base was made from
  converts to that base byte for byte once its progression byte is set as it was then (8); a save that is
  already classic is refused; and tools/levelup_saves.py builds its saves (level and experience as asked) twice
  with the same bytes.
- QuestBitsTest (plan 0032 Phase 0) covers "quest_bits": exactly the asked bits change against the base (set,
  and clear of bits that "quests" set), the refusals (word, bit, a bit both set and cleared, a difficulty), and the
  simple quest item's required "quest_diff" (stat 356). Plan 0042 Phase 0: tools/quest_saves.py check passes on
  its 33 recipes (14 of Phase 0, 3 of Phase 1 (c), 16 of Phase 2: plan 0049 Phase 0) and build writes the
  whole set. Plan 0044 Phase 2:
  tools/mp_saves.py check passes on its 30 recipes and 21 pairs and build writes the whole set.
- MercTest (plan 0033 Phase 0) covers the "merc" key: the header fields 0xAF..0xBE, the mercenary item list after
  'jf' (equipped, hand item last) read back and round-trip byte for byte, the dead flag (bit 16), and the refusals
  (no row of the save's Version, seed 0, a name id past NameLast, items in a classic save, an item not placed with
  "equip").
- ExtendedTest (backlog 2026-10-27, the plan 0038 H1a gaps) covers the extension keys and the extended reader:
  build reproduces tools/h1a_saves.py's v94, v94s12 and skills29 cases byte for byte; the default parser still
  refuses them and realm data; realm words per version (three above 93); an ear's realm bit; the 8-bit stat 72 at
  <= 95; the old stat form at <= 94; the refusals (92, < 92, 97, stat_slots, a stat past the slots, a cut-off skill).
- LegacyTest (backlog 2026-10-27, the d2s legacy layouts) builds save_version 87 and 71 (the legacy layout of
  save/0001 § Plan 0038 lane/rlg, read back with d2s.parse_legacy: section tags and lengths, the header's skill
  bytes, the 0x12-byte and version-71 mercenaries, the hotkey tail, the 25-byte and code-form records, the corpse
  list) and 92 (the 1.09 widths, the <= 92 per-id encodings, the Sets id), and the refusals. The game has loaded
  none of these files: the tests check the builder against d2s.md, not d2s.md against the game.
- ExcelEditTest edits integer and text cells through excel_edit.py and checks that nothing else changed.
"""
import contextlib
import hashlib
import io
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import warnings

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import d2s  # noqa: E402
import excel_edit  # noqa: E402

REPO = os.path.dirname(HERE)
WS = os.path.join(REPO, "workspace")
EXCEL = os.path.join(WS, "merged", "data", "global", "excel")
BASE_X = os.path.join(WS, "samples", "d2s-owner", "smpsor-l50.d2s")       # expansion Sorceress
BASE_C = os.path.join(WS, "runtime", "monspawn-chars", "cls", "smpsor.d2s")  # classic Sorceress
BASE_N = os.path.join(WS, "samples", "d2s", "smpnec.d2s")                # expansion Necromancer
BASE_RW = os.path.join(WS, "samples", "d2s", "qitbarb.d2s")              # expansion Barbarian, runeword sword
BASE_PAL = os.path.join(WS, "samples", "d2s", "smppal.d2s")              # expansion Paladin
RECIPES = os.path.join(HERE, "d2s_recipes")
P0005 = os.path.join(WS, "runtime", "saves-backup", "p0005")              # run:2026-10-16-calc bases (smp<cls>.d2s)
SAMPLES = os.path.join(WS, "samples", "d2s")                               # run:2026-10-16-player level-up bases

# recipe -> (base save, sha256 of the built save as a run record gives it, or None)
RECIPE_BASES = {
    "leg71act2": (BASE_X, None),    # plan 0038 H1c: leg71merc with the act II header byte (run:2026-10-27-sweep-d2s-legacy)
    "leg71merc": (BASE_X, None),    # backlog 2026-10-27 legacy builder: hirelings 30, 33 (run:2026-10-27-sweep-d2s-legacy)
    "leg71sock": (BASE_X, None),    # plan 0038 H1c: a socketed item with a child at version 71 (run:2026-10-27-sweep-d2s-legacy)
    "leg71uniq": (BASE_X, None),    # backlog 2026-10-27 legacy builder: items-uniques-sets 21 (run:2026-10-27-sweep-d2s-legacy)
    "leg87merc": (BASE_X, None),    # backlog 2026-10-27 legacy builder: hirelings 3, 33 (run:2026-10-27-sweep-d2s-legacy)
    "leg87new": (BASE_X, None),     # backlog 2026-10-27 legacy builder: player-creation 1 (run:2026-10-27-sweep-d2s-legacy)
    "leg92props": (BASE_X, None),   # backlog 2026-10-27 legacy builder: save-d2s 126 (run:2026-10-27-sweep-d2s-legacy)
    "calc-ama": (os.path.join(P0005, "smpama.d2s"), "527952cb6672585f2fc465a99b763fe7dd036a4f383ed4c9fa56cfa167afc944"),  # run:2026-10-16-calc
    "calc-ama-field": (os.path.join(P0005, "smpama.d2s"), "3ae9a886bad294ca3f17b3bd4695929cd3e1f8485afe729c31d18edfa70fc15a"),  # run:2026-10-16-calc
    "calc-ass": (os.path.join(P0005, "smpasn.d2s"), "d28ac300eaeac7176c59e028caa2b735cd457349ed00c9a4d181a5ccdd89820f"),  # run:2026-10-16-calc
    "calc-ass-field": (os.path.join(P0005, "smpasn.d2s"), "4ed3eb4e710fd2b601040411fe8bc0358e04151c525065e69b1927f81293cc93"),  # run:2026-10-16-calc
    "calc-bar": (os.path.join(P0005, "smpbar.d2s"), "7323b23dcba642fe656f2e28965c6a05be7cccb79ec7b022788da5f916724fde"),  # run:2026-10-16-calc
    "calc-bar-field": (os.path.join(P0005, "smpbar.d2s"), "9b7da6b7bd55a63a70236c5c6f34a2e050bbe9257fc756be7e5470e73395e1fc"),  # run:2026-10-16-calc
    "calc-dru": (os.path.join(P0005, "smpdru.d2s"), "d6185cb4f79b6bed3f1dbfedaac3f5227a750bd38d4c887711a5f00d955dfc85"),  # run:2026-10-16-calc
    "calc-dru-field": (os.path.join(P0005, "smpdru.d2s"), "b437f8958d36892cfc6c5dab8b184600a4860104310f5004b6a0b96b151a6799"),  # run:2026-10-16-calc
    "calc-nec": (os.path.join(P0005, "smpnec.d2s"), "90cceb9798d73fca39e106fa6429069af889f3443a4cc46e312739f5f115fac6"),  # run:2026-10-16-calc
    "calc-nec-field": (os.path.join(P0005, "smpnec.d2s"), "542a53e5a4a58525b7ab409be0843375460005b0f989f9c496243a53ad21ff0a"),  # run:2026-10-16-calc
    "calc-pal": (os.path.join(P0005, "smppal.d2s"), "0591a06e6f6d82e103b4ea8b6c4a972d4c76a7943b580d268e71e5b527839345"),  # run:2026-10-16-calc
    "calc-pal-field": (os.path.join(P0005, "smppal.d2s"), "0412888bc2cf2fc3dc46ffffa2d767d58c028332988eab1151616efa4ffdbdd6"),  # run:2026-10-16-calc
    "calc-sor": (os.path.join(P0005, "smpsor.d2s"), "787a2291f0ff02cf2b6cec9796fdd2f201ca5fbb005ebfe90f45a8d93b49acf6"),  # run:2026-10-16-calc
    "calc-sor-field": (os.path.join(P0005, "smpsor.d2s"), "b26247d58c0247d91ee3c57949c0b10b3e479a603fd028640d5b0cccb4b76737"),  # run:2026-10-16-calc
    "lvbara": (os.path.join(SAMPLES, "smpbar.d2s"), None),  # run:2026-10-16-player (no built hash pinned)
    "lvbarb": (os.path.join(SAMPLES, "smpbar.d2s"), None),  # run:2026-10-16-player (no built hash pinned)
    "lvbarc": (os.path.join(SAMPLES, "smpbar.d2s"), None),  # run:2026-10-16-player (no built hash pinned)
    "lvbard": (os.path.join(SAMPLES, "smpbar.d2s"), None),  # run:2026-10-16-player (no built hash pinned)
    "lvpala": (os.path.join(SAMPLES, "smppal.d2s"), None),  # run:2026-10-16-player (no built hash pinned)
    "lvpalb": (os.path.join(SAMPLES, "smppal.d2s"), None),  # run:2026-10-16-player (no built hash pinned)
    "lvpalc": (os.path.join(SAMPLES, "smppal.d2s"), None),  # run:2026-10-16-player (no built hash pinned)
    "lvpald": (os.path.join(SAMPLES, "smppal.d2s"), None),  # run:2026-10-16-player (no built hash pinned)
    "lvsora": (os.path.join(SAMPLES, "smpsor.d2s"), None),  # run:2026-10-16-player (no built hash pinned)
    "lvsorb": (os.path.join(SAMPLES, "smpsor.d2s"), None),  # run:2026-10-16-player (no built hash pinned)
    "lvsorc": (os.path.join(SAMPLES, "smpsor.d2s"), None),  # run:2026-10-16-player (no built hash pinned)
    "lvsord": (os.path.join(SAMPLES, "smpsor.d2s"), None),  # run:2026-10-16-player (no built hash pinned)
    "classicsorc": (BASE_C, None),
    "collnova": (BASE_X, "b164aec5fd4b82a0ee2304325612dc01fe7561151e124dbfc0ae13d3f0cdf643"),  # run:2026-10-14-collision
    "collsorc": (BASE_X, None),
    "combatbar": (os.path.join(SAMPLES, "smpbar.d2s"), "107f3ac19d9a75eee61b876db367022b5cc4cef6923b74990a369c46eeb54e2b"),  # run:2026-10-16-combat
    "combatclassic": (BASE_C, "8e1625b211a99df0dc4133e2d6bb590942d9532fcaa76b141f21c50722ae061e"),  # run:2026-10-16-combat
    "combatsolo": (BASE_X, "a2a64d7284ceb74d4614205d84ce7dd15f0c8dac8326b6a8813fbe61e4ab7599"),  # run:2026-10-16-combat
    "combatsor": (BASE_X, "1d9de374cb681c1f4260066694f27b92306f919c758e46187b683d61d3dd22fe"),  # run:2026-10-16-combat
    "combatow": (BASE_X, None),     # run:2026-10-16-combat resume lane (no built hash pinned; listed by plan 0041 P2)
    "combatsorh": (BASE_X, None),   # run:2026-10-16-combat resume lane (no built hash pinned; listed by plan 0041 P2)
    "statsbar": (os.path.join(SAMPLES, "smpbar.d2s"), "93072706ffc6c6d425fc73312f08f780da14061ce5ac7583b5fcb2e62b068e6b"),    # run:2026-10-17-stats
    "statsbarb": (os.path.join(SAMPLES, "smpbar.d2s"), "7e007ad0a96f488115c980e6355b47959ae1f3d0fb8319f9398f1b4330683a3e"),   # run:2026-10-17-stats
    "statspal": (os.path.join(SAMPLES, "smppal.d2s"), "709bcc4f27b622f945b5c127ebf6e52751921856bd0d3b2fb653462c7e3cfa53"),    # run:2026-10-17-stats
    "statsbard": (os.path.join(SAMPLES, "smpbar.d2s"), "e361d5cc96e6027fe639c36dd5477d11513b3c9e3a0c287c51766bbf0f9b12cc"),   # run:2026-10-17-stats
    "statsbarc": (os.path.join(SAMPLES, "smpbar.d2s"), "de9603266e41c5e1f04ab7dfab68447125e831faf3ee42ab171870837e01ec9e"),   # run:2026-10-17-stats
    "statsnec": (os.path.join(SAMPLES, "smpnec.d2s"), "ed25c961226f575e1c4fcb34a70b7b07b2d461872e7a0bb126474bc416a384fd"),    # run:2026-10-17-stats
    "statspalb": (os.path.join(SAMPLES, "smppal.d2s"), "2e06b8a693734228984d4ef033a3ae020df822a55fa63bea80db3ac39d633a0f"),   # run:2026-10-17-stats
    "statspalc": (os.path.join(SAMPLES, "smppal.d2s"), "3c3a1fe393f23ed53eb7aaca400ee28252e81921e73fd472af46a299c836d4f2"),   # run:2026-10-17-stats
    "cube-cal": (BASE_X, "65c1b6e8cc4324f618a8f932c00df354d52d21c2296039d6beb9d44739243067"),  # run:2026-10-15-cube
    "cube-classic": (BASE_C, "d5da5eb053c22cd4522c404ac5d59ddf007c7710f2515842cbf080a81b6f4d74"),  # run:2026-10-15-cube
    "cube-cowbaal": (BASE_X, "8e644d571e68da192fa207aa69c6bb891af58727c373d51a4d2c7bb299d98f7d"),  # run:2026-10-15-cube
    "cube-cowhell": (BASE_X, "a1bcfc53f9f09207119f4110b0dc94b013f438bdbf03c9c44fe56b17f5b9accd"),  # run:2026-10-15-cube
    "cube-cowking": (BASE_X, "e424e3fc2654ac3cb82ca712f853881c02a3da14c07879b6ee4441b96354f85d"),  # run:2026-10-15-cube
    "cube-cownm": (BASE_X, "23745b9428e898d141f9e267f38594fda8a6effac6bc2f72354c5f0b677b12c0"),  # run:2026-10-15-cube
    "cube-cowopen": (BASE_X, "433fdc140f4f08173168812bc919e73ed387311e509a035d23a25c017b1c0dd7"),  # run:2026-10-15-cube
    "cube-craft1": (BASE_X, "a86b161a5244f26f793ecb66fd5e047cebf76f83525bffee5092f764140ac019"),  # run:2026-10-15-cube
    "cube-craft2": (BASE_X, "68fae1a76acef93bc36ea06e077fdcdf80d21ee18e7f88c199c356775077c77c"),  # run:2026-10-15-cube
    "cube-craft3": (BASE_X, "2bca7fe67ddc1349438a4130e79514b5f7612daa8f65055a14ba700c673bdfa1"),  # run:2026-10-15-cube
    "cube-craft4": (BASE_X, "ee32715b0fb9f9cd3988adb8a95e4c0cfaa8e9e883690dc87e1756fdd7eaac7c"),  # run:2026-10-15-cube
    "cube-craft5": (BASE_X, "317c3fbc460a0813869a81b224a748299da4930b6a8c7f20bd886981766819a7"),  # run:2026-10-15-cube
    "cube-craftgear": (BASE_X, "47584b5529fa892e3ac41d79fe241c072af6c4d8e91e0a92550f2ad0c3f447be"),  # run:2026-10-15-cube
    "cube-forced": (BASE_X, "ff91be7fc0d50bb7c9e2dbb7cbd081481d956373ccbe868a29f12e42f422361a"),  # run:2026-10-15-cube
    "cube-h6a-cowa4": (BASE_X, "2a10c928773b8614f42e82696a3adf7154af83496e88b9c5b3f2db6e397c664b"),  # run:2026-10-27-sweep-cube
    "cube-h6a-cowcl0": (BASE_C, "d1ad2732eb2d9870153122f7b29d81a137340d6dd05b166c67080b001812aafa"),  # run:2026-10-27-sweep-cube
    "cube-h6a-cowcl1": (BASE_C, "3839e7ba4b4da7d0938c4e9c9a7daf9c7d79a503fa63e151dfe125ad32bee3f6"),  # run:2026-10-27-sweep-cube
    "cube-h6a-craftlow": (BASE_X, "aae80fc0b6b5c62a01a9263ac6a3934cc4932ec7826e3695c2af7bd5b6d88fe3"),  # run:2026-10-27-sweep-cube
    "cube-h6a-quest": (BASE_X, "5cf60735f06e95a519b14e277aa21e983ec71e055268935149bd67095625eefe"),  # run:2026-10-27-sweep-cube
    "cube-h6a-repair": (BASE_X, "39fa3e939ed72342ed6436d53023c0af3f0ea3f3a6a0c54e39b7d83273753903"),  # run:2026-10-27-sweep-cube
    "cube-h6a-upgc": (BASE_X, "3d642dc9d30f5a09fa0018bfcec1b6b05185cb7423f8f55105ba7d4d0c022852"),  # run:2026-10-27-sweep-cube
    "cube-h6a-upgu": (BASE_X, "52bfa7721ae14058a0fbcac253ef19b343c1a07d01540e5367ca94fd44a752ba"),  # run:2026-10-27-sweep-cube
    "cube-kinds1": (BASE_X, "0051a31bad0faa0cd8790ffd9b2ed4c77f401969ba3743ae847946ebd8e6d980"),  # run:2026-10-15-cube
    "cube-kinds2": (BASE_X, "9318cf69b85b8d10d93db03729566dadbd45ecd8ace1b12854c58452d65c6663"),  # run:2026-10-15-cube
    "cube-nomatch": (BASE_X, "96ed5e8b3d91286dd96c1ae8255c12c52820136c8f7757bdc0baa7fc365038d2"),  # run:2026-10-15-cube
    "cube-rare1": (BASE_X, "3e04f66f63aa566392fe7abb09eb1e805c27d5965e34e1988e5acc7c1b84d09f"),  # run:2026-10-15-cube
    "cube-rare2": (BASE_X, "2f7af278376ccd6eabeaeb2d8e58b61d7c3399655bf81e364adffcede8fe587e"),  # run:2026-10-15-cube
    "cube-reroll1": (BASE_X, "250b5c60f1d036d8a6e1ee5e33c92d00365e679b4b6d27d535cbc8f8184d186b"),  # run:2026-10-15-cube
    "cube-reroll2": (BASE_X, "73d4772832fd9e01b623bf1863a9bad154186239c51ae7434834941a4216c00a"),  # run:2026-10-15-cube
    "cube-reroll3": (BASE_X, "2584b04c8add1fdb2c46b2b089597f0ff2391e1cd8f5410e1a20ac40500ed29a"),  # run:2026-10-15-cube
    "cube-sock1": (BASE_X, "e03803fd8bc45c7fa53b782f3e5a28cd8ab43ce8757461b761a9d84bd5b398f4"),  # run:2026-10-15-cube
    "cube-sock2": (BASE_X, "153d91e0e7d1d0f9a9cf7a0c9b76a1a82a16e6707df7bf5945e56091d2e4000f"),  # run:2026-10-15-cube
    "cube-sock3": (BASE_X, "4edba9dccbb3d832b48ba7a69fd4ec583b95ddb7b3b8027232b3d718f2f8df31"),  # run:2026-10-15-cube
    "cube-sock4": (BASE_X, "74be71439194bc7484d2caf2c5bbfa23e4c8030cb17544016034421724077b1f"),  # run:2026-10-15-cube
    "cube-sock5": (BASE_X, "bbac273de85b0060acd33e498a19c7544166275bab5fcc90f6b76c59dcbaecd0"),  # run:2026-10-15-cube
    "cube-upg1": (BASE_X, "9ea9b8e2e5c1f8e0ab6d4c8335d11d962b3abbdd81d859361e069f8fdcee1105"),  # run:2026-10-15-cube
    "cube-upg2": (BASE_X, "00a42c9ae96bf2e2908fe6bbcc057f4f77d18d671344ef51ac6b2043741d593a"),  # run:2026-10-15-cube
    "cubeclassic": (BASE_C, "a87fba7a84b3f76e88b79768fc0f8c69451cde8605b3be7d5bd4a08bf0b06093"),  # run:2026-10-15-cube-saves
    "cubecraft": (BASE_X, "6b4c6eb6b0194c075813974fb728a77dd07e9204cdcecd5900b4db7eeed025e6"),  # run:2026-10-15-cube-saves
    "cubeportal": (BASE_X, "3b8a86449deaca038dfb3898232e97994e94c5c1ab4bedea7a4055b9903732a2"),  # run:2026-10-15-cube-saves
    "cubereroll": (BASE_X, "1a1ec8918f4860bb026b3346b7ad5143026eb6303b8505ae2f4d79d03021a17d"),  # run:2026-10-15-cube-saves
    "cuberunes": (BASE_X, "416cb60e442bf2e13bfeaeace0f322206d4344e2a35f0094b175340693261b7c"),  # run:2026-10-15-cube-saves
    "cubesock": (BASE_X, "fc5674f780e62ac90791636433212c4cbbc39348a963c42aaac367da1ef3d52d"),  # run:2026-10-15-cube-saves
    "h2afind": (os.path.join(SAMPLES, "smpbar.d2s"), "38f0fc5792475a073a9da3838c5dd6864c687f4b5484f6d2cfc2cfbf14f426db"),  # run:2026-10-20-sweep-items-tc (H2a FindBar)
    "h2bjewel": (os.path.join(SAMPLES, "smpsor.d2s"), "03afa56fce9073fb98d7581dbc025decaad2c4ea18dcf93bcdd8aee19b05fcab"),  # run:2026-10-20-sweep-items-chain (H2b)
    "h2bthrow": (BASE_C, "b965d6b9e65ab8d7e5444515a81074a3bf48953da7bd2295cd8ecc198d536987"),  # run:2026-10-20-sweep-items-chain (H2b)
    "keynova": (BASE_X, "88ebd25f6db285ef3d863377e4cf4fe9a0554664d448cb6b53f762585e46d635"),  # run:2026-10-15-drlg-outdoor
    "cownova": (BASE_X, "8c66964bb82a2cc5757bac9b154756571af953ca960d5847ecc77c99389efbc8"),  # plan 0027 Phase 3 (level 39)
    "lightsorc": (BASE_X, None),
    "mercclassic": (BASE_C, "69381d3af176f354313cd3ea44fc0d5c6cf3d93fc2a3860794da2c45020d63f8"),  # run:2026-10-16-hirelings
    "mercnova": (BASE_X, "1a80a8335239deaa0199dea7816a84155f152f64b24368d5bdc76df633093140"),  # run:2026-10-16-hirelings
    "mercmf": (BASE_X, "e98a6b9d06bf310fd1f95e312d3cd28f06ff417f007f3da4f02e2995e038b6cc"),  # run:2026-10-16-hirelings
    "mfnecro": (BASE_N, "da6ee2f5639793bcf8d355de0d853b815a633bfd2165e9b754f8d2d1ef922a56"),  # items/experiments
    "novasorc": (BASE_X, None),
    "questb6": (BASE_X, "c28e894cc7558528275815cf4a93a876a7a6c36879f6876309f640fbf0309b23"),  # run:2026-10-16-quest-drops
    "questcows": (BASE_X, "6700b4e3d5c75957923263841014493d56388b226996fd877c555ed1e1b47ca0"),  # run:2026-10-16-quest-drops
    "questfresh": (BASE_X, "9a12da6e0ea1524c6e001c8ef96a7791f4689b0a0b81982b4f0b086d6ce5f095"),  # run:2026-10-16-quest-drops
    "questfreshv": (BASE_X, "0a495ee73799c6ee5b84204df98d66945369d39b71859b5c64dcc33ed5560b93"),  # run:2026-10-16-quest-drops
    "questfreshvh": (BASE_X, "a3ef1b2071132257d0e17a5bfa82fdbd45b5c46c15f9b75ae676e05db2db150f"),  # run:2026-10-16-quest-drops
    "questdurielk": (BASE_X, "fc022ab59d845674b919c8d0220e89f27d42c0ad43af371edd627aeeb5dc0200"),  # run:2026-10-16-quest-drops
    # questrewards/questrewardsh: hammer equipped (and 356 = 2 on the H hammer) after run:2026-10-16-quest-drops;
    # the earlier loaded revisions (7dfe9bc2..., 4e7b9134...) are the recipes at 32a1a6e. These builds were loaded and
    # saved in run:2026-10-27-sweep-d2s-play (plan 0038 H1b, sessions qr and qrh).
    "questrewards": (BASE_X, "246515c51710408563eb63aa8a5f7ff4543cbea846a792d300733a2e3fb99f16"),  # run:2026-10-27-sweep-d2s-play
    "questrewardsh": (BASE_X, "14c285261e43751c5fc94d54d08b5baad753185fb3cc3f8c5d27cd0b72c9e95e"),  # run:2026-10-27-sweep-d2s-play
    "h1bsor": (BASE_X, "116d0f90d80a06104e5e42368875aad6cf7238e680caf0161016165c18dc2f00"),  # run:2026-10-27-sweep-d2s-play
    "h1bdead": (BASE_X, "9ff431ea8d3f9b1846fe7c8bbfdab42eea1b459f2b30b861f81b61dfd100bc45"),  # run:2026-10-27-sweep-d2s-play
    "h1bweak": (BASE_X, "3acba754d2c2a5d26b5a9b6d86b41c127800375a3dbc83cb3224000fa077ba31"),  # run:2026-10-27-sweep-d2s-play
    "h1bhire": (BASE_X, "a1313dd0c53dbf571e2e4c65fc7442e7ca5ec4b8448023676d001e2eaf748b5e"),  # run:2026-10-27-sweep-d2s-play
    "sock-cases1": (BASE_X, "ff6866163d45c8223c5d357fbf781d31caf0378a1bb248dd3bb1829a2b2596cd"),  # run:2026-10-15-sockets
    "sock-cases2": (BASE_X, "b1a24d0b73566cf2c55644cbacf244bb15efd98c99786d8939c90dc54f9da925"),  # run:2026-10-15-sockets
    "sock-classic1": (BASE_C, "92c1c91c91212a7dfd90fc0164641bff1980b8a19594a9043b12ec80929ec021"),  # run:2026-10-15-sockets
    "sock-classic2": (BASE_C, "9826e6fdb01b43120c5461a0afae06533c806c890f55c51551310dc11b96bfd0"),  # run:2026-10-15-sockets
    "sock-cubenef": (BASE_X, "03208dab12b55562f7a6d07152c2ff9cb0d52e587e4f0ef45ced2dda3bfd8909"),  # run:2026-10-15-sockets
    "sock-forced": (BASE_X, "e521a91536ecc721902c8eeae535cfda3240ec69ec43b160c6bc00d75c76a0cd"),  # run:2026-10-15-sockets
    "sock-gems1": (BASE_X, "8540bd5fdf9d010992f4400a1348a393b1402c19a4210f9745f95a1b7c6d2318"),  # run:2026-10-15-sockets
    "sock-gems2": (BASE_X, "2acb246af1ffdca8e10b432600617448d88f6cd8c971cfdc68dad3fd80f2b5e5"),  # run:2026-10-15-sockets
    "sock-gems3": (BASE_X, "c7627f8888aaca2e0bf9bfe12a07f4b7ac21d38d8fc443752468fac373a60e98"),  # run:2026-10-15-sockets
    "sock-gems4": (BASE_X, "74a3eec0be066e83406f8b13279c054f6d093bea7ea8b8fddbd33e6855102743"),  # run:2026-10-15-sockets
    "sock-gems5": (BASE_X, "f444d597c88e1bef846afcad400cad995aeb27a8352523b28c35cac4f6e543dc"),  # run:2026-10-15-sockets
    "sock-jewels": (BASE_X, "8f74990e7610c33db1bfaa71fca56f50508beb2636ba594c9f5cf1c9136d404c"),  # run:2026-10-15-sockets
    "sock-refuse": (BASE_X, "e24c7a9ba0c3915506a5873808af0025db1114d218d3db16556caedb9dcb9aaf"),  # run:2026-10-15-sockets
    "sock-rw1": (BASE_X, "c09342303933a0a9252d5dac092c64e3cf3a57225f69ac850328b4988c05f4f1"),  # run:2026-10-15-sockets
    "sock-rw2": (BASE_X, "218f04dc70ff5c6ea7e95c1e4f95e1ea2e2de9c68f59a18e036c57d7055a8bd8"),  # run:2026-10-15-sockets
    "sock-rw3": (BASE_X, "1053522312a22fcaa27b4bbea9255706583a184f094bffcb528d2369978a405d"),  # run:2026-10-15-sockets
    "sock-rw4": (BASE_X, "3b881af4ef14fa20fe92862d0ee420c5c606407fc3288d22378c7afbeafd2de0"),  # run:2026-10-15-sockets
    "sock-rw5": (BASE_X, "d11767d7d628408e65e18a3a85ea34f26c43e1e10504367cd2771391a474cd0a"),  # run:2026-10-15-sockets
    "sock-rw6": (BASE_X, "1f5c9d2bf309a55b4950be2562b73fb9d59fe10bad6e951a6fb20918272daa42"),  # run:2026-10-15-sockets
    "sock-rw7": (BASE_X, "cbdbc9351b6fd678d325627c6fb78fcdb4ce8e20dac977ce5ed73f0991d02fa2"),  # run:2026-10-15-sockets
    "questservices": (BASE_X, "a9e32c29500f7a7ca1fd210432d62e661cb7e34050cd4f802e1891d85eb0fb57"),  # run:2026-10-16-quest-drops
    "socketclassic": (BASE_C, "5e14a113d06656efac1f5171df6ffd600c033279b04855f3f6f6f05cb9cf612a"),  # run:2026-10-15-socket-saves
    "socketnova": (BASE_X, "2f2cb8dde892ed0619813f22278f919b98dcfbcaf8b4cc49e6dd77995c14ff1a"),  # run:2026-10-15-socket-saves
    "objclassic": (BASE_C, "0f1afac19e57b99112562e5a5786ef7cd7ee6a1c974548b90b5bdefd01b44d85"),  # run:2026-10-15-objects
    "objnova": (BASE_X, "d54d5dc3656ed70dfd7fff28271c1437db7f2e97102e8d73836934999456a708"),  # run:2026-10-15-objects
    "specclassic": (BASE_C, "6d85055ea279c31497d6d67a2c9c53d9d181e0ff6458139a206c2b0476a78930"),  # run:2026-10-14-mon-special
    "specnova": (BASE_X, "649f84505667ffc4d17d067d200e15ddb2b96c2293cef359b3b80280eba02dd5"),  # run:2026-10-14-mon-special
    "uniqclassic": (BASE_C, "68e46a96698d98991ec362e273c26201f365f276444c4640d28c0bd931eaf0ea"),  # run:2026-10-14-uniques
    "uniqnova": (BASE_X, "2c793a3df3773c0f9d63d8c4ddc155e7eb384cc16b0495ac5eb00ab9d7ddc376"),  # run:2026-10-14-uniques rev 4
    "vendorclassic": (BASE_C, "d2e264dccbae35a21914754ed4ddcc878e4d1a2cfffaba8e08757e4df1058228"),  # run:2026-10-15-vendors
    "econa": (BASE_X, None),  # run:2026-10-17-economy (plan 0043 P2)
    "econb": (BASE_X, None),  # run:2026-10-17-economy (plan 0043 P2)
    "econc": (BASE_X, None),  # run:2026-10-17-economy (plan 0043 P2)
    "econd": (BASE_X, None),  # run:2026-10-17-economy (plan 0043 P2)
    "econdl3": (BASE_X, None),  # run:2026-10-17-economy (plan 0043 P2)
    "econdl75": (BASE_X, None),  # run:2026-10-17-economy (plan 0043 P2)
    "econh": (BASE_X, None),  # run:2026-10-19-economy2 (plan 0043 P2b)
    "econq": (BASE_X, None),  # run:2026-10-19-economy2 (plan 0043 P2b)
    "econg": (BASE_X, None),  # run:2026-10-17-economy (plan 0043 P2)
    "econn": (BASE_X, None),  # run:2026-10-17-economy (plan 0043 P2)
    "econk1": (BASE_X, None),  # run:2026-10-17-economy (plan 0043 P2)
    "econk2": (BASE_X, None),  # run:2026-10-17-economy (plan 0043 P2)
    "econk3": (BASE_X, None),  # run:2026-10-17-economy (plan 0043 P2)
    "econk4": (BASE_X, None),  # run:2026-10-17-economy (plan 0043 P2)
    "econk5": (BASE_X, None),  # run:2026-10-17-economy (plan 0043 P2)
    "econk6": (BASE_X, None),  # run:2026-10-17-economy (plan 0043 P2)
    "econk7": (BASE_X, None),  # run:2026-10-17-economy (plan 0043 P2)
    "econk8": (BASE_X, None),  # run:2026-10-17-economy (plan 0043 P2)
    "econk9": (BASE_X, None),  # run:2026-10-17-economy (plan 0043 P2)
    "econk10": (BASE_X, None),  # run:2026-10-17-economy (plan 0043 P2)
    "econw": (os.path.join(SAMPLES, "smpbar.d2s"), None),  # run:2026-10-17-economy (plan 0043 P2)
    "econt": (os.path.join(SAMPLES, "smpbar.d2s"), None),  # run:2026-10-17-economy (plan 0043 P2)
    "vendornova": (BASE_X, "eed8939c568f3db4e471220571649af51be9a7417feb918cabcf41a20365bb5c"),  # run:2026-10-15-vendors
    "vendornova75": (BASE_X, "dc2ca9397496b485df54b0547def9023d83c4b68390cd8eb91727831e82cae67"),  # run:2026-10-15-vendors
    # plan 0042 Phase 0 and Phase 1 (c) (tools/quest_saves.py): the 17 built saves loaded by plan 0042 Phase 2
    # (run:2026-10-17-quests, workspace/logs/quests/loads/loads.txt built prefixes); pinned by plan 0049 Phase 0
    "questfreshc": (BASE_C, "71eb65eaa6eaeb40175402bc324f2856b887421ce4d69744fd49f0f294690924"),  # run:2026-10-17-quests (loads)
    "travel-act2": (BASE_X, "3d172a6f3e1f961fdb3b483533fa2d79d223a128a5ec4203319155f069b5e171"),  # run:2026-10-17-quests (loads)
    "travel-act3": (BASE_X, "bd04bc2513e6e7abeccb76a16d918d616c4ec47d65ec59dcff48b2b63ae6dc7e"),  # run:2026-10-17-quests (loads)
    "travel-act4": (BASE_X, "5b3cbe8ae6d46bb5dd91d199b09cefd0cffecb72498db5fbeffe17c94aca03e1"),  # run:2026-10-17-quests (loads)
    "travel-act5": (BASE_X, "10155a1c27b19e9f8062b5e18da946cfd40ce390864b0df217300b19b5d6690d"),  # run:2026-10-17-quests (loads)
    "travel-arcane": (BASE_X, "439e0f2cb9ce954b67f87099669a58abef68980e33bee52bd72687e72b95d7dc"),  # run:2026-10-17-quests (loads)
    "travel-tab2": (BASE_X, "c2bac478d3b0475ab0360d8a32a2886c669a1f1240e20b111cd02dd0c4010ade"),  # run:2026-10-17-quests (loads)
    "travel-tab5d": (BASE_X, "c7487a6bce6617480c9631ac30389af91f6475946c678f854a9effc5d9100f99"),  # run:2026-10-17-quests (loads)
    "travel-wp1": (BASE_X, "a6204557593ad983c5c3c5f9ff6a9f3fba89d09bb032f730a476c6ecabb7e704"),  # run:2026-10-17-quests (loads)
    "travel-wp2": (BASE_X, "57b84f11026fb06283a3825e5300cd8f73c90dd09570ea1aa14f8c5debe98920"),  # run:2026-10-17-quests (loads)
    "travel-wp3": (BASE_X, "29aec1faa57f4e0d2b99a4491c84fc43d71fe846c41bc2eda6e243c521875902"),  # run:2026-10-17-quests (loads)
    "travel-wp4": (BASE_X, "7ff3eafb6b7809723b21bc0dce076691f4addd22b288281609db5284194b0fdd"),  # run:2026-10-17-quests (loads)
    "travel-wp5": (BASE_X, "9a0d88e802c9f8ea0f9d14109d7af4557846b628d6d33256640a3512f406c37c"),  # run:2026-10-17-quests (loads)
    "travel-wpnone": (BASE_X, "171a6a23524e3f69fa5332b45dc85e2cd2446674aeccc4081b21e14e4fd61c93"),  # run:2026-10-17-quests (loads)
    "quest-w9lost": (BASE_X, "20713178d063263231f536e21cca856ae11201868aefd5ae40c411ed0e22e947"),  # run:2026-10-17-quests (loads)
    "quest-w9book": (BASE_X, "c919898aae77149a760b4a08aed0fed2785e21db902f9bbea831e7cfdfa1d092"),  # run:2026-10-17-quests (loads)
    "quest-w39summit": (BASE_X, "f9dab74b53efdfe7eae14238dbf45eacaf9c0232cf3b080905fda76928efa7be"),  # run:2026-10-17-quests (loads)
    # plan 0042 Phase 2 recipes (tools/quest_saves.py, plan 0049 Phase 0): the built hash is the installed save the
    # run kept as <log>.in.d2s (hashed in the run's manifest); the sessions that loaded it in the comment
    "quest-tpc": (BASE_C, "fa2c8ba311cf764eacb6c9ef8992bcbf004a120c7fb3ca000174baabf391f704"),  # run:2026-10-17-quests (loads; c-tp, c-wp)
    "quest-talk1": (BASE_X, "c3dd8f0245f9038639c3f82b220d97a1f04df11c518ea20b9cf2da283e2fd441"),  # run:2026-10-18-quests2 (x-talk1, h-talk1)
    "quest-talk2": (BASE_X, "4c7668472aba46c321578267ba79ea13810ffdb4bbd5e465f1c7a9880c4a48db"),  # run:2026-10-18-quests2 (x-talk2)
    "quest-talk3": (BASE_X, "b12c2c9a29c3baf5cb4b1844409afe2df0b83ee47c66f3d34b281b8fbd441528"),  # run:2026-10-18-quests2 (x-talk3, x-talk3b, h-talk3)
    "quest-talk4": (BASE_X, "f7faffb80911dc9199195c848fe026cd6f38a40ac933a2da46b9e83dc1199447"),  # run:2026-10-18-quests2 (x-talk4, h-talk4)
    "quest-talk5": (BASE_X, "519649118d9af3a2e609cda4cbd172cabdb5f0bc9b0658ed9ed0ef1496c9f119"),  # run:2026-10-18-quests2 (x-talk5)
    "quest-talk1c": (BASE_C, "8b4fa87c3fd463bd068b99f63dbce98d47c0a5a5bc13fab442dff36288817e95"),  # run:2026-10-18-quests2 (c-talk1)
    "quest-talk2c": (BASE_C, None),  # built by run:2026-10-18-quests2, no session loaded it
    "quest-talk3c": (BASE_C, None),  # built by run:2026-10-18-quests2, no session loaded it
    "quest-talk4c": (BASE_C, "e89490978c073a481e60782e8215eee7a61684a345bcef39eb21abd615605698"),  # run:2026-10-18-quests2 (c-talk4)
    "quest-orbwill": (BASE_X, "271f3d56260ca02d9d0f31602a98375667824c70bbc18ea1a03b6684893f1fb7"),  # run:2026-10-18-quests2 (x-orb)
    "quest-death": (BASE_X, "4fb9af452b6c110b393f8779ea81bcaad6c6a5a386cb157d017ba8a8c2634fdd"),  # run:2026-10-19-quests3 (h-death3)
    "quest-p3entry": (BASE_X, "9aba95c47858c951801c4b4c1380f20ded0d5ce82af6f07980ffa10ffcea18e2"),  # run:2026-10-19-quests3 (x-entry, x-entry2, h-entry)
    "quest-p3anya": (BASE_X, "079bc38d014e3adcccb2e2406fefd9b4010fba3bd2b4533001980e361d91e7dd"),  # run:2026-10-19-quests3 (x-anya, nm-anya, h-anya)
    "quest-p3meshif": (BASE_X, "9927619642bd21f43b44a9e5555ae433715ca5d05447d8fdc16a98b1e936d0c0"),  # run:2026-10-19-quests3 (x-meshifw)
    "quest-p3wpact": (BASE_X, "c0371020861814b6dc9fb27a6e3edc047610d024add16f94d0b7a4884590698c"),  # run:2026-10-19-quests3 (x-wpact1-0, x-wpactr-0)
    # plan 0047 Phase 1 (tools/combat_sessions.py, tools/stats_sessions.py, tools/quest_sessions.py): built, not run yet
    "combatdr": (BASE_X, "639afd6a6c38a2e865c0ea61d2b859d15ca55d276a541c2267d6a3ce0670f297"),
    "combatabs": (BASE_X, "05f4741c6f17e3260868aac6c761f0a5523aa0670bc3210ca28d9daa1b6cc431"),
    "combatfrz": (BASE_X, "c1ed1c393a0bbc895def710550bf301dbeb36f187d296370a9e26af8bee58759"),
    "combatowf": (BASE_X, "77807e000c7c7c863752a795a45b446525dd38020c86a22ea1584c8c2639903c"),  # 5871b00's CombatOW, renamed
    "combatama": (os.path.join(SAMPLES, "smpama.d2s"), "5b694383e89d63d2c52d07968e1b265b4754f239b55a7fba0d2c42042e126522"),
    "combatamad": (os.path.join(SAMPLES, "smpama.d2s"), "d4572d07d582af3dc2fea3d7091900f71a75f46030593bccc1273d8e93a68cfd"),
    "combatamaw": (os.path.join(SAMPLES, "smpama.d2s"), "fa9c41625e302bad2b7a3af49b327712b4938e4ae6e375ba4487a667e15029cd"),
    "combatass": (os.path.join(SAMPLES, "smpasn.d2s"), "e0ea31a2df0dce6a63d4c705f4cdd9ce0c2b94716d71b3e8f692d0a49fc7af48"),
    "combatasso": (os.path.join(SAMPLES, "smpasn.d2s"), "c4dc7172e72c896accb07ebf77bfe05fd460eae75e4c757374039ae675b96475"),
    "statssor": (os.path.join(SAMPLES, "smpsor.d2s"), "963ed3809c35d69f29800a1292b9f9c4f4104245e612c4632206c123760efadd"),
    "statspald": (os.path.join(SAMPLES, "smppal.d2s"), "9fd320d2eb0859fa1f75b4b0cbd274a1ff85a2551fa5b8d2a0a5e4e3c3729870"),
    "statsass": (os.path.join(SAMPLES, "smpasn.d2s"), "5eb48cc0be61071d9e1e64549a365f58ecb6b62f5e12fa0b8a49f5cfc3ccdbde"),
    "statsdru": (os.path.join(SAMPLES, "smpdru.d2s"), "58cc838b578534b0d0dd0329bfb54188e737a6994576d3957ff0c9bbfebd312c"),
    "statsfloor": (os.path.join(SAMPLES, "smppal.d2s"), "82db5212c3cc57367313a0e731336ffd83234dd94a55781070bf90e093eac5ca"),
    "statsfloorb": (os.path.join(SAMPLES, "smppal.d2s"), "f52e41481604f10d3d36f7182d6e456b30f9a4dc34c2c684f648adf5eb320461"),   # plan 0047 Phase 2b: experience at level 85's start
    "statsneca": (os.path.join(SAMPLES, "smpnec.d2s"), "21b42e85994cfb5e6e6bac3f4d812294944f9b96e73dc58b847fb7df9e54ea54"),  # plan 0047 P2: Attract
    "statspot": (os.path.join(SAMPLES, "smpbar.d2s"), "a18f03a9f2dacaa2218ac200e1f555b3aca5a79cebf7a0e706298d5ab010dc6c"),
    "quest-p47wp": (BASE_X, "f3c935c349d44ca2fcaad2c803626b7bf62d56657d20036a39a98351b64a31d0"),
    # plan 0044 Phase 2 pairs (tools/mp_saves.py): not loaded yet
    "mp-nova-host": (BASE_X, None),
    "mp-nova-weak": (BASE_X, None),
    "mp-nova-low": (BASE_X, None),
    "mp-tank-join": (BASE_X, None),
    "mp-mf-host": (BASE_X, None),
    "mp-merc-host": (BASE_X, None),
    "mp-forge-host": (BASE_X, None),
    "mp-forge-join": (BASE_X, None),
    "mp-forge-done": (BASE_X, None),
    "mp-andy-open": (BASE_X, None),
    "mp-andy-done": (BASE_X, None),
    "mp-andy-weak": (BASE_X, None),
    "mp-den-host": (BASE_X, None),
    "mp-den-join": (BASE_X, None),
    "mp-dur-host": (BASE_X, None),
    "mp-dur-closed": (BASE_X, None),
    "mp-dur-open": (BASE_X, None),
    "mp-anc-join": (BASE_X, None),
    "mp-anc-low": (BASE_X, None),
    "mp-scroll-join": (BASE_X, None),
    "mp-quest-host": (BASE_X, None),
    "mp-quest-join": (BASE_X, None),
    "mp-cow-host": (BASE_X, None),
    "mp-pvp-host": (BASE_X, None),
    "mp-pvp-join": (BASE_X, None),
    "mp-pal-join": (BASE_PAL, None),
    # plan 0051 Phase 1a's staged pairs (MP18, MP25 offensive, open wounds): not loaded yet; hashes pinned at the build (lane/a2t)
    "mp-sock-join": (BASE_X, "7526561af0c9ee6e46e10918514e7a8b5f06701088ea70132e52812c414570e0"),
    "mp-wound-join": (BASE_X, "a10d0efa7056a774fa9af29e00a3f5cdf51554927dd9ab7f44c8a12008bba611"),
    "mp-pal-conv": (BASE_PAL, "4f6906111cecf8dbc377e194a7754d768a3847b09035cffaa73b9eb904517d14"),
    # plan 0045 Phase 2 (tools/skills_sessions.py SAVES, bases p0005/smp<cls>.d2s): hashes equal the kept saves of
    # run:2026-10-27-skills (2026-10-27-skills-manifest.sha256)
    "skills-sor": (os.path.join(P0005, "smpsor.d2s"), "d033b674bb0e6f03b3006f4d433fd23ad5b17e515dde6a0a8ca51caba64f5239"),  # run:2026-10-27-skills
    "skills-sorlow": (os.path.join(P0005, "smpsor.d2s"), "4af9bda6fcbfe4ab48450c100bb3799abb6bb418e563356b1292de8587373e0c"),  # run:2026-10-27-skills
    "skills-ama": (os.path.join(P0005, "smpama.d2s"), "e62bbee3a38172f50fe36d538d48a49cbf2335639f9d42a03fadb32b7d589215"),  # run:2026-10-27-skills
    "skills-amaj": (os.path.join(P0005, "smpama.d2s"), "ebc1da7ab733fc055f63420e088436a43d737053ad090c0f114a6b68faf39dae"),  # run:2026-10-27-skills
    "skills-nec": (os.path.join(P0005, "smpnec.d2s"), "4ff1948c372d2bae36f72b3592f5f5cb974cdad3d063522291a16a722ec978ad"),  # run:2026-10-27-skills
    "skills-dru": (os.path.join(P0005, "smpdru.d2s"), "6ed45fc4394835746383c91d640fbe490edae294bfec630a74997361a86b02e9"),  # run:2026-10-27-skills
    "skills-bar": (os.path.join(P0005, "smpbar.d2s"), "acefd40dfe0bd209aa497d9221f967ab1f4837715d908ac24ce57a024fcb2c2b"),  # run:2026-10-27-skills
    "skills-barh": (os.path.join(P0005, "smpbar.d2s"), "8d5978557b2532f67660c31a909c43630985f7a3dd0a83a7cdbb46852ae86373"),  # run:2026-10-27-skills
    "skills-pal": (os.path.join(P0005, "smppal.d2s"), "d5dcb6aba4e3408613ad1479e5ef6f792e214d22b0604d12efed878bad6efeb3"),  # run:2026-10-27-skills
    "skills-ass": (os.path.join(P0005, "smpasn.d2s"), "a89fc6e77b20559f6fc888703dd1cde8ad0db290a74608cc34aa615a842a603f"),  # run:2026-10-27-skills
    # recipes committed by session lanes without a base entry here (found by test_every_recipe_has_a_base, lane/arc5)
    "combatow": (BASE_X, None),
    "combatsorh": (BASE_X, None),
    "questalldone": (BASE_X, None),
    "questbaalf": (BASE_X, None),
    "questfreshct": (BASE_C, None),
    "questfreshm": (BASE_X, None),
    "questfresht": (BASE_X, None),
    "questservicesone": (BASE_X, None),
    # plan 0038 batch H6e2 (run:2026-10-27-sweep-quest-items): the saves of the run record
    "quest-h6e2-questgated": (BASE_X, "fa1794ecb0db6769257c1f34286afb0ad2d5cb1700187a43b2e0e3c2283f8bea"),
    "quest-h6e2-questgatef": (BASE_X, "5d0635bd80d70d5e18a8e1e9d741aadee9eb092d51080548c01d0b071f3fbdac"),
    "quest-h6e2-questboxh": (BASE_X, "284ac719ebcbfdde00a593ac97941c0e0555a51122dda5487bfe984abe665b61"),
    "quest-h6e2-questmsfn": (BASE_X, "8c85a0112726494bd502e73412424c1bb3066ca453fdff3c58c4998cf1a01b75"),
    "quest-h6e2-questfresht-a4": (BASE_X, "d6d11161a9375a3d9b151bc10822c7d729b3c4b3fad3069b518cca1da3c23f08"),
    "quest-h6e2-questboxh-a4": (BASE_X, "54ac3e3dee32ee1c207f89c1a6405250016641cf4735e5e9f9bc00f508bb238b"),
    "quest-h6e2-questmsfn-a4": (BASE_X, "1b6796d678b1c05b7f54ec26c2fd66258508effcbfe9cb40a185d38145846a52"),
    "h3brare": (BASE_X, "ce57d8f76eaabcad6bdb6eea7b06082ae400ae8c01be85404ec11dfa9cf86317"),  # run:2026-10-27-sweep-data-load
    "player-h6g-anc": (BASE_X, "b7366902ea1892ba8253c6845b9511b3bc1c28c5b0a813fcca8577ec460bb335"),  # run:2026-10-27-sweep-player
    "player-h6g-cap98": (BASE_X, "374fc7eb7e644e04a5832bb4eaf078a194e23ad65902d645129928b51189e702"),  # run:2026-10-27-sweep-player
    "player-h6g-deathh": (BASE_X, "36d99e01ddcd346649d43ac7452cf7b7acc130c0f711106a35000a3ea98f39e1"),  # run:2026-10-27-sweep-player
    "player-h6g-deathn": (BASE_X, "bc6150bd83d5276c1f1cb4f79fe12b6a81a315cde108737bec41b8c98d5ffdfd"),  # run:2026-10-27-sweep-player
    "player-h6g-deathnm": (BASE_X, "8f9fd1801f23094065ee2501b7646b85b54ae01efc47d282927ed422b9acef20"),  # run:2026-10-27-sweep-player
    "player-h6g-town": (BASE_X, "d32d3ad609d9e5ac28ed10664635f7f8ad41a310e700eab7ca987e4dc2e6dfe7"),  # run:2026-10-27-sweep-player
    "player-h6g-xp85": (BASE_X, "bce8ad899d09a053845d9636d8e63e950ccd8f6cc43a6ab0444e104c60fde250"),  # run:2026-10-27-sweep-player
    "quest-h6e1-give": (BASE_X, "3668f330864628d73c64277ed22326df2eb829eccb6eacb491160d80a9fa3cca"),  # run:2026-10-27-sweep-quest-npc
    "quest-h6e1-imb5": (BASE_X, "f4aa33741cea53bfc1f48bf5387b83351fff8bc80308eee892f378fb4c601f9f"),
    "quest-h6e1-imb6": (BASE_X, "5bf8e6702cc54bb2fbc5ca6cee87de97a215d0a1acf1cc9d93a7ad46ce6c77c5"),
    "quest-h6e1-svca": (BASE_X, "7dd9f00355fbf41af37e03d2c2f111f4d510abdc6930a2f3a83177165afab47f"),
    "quest-h6e1-svcb": (BASE_X, "636db82b21cd5eb7e1c308fadf005735a02c278af531abcf3bfa2ab1d0de4058"),
    "quest-h6e1-svcc": (BASE_X, "406d719aa7cf2db52cf204b617f01f6e6ea173b435f035d5e0e81760080de10c"),
    "h6f-ash": (BASE_X, "439e1af13ad83c02e6b9cb93e4a40a9a421b0eed4aa67272f21b1fc97a2ee083"),  # run:2026-10-27-sweep-hirelings
    "h6f-cl1": (BASE_C, "a704d08566f552bbe1a15b28c37ff8ea695d96f93f504ec38e37c346f5c6a7ad"),
    "h6f-cl2": (BASE_C, "9c6f016ae7e02f8798158f9e558a57f65015d4de1d5374129197e456d13468ea"),
    "h6f-cl3": (BASE_C, "eedba74b0241154705595149f1147a69a0de6c4cc8a08cf731dbe210c9f0b7f6"),
    "h6f-dead": (BASE_X, "cefa66a010a2ed382b0c1c96c5d21e21f4367f15c4bb0b56fb315cc9b6e28010"),
    "h6f-floor": (BASE_X, "35e5ca2f3aee9b99576530ebd4435aebea6703a4fb9aab9efb73ac422a5450c5"),
    "h6f-free": (BASE_X, "5f36f23b5c832648349bac18bc993f736de4e7d98d38d280f8f351b5c67e9edd"),
    "h6f-hexp": (BASE_X, "04f9064c5d8a964565d59ef2e878a7d69bea0164cd0b2349493059f9fbac2989"),
    "h6f-hx3": (BASE_X, "eeae3daab8a036ff1793102ab1cc32b90a4a7f51981598d245223c17f8820465"),
    "h6f-hx85": (BASE_X, "99dd45cb76ed22a617f5775c3d0b32adde63dac6a296a31d022a28e03096bcd4"),
    "h6f-l30": (BASE_X, "67c2608a1564d0d130350fd7696541466d33870583c2a493f13b34a64cf6db30"),
    "h6f-lvl": (BASE_X, "7bb6651966af8ada566c0f31e4069731a71419f431a9c57bef2ecd94f50e04ba"),
    "h6f-mact": (BASE_X, "4a7a100ca8a34e043972e303685ed43f522260e79fa4f1ef0e0d184f417f0f72"),
    "h6f-n99": (BASE_X, "6b4a6744167e815efffa5296d236d0594b141c8b5a474244bd07d7e2e4d5331d"),
    "h6f-qk": (BASE_X, "7605a13197bfdb05ef818aa126ca898219b415bae68acd6bc456f3e976e43f0f"),
    "sock-h6b-low": (BASE_RW, "6fe4ad5619497d909b4e01d290a8f694f3830ef1ea010eb90d62e965d4ee5d61"),  # run:2026-10-27-sweep-sockets
    "sock-h6b-low2": (BASE_RW, "7e3d88ccc9ad7446fe9594aff0bfb8b5d8fa3f70e07f83e33af96da1aa0915da"),
    "sock-h6b-refuse": (BASE_X, "a9afe50254561549f5d134b8632d33208cdff598c7b4a8992426cef9c6ba65b8"),
    "sock-h6b-svc": (BASE_X, "a0aa3e8ce029d439cae03c8fbc787c0203e02a413bce9d604c0c72d5f46bd783"),
    # plan 0050 Phase 2 (tools/anim_sessions.py SAVES, bases p0005/smp<cls>.d2s): hashes equal the kept saves of
    # run:2026-10-27-anim (2026-10-27-anim-manifest.sha256); each built twice with the same bytes (lane/a4t); the part 2
    # recipes (gh5-gh10, th, slow) equal the saves of run:2026-10-27-anim-p2 (2026-10-27-anim-p2-manifest-ckpt2.sha256)
    "anim-ama-t0": (os.path.join(P0005, "smpama.d2s"), "4aa14ba936cb2ddb34631b734dd3f234ccd752ee996defbd228d13d3ee681549"),  # run:2026-10-27-anim AnimAma0
    "anim-ama-t0-bk": (os.path.join(P0005, "smpama.d2s"), "d7da37549a107bf1fbd346af842493b5a9f37e772f7a1971c89bc0646c6ce2f0"),  # run:2026-10-27-anim bk/AnimAmaB0
    "anim-ama-t0-gh": (os.path.join(P0005, "smpama.d2s"), "56947ae53ef954d48fd4e016490fa2d7868d167c42f7e6febba4e96339c6fe81"),  # run:2026-10-27-anim gh/AnimAma0
    "anim-ama-t0-gh10": (os.path.join(P0005, "smpama.d2s"), "eebc2373432027f95cc2bf078274ecba061d833e4f3594218b20d48faa4a782d"),  # run:2026-10-27-anim-p2 gh5/AnimAmaR0
    "anim-ama-t0-gh2": (os.path.join(P0005, "smpama.d2s"), "ad0ba7b788aaacb1798a96f88b0752a3cfd16be009e0447af54b6ac97ee6c07f"),  # run:2026-10-27-anim gh2/AnimAmaH0
    "anim-ama-t0-gh3": (os.path.join(P0005, "smpama.d2s"), "fc06d8e27058f2154e831248bf9eff807cff312df9339f745bd3803657725cfb"),  # run:2026-10-27-anim gh3/AnimAmaL0
    "anim-ama-t0-gh4": (os.path.join(P0005, "smpama.d2s"), "9b977e47b615f829291fe1cc84cdaa773b9fd0ad6fe86af8f40e3ee8ce5fc998"),  # run:2026-10-27-anim gh4/AnimAmaM0
    "anim-ama-t0-gh9": (os.path.join(P0005, "smpama.d2s"), "40f09344d396471f7fc2c4bd13714bd3a1a1580c2ca5dc3034519ad43139ffb0"),  # run:2026-10-27-anim-p2 gh5/AnimAmaQ0
    "anim-ama-t1": (os.path.join(P0005, "smpama.d2s"), "9236413fedcb2f533d51d2c30a568ae7c3ebbabd612307b5e3bafbc1bc673b72"),  # run:2026-10-27-anim AnimAma1
    "anim-ama-t1-bk": (os.path.join(P0005, "smpama.d2s"), "d9394b9b3b8cc6ef2ea7ef2655ea779a39ecf11738258a877e3871526c979dcf"),  # run:2026-10-27-anim bk/AnimAmaB1
    "anim-ama-t1-gh": (os.path.join(P0005, "smpama.d2s"), "eab475fe08b4760ae3d5c443c59155ddfc4ef7fd5d25701f2bbfd44fe226cf3a"),  # run:2026-10-27-anim gh/AnimAma1
    "anim-ama-t1-gh10": (os.path.join(P0005, "smpama.d2s"), "b4297b4abfda212add3ecb661fc39ac3ce161c5b41769d01a7f5a3b30435dbfa"),  # run:2026-10-27-anim-p2 gh5/AnimAmaR1
    "anim-ama-t1-gh2": (os.path.join(P0005, "smpama.d2s"), "4fc22ccc3081cce43a3b772f5582bfd39ed2f7cc8a1a5741126dad9600d4b932"),  # run:2026-10-27-anim gh2/AnimAmaH1
    "anim-ama-t1-gh3": (os.path.join(P0005, "smpama.d2s"), "0deaa4b4329b5a1f7ec8724be2a05e3a0b98955e86b776c1783a4eb078e4c3f3"),  # run:2026-10-27-anim gh3/AnimAmaL1
    "anim-ama-t1-gh4": (os.path.join(P0005, "smpama.d2s"), "b16d7c84c2728b96264394c47cbab2e88fa3617f5f11a1c7addfd973205113f8"),  # run:2026-10-27-anim gh4/AnimAmaM1
    "anim-ama-t1-gh9": (os.path.join(P0005, "smpama.d2s"), "430d69b1707d9ab3c1aeec28557c6184cb3a4262e7d230da158c280aa869f057"),  # run:2026-10-27-anim-p2 gh5/AnimAmaQ1
    "anim-ama-t2": (os.path.join(P0005, "smpama.d2s"), "5aad38743d51aabd3963bae53af731f2f493d9dc353c2dc4730010f6201be329"),  # run:2026-10-27-anim AnimAma2
    "anim-ama-t2-bk": (os.path.join(P0005, "smpama.d2s"), "82bcf7b05ea362b1d565c4176c14931db5a104c7bcadce98575a66d1df79536d"),  # run:2026-10-27-anim bk/AnimAmaB2
    "anim-ama-t2-gh": (os.path.join(P0005, "smpama.d2s"), "3b61644b6fbb98bd5c608197bef9fc37316af6b2d2481cd990430e447c24d08e"),  # run:2026-10-27-anim gh/AnimAma2
    "anim-ama-t2-gh10": (os.path.join(P0005, "smpama.d2s"), "2dd52c0ce00459bf0e22b03809a5baa939284bc9001b3781a415300879aa6de8"),  # run:2026-10-27-anim-p2 gh5/AnimAmaR2
    "anim-ama-t2-gh2": (os.path.join(P0005, "smpama.d2s"), "f219eee3b794833dca8e22231eab740e25bab26d5ac98fb2ee764253239e0627"),  # run:2026-10-27-anim gh2/AnimAmaH2
    "anim-ama-t2-gh3": (os.path.join(P0005, "smpama.d2s"), "7e8857a0bc957352b96e2c0ac37481fc475f1bf3b17fdb75cac6d84d1a9ac567"),  # run:2026-10-27-anim gh3/AnimAmaL2
    "anim-ama-t2-gh4": (os.path.join(P0005, "smpama.d2s"), "c6d06aa69abefaa354140e00d6fe216abce3dfa35dabc4341b73c57a853078fc"),  # run:2026-10-27-anim gh4/AnimAmaM2
    "anim-ama-t2-gh9": (os.path.join(P0005, "smpama.d2s"), "6de1a5d02c05722149839003647eec5cf5ccd4bf48edb0882914af0bcc221584"),  # run:2026-10-27-anim-p2 gh5/AnimAmaQ2
    "anim-ass-bos": (os.path.join(P0005, "smpasn.d2s"), "74154b8f76ea61ec6d551f9f739608c41dc382b271b1cca257ab467b7bc87a8f"),  # run:2026-10-27-anim sp/AnimAssBos
    "anim-ass-t0": (os.path.join(P0005, "smpasn.d2s"), "aa1a83d9c058fc40ea13d56148dc34b4d7e0d5f46f0dc4af4e2318f2d10df27e"),  # run:2026-10-27-anim AnimAss0
    "anim-ass-t0-bk": (os.path.join(P0005, "smpasn.d2s"), "04a236f0adc6658238286fdecd0c6775a77a9f4754914f78b0c078e52210571c"),  # run:2026-10-27-anim bk/AnimAssB0
    "anim-ass-t0-gh": (os.path.join(P0005, "smpasn.d2s"), "a4fdafe66b778365182471c4f62ac5f89022f3dbc294e07abb617c381a812b9e"),  # run:2026-10-27-anim gh/AnimAss0
    "anim-ass-t0-gh10": (os.path.join(P0005, "smpasn.d2s"), "241bb232e78ae268cee3c4e0db42f0ad19851bc4037c91da9cd6e16ec53bd80c"),  # run:2026-10-27-anim-p2 gh5/AnimAssR0
    "anim-ass-t0-gh2": (os.path.join(P0005, "smpasn.d2s"), "a2f0c596b0efc0f1258bf5ae8fdac8fce2e57d4056c0bab9735045c2bf631cff"),  # run:2026-10-27-anim gh2/AnimAssH0
    "anim-ass-t0-gh3": (os.path.join(P0005, "smpasn.d2s"), "17c1e76768d28220c0f388160ef832760bf77ef0ecefee8fd1301b9626df2871"),  # run:2026-10-27-anim gh3/AnimAssL0
    "anim-ass-t0-gh4": (os.path.join(P0005, "smpasn.d2s"), "5bd03059c3d23707140c8dce94d334938ca0dd8b0c84e73c33fef7863db8fd56"),  # run:2026-10-27-anim gh4/AnimAssM0
    "anim-ass-t0-gh9": (os.path.join(P0005, "smpasn.d2s"), "9c807ea56e85e38512811c059be958ee50e718645832b961a1a9bc5dce200ff4"),  # run:2026-10-27-anim-p2 gh5/AnimAssQ0
    "anim-ass-t1": (os.path.join(P0005, "smpasn.d2s"), "b0d6002c321d87fbcb2462e6e563251583404f3efa904ae1a4ec7a3f8b99dec9"),  # run:2026-10-27-anim AnimAss1
    "anim-ass-t1-bk": (os.path.join(P0005, "smpasn.d2s"), "8526a02d2b806ec175b59d73d7285197a52bac798bba705aa5c6d1023ab35323"),  # run:2026-10-27-anim bk/AnimAssB1
    "anim-ass-t1-gh": (os.path.join(P0005, "smpasn.d2s"), "73401cc52b29cf8536fd958f7d0f562c25c25ce3912bcaa6bd5afa3f124d62ee"),  # run:2026-10-27-anim gh/AnimAss1
    "anim-ass-t1-gh10": (os.path.join(P0005, "smpasn.d2s"), "46c03705f4e0abede27d2d2635e15503f54191ab6ae44da6fb28012e0f41003b"),  # run:2026-10-27-anim-p2 gh5/AnimAssR1
    "anim-ass-t1-gh2": (os.path.join(P0005, "smpasn.d2s"), "7da5a9c9d8ccf4399b07054d366d4242479a1cf7f6b889eb4e8ffb03db6c5257"),  # run:2026-10-27-anim gh2/AnimAssH1
    "anim-ass-t1-gh3": (os.path.join(P0005, "smpasn.d2s"), "8d85be9854a4562aaff0e758e11ebc1682694c8523de423c3b8d1314d8b37353"),  # run:2026-10-27-anim gh3/AnimAssL1
    "anim-ass-t1-gh4": (os.path.join(P0005, "smpasn.d2s"), "16be5e102b31a974b2975c2d0aa3aea9993d6f0620cf3202fb0934699d62c8c0"),  # run:2026-10-27-anim gh4/AnimAssM1
    "anim-ass-t1-gh9": (os.path.join(P0005, "smpasn.d2s"), "6be5dcaa639ec2a334887ac55166d48b199dd813df4d082cd41232dd347cdb2f"),  # run:2026-10-27-anim-p2 gh5/AnimAssQ1
    "anim-ass-t2": (os.path.join(P0005, "smpasn.d2s"), "9111863df74cbddbff63eeaf3185aa8eeb09e5aea9ac55b3098ac195fe5e989d"),  # run:2026-10-27-anim AnimAss2
    "anim-ass-t2-bk": (os.path.join(P0005, "smpasn.d2s"), "50e5ed3f5edaf90cf8bb57ad258ab0103ee213b38f2d73bbbe11a416b1361612"),  # run:2026-10-27-anim bk/AnimAssB2
    "anim-ass-t2-gh": (os.path.join(P0005, "smpasn.d2s"), "5d7d58b8ea77a1046b7a110e5a7c71904480a86214433c3373f1947abb95e1d9"),  # run:2026-10-27-anim gh/AnimAss2
    "anim-ass-t2-gh10": (os.path.join(P0005, "smpasn.d2s"), "8b4b1c585261742fec22b1b9780cbfa1251fd5e998a4408d979be563b625fe6f"),  # run:2026-10-27-anim-p2 gh5/AnimAssR2
    "anim-ass-t2-gh2": (os.path.join(P0005, "smpasn.d2s"), "eed786d8f8145143f351668439140f3d2dd7fee0420134751f121f30af0317c1"),  # run:2026-10-27-anim gh2/AnimAssH2
    "anim-ass-t2-gh3": (os.path.join(P0005, "smpasn.d2s"), "7fff306b0c1fc19f6dc44278091e59ace1e3ad8c8f6e1e9e890d8f67f15d2c23"),  # run:2026-10-27-anim gh3/AnimAssL2
    "anim-ass-t2-gh4": (os.path.join(P0005, "smpasn.d2s"), "02aa2f5c7a9ee65249f9273434dfb008dcd6e12600b8ef7ff370ab3d7c229a15"),  # run:2026-10-27-anim gh4/AnimAssM2
    "anim-ass-t2-gh9": (os.path.join(P0005, "smpasn.d2s"), "862d398baa2e90dd0184355af7d194b7558988d244382f058b89bfeb3c37346c"),  # run:2026-10-27-anim-p2 gh5/AnimAssQ2
    "anim-bar-dw": (os.path.join(P0005, "smpbar.d2s"), "a5f0ac076e7f302eeb624eeda6215aca9a5331510e68741186775f0f43e162cc"),  # run:2026-10-27-anim sp/AnimBarDw
    "anim-bar-t0": (os.path.join(P0005, "smpbar.d2s"), "69e2a08fc917e9f9228a8092ac0c7f6a65c14d8419fdb08f7a25f8f70ff5902a"),  # run:2026-10-27-anim AnimBar0
    "anim-bar-t0-bk": (os.path.join(P0005, "smpbar.d2s"), "b69f5e1e8fa8055da48bcb1e202b03ffb4a72f9e39340215ee4008c6a1a67a7b"),  # run:2026-10-27-anim bk/AnimBarB0
    "anim-bar-t0-gh": (os.path.join(P0005, "smpbar.d2s"), "cbde0ea4e43bdfd43d8ca81ae60030b4c3a3bd2ac2e10565bf741a700da5f4ab"),  # run:2026-10-27-anim gh/AnimBar0
    "anim-bar-t0-gh10": (os.path.join(P0005, "smpbar.d2s"), "1c6615916246de2fd162cd1f5d62c9b903440d296e84cb18d4f2403a6427f2f1"),  # run:2026-10-27-anim-p2 gh5/AnimBarR0
    "anim-bar-t0-gh2": (os.path.join(P0005, "smpbar.d2s"), "b97a05137a72d597a3fa92f19daaaff4c0bb72580229c41a4f9e900e76bddc6c"),  # run:2026-10-27-anim gh2/AnimBarH0
    "anim-bar-t0-gh3": (os.path.join(P0005, "smpbar.d2s"), "c0f1bfb30c44d05e68e7fb76f4a273fb18e3a0f6af242698fa40058127102843"),  # run:2026-10-27-anim gh3/AnimBarL0
    "anim-bar-t0-gh4": (os.path.join(P0005, "smpbar.d2s"), "824535b30c1f4e41cfebd45a6e1f4c9f14e2c6c110622d96fc98c3925db4d26d"),  # run:2026-10-27-anim gh4/AnimBarM0
    "anim-bar-t0-gh7": (os.path.join(P0005, "smpbar.d2s"), "351bcb61e7df4f0365875b9d7075f5812019487d3926cf96771a1838d476e81f"),  # run:2026-10-27-anim-p2 gh5/AnimBarK0
    "anim-bar-t0-gh8": (os.path.join(P0005, "smpbar.d2s"), "6f1c21c6fee04cda1dff306b25e6a74601a5de0a72fc1b4a26ac38692382a5ef"),  # run:2026-10-27-anim-p2 gh5/AnimBarP0
    "anim-bar-t0-gh9": (os.path.join(P0005, "smpbar.d2s"), "f2c083d6c4d6832285fbada796c0c301a3933c0533341388fff7adf78471519a"),  # run:2026-10-27-anim-p2 gh5/AnimBarQ0
    "anim-bar-t1": (os.path.join(P0005, "smpbar.d2s"), "56800d91726315691c929c9bcdef7d24e26899d4acc60edbb56eed6739926054"),  # run:2026-10-27-anim AnimBar1
    "anim-bar-t1-bk": (os.path.join(P0005, "smpbar.d2s"), "b900610cf6e9083d8d99b97d4bab75c25ea6140d2d90217e6787cde41d9196f5"),  # run:2026-10-27-anim bk/AnimBarB1
    "anim-bar-t1-gh": (os.path.join(P0005, "smpbar.d2s"), "da5257db719af6cd9de7cd610c00bb5947185e8e89bef81de29da974b2feebc0"),  # run:2026-10-27-anim gh/AnimBar1
    "anim-bar-t1-gh10": (os.path.join(P0005, "smpbar.d2s"), "43146945ef54e1897d0d2505b79872958a344d920673057b1b2d8fb9da0c2d07"),  # run:2026-10-27-anim-p2 gh5/AnimBarR1
    "anim-bar-t1-gh2": (os.path.join(P0005, "smpbar.d2s"), "2d502fc814f8ed0e3ba06ee6669525ff86074e8641e1f3464300818bbe04dfb5"),  # run:2026-10-27-anim gh2/AnimBarH1
    "anim-bar-t1-gh3": (os.path.join(P0005, "smpbar.d2s"), "638bd747f99143e6b170f3a36334fcc36ebad0e629bdeb89c00cb18af7504e0d"),  # run:2026-10-27-anim gh3/AnimBarL1
    "anim-bar-t1-gh4": (os.path.join(P0005, "smpbar.d2s"), "5551114336b7ea7609bec6feddd870ab9f7eca8c2c57c131d10a6f0872fa1b9e"),  # run:2026-10-27-anim gh4/AnimBarM1
    "anim-bar-t1-gh9": (os.path.join(P0005, "smpbar.d2s"), "db32ce717d292da734d57e7d7da5bd57d6c88146c51a97ea7c1e162339f3f32c"),  # run:2026-10-27-anim-p2 gh5/AnimBarQ1
    "anim-bar-t2": (os.path.join(P0005, "smpbar.d2s"), "b732059f7a4132498d535a9bfc932e86dd79015f2f1543e34e8b4b69fdd8f9df"),  # run:2026-10-27-anim AnimBar2
    "anim-bar-t2-bk": (os.path.join(P0005, "smpbar.d2s"), "401652187739c0711a2b8be11de83707985505f23cdbba0284831dafd6d0a02f"),  # run:2026-10-27-anim bk/AnimBarB2
    "anim-bar-t2-gh": (os.path.join(P0005, "smpbar.d2s"), "9a2c501d24af6c0b432c704b81cb8308cb73129e0554b31f72ada852ca2592c4"),  # run:2026-10-27-anim gh/AnimBar2
    "anim-bar-t2-gh10": (os.path.join(P0005, "smpbar.d2s"), "e8396696046b6f6651c64d71e3067cb11c5c2e28bbb10d6931aae03cfd410afb"),  # run:2026-10-27-anim-p2 gh5/AnimBarR2
    "anim-bar-t2-gh2": (os.path.join(P0005, "smpbar.d2s"), "efb89bc0250dd229d9959d1685a2af741a3dfc6793a554547ec475d60c451ba5"),  # run:2026-10-27-anim gh2/AnimBarH2
    "anim-bar-t2-gh3": (os.path.join(P0005, "smpbar.d2s"), "8de4122ad2a676d27ddd2659833b0e0a6ccded472fbc99240e9e31d22a482c9a"),  # run:2026-10-27-anim gh3/AnimBarL2
    "anim-bar-t2-gh4": (os.path.join(P0005, "smpbar.d2s"), "e5af502340a58f5f07149103f241339fba8481c18b4e3f78a202a4673316890a"),  # run:2026-10-27-anim gh4/AnimBarM2
    "anim-bar-t2-gh9": (os.path.join(P0005, "smpbar.d2s"), "27a8c20d2772ae381a5105877b62b1b158b36edd1b2fbc3de86621c96f4c7317"),  # run:2026-10-27-anim-p2 gh5/AnimBarQ2
    "anim-dru-2hs": (os.path.join(P0005, "smpdru.d2s"), "e39c19aca9f20d8d2e63e88f841665e9b6d7dea979fdfbb68737999eeedbab72"),  # run:2026-10-27-anim sp/AnimDruH2s
    "anim-dru-form": (os.path.join(P0005, "smpdru.d2s"), "2d951e7bebb446adf8a818876fb1facd52305fe5aa30fa32500b36d231f6c26c"),  # run:2026-10-27-anim sp/AnimDruForm
    "anim-dru-form2": (os.path.join(P0005, "smpdru.d2s"), "cf767a1e8f9620eec8dbf0d58bdc8005fc92e132b40dbae27af787b38cddb7d5"),  # run:2026-10-27-anim sp/AnimDruForm2
    "anim-dru-t0": (os.path.join(P0005, "smpdru.d2s"), "01671fee56ebd6dff9c6a452e6406b4263875fc73739aa00e22d0a90b594e5c7"),  # run:2026-10-27-anim AnimDru0
    "anim-dru-t0-bk": (os.path.join(P0005, "smpdru.d2s"), "167640b2e53373511a929d8a1c794f264a30ae68846920c8c1ccf172a412eab7"),  # run:2026-10-27-anim bk/AnimDruB0
    "anim-dru-t0-gh": (os.path.join(P0005, "smpdru.d2s"), "3ce856c737a4859900a6273c27a0486bd28752c52e1b63adade6b976545d86d4"),  # run:2026-10-27-anim gh/AnimDru0
    "anim-dru-t0-gh10": (os.path.join(P0005, "smpdru.d2s"), "c158fdd413cfdb80d98abbbcd273f443cbafa95d439f39461504ebceb53efd81"),  # run:2026-10-27-anim-p2 gh5/AnimDruR0
    "anim-dru-t0-gh2": (os.path.join(P0005, "smpdru.d2s"), "28036a9f2d58316a9c7f6a0aa9e72f258d6c9b6133e283c680265e29f0510142"),  # run:2026-10-27-anim gh2/AnimDruH0
    "anim-dru-t0-gh3": (os.path.join(P0005, "smpdru.d2s"), "4e668990063dfb0bebd3ac51b6786b6d64e8212919f67d18863f33f4a5854b58"),  # run:2026-10-27-anim gh3/AnimDruL0
    "anim-dru-t0-gh4": (os.path.join(P0005, "smpdru.d2s"), "40a608be23604732a2c94e92d8a51acfc884f914fe8324a538399accf0c9fadd"),  # run:2026-10-27-anim gh4/AnimDruM0
    "anim-dru-t0-gh9": (os.path.join(P0005, "smpdru.d2s"), "92f6243749ab17237ffb56d7fcc6f44cbd7c15e805c1dea2a5a97a0720f455ab"),  # run:2026-10-27-anim-p2 gh5/AnimDruQ0
    "anim-dru-t1": (os.path.join(P0005, "smpdru.d2s"), "ff33317ce3a3e75b6d4e858c296e908af5e58e1198a72b495f863faf787a3c6c"),  # run:2026-10-27-anim AnimDru1
    "anim-dru-t1-bk": (os.path.join(P0005, "smpdru.d2s"), "26906db5fe46931a7f2f4ef79c31a06e1697aefd238d07e8ad186a05afcf7a12"),  # run:2026-10-27-anim bk/AnimDruB1
    "anim-dru-t1-gh": (os.path.join(P0005, "smpdru.d2s"), "b8abf9cb34ab3b9b3c94c297f5baab15f1f108bf598952f2c3c59adeb7b3ca6b"),  # run:2026-10-27-anim gh/AnimDru1
    "anim-dru-t1-gh10": (os.path.join(P0005, "smpdru.d2s"), "817b1bf7904294296fe33f71927ce076bbe2a582172f58d3cb28553b73d72f70"),  # run:2026-10-27-anim-p2 gh5/AnimDruR1
    "anim-dru-t1-gh2": (os.path.join(P0005, "smpdru.d2s"), "3d75ea5a91419b448c447c2846683c8afa4f28f208d35d8de022d7598290edea"),  # run:2026-10-27-anim gh2/AnimDruH1
    "anim-dru-t1-gh3": (os.path.join(P0005, "smpdru.d2s"), "526d4cef44ee574ff790247cda5c961d37fa914b064098661e85a72b3c6f91c1"),  # run:2026-10-27-anim gh3/AnimDruL1
    "anim-dru-t1-gh4": (os.path.join(P0005, "smpdru.d2s"), "5758c963a6ead5b515c45ddf42080898dbb126f9e6b7faf8a0e771a50353f661"),  # run:2026-10-27-anim gh4/AnimDruM1
    "anim-dru-t1-gh9": (os.path.join(P0005, "smpdru.d2s"), "2e4ad9b7ec3ed7d87c481ab2119dc7832c70cbf9d68ade4c911053dd2b17c97f"),  # run:2026-10-27-anim-p2 gh5/AnimDruQ1
    "anim-dru-t2": (os.path.join(P0005, "smpdru.d2s"), "8ff19ebcc0d8bdef6ae3ddbc781ba6022a3311c8787d8060041da7fe764ce948"),  # run:2026-10-27-anim AnimDru2
    "anim-dru-t2-bk": (os.path.join(P0005, "smpdru.d2s"), "7bdabe5858c143a3e573bb8fb6cc683cf07341435b02965bc016703f8cce1324"),  # run:2026-10-27-anim bk/AnimDruB2
    "anim-dru-t2-gh": (os.path.join(P0005, "smpdru.d2s"), "a20ab213a3aedd631260b5f19efa36961fada64d036c26ae5ede2e4df0bf4d59"),  # run:2026-10-27-anim gh/AnimDru2
    "anim-dru-t2-gh10": (os.path.join(P0005, "smpdru.d2s"), "b367e40afc2c149f3a563780547394d9ea50297a6d20f9878a2af80d94b9da78"),  # run:2026-10-27-anim-p2 gh5/AnimDruR2
    "anim-dru-t2-gh2": (os.path.join(P0005, "smpdru.d2s"), "7e4c6a2e90a3ecee93d9b8cc0e2ed9642ccdd5fe2a62a526aac2f18bf5a5dc4e"),  # run:2026-10-27-anim gh2/AnimDruH2
    "anim-dru-t2-gh3": (os.path.join(P0005, "smpdru.d2s"), "bf758aae914c60e0cc4ee21c3533f41162d94d8cefc4e9e0c944649e22a2f5a4"),  # run:2026-10-27-anim gh3/AnimDruL2
    "anim-dru-t2-gh4": (os.path.join(P0005, "smpdru.d2s"), "ea98fe8dce3c9e2989f1ee2fae57ca9b92e20416d6469dafa9fe728d930b63d5"),  # run:2026-10-27-anim gh4/AnimDruM2
    "anim-dru-t2-gh9": (os.path.join(P0005, "smpdru.d2s"), "4737bc6cebba52fadf7a8b6e6327c5eb31b25c8119f2ca84041f9a188d2a3807"),  # run:2026-10-27-anim-p2 gh5/AnimDruQ2
    "anim-dru-th": (os.path.join(P0005, "smpdru.d2s"), "d8a4769100b290733c4ab6cd2253421e92cc300b7caf270b31e0b7d17279bdc2"),  # run:2026-10-27-anim-p2 gh5/AnimDruT0
    "anim-nec-t0": (os.path.join(P0005, "smpnec.d2s"), "03e2c90824e47b2c35f38e8ec553833432c08d13400a9e68522db698fdcba664"),  # run:2026-10-27-anim AnimNec0
    "anim-nec-t0-bk": (os.path.join(P0005, "smpnec.d2s"), "50281e20537b37e58e26acdd0eaeedfb42e50ba93a2f7dc67a0184d8b0023094"),  # run:2026-10-27-anim bk/AnimNecB0
    "anim-nec-t0-gh": (os.path.join(P0005, "smpnec.d2s"), "2dbc062130a0a806a5c58e76de4409aabc3a64138a9f75753e4c5541aa61a4cd"),  # run:2026-10-27-anim gh/AnimNec0
    "anim-nec-t0-gh10": (os.path.join(P0005, "smpnec.d2s"), "38f064a7d19ec8f434debd21d6826079b6c03b7a6e4039e6a3c36e6f13d5104d"),  # run:2026-10-27-anim-p2 gh5/AnimNecR0
    "anim-nec-t0-gh2": (os.path.join(P0005, "smpnec.d2s"), "c1748ea66eb6460974c06c1bb24be87cf4fd75315259a10edd6382fff5adf128"),  # run:2026-10-27-anim gh2/AnimNecH0
    "anim-nec-t0-gh3": (os.path.join(P0005, "smpnec.d2s"), "fb7f87fd2c0f4658fb17038468d35737fca59abc539b6e2147cb92186f6f005e"),  # run:2026-10-27-anim gh3/AnimNecL0
    "anim-nec-t0-gh4": (os.path.join(P0005, "smpnec.d2s"), "fdb9c518e3915248d19f6bb04f6d2438a6cf74358a2e737d2a02d10cbee1502d"),  # run:2026-10-27-anim gh4/AnimNecM0
    "anim-nec-t0-gh9": (os.path.join(P0005, "smpnec.d2s"), "1e42aa1709cd3e562c9161b9e28d5e02fd5f8b2ac594be2ca0228d839fd1ba87"),  # run:2026-10-27-anim-p2 gh5/AnimNecQ0
    "anim-nec-t1": (os.path.join(P0005, "smpnec.d2s"), "b11119eba34bc05983be5538e9aaf15ec306b495eb38f8721244696a823759e6"),  # run:2026-10-27-anim AnimNec1
    "anim-nec-t1-bk": (os.path.join(P0005, "smpnec.d2s"), "87a354ef7158fafbd69aa0bd1706a8b8e955452771015ae21a303498d6a62b80"),  # run:2026-10-27-anim bk/AnimNecB1
    "anim-nec-t1-gh": (os.path.join(P0005, "smpnec.d2s"), "2735f88b6d86dc6ef6c71f2ca382d55f73d4bbc30a2d783bdccff182e20f1a8f"),  # run:2026-10-27-anim gh/AnimNec1
    "anim-nec-t1-gh10": (os.path.join(P0005, "smpnec.d2s"), "1b3364d6812832b1630c35a0abe640aeb71f6a609b3235e7488167903e7f2522"),  # run:2026-10-27-anim-p2 gh5/AnimNecR1
    "anim-nec-t1-gh2": (os.path.join(P0005, "smpnec.d2s"), "7a54a7d572c1a67371423310ea46cc9d1e8a5003e1db46f0aaa1899c384e43cc"),  # run:2026-10-27-anim gh2/AnimNecH1
    "anim-nec-t1-gh3": (os.path.join(P0005, "smpnec.d2s"), "fa0b89f4d8bccca9f05b5c6f31d1e87d4812f737ba1a0cfbfcab2f788e6008de"),  # run:2026-10-27-anim gh3/AnimNecL1
    "anim-nec-t1-gh4": (os.path.join(P0005, "smpnec.d2s"), "49805555e6eb0d385057d387e09550c27f3c7e46da45cbdca667d1b2a5fe27e3"),  # run:2026-10-27-anim gh4/AnimNecM1
    "anim-nec-t1-gh9": (os.path.join(P0005, "smpnec.d2s"), "3762986f0a7460297a04ff7b6a0857c41997e4f47c22723e55e36d7a31f11939"),  # run:2026-10-27-anim-p2 gh5/AnimNecQ1
    "anim-nec-t2": (os.path.join(P0005, "smpnec.d2s"), "8ba189145f726a1549cd06f1883f3850b7ff92a613259020612feb8515b53800"),  # run:2026-10-27-anim AnimNec2
    "anim-nec-t2-bk": (os.path.join(P0005, "smpnec.d2s"), "bc8cd878943dc336b7cb7205654daa3a6b90cbaa985fd4fe50b4bc16b1a8570c"),  # run:2026-10-27-anim bk/AnimNecB2
    "anim-nec-t2-gh": (os.path.join(P0005, "smpnec.d2s"), "69dbda8e9ce817b8784d19798d56152e0b54ebb908b891d7f32644c2bff3c8e2"),  # run:2026-10-27-anim gh/AnimNec2
    "anim-nec-t2-gh10": (os.path.join(P0005, "smpnec.d2s"), "30ae561679e7b78dff26d8ac50656f2e6605cd5aba3fb63d196751487cbbc377"),  # run:2026-10-27-anim-p2 gh5/AnimNecR2
    "anim-nec-t2-gh2": (os.path.join(P0005, "smpnec.d2s"), "bad2b1113659b434edc3bdec7f40dae18d3623c31bc26bb1c559450ba6e63239"),  # run:2026-10-27-anim gh2/AnimNecH2
    "anim-nec-t2-gh3": (os.path.join(P0005, "smpnec.d2s"), "d2db63ad0ebf2563772d11772abd4a33cc841d714b519ab4f47328e963138bac"),  # run:2026-10-27-anim gh3/AnimNecL2
    "anim-nec-t2-gh4": (os.path.join(P0005, "smpnec.d2s"), "9c988ae839a4601d0d2e1790ae31bc168b7a3fc0d7d6e09b7af91c2eb2dee4ff"),  # run:2026-10-27-anim gh4/AnimNecM2
    "anim-nec-t2-gh9": (os.path.join(P0005, "smpnec.d2s"), "827e10f8e5b21ab2449cc0332d6254f7ab698ca20c3528fc5d57ba010811e2eb"),  # run:2026-10-27-anim-p2 gh5/AnimNecQ2
    "anim-pal-chg": (os.path.join(P0005, "smppal.d2s"), "549ba36d63d844a88d394f64544e128d22ffff52418ac199202e13554ea3ebd6"),  # run:2026-10-27-anim sp/AnimPalChg
    "anim-pal-slow": (os.path.join(P0005, "smppal.d2s"), "da6912a7da9c336cab0e07433a633299c0ada78c2340c2a6ef5914d2dcc79110"),  # run:2026-10-27-anim-p2 gh5/AnimPalS1
    "anim-pal-t0": (os.path.join(P0005, "smppal.d2s"), "7d8ae2c4948db8d651114f1a26bfdd000f6ad12cbe18010b39040dc7d8d38a21"),  # run:2026-10-27-anim AnimPal0
    "anim-pal-t0-bk": (os.path.join(P0005, "smppal.d2s"), "7e1512ca733a09d581b0e3d931a850779aa32516d7ac944a8dd2ed3153c87bb3"),  # run:2026-10-27-anim bk/AnimPalB0
    "anim-pal-t0-gh": (os.path.join(P0005, "smppal.d2s"), "577f587ced8db018764d0c452f27bc06c6d7955b54d64afa86d9a4a51df2cdf0"),  # run:2026-10-27-anim gh/AnimPal0
    "anim-pal-t0-gh10": (os.path.join(P0005, "smppal.d2s"), "9db3a24e0c9f1370bf88c2a3c570b8283e5ca6cd02a61c394b24a284d55ef83e"),  # run:2026-10-27-anim-p2 gh5/AnimPalR0
    "anim-pal-t0-gh2": (os.path.join(P0005, "smppal.d2s"), "13077c68c18b620407280c0324bf78ab4e9ed6bd769de789a0a936aab957fdeb"),  # run:2026-10-27-anim gh2/AnimPalH0
    "anim-pal-t0-gh3": (os.path.join(P0005, "smppal.d2s"), "05341120c13cb211fea948959f804e81441b001b97f6e86604f9509a911274a6"),  # run:2026-10-27-anim gh3/AnimPalL0
    "anim-pal-t0-gh4": (os.path.join(P0005, "smppal.d2s"), "7820ec36727d7339650ca2aa385238bdb87c99f38d13f5801eb07220ceb622eb"),  # run:2026-10-27-anim gh4/AnimPalM0
    "anim-pal-t0-gh9": (os.path.join(P0005, "smppal.d2s"), "f2e587a0024e2cab4b9b8ca0214117e30c5267a9ce64d60230da097293e8c8d4"),  # run:2026-10-27-anim-p2 gh5/AnimPalQ0
    "anim-pal-t1": (os.path.join(P0005, "smppal.d2s"), "f1900646554ce9de4239b87a2b50e85d52343024e28e79830cdd80fe3468efef"),  # run:2026-10-27-anim AnimPal1
    "anim-pal-t1-bk": (os.path.join(P0005, "smppal.d2s"), "e4feee94abdf846d8511b9da9d02b69326e33ca74931b7f891fc0ca628f9514f"),  # run:2026-10-27-anim bk/AnimPalB1
    "anim-pal-t1-gh": (os.path.join(P0005, "smppal.d2s"), "b2fc52e420ef3732996ae973b470362701ecf7081b03d1f7353c1bb325fe3d5b"),  # run:2026-10-27-anim gh/AnimPal1
    "anim-pal-t1-gh10": (os.path.join(P0005, "smppal.d2s"), "422916766813ddbae4bdf5cdb9948a2ae7e0a7ab1056e1fe842005c54614b880"),  # run:2026-10-27-anim-p2 gh5/AnimPalR1
    "anim-pal-t1-gh2": (os.path.join(P0005, "smppal.d2s"), "23638474786a0599107609f7684aec72fe4f486c240d414e40c05ba7b706abde"),  # run:2026-10-27-anim gh2/AnimPalH1
    "anim-pal-t1-gh3": (os.path.join(P0005, "smppal.d2s"), "81f6b0f44f75385d3a44761ceef7bbb138a96ec8d772d0c7ea9ebc68a3390bc9"),  # run:2026-10-27-anim gh3/AnimPalL1
    "anim-pal-t1-gh4": (os.path.join(P0005, "smppal.d2s"), "65c24fe559e7c583f0fc693e9fea5a985cf5d0933306cef429f9dff3aa017698"),  # run:2026-10-27-anim gh4/AnimPalM1
    "anim-pal-t1-gh9": (os.path.join(P0005, "smppal.d2s"), "690a6cd32c2154eaa10a217b6b1780019e5bcf5f2151428b094ef296dc945e6c"),  # run:2026-10-27-anim-p2 gh5/AnimPalQ1
    "anim-pal-t2": (os.path.join(P0005, "smppal.d2s"), "f5e1177f0729a512b63b95849c93b9257eef13b4d014b997fdb6ceef44151bbe"),  # run:2026-10-27-anim AnimPal2
    "anim-pal-t2-bk": (os.path.join(P0005, "smppal.d2s"), "94eb827465b6be2e7b230fcc2c2c126e60e48e77cd726fab46226132eeccf122"),  # run:2026-10-27-anim bk/AnimPalB2
    "anim-pal-t2-gh": (os.path.join(P0005, "smppal.d2s"), "cd4220feff47bd415ef47a5044530c8ed9e69a38492b435f18ee7f96b47d98b3"),  # run:2026-10-27-anim gh/AnimPal2
    "anim-pal-t2-gh10": (os.path.join(P0005, "smppal.d2s"), "62c21965bdb833585f423446ecf97bbef13e316a8b54a8d8ae061d73836c9e63"),  # run:2026-10-27-anim-p2 gh5/AnimPalR2
    "anim-pal-t2-gh2": (os.path.join(P0005, "smppal.d2s"), "1526b332d41b7738f2694f5632e23d311932321035629eaf8fd8d400d1fad1f0"),  # run:2026-10-27-anim gh2/AnimPalH2
    "anim-pal-t2-gh3": (os.path.join(P0005, "smppal.d2s"), "76be8d4bba5544d446cd2b8acb89383ce65dd336bcf832cf861bb884fe1545a0"),  # run:2026-10-27-anim gh3/AnimPalL2
    "anim-pal-t2-gh4": (os.path.join(P0005, "smppal.d2s"), "4102034a460b1c25bd21c90592196a3f9744c6da3f1a9656f6b6e0b72bace9de"),  # run:2026-10-27-anim gh4/AnimPalM2
    "anim-pal-t2-gh9": (os.path.join(P0005, "smppal.d2s"), "ee74c100de3980e69d530f6dd245e97e597020c92f01d0e8d52c87a0bb88d805"),  # run:2026-10-27-anim-p2 gh5/AnimPalQ2
    "anim-sor-br": (os.path.join(P0005, "smpsor.d2s"), "a6a7b0d259749fa6783dae72135c33ccb633cae55b7a629dce2a869343e396b4"),  # run:2026-10-27-anim sp/AnimSorBr
    "anim-sor-mon": (os.path.join(P0005, "smpsor.d2s"), "4d675f3fe9f6cc95c891ea5c6cb5dc523ec3c7bac76e45b9d2e7c7328445891e"),  # run:2026-10-27-anim AnimSorMon
    "anim-sor-t0": (os.path.join(P0005, "smpsor.d2s"), "11f111c5e2af199184a72e247a6336a161ff3cda39929f89fe3ac693045d1776"),  # run:2026-10-27-anim AnimSor0
    "anim-sor-t0-bk": (os.path.join(P0005, "smpsor.d2s"), "5d8defea7c210a2143cbc387686d32abd588fd5f1190c0e4cc4338f644b2925a"),  # run:2026-10-27-anim bk/AnimSorB0
    "anim-sor-t0-gh": (os.path.join(P0005, "smpsor.d2s"), "6eb7e04d2c465e2711a012d490a77c27e9db1c91c809de17f3fbc9d1bbf37159"),  # run:2026-10-27-anim gh/AnimSor0
    "anim-sor-t0-gh10": (os.path.join(P0005, "smpsor.d2s"), "8af338ddf5f4f30bd4ce6c32a5029ef7bb68b44e281deb3b59b15c8c609d4b05"),  # run:2026-10-27-anim-p2 gh5/AnimSorR0
    "anim-sor-t0-gh2": (os.path.join(P0005, "smpsor.d2s"), "94aa769d45f42aee559840ebd679a6f1a2d2db639bc507bfd30b12efa1f0af40"),  # run:2026-10-27-anim gh2/AnimSorH0
    "anim-sor-t0-gh3": (os.path.join(P0005, "smpsor.d2s"), "bf45d135d83d21e450d18c48e8217b17f21b9c0caecf357c0fdf954cec643c8c"),  # run:2026-10-27-anim gh3/AnimSorL0
    "anim-sor-t0-gh4": (os.path.join(P0005, "smpsor.d2s"), "1a8afad5131b92a2af2ecf9d3fc6b1cdb0e4332a0c0e66327faa56ed67ea9396"),  # run:2026-10-27-anim gh4/AnimSorM0
    "anim-sor-t0-gh5": (os.path.join(P0005, "smpsor.d2s"), "6371c936360b4414120bb7ff2194de57e662ddbbf1b7b263982887be48d5fc02"),  # run:2026-10-27-anim-p2 gh5/AnimSorG0
    "anim-sor-t0-gh6": (os.path.join(P0005, "smpsor.d2s"), "6c94e8c7dd51279dae43cff8e90401c70e466a0b24af06cd15f45f1abff52ef3"),  # run:2026-10-27-anim-p2 gh5/AnimSorJ0
    "anim-sor-t0-gh7": (os.path.join(P0005, "smpsor.d2s"), "3b0cf5f022c7ef1b447891a6ea351b61f17ea41d9e653838755ba5e51a1e686c"),  # run:2026-10-27-anim-p2 gh5/AnimSorK0
    "anim-sor-t0-gh9": (os.path.join(P0005, "smpsor.d2s"), "8e6862295982f0a4bc1c23eb68a616cac833c59bf56030529d3772a7698b8348"),  # run:2026-10-27-anim-p2 gh5/AnimSorQ0
    "anim-sor-t1": (os.path.join(P0005, "smpsor.d2s"), "b7b60852bea49fcd44900991b3b98201b0a85d8364492263edb861b71406599e"),  # run:2026-10-27-anim AnimSor1
    "anim-sor-t1-bk": (os.path.join(P0005, "smpsor.d2s"), "bcdb169a5098b77d9203b2ed10d7fa606991b7ff9b654c791a5c4417856d94d1"),  # run:2026-10-27-anim bk/AnimSorB1
    "anim-sor-t1-gh": (os.path.join(P0005, "smpsor.d2s"), "7c2839b54cb316db6809a3d19a7504671de15d43b4f8800f00cea1dad9e78531"),  # run:2026-10-27-anim gh/AnimSor1
    "anim-sor-t1-gh10": (os.path.join(P0005, "smpsor.d2s"), "5c331672c4a79f31eba00d3cb7ac3513578afe4721072d38240c344b16b8c052"),  # run:2026-10-27-anim-p2 gh5/AnimSorR1
    "anim-sor-t1-gh2": (os.path.join(P0005, "smpsor.d2s"), "d4812cc38c2a18fa5491e292cbd253e61b50750d925d0ae7de8b24c4736d707a"),  # run:2026-10-27-anim gh2/AnimSorH1
    "anim-sor-t1-gh3": (os.path.join(P0005, "smpsor.d2s"), "aae5478030551160f3537603a87608c584d909ade801ac12ac179262b7a559ef"),  # run:2026-10-27-anim gh3/AnimSorL1
    "anim-sor-t1-gh4": (os.path.join(P0005, "smpsor.d2s"), "b7824ab917d9fc011f35229db59edbfc3b1184c25f0b878da1a6d1cb78b924ab"),  # run:2026-10-27-anim gh4/AnimSorM1
    "anim-sor-t1-gh9": (os.path.join(P0005, "smpsor.d2s"), "fb25a1842168b80678696b4b0494f6f879b83fce52b60c95dabbf8f782780bc8"),  # run:2026-10-27-anim-p2 gh5/AnimSorQ1
    "anim-sor-t2": (os.path.join(P0005, "smpsor.d2s"), "87db5a5684cda29c3c9957d42e073f2ca99d8afc5521dba6e8f1d8dc6476f2e4"),  # run:2026-10-27-anim AnimSor2
    "anim-sor-t2-bk": (os.path.join(P0005, "smpsor.d2s"), "fcb84d7e53188ef7f77a33a479e8959d3a9ab197153e5a675d595d268c956091"),  # run:2026-10-27-anim bk/AnimSorB2
    "anim-sor-t2-gh": (os.path.join(P0005, "smpsor.d2s"), "bdc10bf9853ddcc092fe0c4236e97726ebacd3d1ce6e2620caf94171ecb477fa"),  # run:2026-10-27-anim gh/AnimSor2
    "anim-sor-t2-gh10": (os.path.join(P0005, "smpsor.d2s"), "5c30c2f9debe26c03a37f762f8e50a2246a8e4009cca75a7ba48ef1b714a7a19"),  # run:2026-10-27-anim-p2 gh5/AnimSorR2
    "anim-sor-t2-gh2": (os.path.join(P0005, "smpsor.d2s"), "4a2645f19c32669ce2a0fa1d28e252f3e1ff9fd6301537c3f68ba9f9182b46ff"),  # run:2026-10-27-anim gh2/AnimSorH2
    "anim-sor-t2-gh3": (os.path.join(P0005, "smpsor.d2s"), "816bd267c30957e647091a3442b75a4e748d2ec9279d6a0c7192cb2ce3be7917"),  # run:2026-10-27-anim gh3/AnimSorL2
    "anim-sor-t2-gh4": (os.path.join(P0005, "smpsor.d2s"), "3a74647031c9c34de079b84a1fc2d5e988af02425c06961901d37dd6a37e67c0"),  # run:2026-10-27-anim gh4/AnimSorM2
    "anim-sor-t2-gh9": (os.path.join(P0005, "smpsor.d2s"), "2c4d391904e510efd5d5dbfc4777133ad0d711da40c824c6e6a6d9d58e79c539"),  # run:2026-10-27-anim-p2 gh5/AnimSorQ2
    "vend-h6c-low": (BASE_X, "b0334a6eb3f6ae25c6dfd1b08fb79e16b144e970701d953123f26a3a3419161c"),  # run:2026-10-27-sweep-vendors
    "vend-h6c-lvl": (BASE_X, "45223841c311618199df65291cccab69a9be2f6ea74c247c4aa79f34f14522a0"),
    "vend-h6c-h99e": (BASE_X, "b7e77e44c6c5ec6bf235a0a2a52ef46b3e3a50afd19c5310cec44bf87feed8ea"),
    "vend-h6c-n19": (BASE_X, "1a48c28694629c582dc256f3a3f6e3eeb0c28057d41a003ebd42c1e3a952ebe0"),
}

_TABLES = []


def readb(path):
    with open(path, "rb") as fh:
        return fh.read()


def tables():
    if not _TABLES:
        _TABLES.append(d2s.Tables(EXCEL))
    return _TABLES[0]


def need(*paths):
    missing = [p for p in (EXCEL,) + paths if not os.path.exists(p)]
    if missing:
        raise unittest.SkipTest("needs workspace/: %s" % ", ".join(os.path.relpath(p, REPO) for p in missing))


def stored(code, x, y, store=1, **kw):
    return dict(code=code, location=0, store=store, x=x, y=y, body=0, **kw)


class LayoutTest(unittest.TestCase):
    SIZES = {"cm1": (1, 1), "cm3": (1, 3), "tsc": (1, 1), "isc": (1, 1), "amu": (1, 1), "sst": (1, 3)}

    def check(self, items):
        d2s.check_layout(items, self.SIZES)

    def refused(self, items, *words):
        with self.assertRaises(d2s.D2sError) as cm:
            self.check(items)
        for w in words:
            self.assertIn(w, str(cm.exception))

    def test_disjoint_items_pass(self):
        # the uniqnova layout: a 1x3 charm at (0, 0), small charms from column 1 on
        self.check([stored("cm3", 0, 0)] + [stored("cm1", x, y) for x in range(1, 10) for y in range(4)])

    def test_kept_scroll_over_charm_is_refused(self):
        # rev 1 and 2 of run:2026-10-14-uniques: the base save's scrolls at (9, 2) and (9, 3) under two charms
        self.refused([stored("isc", 9, 2), stored("tsc", 9, 3), stored("cm1", 9, 2), stored("cm1", 9, 3)],
                     "inventory", "cm1 at (9, 2) overlaps isc at (9, 2)", "cm1 at (9, 3) overlaps tsc at (9, 3)")

    def test_tall_item_covers_lower_cells(self):
        self.refused([stored("cm3", 0, 0), stored("cm1", 0, 2)], "cm1 at (0, 2) overlaps cm3 at (0, 0)")
        self.check([stored("cm3", 0, 0), stored("cm1", 0, 3), stored("cm1", 1, 0)])

    def test_pages_are_separate(self):
        self.check([stored("cm1", 0, 0, store=1), stored("cm1", 0, 0, store=4), stored("cm1", 0, 0, store=5)])
        self.refused([stored("sst", 0, 0, store=4), stored("amu", 0, 1, store=4)], "cube")

    def test_one_report_per_pair(self):
        with self.assertRaises(d2s.D2sError) as cm:
            self.check([stored("sst", 0, 0), stored("cm3", 0, 0)])
        self.assertEqual(str(cm.exception).count("overlaps"), 1)

    def test_belt_and_body_slots(self):
        belt = dict(code="rvl", location=2, store=0, x=3, y=0, body=0)
        self.refused([belt, dict(belt)], "belt slot 3")
        self.check([belt, dict(belt, x=7)])
        ring = dict(code="rin", location=1, store=0, x=6, y=0, body=6)
        self.refused([ring, dict(ring)], "body 6")
        self.check([ring, dict(ring, x=7, body=7)])

    def test_socketed_children_are_ignored(self):
        self.check([stored("cm1", 0, 0), dict(stored("cm1", 0, 0), location=6, parent=0)])

    def test_unknown_size_is_an_error(self):
        self.refused([stored("zzz", 0, 0)], "zzz")


class Scratch(unittest.TestCase):
    def setUp(self):
        quiet = contextlib.redirect_stdout(io.StringIO())   # build and excel_edit print a line per item / cell
        quiet.__enter__()
        self.addCleanup(quiet.__exit__, None, None, None)
        warnings.filterwarnings("ignore", category=ResourceWarning)   # the table readers use open().read()
        self.tmp = tempfile.mkdtemp(prefix="test-d2s-")
        self.addCleanup(shutil.rmtree, self.tmp)

    def path(self, name):
        return os.path.join(self.tmp, name)


class RecipeTest(Scratch):
    def test_every_recipe_has_a_base(self):
        names = sorted(n[:-5] for n in os.listdir(RECIPES) if n.endswith(".json"))
        self.assertEqual(names, sorted(RECIPE_BASES), "add the new recipe's base save to RECIPE_BASES")

    def test_recipes_build(self):
        for name, (base, sha) in sorted(RECIPE_BASES.items()):
            with self.subTest(recipe=name):
                need(base)
                out = self.path(name + ".d2s")
                d2s.build(EXCEL, os.path.join(RECIPES, name + ".json"), base, out)
                b = readb(out)
                ver = d2s.u32(b, 4)
                if ver in d2s.LEGACY_VERSIONS:   # the legacy layout: no checksum, its own reader
                    f = d2s.parse_legacy(b, tables().isc, tables().kinds, d2s.classic_codes(tables()))
                    self.assertEqual(f["end"], len(b))
                else:
                    self.assertEqual(d2s.checksum(b), d2s.u32(b, 12))
                    self.assertEqual(d2s.parse(b, tables().isc, tables().kinds, extended=ver != 96)["end"], len(b))
                if sha:
                    self.assertEqual(hashlib.sha256(b).hexdigest(), sha)


class KeysTest(Scratch):
    def build(self, recipe, base=BASE_X):
        need(base)
        rp, out = self.path("r.json"), self.path("out.d2s")
        game = "classic" if base == BASE_C else "expansion"
        with open(rp, "w") as fh:
            json.dump(dict(dict(seed=1, game=game), **recipe), fh)
        d2s.build(EXCEL, rp, base, out)
        b = readb(out)
        return b, d2s.parse(b, tables().isc, tables().kinds)

    def test_suffix_magic_item(self):
        t = tables()
        for roll in ("max", "min"):
            b, f = self.build(dict(stats={"level": 1}, items=[
                dict(code="cm1", suffix=290, roll=roll, store="inventory", x=0, y=0)]))
            it = [i for i in f["items"]["items"] if i.get("code", "").strip() == "cm1"][0]
            self.assertEqual((it["quality"], it["prefix"], it["suffix"]), (4, 0, 290))
            sfx = t.suffixes[290]
            row = {"prop1": sfx["mod1code"], "par1": sfx["mod1param"], "min1": sfx["mod1min"], "max1": sfx["mod1max"]}
            self.assertEqual(it["props"], d2s.props_list(d2s.unique_stats(t, row, roll)))
            self.assertTrue(it["props"])

    def test_suffix_refusals(self):
        for spec in (dict(code="cm1", suffix=0), dict(code="cm1", suffix=10 ** 6),
                     dict(code="rin", unique="Nagelring", suffix=290)):
            with self.subTest(spec=spec), self.assertRaises(d2s.D2sError):
                self.build(dict(stats={"level": 1}, items=[dict(spec, store="inventory", x=0, y=0)]))

    def test_lone_follower_test_state(self):
        """backlog 2026-10-27 (plan 0038 H1b row 124): a group follower without its head (49 fire-max, no 48
        fire-min) is refused by default and written alone, with its own Save Bits, under "lone_follower"."""
        spec = dict(code="cap", store="inventory", x=0, y=0, item_stats={"49": 10})
        with self.assertRaises(d2s.D2sError) as cm:
            self.build(dict(stats={"level": 1}, items=[spec]))
        self.assertIn("stat 49 without its group head 48", str(cm.exception))
        b, f = self.build(dict(stats={"level": 1}, items=[dict(spec, lone_follower=True)]))
        cap = [i for i in f["items"]["items"] if i.get("code", "").strip() == "cap"][0]
        self.assertEqual(cap["props"], [(49, None, [10])])
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(d2s.roundtrip(EXCEL, [self.path("out.d2s")]), 0)
        # with the head present the key changes nothing: one grouped entry, as without it
        _b, f2 = self.build(dict(stats={"level": 1}, items=[dict(spec, item_stats={"48": 5, "49": 10},
                                                                  lone_follower=True)]))
        cap2 = [i for i in f2["items"]["items"] if i.get("code", "").strip() == "cap"][0]
        self.assertEqual(cap2["props"], [(48, None, [5, 10])])

    def test_belt_fill_columns(self):
        t = tables()
        cols = ["rvl", "hp5", "mp5", "rvs"]
        b, f = self.build(dict(stats={"level": 1}, items=[dict(code="hbl", equip="belt")], belt_fill=cols))
        belt = sorted((i["x"], i["code"].strip()) for i in f["items"]["items"] if i["location"] == 2)
        boxes = t.belts[int(t.base["hbl"]["belt"])]
        self.assertEqual(belt, [(k, cols[k % 4]) for k in range(boxes)])
        with self.assertRaises(d2s.D2sError):
            self.build(dict(stats={"level": 1}, items=[dict(code="hbl", equip="belt")], belt_fill=cols[:3]))
        with self.assertRaises(d2s.D2sError):
            self.build(dict(stats={"level": 1}, belt_fill="rvl"))  # no belt equipped

    def test_hotkeys(self):
        t = tables()
        base = readb(BASE_X) if os.path.exists(BASE_X) else None
        b, f = self.build(dict(stats={"level": 1}, hotkeys=["Nova", "left:Teleport"]))
        hk = f["header"]["hotkeys"]
        self.assertEqual(hk[0], t.skills["Nova"]["id"])
        self.assertEqual(hk[1], t.skills["Teleport"]["id"] | 0x8000)
        self.assertEqual(b[0x38 + 8:0x78], base[0x38 + 8:0x78])  # the other slots stay as in the base
        for bad in (["Novaa"], ["left:Novaa"], ["Nova"] * 17):
            with self.subTest(hotkeys=bad[:2]), self.assertRaises(d2s.D2sError):
                self.build(dict(stats={"level": 1}, hotkeys=bad))

    def test_overlap_refused_and_nothing_written(self):
        recipe = dict(stats={"level": 1}, keep_items=["tsc", "isc"],
                      items=[dict(code="cm1", suffix=290, store="inventory", x=9, y=2)])
        with self.assertRaises(d2s.D2sError) as cm:
            self.build(recipe)
        self.assertIn("cm1 at (9, 2) overlaps isc at (9, 2)", str(cm.exception))
        self.assertFalse(os.path.exists(self.path("out.d2s")))
        # the command line exits 1 with the message, no traceback
        rp = self.path("r.json")
        p = subprocess.run([sys.executable, "-I", os.path.join(HERE, "d2s.py"), "build", EXCEL, rp, BASE_X,
                            self.path("cli.d2s")], capture_output=True, text=True)
        self.assertEqual(p.returncode, 1)
        self.assertIn("overlaps", p.stderr)
        self.assertNotIn("Traceback", p.stderr)
        self.assertFalse(os.path.exists(self.path("cli.d2s")))


class GameTest(Scratch):
    build = KeysTest.build

    def build_raw(self, recipe, base):
        need(base)
        rp, out = self.path("g.json"), self.path("g.d2s")
        with open(rp, "w") as fh:
            json.dump(dict(dict(seed=1, stats={"level": 1}), **recipe), fh)
        d2s.build(EXCEL, rp, base, out)
        return readb(out)

    def refused(self, recipe, base, *words):
        with self.assertRaises(d2s.D2sError) as cm:
            self.build_raw(recipe, base)
        for w in words:
            self.assertIn(w, str(cm.exception))
        self.assertFalse(os.path.exists(self.path("g.d2s")))

    def test_bases(self):
        need(BASE_X, BASE_C)
        self.assertEqual(readb(BASE_X)[0x24] & 0x20, 0x20)
        self.assertEqual(readb(BASE_C)[0x24] & 0x20, 0)

    def test_matching_game_builds(self):
        for game, base in (("expansion", BASE_X), ("classic", BASE_C)):
            with self.subTest(game=game):
                b = self.build_raw(dict(game=game), base)
                self.assertEqual(b[0x24] & 0x20, 0x20 if game == "expansion" else 0)

    def test_classic_recipe_on_expansion_base_refused(self):
        self.refused(dict(game="classic"), BASE_X, "recipe game 'classic'", "base save is expansion")

    def test_expansion_recipe_on_classic_base_refused(self):
        self.refused(dict(game="expansion"), BASE_C, "recipe game 'expansion'", "base save is classic")

    def test_game_key_required(self):
        for recipe in ({}, dict(game="lod"), dict(game=True)):
            with self.subTest(recipe=recipe):
                self.refused(recipe, BASE_X, '"game"')

    def test_tome_in_cube_round_trips(self):
        # the plan 0026 follow-up (a) recipe shape: Wirt's Leg and a Tome of Town Portal in the cube
        b, f = self.build(dict(stats={"level": 1}, items=[
            dict(code="box", store="inventory", x=0, y=0),
            dict(code="leg", store="cube", x=0, y=0),
            dict(code="tbk", store="cube", x=1, y=0, quantity=5)]))
        tome = [i for i in f["items"]["items"] if i.get("code", "").strip() == "tbk"]
        self.assertEqual(len(tome), 1)
        self.assertEqual((tome[0]["store"], tome[0]["tome"], tome[0]["quantity"]), (4, 0, 5))
        self.assertEqual(f["end"], len(b))
        rc = d2s.roundtrip(EXCEL, [self.path("out.d2s")])
        self.assertEqual(rc, 0)

    def test_quest_bits_and_quest_item_stats(self):
        # plan 0030 Phase 2: the cow portal's quest words and stat 356 on Wirt's Leg (extended) and an eye (simple)
        b, f = self.build(dict(stats={"level": 1}, quests="all",
                               quest_bits=[["normal", 4, 10, 1], ["hell", 40, 0, 0]],
                               items=[dict(code="leg", store="inventory", x=0, y=0, item_stats={"356": 2}),
                                      dict(code="qey", store="inventory", x=1, y=0, quest_diff=1)]))
        word = lambda d, q: d2s.u16(b, d2s.QUEST_OFF + 10 + 0x60 * d + 2 * q)  # noqa: E731
        self.assertTrue(word(0, 4) & (1 << 10))
        self.assertFalse(word(2, 40) & 1)
        self.assertTrue(word(1, 40) & 1)                       # quests "all" set it, the bit list left it
        leg = [i for i in f["items"]["items"] if i.get("code", "").strip() == "leg"][0]
        self.assertEqual(leg["props"], [(356, None, [2])])
        eye = [i for i in f["items"]["items"] if i.get("code", "").strip() == "qey"][0]
        self.assertEqual(eye["quest_diff"], 1)
        self.assertEqual(d2s.roundtrip(EXCEL, [self.path("out.d2s")]), 0)


class SocketTest(Scratch):
    build = KeysTest.build

    def items(self, f):
        return f["items"]["items"]

    def test_filled_parent_and_children(self):
        b, f = self.build(dict(stats={"level": 1}, items=[
            dict(code="cap", store="inventory", x=0, y=0, sockets=2),
            dict(code="sml", store="inventory", x=2, y=0, sockets=2,
                 filled=[dict(code="gsv"), dict(code="jew", suffix=260)]),
            dict(code="crs", store="stash", x=0, y=0, sockets=6, filled=[dict(code="r01")])]))
        its = self.items(f)
        codes = [(i.get("code", "").strip(), i["location"], i["x"], "parent" in i) for i in its]
        self.assertEqual(codes, [("cap", 0, 0, False), ("sml", 0, 2, False), ("gsv", 6, 0, True),
                                 ("jew", 6, 1, True), ("crs", 0, 0, False), ("r01", 6, 0, True)])
        cap, sml, gem, jew, crs, rune = its
        self.assertEqual((cap["socketed"], cap["sockets"], cap["n_filled"]), (1, 2, 0))
        self.assertEqual((sml["socketed"], sml["sockets"], sml["n_filled"]), (1, 2, 2))
        self.assertEqual((crs["store"], crs["sockets"], crs["n_filled"]), (5, 6, 1))
        self.assertEqual((gem["simple"], gem["store"], gem["body"], gem["y"]), (1, 0, 0, 0))
        self.assertEqual((jew["simple"], jew["quality"], jew["suffix"]), (0, 4, 260))
        self.assertEqual(sml["props"], [])            # the builder copies no filler stats into the parent
        self.assertEqual(f["items"]["count"], 3)      # socketed items are not counted
        self.assertEqual(d2s.roundtrip(EXCEL, [self.path("out.d2s")]), 0)

    def test_refusals(self):
        bad = [
            (dict(code="cap", sockets=3), "takes 1..2"),             # gemsockets 2
            (dict(code="buc", sockets=2), "takes 1..1"),             # gemsockets 1
            (dict(code="cap", sockets=0), "takes 1..2"),
            (dict(code="crs", sockets=6, ilvl=20), "takes 1..3"),    # swor MaxSock1 3 below ilvl 26
            (dict(code="cap", sockets=1, filled=[dict(code="gsv"), dict(code="gsv")]), "2 filled items, 1 sockets"),
            (dict(code="cap", filled=[dict(code="gsv")]), "needs"),
            (dict(code="cap", sockets=2, filled=[dict(code="hp1")]), "not a socket filler"),
            (dict(code="cap", sockets=2, filled=[dict(code="gsv", store="inventory", x=0, y=0)]), "no placement"),
        ]
        for spec, words in bad:
            with self.subTest(spec=spec), self.assertRaises(d2s.D2sError) as cm:
                self.build(dict(stats={"level": 1}, items=[dict(spec, store="inventory", x=0, y=0)]))
            self.assertIn(words, str(cm.exception))

    def test_quality_clamp(self):
        """Above the ITEMS_SetSockets quality clamp (magic 4, rare 2; items/0007) build refuses, unless the item
        carries "unclamped_sockets": true; normal items have no quality clamp."""
        refused = [dict(code="crs", suffix=260, sockets=5), dict(code="crs", suffix=260, sockets=6),
                   dict(code="crs", rare=[160, 121], sockets=3)]
        for spec in refused:
            with self.subTest(spec=spec), self.assertRaises(d2s.D2sError) as cm:
                self.build(dict(stats={"level": 1}, items=[dict(spec, store="inventory", x=0, y=0)]))
            self.assertIn("unclamped_sockets", str(cm.exception))
        b, f = self.build(dict(stats={"level": 1}, items=[
            dict(code="crs", suffix=260, sockets=4, store="inventory", x=0, y=0),
            dict(code="crs", suffix=260, sockets=6, unclamped_sockets=True, store="inventory", x=2, y=0),
            dict(code="crs", rare=[160, 121], sockets=2, store="inventory", x=4, y=0),
            dict(code="crs", rare=[160, 121], sockets=3, unclamped_sockets=True, store="inventory", x=6, y=0),
            dict(code="crs", sockets=6, store="stash", x=0, y=0)]))
        got = [(i["quality"], i["sockets"]) for i in self.items(f)]
        self.assertEqual(got, [(4, 4), (4, 6), (6, 2), (6, 3), (2, 6)])
        self.assertEqual(d2s.roundtrip(EXCEL, [self.path("out.d2s")]), 0)

    def test_rare(self):
        b, f = self.build(dict(stats={"level": 1}, items=[
            dict(code="rin", rare=[160, 121], store="inventory", x=0, y=0),
            dict(code="amu", rare=[171, 135], suffix=277, store="inventory", x=1, y=0)]))
        rin, amu = self.items(f)
        self.assertEqual((rin["quality"], rin["names"], rin["affixes"], rin["props"]),
                         (6, (160, 121), [None] * 6, []))
        self.assertEqual((amu["quality"], amu["affixes"][1]), (6, 277))
        self.assertTrue(amu["props"])
        self.assertEqual(d2s.roundtrip(EXCEL, [self.path("out.d2s")]), 0)
        with self.assertRaises(d2s.D2sError):
            self.build(dict(stats={"level": 1}, items=[dict(code="rin", rare=[300, 1], store="inventory", x=0, y=0)]))

    def test_equipped_socketed_weapon_moves_with_children(self):
        b, f = self.build(dict(stats={"level": 1}, items=[
            dict(code="crs", equip="rarm", sockets=3, filled=[dict(code="r03"), dict(code="r01")]),
            dict(code="cap", equip="head")]))
        codes = [i.get("code", "").strip() for i in self.items(f)]
        self.assertEqual(codes, ["cap", "crs", "r03", "r01"])

    def test_quality_and_unidentified_test_states(self):
        b, f = self.build(dict(stats={"level": 1}, items=[
            dict(code="cap", store="inventory", x=0, y=0, sockets=2, quality="low"),
            dict(code="sml", store="inventory", x=2, y=0, sockets=2, quality="superior", qdata=1),
            dict(code="ssd", store="inventory", x=4, y=0, sockets=2, quality="rare"),
            dict(code="ssd", store="inventory", x=5, y=0, sockets=2, quality="crafted", names=[157, 3]),
            dict(code="jew", suffix=260, store="inventory", x=6, y=0, identified=False)]))
        cap, sml, rare, crf, jew = self.items(f)
        self.assertEqual((cap["quality"], cap["qdata"], cap["sockets"]), (1, 0, 2))
        self.assertEqual((sml["quality"], sml["qdata"]), (3, 1))
        self.assertEqual((rare["quality"], rare["names"], rare["affixes"]), (6, (160, 121), [None] * 6))
        self.assertEqual((crf["quality"], crf["names"]), (8, (157, 3)))
        self.assertEqual((jew["identified"], cap["identified"]), (0, 1))
        self.assertEqual(d2s.roundtrip(EXCEL, [self.path("out.d2s")]), 0)
        for spec in (dict(code="cap", quality="magic"), dict(code="cm1", suffix=290, quality="low")):
            with self.subTest(spec=spec), self.assertRaises(d2s.D2sError):
                self.build(dict(stats={"level": 1}, items=[dict(spec, store="inventory", x=0, y=0)]))

    def test_keep_socketed_item(self):
        need(BASE_RW)
        base = readb(BASE_RW)
        fb = d2s.parse(base, tables().isc, tables().kinds)
        sword = [i for i in self.items(fb) if i.get("code", "").strip() == "lsd"]
        self.assertEqual(sword[0]["n_filled"], 2)
        b, f = self.build(dict(stats={"level": 1}, keep_items=["lsd"]), base=BASE_RW)
        its = self.items(f)
        self.assertEqual([i.get("code", "").strip() for i in its], ["lsd", "r03", "r01"])
        old = base[sword[0]["off"]:sword[0]["off"] + sum(i["end"] - i["off"] for i in self.items(fb)
                                                        if i is sword[0] or i.get("parent") == sword[0]["off"])]
        new = b[its[0]["off"]:its[-1]["end"]]
        self.assertEqual(old, new)


BASE_C_SRC = os.path.join(WS, "runtime", "monspawn-chars", "exphell", "smpsor.d2s")  # BASE_C before conversion


class ClassicTest(Scratch):
    def test_reproduces_classic_base(self):
        need(BASE_C_SRC, BASE_C)
        t = tables()
        out = bytearray(d2s.to_classic(readb(BASE_C_SRC), t.isc, t.kinds))
        out[0x25] = 8
        self.assertEqual(bytes(d2s.finish(out)), readb(BASE_C))

    def test_refusals(self):
        need(BASE_C)
        t = tables()
        with self.assertRaises(d2s.D2sError) as cm:
            d2s.to_classic(readb(BASE_C), t.isc, t.kinds)
        self.assertIn("already classic", str(cm.exception))

    def test_levelup_saves(self):
        need(os.path.join(WS, "samples", "d2s", "smpama.d2s"))
        import levelup_saves
        runs = []
        for k in range(2):
            out = self.path("run%d" % k)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                self.assertEqual(levelup_saves.main([EXCEL, out, "2", "98"]), 0)
            runs.append(buf.getvalue())
        self.assertEqual(runs[0], runs[1])
        self.assertEqual(len(runs[0].splitlines()), 2 * (7 + 5))
        t = tables()
        f = d2s.parse(readb(self.path("run0/XpBarBc/XpBarBc.d2s")), t.isc, t.kinds)
        stats = {s: v for s, _, v in f["stats"]}
        self.assertEqual((f["header"]["level"], stats[12], stats[13]), (97, 97, 3229426755))
        self.assertEqual(f["header"]["status"] & 0x20, 0)


class QuestBitsTest(Scratch):
    def build_rc(self, extra, base=BASE_X):
        need(base)
        rp, out = self.path("q.json"), self.path("q.d2s")
        with open(rp, "w") as fh:
            json.dump(dict(dict(game="expansion", seed=1, stats={"level": 1}), **extra), fh)
        d2s.build(EXCEL, rp, base, out)
        return readb(out)

    def changed(self, b, base=BASE_X):
        old, new = d2s.quest_words(readb(base)), d2s.quest_words(b)
        return {(d, q, x, new[d][q] >> x & 1) for d in range(3) for q in range(d2s.QUEST_WORD_COUNT)
                for x in range(16) if (old[d][q] ^ new[d][q]) >> x & 1}

    def test_exact_bits(self):
        b = self.build_rc({"quest_bits": {"normal": {"3": [1], "35": {"set": [1, 3]}}, "hell": {"47": [15]}}})
        self.assertEqual(self.changed(b), {(0, 3, 1, 1), (0, 35, 1, 1), (0, 35, 3, 1), (2, 47, 15, 1)})

    def test_clear_after_quests(self):
        plain = self.changed(self.build_rc({"quests": ["nightmare"]}))
        b = self.build_rc({"quests": ["nightmare"], "quest_bits": {"nightmare": {"26": {"clear": [0]}}}})
        self.assertEqual(self.changed(b), plain - {(1, 26, 0, 1)})
        self.assertIn((1, 26, 0, 1), plain)

    def test_refusals(self):
        for qb, word in (({"normal": {"48": [0]}}, "word"), ({"normal": {"3": [16]}}, "bit"),
                         ({"normal": {"3": {"set": [1], "clear": [1]}}}, "both"),
                         ({"normal": {"3": {"toggle": [1]}}}, "give a list"), ({"easy": {"3": [1]}}, "difficulty")):
            with self.subTest(qb=qb):
                with self.assertRaises(d2s.D2sError) as cm:
                    self.build_rc({"quest_bits": qb})
                self.assertIn(word, str(cm.exception))

    def test_simple_quest_item_needs_quest_diff(self):
        with self.assertRaises(d2s.D2sError) as cm:
            self.build_rc({"items": [{"code": "mss", "store": "inventory", "x": 0, "y": 0}]})
        self.assertIn("quest_diff", str(cm.exception))
        b = self.build_rc({"items": [{"code": "mss", "store": "inventory", "x": 0, "y": 0, "quest_diff": 2}]})
        t = tables()
        mss = [it for it in d2s.parse(b, t.isc, t.kinds)["items"]["items"] if it["code"].strip() == "mss"]
        self.assertEqual([it["quest_diff"] for it in mss], [2])

    def test_quest_saves_check(self):
        """plan 0042 Phase 0: every plan 0042 recipe holds the state of its EXPECT row (tools/quest_saves.py check),
        and every recipe of the set builds into <Name>/<Name>.d2s."""
        need(BASE_C)
        import quest_saves
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(quest_saves.main(["check", EXCEL]), 0, buf.getvalue())
        self.assertIn("SURVEY quest_saves recipes=33 bad=0", buf.getvalue())
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(quest_saves.main(["build", EXCEL, self.path("set")]), 0)
        self.assertTrue(os.path.exists(self.path("set/ActFourDurance/ActFourDurance.d2s")))
        self.assertEqual(len(os.listdir(self.path("set"))), len(quest_saves.SET))

    def test_mp_saves_check(self):
        """plan 0044 Phase 2: every two-client pair holds the state of its cases (tools/mp_saves.py check), and
        every recipe of the set builds into <Name>/<Name>.d2s."""
        need(BASE_X, BASE_PAL)
        import mp_saves
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(mp_saves.main(["check", EXCEL]), 0, buf.getvalue())
        self.assertIn("SURVEY mp_saves recipes=30 bad=0 pairs=21 pairs_bad=0", buf.getvalue())
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(mp_saves.main(["build", EXCEL, self.path("mp")]), 0)
        self.assertEqual(len(os.listdir(self.path("mp"))), len(mp_saves.SET))


class MercTest(Scratch):
    MERC = dict(id=0, seed=12345, name=3, exp=2790000,
                items=[dict(code="sbw", equip="rarm"), dict(code="lea", equip="tors"), dict(code="cap", equip="head")])

    def build(self, merc, base=BASE_X):
        need(base)
        rp, out = self.path("r.json"), self.path("out.d2s")
        game = "classic" if base == BASE_C else "expansion"
        with open(rp, "w") as fh:
            json.dump(dict(seed=1, game=game, stats={"level": 30}, merc=merc), fh)
        d2s.build(EXCEL, rp, base, out)
        b = readb(out)
        return out, b, d2s.parse(b, tables().isc, tables().kinds)

    def refused(self, merc, word, base=BASE_X):
        with self.assertRaises(d2s.D2sError) as cm:
            self.build(merc, base)
        self.assertIn(word, str(cm.exception))

    def test_header_and_items(self):
        out, b, f = self.build(self.MERC)
        h = f["header"]
        self.assertEqual((h["merc_seed"], h["merc_name"], h["merc_type"], h["merc_exp"], h["merc_dead"]),
                         (12345, 3, 0, 2790000, 0))
        items = f["merc_items"]["items"]
        self.assertEqual([i["code"].strip() for i in items], ["lea", "cap", "sbw"])   # hand item last
        self.assertTrue(all(i["location"] == 1 for i in items))
        self.assertEqual(f["end"], len(b))
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(d2s.roundtrip(EXCEL, [out]), 0)

    def test_dead_flag(self):
        _, b, f = self.build(dict(self.MERC, dead=True, items=[]))
        self.assertEqual(d2s.u32(b, 0xAF), 0x10000)
        self.assertEqual(f["merc_items"]["count"], 0)

    def test_classic_header_only(self):
        _, b, f = self.build(dict(id=0, seed=7, exp=100), BASE_C)
        self.assertEqual((f["header"]["merc_seed"], f["header"]["merc_type"]), (7, 0))
        self.assertNotIn("merc_items", f)
        self.refused(dict(self.MERC), "classic", BASE_C)

    def test_refusals(self):
        self.refused(dict(self.MERC, id=99), "no hireling.txt row")
        self.refused(dict(self.MERC, seed=0), "seed")
        self.refused(dict(self.MERC, name=41), "name 41 outside 0 .. 40")
        self.refused(dict(self.MERC, items=[dict(code="cap", store="inventory", x=0, y=0)]), "equip")
        self.refused(dict(self.MERC, level=3), "unknown key")

    def test_name_unchecked_test_state(self):
        """backlog 2026-10-27 (plan 0038 H1b row 48): "name_unchecked" writes a name id past the row's range as
        given; it is still refused outside the u16, and the default stays the range check."""
        out, b, f = self.build(dict(self.MERC, name=41, name_unchecked=True))
        self.assertEqual(f["header"]["merc_name"], 41)
        self.assertEqual(struct.unpack_from("<H", b, 0xB7)[0], 41)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(d2s.roundtrip(EXCEL, [out]), 0)
        self.refused(dict(self.MERC, name=0x10000, name_unchecked=True), "u16")
        self.refused(dict(self.MERC, name=-1, name_unchecked=True), "u16")
        self.refused(dict(self.MERC, name=41, name_unchecked=False), "name 41 outside 0 .. 40")


class ExtendedTest(Scratch):
    """backlog 2026-10-27 (plan 0038 H1a gaps): the extended reading and writing (versions 93..95, the old stat
    form, the stat-slot and skill counts, realm data, an ear's realm bit), off unless asked for."""
    QITSOR = os.path.join(SAMPLES, "qitsor.d2s")
    STATS = {"0": 10, "1": 35, "2": 25, "3": 10, "6": 40, "7": 40, "8": 35, "9": 35, "10": 74, "11": 74, "12": 1}
    KEEP = ["hp1", "tsc", "box", "rin", "amu", "jew", "cm1", "cap", "lgl", "sst"]

    def build(self, recipe, base=None, name="out.d2s"):
        base = base or self.QITSOR
        need(base)
        out = self.path(name)
        d2s.build(EXCEL, dict(dict(seed=1, game="expansion"), **recipe), base, out)
        return readb(out)

    def ext(self, b):
        return d2s.parse(b, tables().isc, tables().kinds, extended=True)

    def items_round_trip(self, b, f):
        t = tables()
        for it in d2s.all_items(f):
            self.assertEqual(d2s.encode_item(it, t.isc, t.kinds, f["ver"]), b[it["off"]:it["end"]])

    def test_h1a_cases_rebuilt_byte_for_byte(self):
        """The v94, v94s12 and skills29 saves of tools/h1a_saves.py (loaded in run:2026-10-27-sweep-d2s-load) come
        out of build with the new keys byte for byte."""
        import h1a_saves
        ref = self.path("h1a")
        with contextlib.redirect_stdout(io.StringIO()):
            h1a_saves.main([EXCEL, ref])
        keep = dict(keep_items=self.KEEP)
        cases = {"v94": dict(keep, stats=self.STATS, save_version=94),
                 "v94s12": dict(keep, stats={k: v for k, v in self.STATS.items() if int(k) < 12}, save_version=94,
                                stat_slots=12),
                 "skills29": dict(keep, stats=self.STATS, name="QITSOR", skills={"Fire Bolt": 1, "Frozen Orb": 1},
                                  skill_count=29)}
        for case, rc in cases.items():
            with self.subTest(case=case):
                b = self.build(rc, name=case + ".d2s")
                self.assertEqual(b, readb(os.path.join(ref, case, "qitsor.d2s")))
                f = self.ext(b)
                self.assertEqual(f["end"], len(b))
                self.items_round_trip(b, f)
        # the items case (realm data on the gloves, an ear) reads and re-encodes item by item
        b = readb(os.path.join(ref, "items", "qitsor.d2s"))
        f = self.ext(b)
        self.assertEqual(f["end"], len(b))
        self.items_round_trip(b, f)
        realm = [it["realm_data"] for it in d2s.all_items(f) if it.get("realm")]
        self.assertEqual(realm, [[0x11223344, 0x55667788, 0x99AABBCC]])
        ears = [it for it in d2s.all_items(f) if it["ear"]]
        self.assertEqual([(e["ear_class"], e["ear_level"], e["ear_name"], e["realm"]) for e in ears],
                         [(3, 42, "earname", 0)])

    def test_default_reading_unchanged(self):
        """Without extended the parser refuses what it refused before: a version other than 96, realm data, and a
        skill count other than 30 (read as 30 bytes, so the item list tag is missed)."""
        t = tables()
        for rc, word in ((dict(stats=self.STATS, keep_items=self.KEEP, save_version=94), "version 94"),
                         (dict(stats=self.STATS, keep_items=self.KEEP, skill_count=29), "item list tag"),
                         (dict(stats=self.STATS, items=[dict(code="lgl", store="inventory", x=6, y=0,
                                                             realm=[1, 2, 3])]), "realm data")):
            with self.subTest(word=word):
                b = self.build(rc)
                with self.assertRaises(d2s.D2sError) as cm:
                    d2s.parse(b, t.isc, t.kinds)
                self.assertIn(word, str(cm.exception))
                self.assertEqual(self.ext(b)["end"], len(b))

    def test_realm_words_by_version(self):
        lgl = dict(code="lgl", store="inventory", x=6, y=0)
        for ver, words in ((96, [7, 8, 0]), (95, [7, 8, 9]), (94, [1, 2, 0]), (93, [5, 6])):
            with self.subTest(ver=ver):
                b = self.build(dict(stats=self.STATS, save_version=ver, items=[dict(lgl, realm=words)]))
                f = self.ext(b)
                self.assertEqual(d2s.u32(b, 4), ver)
                self.assertEqual([it["realm_data"] for it in d2s.all_items(f) if it.get("realm")], [words])
                self.items_round_trip(b, f)
        for ver, words in ((96, [7, 8]), (93, [5, 6, 0])):
            with self.subTest(refused=ver):
                with self.assertRaises(d2s.D2sError) as cm:
                    self.build(dict(stats=self.STATS, save_version=ver, items=[dict(lgl, realm=words)]))
                self.assertIn("words for version %d" % ver, str(cm.exception))
        with self.assertRaises(d2s.D2sError):
            self.build(dict(stats=self.STATS, items=[dict(lgl, realm=[1 << 32, 0, 0])]))
        # a simple item takes realm data too (the realm bit after its code)
        b = self.build(dict(stats=self.STATS, items=[dict(code="hp1", store="inventory", x=6, y=0, realm=[3, 4, 0])]))
        self.assertEqual([it["realm_data"] for it in d2s.all_items(self.ext(b)) if it.get("realm")], [[3, 4, 0]])

    def test_ear_realm_bit(self):
        """An ear's realm bit after the name: one more byte only when the name ends on a byte boundary
        (5 or 13 characters in the stored/equipped common part); the default encoder writes none."""
        t = tables()
        for n in range(2, 16):
            with self.subTest(n=n):
                ear = dict(flags=(1 << 4) | (1 << 16) | (1 << 21) | (1 << 23), version=101, location=0, body=0, x=0,
                           y=0, store=1, ear_class=3, ear_level=42, ear_name="e" * n)
                old, new = d2s.encode_item(ear, t.isc, t.kinds), d2s.encode_item(ear, t.isc, t.kinds, 96)
                self.assertEqual(len(new) - len(old), 1 if n in (5, 13) else 0)
                self.assertEqual(new[:len(old)], old)
                it, end = d2s.parse_item(new, 0, t.isc, t.kinds, 96)
                self.assertEqual((it["ear_name"], it["realm"], end), ("e" * n, 0, len(new)))
                rd = dict(ear, realm=1, realm_data=[9, 10, 0])
                it, end = d2s.parse_item(d2s.encode_item(rd, t.isc, t.kinds, 96), 0, t.isc, t.kinds, 96)
                self.assertEqual(it["realm_data"], [9, 10, 0])

    def test_durability_width(self):
        """Stat 72 is 8 bits for a save version <= 95, Save Bits (9) at 96; v95 keeps the bit-form stats."""
        t = tables()
        rc = dict(stats=self.STATS, items=[dict(code="lgl", store="inventory", x=6, y=0, dur=5)])
        for ver in (95, 96):
            with self.subTest(ver=ver):
                b = self.build(dict(rc, save_version=ver))
                f = self.ext(b)
                self.assertEqual(b[d2s.HEADER_SIZE:d2s.HEADER_SIZE + 2], b"gf")
                self.assertEqual(sorted(s for s, _, _ in f["stats"]), sorted(int(k) for k in self.STATS))
                gl = [it for it in d2s.all_items(f) if it.get("code") == "lgl "]
                self.assertEqual([it["dur"] for it in gl], [5])
                self.items_round_trip(b, f)
        with self.assertRaises(d2s.D2sError):    # 256 does not fit the 8-bit width
            d2s.encode_item(dict(gl[0], dur=256), t.isc, t.kinds, 95)
        d2s.encode_item(dict(gl[0], dur=256), t.isc, t.kinds, 96)

    def test_old_stat_form(self):
        b = self.build(dict(stats=self.STATS, save_version=93))
        f = self.ext(b)
        mask = struct.unpack_from("<H", b, d2s.HEADER_SIZE + 2)[0]
        self.assertEqual(mask, sum(1 << int(k) for k in self.STATS))
        self.assertEqual(f["stats"], [(int(k), None, v << 8 if 6 <= int(k) <= 11 else v)
                                      for k, v in sorted(self.STATS.items(), key=lambda kv: int(kv[0]))])
        self.assertEqual(b[d2s.HEADER_SIZE + 4 + 4 * len(self.STATS):][:2], b"if")

    def test_refusals(self):
        def refused(rc, word, base=None):
            with self.assertRaises(d2s.D2sError) as cm:
                self.build(dict(dict(stats=self.STATS), **rc), base)
            self.assertIn(word, str(cm.exception))
        refused(dict(save_version=91), "71, 87, 92")    # backlog 2026-10-27: 71, 87 and 92 are built now
        refused(dict(save_version=70), "71, 87, 92")
        refused(dict(save_version=97), "93..96")
        refused(dict(save_version=94, stat_slots=8), "9..16")
        refused(dict(save_version=94, stat_slots=12), "stat 12")
        refused(dict(save_version=94, stat_slots=13, stats=dict(self.STATS, experience=1)), "stat 13")
        refused(dict(skill_count=29, skills={"Cold Mastery": 1}), "cuts off")
        refused(dict(skill_count=300), "a byte")
        # a base whose trailer holds mercenary items (version-96 widths) is refused for another version
        merc = os.path.join(self.tmp, "merc.d2s")
        need(BASE_X)
        d2s.build(EXCEL, dict(seed=1, game="expansion", stats={"level": 30},
                              merc=dict(id=0, seed=5, name=3, exp=100, items=[dict(code="cap", equip="head")])),
                  BASE_X, merc)
        refused(dict(save_version=95), "mercenary", merc)
        self.build(dict(stats=self.STATS, save_version=95, merc=dict(id=0, seed=5, name=3, exp=100, items=[])),
                   merc, "merc95.d2s")   # replaced by the recipe's merc: written in the version's widths
        # a 92 file is read by the extended reader only (LegacyTest builds and reads real ones)
        b = bytearray(self.build(dict(stats=self.STATS)))
        struct.pack_into("<I", b, 4, 92)
        with self.assertRaises(d2s.D2sError) as cm:
            d2s.parse(d2s.finish(b), tables().isc, tables().kinds)
        self.assertIn("version 92", str(cm.exception))

    def test_skill_count_over_30(self):
        b = self.build(dict(stats=self.STATS, skill_count=32))
        f = self.ext(b)
        self.assertEqual((b[0x2A], len(f["skills"]), f["skills"][30:]), (32, 32, [0, 0]))
        self.assertEqual(f["end"], len(b))


class LegacyTest(Scratch):
    """backlog 2026-10-27 (reverser -> archivist, the d2s legacy layouts): save_version 71, 87 and 92, built from the
    static reading of save/0001 § Plan 0038 lane/rlg and read back with d2s.parse_legacy (71, 87) or the extended
    parser (92). No file of these versions has been loaded by the game: these tests check the builder against the
    layout as d2s.md states it, not the layout against the game."""
    STATS = {"strength": 30, "energy": 10, "dexterity": 20, "vitality": 25, "hitpoints": 100, "maxhp": 100,
             "mana": 50, "maxmana": 50, "stamina": 80, "maxstamina": 80, "level": 20, "experience": 300000}
    MOUSE = {"left": "Charged Bolt", "right": "Teleport", "swap_left": "Nova", "swap_right": "Static Field"}
    HOT = ["Teleport", "Nova", "Frost Nova", "Static Field", "Telekinesis", "Charged Bolt", "Teleport", "Nova",
           "Frost Nova"]

    def build(self, recipe, name="out.d2s"):
        need(BASE_X)
        out = self.path(name)
        d2s.build(EXCEL, dict(dict(seed=1, game="expansion", stats=self.STATS), **recipe), BASE_X, out)
        return readb(out)

    def legacy(self, b):
        t = tables()
        f = d2s.parse_legacy(b, t.isc, t.kinds, d2s.classic_codes(t))
        self.assertEqual(f["end"], len(b))
        return f

    def refused(self, rc, word):
        with self.assertRaises(d2s.D2sError) as cm:
            self.build(rc)
        self.assertIn(word, str(cm.exception))

    def sections(self, b):
        """Offsets of the legacy sections after the header, checked tag by tag (lane/rlg (a), Order and framing)."""
        p = d2s.LEGACY_HEADER_SIZE
        self.assertEqual(b[p:p + 4], b"Woo!")
        self.assertEqual(d2s.u32(b, p + 4), 6)
        p += 0x12A
        self.assertEqual(b[p:p + 2], b"WS")
        p += 0x50
        self.assertEqual(b[p:p + 2], b"\x01w")
        p += 0x34
        self.assertEqual(b[p:p + 2], b"gf")
        mask = int.from_bytes(b[p + 2:p + 5], "little")
        p += 5 + 4 * bin(mask).count("1")
        self.assertEqual(b[p:p + 2], b"if")
        return mask, p + 32

    def test_v87_layout(self):
        b = self.build(dict(save_version=87, skills={"Teleport": 1, "Nova": 1}, mouse=self.MOUSE, hotkeys=self.HOT,
                            items=[dict(code="cap", store="inventory", x=0, y=0, item_stats={"39": 20, "74": 3}),
                                   dict(unique="The Gnasher", store="inventory", x=2, y=0)],
                            merc=dict(id=1, seed=1234, name=2, exp=5000, dead=True,
                                      items=[dict(code="cap", equip="head")])))
        t = tables()
        self.assertEqual((d2s.u32(b, 0), d2s.u32(b, 4), d2s.u16(b, 0x20), d2s.u16(b, 0x22)), (d2s.MAGIC, 87, 0x82, 1))
        mask, p = self.sections(b)
        self.assertEqual(mask, sum(1 << t.stat_id(k) for k in self.STATS))
        f = self.legacy(b)
        h = f["header"]
        self.assertEqual((h["status"] & 0x21, h["level"], h["left"], h["right"]),
                         (0x20, 20, t.skills["Charged Bolt"]["id"], t.skills["Teleport"]["id"]))
        self.assertEqual([s for s, _ in h["hotkeys"]], [t.skills[n]["id"] for n in self.HOT[:8]])
        self.assertEqual(f["hotkeys_tail"][0][0], t.skills[self.HOT[8]]["id"])
        self.assertEqual(f["hotkeys_tail"][1][0], -1)
        self.assertEqual(f["swap"], (t.skills["Nova"]["id"], t.skills["Static Field"]["id"]))
        self.assertEqual(f["merc"], dict(dead=1, seed=1234, name=2, id=1, exp=5000))
        self.assertEqual([it["code"] for it in f["merc_items"]["items"]], ["cap "])
        cap, gn = f["items"]["items"]
        self.assertEqual(cap["props"], [(39, None, [20]), (74, None, [3])])
        self.assertEqual((gn["quality"], gn["qid"]), (7, t.unique("The Gnasher")[0]))
        for it in f["items"]["items"] + f["merc_items"]["items"]:    # each record re-encodes byte for byte
            self.assertEqual(d2s.encode_item(it, t.isc, t.kinds, 87), b[it["off"]:it["end"]])
        # stat 74 at <= 89: 5 bits, add 10 (the 1.09 column: 6 bits, add 30)
        w = d2s.BitWriter()
        d2s.encode_props_109(w, [(74, None, [3])], t.isc, 87)
        self.assertEqual((len(w.bits), d2s.Bits(w.tobytes()).read(14)), (9 + 5 + 9, 74 | 13 << 9))
        # the corpse list (JM, count 0) and the 0x12-byte mercenary follow the item list
        c = f["items"]["items"][-1]["end"]
        self.assertEqual(b[c:c + 4], b"JM\0\0")
        self.assertEqual((b[c + 4], d2s.u32(b, c + 6)), (1, 0x10000))
        self.assertEqual(len(b) - f["merc_items"]["items"][-1]["end"], 0x38)   # the hotkey tail, >= 82

    def test_v87_new_char_and_refusals(self):
        b = self.build(dict(save_version=87, legacy_new_char=True))
        self.assertEqual(d2s.u32(b, 0x18) & 1, 1)
        f = self.legacy(b)
        seed = d2s.u32(readb(BASE_X), 0xB3)     # the base's mercenary header, carried into the legacy record
        self.assertEqual(f["merc"] and f["merc"]["seed"], seed or None)
        self.refused(dict(legacy_new_char=True), "legacy_new_char")
        self.refused(dict(save_version=87, items=[dict(code="cap", suffix=290, store="inventory", x=0, y=0)]),
                     "magic, rare")
        self.refused(dict(save_version=87, items=[dict(code="cap", store="inventory", x=0, y=0,
                                                       item_stats={"93": 10})]), "older override")
        self.refused(dict(save_version=87, stat_slots=16), "header fields")
        self.refused(dict(save_version=87, stats=dict(self.STATS, **{"16": 1})), "stats 0..15")

    def test_v71_layout(self):
        t = tables()
        classic = d2s.classic_codes(t)
        b = self.build(dict(save_version=71, mouse=self.MOUSE, hotkeys=self.HOT,
                            items=[dict(unique="The Gnasher", store="inventory", x=0, y=0),
                                   dict(set="Civerb's Ward", store="stash", x=2, y=0),
                                   dict(code="jew", store="inventory", x=4, y=0, v71=dict(unit_seed=7)),
                                   dict(code="hp1", belt_slot=3)],
                            merc=dict(id=1, seed=1234, name=2, exp=5000)))
        self.assertEqual(d2s.u32(b, 4), 71)
        _, p = self.sections(b)
        self.assertEqual((b[p:p + 2], d2s.u16(b, p + 2)), (b"JM", 4))
        f = self.legacy(b)
        gn, cw, jw, hp = f["items"]["items"]
        self.assertEqual([it["end"] - it["off"] for it in (gn, cw, hp)], [27, 27, 27])   # JM + 25 (index form)
        self.assertEqual((gn["form"], gn["index"], gn["code"], gn["quality"], gn["file_index"]),
                         ("index", classic.index("hax"), "hax ", 7, t.unique("The Gnasher")[0]))
        self.assertEqual((cw["quality"], cw["file_index"], cw["page"]), (5, t.setitem("Civerb's Ward")[0], 4))
        self.assertEqual((jw["form"], jw["code"], jw["unit_seed"], jw["end"] - jw["off"]), ("code", "jew ", 7, 2 + 29))
        self.assertEqual(jw["flags"] & 0x300000, 0x100000)
        self.assertEqual((hp["location"], hp["x"], hp["flags"] & 0x200000), (2, 3, 0))
        self.assertEqual(f["merc"], dict(seed=1234, name=2))
        self.assertEqual(b[f["items"]["items"][-1]["end"]:][:4], b"JM\0\0")
        self.assertEqual(len(b) - f["items"]["items"][-1]["end"], 4 + 8)       # corpses, mercenary, no tail
        self.refused(dict(save_version=71, merc=dict(id=1, seed=5, name=2, items=[dict(code="cap", equip="head")])),
                     "no item list")
        self.refused(dict(save_version=71, items=[dict(code="hp1", belt_slot=0, seed=3),
                                                  dict(code="hp1", belt_slot=1, seed=3)]), "skips the second")
        self.refused(dict(save_version=87, items=[dict(code="cap", store="inventory", x=0, y=0, v71={})]),
                     "needs save_version 71")
        self.refused(dict(save_version=71, items=[dict(code="jew", store="inventory", x=0, y=0,
                                                       v71=dict(form="index"))]), "no version-0 row")

    def test_v92_build_and_read(self):
        t = tables()
        props = [[83, 1, 2], [107, 54, 3], [188, 8, 2], [195, 48 << 6 | 3, 10], [126, 1, 2]]
        b = self.build(dict(save_version=92, items=[
            dict(code="cap", store="inventory", x=0, y=0, item_stats={"0": 5, "39": 20}, item_props=props),
            dict(set="Civerb's Ward", store="inventory", x=2, y=0)]))
        self.assertEqual((d2s.u32(b, 4), d2s.checksum(b), d2s.u32(b, 8)), (92, d2s.u32(b, 12), len(b)))
        f = d2s.parse(b, t.isc, t.kinds, extended=True)
        self.assertEqual(f["end"], len(b))
        cap = [it for it in f["items"]["items"] if it.get("code") == "cap "][0]
        self.assertEqual(sorted(cap["props"]), sorted([(0, None, [5]), (39, None, [20])] +
                                                      [(s, p, [v]) for s, p, v in props]))
        cw = [it for it in f["items"]["items"] if it.get("code") == "lrg "][0]
        self.assertEqual(cw["qid"], 0)    # Civerb's Vestments, the Sets record, not the SetItems one
        for it in d2s.all_items(f):
            self.assertEqual(d2s.encode_item(it, t.isc, t.kinds, 92), b[it["off"]:it["end"]])
        # stat 39 is 8 bits with add 0 at 92 (1.09) against add 50 at 96: the raw field is the value itself
        w = d2s.BitWriter()
        d2s.encode_props_109(w, [(39, None, [20])], t.isc, 92)
        self.assertEqual(d2s.Bits(w.tobytes()).read(17), 39 | 20 << 9)
        cap_ = dict(code="cap", store="inventory", x=0, y=0)
        for extra, word in ((dict(item_stats={"97": 1}), "stores it as stat 99"),
                            (dict(item_props=[[151, 40, 3]]), "reads no param"),
                            (dict(item_props=[[204, 54 << 6 | 3, 5]]), "not writable"),
                            (dict(item_props=[[83, c, 2] for c in range(5)]), "folds"),
                            (dict(item_stats={"305": 5}), "no 1.09-Save Bits"),
                            (dict(item_props=[[107, 54, 8]]), "stat 107")):
            with self.subTest(word=word):
                self.refused(dict(save_version=92, items=[dict(cap_, **extra)]), word)

    def test_skill_byte(self):
        self.assertEqual([d2s.skill_byte(s) for s in (0, 155, 217, 221, 281, -1)], [0, 155, 217, 0x9C, 0xD8, 0xFF])
        self.assertEqual([d2s.unskill_byte(x) for x in (0, 155, 0x9C, 0xD8, 0xD9, 0xFF)], [0, 155, 221, 281, 0xD9, -1])
        for s in (156, 216, 282):
            with self.assertRaises(d2s.D2sError):
                d2s.skill_byte(s)


class ExcelEditTest(Scratch):
    def run_edit(self, table, *edits):
        out = self.path("out")
        rc = excel_edit.main([EXCEL, table, out] + list(edits))
        return rc, out

    def test_edit_changes_only_the_cells(self):
        need()
        rc, out = self.run_edit("itemratio", "*:Unique=0", "2:SetMin=900")
        self.assertEqual(rc, 0)
        old = readb(os.path.join(EXCEL, "itemratio.bin"))
        new = readb(os.path.join(out, "itemratio.bin"))
        self.assertEqual(len(old), len(new))
        count, size = struct.unpack_from("<I", old)[0], len(old[4:]) // struct.unpack_from("<I", old)[0]
        fields = {f["col"]: f["off"] for f in excel_edit.excel_bin.get_layout("itemratio")["fields"] if "col" in f}
        want = bytearray(old)
        for r in range(count):
            struct.pack_into("<I", want, 4 + r * size + fields["Unique"], 0)
        struct.pack_into("<I", want, 4 + 2 * size + fields["SetMin"], 900)
        self.assertEqual(new, bytes(want))
        # the .txt pair: the same cells, every other line byte-identical
        told = readb(os.path.join(EXCEL, "itemratio.txt")).split(b"\n")
        tnew = readb(os.path.join(out, "itemratio.txt")).split(b"\n")
        self.assertEqual(len(told), len(tnew))
        self.assertEqual(told[0], tnew[0])
        head = told[0].rstrip(b"\r").split(b"\t")
        for lo, ln in zip(told[1:], tnew[1:]):
            a, b = lo.rstrip(b"\r").split(b"\t"), ln.rstrip(b"\r").split(b"\t")
            for i, (x, y) in enumerate(zip(a, b)):
                if x != y:
                    self.assertIn(head[i], (b"Unique", b"SetMin"))

    def test_refusals(self):
        need()
        for edit in ("0:Function=1",      # .txt-only column, not in the layout
                     "99:Unique=1",       # record outside the table
                     "0:Unique=-1",       # does not fit u32
                     "0:Unique",          # no value
                     "x:Unique=1"):       # record not an index
            with self.subTest(edit=edit):
                rc, out = self.run_edit("itemratio", edit)
                self.assertEqual(rc, 1)
                self.assertFalse(os.path.exists(out))
        rc, out = self.run_edit("montype", "8:equiv1=2")   # a ref field, not an integer one
        self.assertEqual(rc, 1)
        rc, out = self.run_edit("treasureclassex", "0:Item1=" + "x" * 64)   # longer than char[64] - 1
        self.assertEqual(rc, 1)

    def test_text_cell(self):
        need()
        rc, out = self.run_edit("treasureclassex", "200:Item1=The Oculus")
        self.assertEqual(rc, 0)
        old = readb(os.path.join(EXCEL, "treasureclassex.bin"))
        new = readb(os.path.join(out, "treasureclassex.bin"))
        off = {f["col"]: f["off"] for f in excel_edit.excel_bin.get_layout("treasureclassex")["fields"]
               if "col" in f}["Item1"]
        want = bytearray(old)
        o = 4 + 200 * 736 + off
        want[o:o + 64] = b"The Oculus".ljust(64, b"\0")
        self.assertEqual(new, bytes(want))


if __name__ == "__main__":
    unittest.main()
