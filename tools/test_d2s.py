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
  its 14 recipes and build writes the whole set.
- MercTest (plan 0033 Phase 0) covers the "merc" key: the header fields 0xAF..0xBE, the mercenary item list after
  'jf' (equipped, hand item last) read back and round-trip byte for byte, the dead flag (bit 16), and the refusals
  (no row of the save's Version, seed 0, a name id past NameLast, items in a classic save, an item not placed with
  "equip").
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
RECIPES = os.path.join(HERE, "d2s_recipes")
P0005 = os.path.join(WS, "runtime", "saves-backup", "p0005")              # run:2026-10-16-calc bases (smp<cls>.d2s)
SAMPLES = os.path.join(WS, "samples", "d2s")                               # run:2026-10-16-player level-up bases

# recipe -> (base save, sha256 of the built save as a run record gives it, or None)
RECIPE_BASES = {
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
    "statsbar": (os.path.join(SAMPLES, "smpbar.d2s"), None),    # run:2026-10-17-stats
    "statsbarb": (os.path.join(SAMPLES, "smpbar.d2s"), None),   # run:2026-10-17-stats
    "statspal": (os.path.join(SAMPLES, "smppal.d2s"), None),    # run:2026-10-17-stats
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
    # the loaded revisions (7dfe9bc2..., 4e7b9134...) are the recipes at 32a1a6e. Not yet loaded: no pin.
    "questrewards": (BASE_X, None),
    "questrewardsh": (BASE_X, None),
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
    "vendornova": (BASE_X, "eed8939c568f3db4e471220571649af51be9a7417feb918cabcf41a20365bb5c"),  # run:2026-10-15-vendors
    "vendornova75": (BASE_X, "dc2ca9397496b485df54b0547def9023d83c4b68390cd8eb91727831e82cae67"),  # run:2026-10-15-vendors
    # plan 0042 Phase 0 (tools/quest_saves.py): not loaded yet; the first step of Phase 2 loads them and pins the hashes
    "questfreshc": (BASE_C, None),
    "travel-act2": (BASE_X, None),
    "travel-act3": (BASE_X, None),
    "travel-act4": (BASE_X, None),
    "travel-act5": (BASE_X, None),
    "travel-arcane": (BASE_X, None),
    "travel-tab2": (BASE_X, None),
    "travel-tab5d": (BASE_X, None),
    "travel-wp1": (BASE_X, None),
    "travel-wp2": (BASE_X, None),
    "travel-wp3": (BASE_X, None),
    "travel-wp4": (BASE_X, None),
    "travel-wp5": (BASE_X, None),
    "travel-wpnone": (BASE_X, None),
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
                self.assertEqual(d2s.checksum(b), d2s.u32(b, 12))
                self.assertEqual(d2s.parse(b, tables().isc, tables().kinds)["end"], len(b))
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
        """plan 0042 Phase 0: every Phase 0 recipe holds the state of its EXPECT row (tools/quest_saves.py check),
        and every recipe of the set builds into <Name>/<Name>.d2s."""
        need(BASE_C)
        import quest_saves
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(quest_saves.main(["check", EXCEL]), 0, buf.getvalue())
        self.assertIn("SURVEY quest_saves recipes=14 bad=0", buf.getvalue())
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(quest_saves.main(["build", EXCEL, self.path("set")]), 0)
        self.assertTrue(os.path.exists(self.path("set/ActFourDurance/ActFourDurance.d2s")))
        self.assertEqual(len(os.listdir(self.path("set"))), len(quest_saves.SET))


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
