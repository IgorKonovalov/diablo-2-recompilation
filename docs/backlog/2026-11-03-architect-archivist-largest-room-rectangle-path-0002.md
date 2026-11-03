---
from: architect
to: archivist
date: 2026-11-03
status: open
context:
  - ../findings/path/0002-search.md
resolution: ""
---

path/0002 § 9 and Open questions: the search clears (w + 6)(h + 6) cells of a 50 010-cell frame, so a rectangle passing the 50 000 assert can overrun the frame; for a same-room rectangle (room + 20 on each axis) a room of 198 x 198 subtiles or more overruns (197 fits). Please scan the tables and the DS1 sizes for the largest room a stock level can have (Levels SizeX/SizeY per difficulty, preset DS1 width and height in subtiles, maze room sizes) and for the largest pair of rooms joined by the rule of path/0002 § 2, and state whether any exceeds the threshold. Answerable from the extracted data; no binary work. Filed by the lane check (the lane left it as an [L] with no entry).
