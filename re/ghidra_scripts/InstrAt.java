// For each address in a file, report what the listing has there.
// Usage (headless): -postScript InstrAt.java <out-file> <addr-file>
// <addr-file>: one hex address per line. Output, one line per address:
//   0x<addr> insn|data|undefined <function-or-"-"> <instruction text or data type>
// @category d2-recon

import java.io.PrintWriter;
import java.nio.file.Files;
import java.nio.file.Path;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Data;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;

public class InstrAt extends GhidraScript {

	@Override
	public void run() throws Exception {
		String[] args = getScriptArgs();
		if (args.length != 2) throw new IllegalArgumentException("usage: InstrAt.java <out-file> <addr-file>");
		try (PrintWriter w = new PrintWriter(args[0])) {
			for (String line : Files.readAllLines(Path.of(args[1]))) {
				line = line.trim();
				if (line.isEmpty()) continue;
				Address a = toAddr(Long.decode(line));
				Function fn = getFunctionContaining(a);
				String fname = fn == null ? "-" : fn.getName();
				Instruction ins = getInstructionAt(a);
				if (ins != null) {
					w.printf("0x%08X insn %s %s%n", a.getOffset(), fname, ins);
					continue;
				}
				Instruction cont = getInstructionContaining(a);
				if (cont != null) {
					w.printf("0x%08X inside-insn %s 0x%08X %s%n", a.getOffset(), fname, cont.getAddress().getOffset(), cont);
					continue;
				}
				Data d = getDataContaining(a);
				w.printf("0x%08X %s %s %s%n", a.getOffset(), d == null || !d.isDefined() ? "undefined" : "data", fname,
					d == null ? "" : d.getDataType().getName());
			}
		}
	}
}
