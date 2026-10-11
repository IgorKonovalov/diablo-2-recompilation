// Write user-defined symbols back to re/symbols.csv, merged with the existing file.
// Usage (headless): -postScript ExportSymbols.java <symbols.csv>
// - Every USER_DEFINED primary symbol in the program becomes a row (func if a function starts there,
//   otherwise the kind already in the CSV, else label).
// - confidence/subsystem/evidence come from the existing CSV row at that address. New rows get
//   confidence L and empty subsystem/evidence, and are listed in the log so they get filled in.
// - signature is exported only when the function's signature source is USER_DEFINED.
// - CSV rows whose address no longer carries a user symbol are KEPT and reported, never dropped
//   silently (delete them from the CSV by hand if that was intended).
// - Fails on duplicate names. Rows are sorted by address.
// @category d2-recon

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.SourceType;
import ghidra.program.model.symbol.Symbol;
import ghidra.program.model.symbol.SymbolIterator;

public class ExportSymbols extends GhidraScript {

	static final String HEADER = "address,kind,name,signature,confidence,subsystem,evidence";

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

	static String esc(String s) {
		if (s.contains(",") || s.contains("\"")) return "\"" + s.replace("\"", "\"\"") + "\"";
		return s;
	}

	@Override
	public void run() throws Exception {
		String[] args = getScriptArgs();
		if (args.length != 1) throw new IllegalArgumentException("usage: ExportSymbols.java <symbols.csv>");
		TreeMap<Long, List<String>> old = new TreeMap<>();
		try (BufferedReader r = new BufferedReader(new FileReader(args[0]))) {
			String h = r.readLine();
			if (h == null || !h.trim().equals(HEADER)) throw new IllegalStateException("unexpected CSV header: " + h);
			String line;
			while ((line = r.readLine()) != null) {
				if (line.isBlank()) continue;
				List<String> f = parseCsvLine(line);
				old.put(Long.decode(f.get(0)), f);
			}
		}

		TreeMap<Long, List<String>> rows = new TreeMap<>();
		List<String> added = new ArrayList<>();
		SymbolIterator it = currentProgram.getSymbolTable().getAllSymbols(true);
		while (it.hasNext()) {
			Symbol s = it.next();
			if (s.getSource() != SourceType.USER_DEFINED || !s.isPrimary() || s.isExternal()) continue;
			Address a = s.getAddress();
			if (!a.isMemoryAddress()) continue;
			long off = a.getOffset();
			List<String> prev = old.get(off);
			Function fn = getFunctionAt(a);
			String kind = fn != null ? "func" : (prev != null && !prev.get(1).equals("func") ? prev.get(1) : "label");
			String sig = "";
			if (fn != null && fn.getSignatureSource() == SourceType.USER_DEFINED)
				sig = fn.getSignature().getPrototypeString(true);
			List<String> row = new ArrayList<>(List.of(String.format("0x%08X", off), kind, s.getName(), sig,
				prev != null ? prev.get(4) : "L", prev != null ? prev.get(5) : "", prev != null ? prev.get(6) : ""));
			if (prev == null) added.add(row.get(0) + " " + s.getName());
			rows.put(off, row);
		}
		for (Map.Entry<Long, List<String>> e : old.entrySet()) {
			if (!rows.containsKey(e.getKey())) {
				println("ExportSymbols: KEPT (no user symbol in program): " + String.join(",", e.getValue()));
				rows.put(e.getKey(), e.getValue());
			}
		}
		Map<String, String> names = new HashMap<>();
		for (List<String> row : rows.values()) {
			String prevAddr = names.put(row.get(2), row.get(0));
			if (prevAddr != null) throw new IllegalStateException("duplicate name " + row.get(2) + " at " + prevAddr + " and " + row.get(0));
		}
		try (PrintWriter w = new PrintWriter(args[0])) {
			w.print(HEADER + "\n");
			for (List<String> row : rows.values()) {
				List<String> f = new ArrayList<>();
				for (String x : row) f.add(esc(x));
				w.print(String.join(",", f) + "\n");
			}
		}
		for (String a : added) println("ExportSymbols: NEW (confidence L, fill subsystem/evidence): " + a);
		println(String.format("ExportSymbols: %d rows (%d new) -> %s", rows.size(), added.size(), args[0]));
	}
}
