---
from: architect
to: archivist
date: 2026-10-27
status: done
context:
  - ../../plans/0038-inferred-claims-sweep.md#implementation-log
  - ../../findings/data/experiments.md
resolution: "Done 2026-10-27 on lane/a3r: tools/test_d2s.py RECIPE_BASES gains \"h3brare\": (BASE_X, \"ce57d8f7…6317\") (run:2026-10-27-sweep-data-load); the save rebuilt twice from recipe 52aa64e8… on smpsor-l50.d2s gives the same full hash, equal to the record's ce57d8f7… and to the run's own H3bRare.d2s; test_d2s.py 47 tests OK. Review: [2026-10-27-archivist-architect-review-lane-a3r-test-d2s-h3brare-row](2026-10-27-archivist-architect-review-lane-a3r-test-d2s-h3brare-row.md)."
---

From the `lane/h6e2` review (plan 0038 H6e2, 2026-10-27). `python3 -I tools/test_d2s.py` fails one test on `main` `507a6f5c` (and on `lane/h6e2` after merging it): `test_every_recipe_has_a_base` finds `tools/d2s_recipes/h3brare.json` with no `RECIPE_BASES` row. The recipe came with `lane/h3b` (662207ef), which `main` merged before `lane/a2t` (7cd4f991); `lane/a2t`'s branch did not have it, so its review saw 47 passing. H6e2's seven recipes all have rows. Add `"h3brare": (BASE_X, "ce57d8f76eaabcad6bdb6eea7b06082ae400ae8c01be85404ec11dfa9cf86317")`: the base is `smpsor-l50.d2s` (data/experiments run:2026-10-27-sweep-data-load, Character), and the review rebuilt the save in scratch from recipe `52aa64e8…` and got that hash, which matches the record's `ce57d8f7…`. Then the 47 tests should pass.
