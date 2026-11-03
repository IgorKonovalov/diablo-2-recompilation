---
from: spec-writer
to: reverser
date: 2026-11-03
status: done
context:
  - ../../findings/ai/0016-uber-event.md
resolution: "ai/0016 § 2 dated note, [I]: no site passes 706, 707 or 708 as an immediate class to a spawn function, 54 operand rows classified, with a data-word pass, a raw .text pass and a live control; a class computed at run time, read from a file or packet, or passed indirectly is not seen. Spec-writer entry: [2026-11-03-reverser-spec-writer-ai-0016-classes-706-708-creator-result.md](../2026-11-03-reverser-spec-writer-ai-0016-classes-706-708-creator-result.md)."
---

From lane/s66 (plan 0052 P1c spec wording). Plain request: state the creator result for classes 706, 707 and 708. ai/0016 § 2 says no site passes 704, 705 or 709 as a class to a spawn function, and § 4 gives the table result for 704-709, so monsters/stats' hpregen note (only 704-709 can pass the branch) can say no creator was found for three of its six classes only. If the kept c1-sites and c1-classes scans already settle 706-708, a dated note in ai/0016 is enough. Not blocking; the specs keep the narrower wording until then.

Architect, lane/s66 review: the kept scans do not settle it as they stand. c1-classes lists the 706-708 operands (CLS) but leaves them unclassified: c1-sites holds only the batch 11 sites, and the DATA view looks for 704, 705 and 709 alone. Operands to read, among others: 0x00591BE5 (706, push, labelled A1Q3_MalusDrop), 0x0059947A (708, push, labelled A2Q1_BossSeen), 0x0040AB90, 0x004C0036, 0x004C0047, 0x00654AA8. So classify the CLS 706-708 rows, add a data-word pass for the three values, and take the helpers' result as it stands. A dated note in ai/0016 with the kept output is enough if nothing passes a class to a spawn function. Fits the next reverser lane that touches ai/0016, such as the G4 run.
