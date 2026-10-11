// Replay re/symbols.csv into the current program.
// Usage (headless): -postScript ImportSymbols.java <symbols.csv>
// Columns: address,kind,name,signature,confidence,subsystem,evidence (RFC 4180 quoting).
//   func  -> create the function at address if missing, rename it, apply `signature` if non-empty
//   data  -> primary label at address
//   label -> primary label at address
// Every symbol gets a plate/EOL comment "[<confidence>] <subsystem> <evidence>" so the tag is visible
// in Ghidra. All rows are validated (address, kind, signature syntax, calling convention) before
// anything is applied, and the apply pass runs in one transaction that is rolled back on any failure,
// so a broken CSV never half-applies.
// @category d2-recon

import java.io.BufferedReader;
import java.io.FileReader;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import ghidra.app.cmd.function.ApplyFunctionSignatureCmd;
import ghidra.app.script.GhidraScript;
import ghidra.app.util.parser.FunctionSignatureParser;
import ghidra.program.model.address.Address;
import ghidra.program.model.data.FunctionDefinitionDataType;
import ghidra.program.model.listing.CommentType;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.SourceType;
import ghidra.program.model.symbol.Symbol;

public class ImportSymbols extends GhidraScript {

	static List<String> parseCsvLine(String line) {
		List<String> out = new ArrayList<>();
		StringBuilder cur = new StringBuilder();
		boolean q = false;
		for (int i = 0; i < line.length(); i++) {
			char c = line.charAt(i);
			if (q) {
				if (c == '"' && i + 1 < line.length() && line.charAt(i + 1) == '"') { cur.append('"'); i++; }
				else if (c == '"') q = false;
				else cur.append(c);
			}
			else if (c == '"') q = true;
			else if (c == ',') { out.add(cur.toString()); cur.setLength(0); }
			else cur.append(c);
		}
		out.add(cur.toString());
		return out;
	}

	record Row(int line, Address addr, String kind, String name, String cc, String sigText, String tag) {}

	// "void __thiscall Foo(int x)" -> ["__thiscall", "void Foo(int x)"]; no keyword -> [null, sig].
	// FunctionSignatureParser rejects calling-convention keywords, so they are applied separately.
	static final Pattern CC = Pattern.compile("^(.*?)\\s+(__\\w+)\\s+([A-Za-z_]\\w*\\s*\\(.*)$");

	@Override
	public void run() throws Exception {
		String[] args = getScriptArgs();
		if (args.length != 1) throw new IllegalArgumentException("usage: ImportSymbols.java <symbols.csv>");

		// Pass 1: parse and validate every row. Nothing is touched until all rows pass.
		List<Row> rows = new ArrayList<>();
		FunctionSignatureParser parser = new FunctionSignatureParser(currentProgram.getDataTypeManager(), null);
		int lineNo = 0;
		try (BufferedReader r = new BufferedReader(new FileReader(args[0]))) {
			String header = r.readLine();
			lineNo++;
			if (header == null || !header.trim().equals("address,kind,name,signature,confidence,subsystem,evidence"))
				throw new IllegalStateException("unexpected CSV header: " + header);
			String line;
			while ((line = r.readLine()) != null) {
				lineNo++;
				if (line.isBlank()) continue;
				List<String> f = parseCsvLine(line);
				if (f.size() != 7) throw new IllegalStateException("line " + lineNo + ": expected 7 fields, got " + f.size());
				Address a = toAddr(Long.decode(f.get(0)));
				if (currentProgram.getMemory().getBlock(a) == null)
					throw new IllegalStateException("line " + lineNo + ": address not in the image: " + a);
				String kind = f.get(1), name = f.get(2), sig = f.get(3), cc = null;
				if (!kind.equals("func") && !kind.equals("data") && !kind.equals("label"))
					throw new IllegalStateException("line " + lineNo + ": unknown kind " + kind);
				if (!sig.isEmpty()) {
					if (!kind.equals("func")) throw new IllegalStateException("line " + lineNo + ": signature on a non-function");
					Matcher m = CC.matcher(sig);
					if (m.matches()) {
						cc = m.group(2);
						sig = m.group(1) + " " + m.group(3);
						if (currentProgram.getCompilerSpec().getCallingConvention(cc) == null)
							throw new IllegalStateException("line " + lineNo + ": unknown calling convention " + cc);
					}
					try { parser.parse(null, sig); }
					catch (Exception e) { throw new IllegalStateException("line " + lineNo + ": bad signature: " + e.getMessage()); }
				}
				rows.add(new Row(lineNo, a, kind, name, cc, sig, "[" + f.get(4) + "] " + f.get(5) + " " + f.get(6)));
			}
		}

		// Pass 2: apply inside one transaction that is aborted if anything fails.
		int funcs = 0, labels = 0, sigs = 0;
		int tx = currentProgram.startTransaction("ImportSymbols");
		boolean ok = false;
		try {
			for (Row row : rows) {
				Address a = row.addr();
				if (row.kind().equals("func")) {
					Function fn = getFunctionAt(a);
					if (fn == null) {
						disassemble(a);
						fn = createFunction(a, row.name());
						if (fn == null) throw new IllegalStateException("line " + row.line() + ": cannot create function at " + a);
					}
					fn.setName(row.name(), SourceType.USER_DEFINED);
					if (!row.sigText().isEmpty()) {
						FunctionDefinitionDataType def = parser.parse(fn.getSignature(), row.sigText());
						if (row.cc() != null) def.setCallingConvention(row.cc());
						ApplyFunctionSignatureCmd cmd = new ApplyFunctionSignatureCmd(a, def, SourceType.USER_DEFINED);
						if (!cmd.applyTo(currentProgram, monitor))
							throw new IllegalStateException("line " + row.line() + ": signature failed: " + cmd.getStatusMsg());
						sigs++;
					}
					setPlateComment(a, row.tag());
					funcs++;
				}
				else {
					Symbol s = createLabel(a, row.name(), true, SourceType.USER_DEFINED);
					if (s == null) throw new IllegalStateException("line " + row.line() + ": cannot label " + a);
					currentProgram.getListing().setComment(a, CommentType.EOL, row.tag());
					labels++;
				}
			}
			ok = true;
		}
		finally {
			currentProgram.endTransaction(tx, ok);
		}
		println(String.format("ImportSymbols: %d functions (%d signatures), %d labels from %s", funcs, sigs, labels, args[0]));
	}
}
