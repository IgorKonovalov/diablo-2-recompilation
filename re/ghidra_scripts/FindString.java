// Find defined strings containing a substring (case-insensitive) and who references them.
// Usage (headless): -postScript FindString.java <out-file> <text> [<text> ...]
// Output: one line per string, then one indented line per reference:
//   0x<addr> "<string>"
//       <- 0x<from> in <function>@0x<entry>
// Only strings Ghidra's analysis defined are seen. If one is missing, check with r2 (izz).
// @category d2-recon

import java.io.PrintWriter;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Data;
import ghidra.program.model.listing.DataIterator;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Reference;

public class FindString extends GhidraScript {

	@Override
	public void run() throws Exception {
		String[] args = getScriptArgs();
		if (args.length < 2) throw new IllegalArgumentException("usage: FindString.java <out-file> <text>...");
		try (PrintWriter w = new PrintWriter(args[0])) {
			DataIterator it = currentProgram.getListing().getDefinedData(true);
			while (it.hasNext()) {
				Data d = it.next();
				if (!d.hasStringValue()) continue;
				String s = String.valueOf(d.getValue());
				String low = s.toLowerCase();
				boolean hit = false;
				for (int i = 1; i < args.length; i++) hit |= low.contains(args[i].toLowerCase());
				if (!hit) continue;
				w.printf("0x%08X \"%s\"%n", d.getAddress().getOffset(), s.replace("\n", "\\n"));
				for (Reference r : getReferencesTo(d.getAddress())) {
					Function in = getFunctionContaining(r.getFromAddress());
					w.printf("    <- 0x%08X in %s%n", r.getFromAddress().getOffset(),
						in == null ? "-" : String.format("%s@0x%08X", in.getName(), in.getEntryPoint().getOffset()));
				}
			}
		}
	}
}
