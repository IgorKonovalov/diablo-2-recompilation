// List the defined strings each function references (directly, from instructions in its body).
// Usage (headless): -postScript StringsIn.java <out-file> <addr|name> [...]
// Output: "# <name> @ 0x<entry>" then one "  0x<from> \"<string>\"" per reference. Source-path and
// assert strings ("..\\Source\\D2Common\\DRLG\\...") are the main use: they tell which original
// module a function came from.
// @category d2-recon

import java.io.PrintWriter;
import java.util.List;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Data;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.symbol.Reference;

public class StringsIn extends GhidraScript {

	Function resolve(String t) {
		if (t.startsWith("0x") || t.startsWith("0X")) return getFunctionContaining(toAddr(Long.decode(t)));
		List<Function> fs = getGlobalFunctions(t);
		return fs.isEmpty() ? null : fs.get(0);
	}

	@Override
	public void run() throws Exception {
		String[] args = getScriptArgs();
		if (args.length < 2) throw new IllegalArgumentException("usage: StringsIn.java <out-file> <addr|name>...");
		try (PrintWriter w = new PrintWriter(args[0])) {
			for (int i = 1; i < args.length; i++) {
				Function fn = resolve(args[i]);
				if (fn == null) { w.println("# " + args[i] + ": no function"); continue; }
				w.printf("# %s @ 0x%08X%n", fn.getName(), fn.getEntryPoint().getOffset());
				InstructionIterator it = currentProgram.getListing().getInstructions(fn.getBody(), true);
				while (it.hasNext()) {
					Instruction ins = it.next();
					for (Reference r : ins.getReferencesFrom()) {
						Address to = r.getToAddress();
						Data d = getDataAt(to);
						if (d != null && d.hasStringValue())
							w.printf("  0x%08X \"%s\"%n", ins.getAddress().getOffset(), String.valueOf(d.getValue()));
					}
				}
			}
		}
	}
}
