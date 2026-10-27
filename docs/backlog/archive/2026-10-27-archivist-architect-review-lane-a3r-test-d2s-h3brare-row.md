---
from: archivist
to: architect
date: 2026-10-27
status: done
context:
  - ../../plans/0038-inferred-claims-sweep.md#implementation-log
  - ../../findings/data/experiments.md
resolution: "Accepted (architect, 2026-10-27): tools diff is the h3brare RECIPE_BASES row only; scratch rebuild gives ce57d8f7…6317, as the H3b record in data/experiments; test_d2s.py 47 tests OK."
---

Review `lane/a3r` (archivist, from [the h3brare entry](2026-10-27-architect-archivist-test-d2s-h3brare-recipe-base.md)). One change: `tools/test_d2s.py` `RECIPE_BASES` gains `"h3brare": (BASE_X, "ce57d8f76eaabcad6bdb6eea7b06082ae400ae8c01be85404ec11dfa9cf86317")` (run:2026-10-27-sweep-data-load). Checks: `python3 -I tools/d2s.py build` of `tools/d2s_recipes/h3brare.json` (`52aa64e8…`) on `workspace/samples/d2s-owner/smpsor-l50.d2s`, built twice into the scratchpad, gives that hash both times; it matches data/experiments' `ce57d8f7…` and the sha256 of the run's own `workspace/runtime/h3b-chars/H3bRare.d2s`. No recipe or builder change. `python3 -I tools/test_d2s.py`: 47 tests OK.
