// Exports a compact Ghidra analysis summary for the HP 1020 firmware spike.

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.data.StringDataInstance;
import ghidra.program.model.listing.Data;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.program.model.symbol.Reference;

import java.io.FileWriter;
import java.io.PrintWriter;

public class ExportHp1020Summary extends GhidraScript {
    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            println("usage: ExportHp1020Summary <output-path>");
            return;
        }

        try (PrintWriter out = new PrintWriter(new FileWriter(args[0]))) {
            out.println("# Ghidra HP 1020 Firmware Summary");
            out.println();
            out.println("Program: " + currentProgram.getName());
            out.println("Language: " + currentProgram.getLanguageID());
            out.println("Compiler spec: " + currentProgram.getCompilerSpec().getCompilerSpecID());
            out.println("Image base: " + currentProgram.getImageBase());
            out.println("Entry points:");
            for (Address entry : currentProgram.getSymbolTable().getExternalEntryPointIterator()) {
                out.println("- " + entry);
            }

            out.println();
            out.println("Memory blocks:");
            for (MemoryBlock block : currentProgram.getMemory().getBlocks()) {
                out.printf("- %s start=%s size=0x%x r=%s w=%s x=%s%n",
                    block.getName(),
                    block.getStart(),
                    block.getSize(),
                    block.isRead(),
                    block.isWrite(),
                    block.isExecute());
            }

            int functionCount = currentProgram.getFunctionManager().getFunctionCount();
            out.println();
            out.println("Function count: " + functionCount);
            out.println("First functions:");
            FunctionIterator functions = currentProgram.getFunctionManager().getFunctions(true);
            int shown = 0;
            while (functions.hasNext() && shown < 40) {
                Function fn = functions.next();
                out.printf("- %s %s%n", fn.getEntryPoint(), fn.getName());
                shown++;
            }

            out.println();
            out.println("Interesting strings and references:");
            var data = currentProgram.getListing().getDefinedData(true);
            while (data.hasNext()) {
                Data item = data.next();
                StringDataInstance string = StringDataInstance.getStringDataInstance(item);
                if (string == null) {
                    continue;
                }
                String value = string.getStringValue();
                if (value == null || !isInteresting(value)) {
                    continue;
                }

                out.printf("- %s %s%n", item.getAddress(), value.replace("\n", "\\n"));
                Reference[] refs = getReferencesTo(item.getAddress());
                int refCount = Math.min(refs.length, 8);
                for (int i = 0; i < refCount; i++) {
                    out.printf("  ref %s%n", refs[i].getFromAddress());
                }
                if (refs.length > refCount) {
                    out.printf("  ... %d more refs%n", refs.length - refCount);
                }
            }
        }
    }

    private boolean isInteresting(String value) {
        String upper = value.toUpperCase();
        return upper.contains("PJL")
            || upper.contains("ACL")
            || upper.contains("USB")
            || upper.contains("THREAD")
            || upper.contains("FUSER")
            || upper.contains("PAPER")
            || upper.contains("TONER")
            || upper.contains("FWVER")
            || upper.contains("MANGUSTA")
            || upper.contains("JAM")
            || upper.contains("ERROR");
    }
}
