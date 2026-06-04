// Exports data/literal constants used by status-state and engine-status functions.

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.program.model.scalar.Scalar;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.SourceType;
import ghidra.program.model.symbol.Symbol;

import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

public class MapHp1020StatusMasks extends GhidraScript {
    private static final long[] TARGET_FUNCTIONS = {
        0x1000a280L,
        0x1000a2a4L,
        0x10010590L,
        0x10010838L,
        0x10010a3cL,
        0x10010a8cL,
        0x10015c68L,
        0x10015df8L,
        0x100160a8L
    };

    private final Map<Function, String> labels = new LinkedHashMap<>();

    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            println("usage: MapHp1020StatusMasks <output-dir>");
            return;
        }

        File outDir = new File(args[0]);
        outDir.mkdirs();

        applyLabels();

        List<Function> functions = targetFunctions();
        List<DataRefRecord> dataRefs = collectDataRefs(functions);
        List<ScalarRecord> scalars = collectScalars(functions);

        writeDataRefsTsv(dataRefs, new File(outDir, "status-data-refs.tsv"));
        try (PrintWriter out = new PrintWriter(new FileWriter(new File(outDir, "status-mask-map.md")))) {
            writeReport(out, functions, dataRefs, scalars);
        }
    }

    private void applyLabels() {
        label(0x1000a280L, "hp1020_status_code_offset_lookup_candidate");
        label(0x1000a2a4L, "hp1020_status_word_to_pjl_code_candidate");
        label(0x10010590L, "hp1020_status_mgr_thread_candidate");
        label(0x10010838L, "hp1020_status_state_update_candidate");
        label(0x10010a3cL, "hp1020_status_notify_pending_candidate");
        label(0x10010a8cL, "hp1020_status_event_store_candidate");
        label(0x10015c68L, "hp1020_engine_status_io_candidate");
        label(0x10015df8L, "hp1020_engine_status_poll_candidate");
        label(0x100160a8L, "hp1020_engine_preflight_candidate");
    }

    private void label(long rawAddress, String name) {
        Function fn = functionAt(rawAddress);
        if (fn == null) {
            return;
        }
        labels.put(fn, name);
        if (fn.getName().startsWith("FUN_")) {
            try {
                fn.setName(name, SourceType.ANALYSIS);
            }
            catch (Exception ignored) {
                // Report labels are still usable.
            }
        }
    }

    private List<Function> targetFunctions() {
        List<Function> functions = new ArrayList<>();
        for (long raw : TARGET_FUNCTIONS) {
            Function fn = functionAt(raw);
            if (fn != null) {
                functions.add(fn);
            }
        }
        functions.sort(Comparator.comparing(f -> f.getEntryPoint().toString()));
        return functions;
    }

    private List<DataRefRecord> collectDataRefs(List<Function> functions) throws Exception {
        List<DataRefRecord> records = new ArrayList<>();
        Set<String> seen = new LinkedHashSet<>();
        for (Function fn : functions) {
            InstructionIterator instructions = currentProgram.getListing().getInstructions(fn.getBody(), true);
            while (instructions.hasNext()) {
                Instruction instruction = instructions.next();
                for (Reference ref : instruction.getReferencesFrom()) {
                    Address target = ref.getToAddress();
                    MemoryBlock block = currentProgram.getMemory().getBlock(target);
                    if (block == null || !block.isInitialized()) {
                        continue;
                    }
                    boolean literalLoad = "l32r".equals(instruction.getMnemonicString());
                    if (block.isExecute() && !literalLoad) {
                        continue;
                    }
                    if (!currentProgram.getMemory().contains(target.add(3))) {
                        continue;
                    }
                    long value = Integer.toUnsignedLong(currentProgram.getMemory().getInt(target));
                    String key = fn.getEntryPoint() + ":" + instruction.getAddress() + ":" + target;
                    if (seen.add(key)) {
                        records.add(new DataRefRecord(fn, instruction.getAddress(), instruction.toString(),
                            target, symbolName(target), value, classify(value)));
                    }
                }
            }
        }
        records.sort(Comparator
            .comparing((DataRefRecord r) -> r.function.getEntryPoint().toString())
            .thenComparing(r -> r.instructionAddress.toString())
            .thenComparing(r -> r.target.toString()));
        return records;
    }

    private List<ScalarRecord> collectScalars(List<Function> functions) {
        List<ScalarRecord> records = new ArrayList<>();
        Set<String> seen = new LinkedHashSet<>();
        for (Function fn : functions) {
            InstructionIterator instructions = currentProgram.getListing().getInstructions(fn.getBody(), true);
            while (instructions.hasNext()) {
                Instruction instruction = instructions.next();
                for (int i = 0; i < instruction.getNumOperands(); i++) {
                    for (Object obj : instruction.getOpObjects(i)) {
                        if (!(obj instanceof Scalar)) {
                            continue;
                        }
                        long value = ((Scalar) obj).getUnsignedValue();
                        if (!interestingScalar(value)) {
                            continue;
                        }
                        String key = fn.getEntryPoint() + ":" + instruction.getAddress() + ":" + value;
                        if (seen.add(key)) {
                            records.add(new ScalarRecord(fn, instruction.getAddress(), instruction.toString(),
                                value, classify(value)));
                        }
                    }
                }
            }
        }
        records.sort(Comparator
            .comparing((ScalarRecord r) -> r.function.getEntryPoint().toString())
            .thenComparing(r -> r.instructionAddress.toString())
            .thenComparingLong(r -> r.value));
        return records;
    }

    private boolean interestingScalar(long value) {
        if (value <= 0x43 || value == 0xff || value == 0xffffffffL) {
            return true;
        }
        if ((value & 0xffff0000L) != 0) {
            return true;
        }
        return value == 0x64 || value == 0x100 || value == 0x1ff || value == 0x200 ||
            value == 0x400 || value == 0x1000 || value == 0x20000000L || value == 0x10000000L;
    }

    private String classify(long value) {
        if (value == 0xffffffffL) {
            return "wait forever / all bits";
        }
        if (value == 0x80000000L || (value & 0xff000000L) == 0xe6000000L ||
            (value & 0xff000000L) == 0xe7000000L || (value & 0xff000000L) == 0xee000000L ||
            (value & 0xff000000L) == 0xfe000000L || (value & 0xff000000L) == 0xf6000000L ||
            (value & 0xffff0000L) == 0x20000000L) {
            return "engine/status event word";
        }
        if (value != 0 && (value & (value - 1)) == 0) {
            return "single-bit mask";
        }
        if (value <= 0x43) {
            return "small message/config/status id";
        }
        if ((value & 0xffff0000L) != 0) {
            return "status mask/constant";
        }
        return "";
    }

    private void writeDataRefsTsv(List<DataRefRecord> records, File file) throws Exception {
        try (PrintWriter out = new PrintWriter(new FileWriter(file))) {
            out.println("# function\tinstruction\tdata_ref\tsymbol\tvalue\tclassification\tinstruction_text");
            for (DataRefRecord record : records) {
                out.printf(
                    "%s %s\t%s\t%s\t%s\t0x%x\t%s\t%s%n",
                    record.function.getEntryPoint(),
                    displayName(record.function),
                    record.instructionAddress,
                    record.target,
                    record.symbol,
                    record.value,
                    record.classification,
                    record.instructionText
                );
            }
        }
    }

    private void writeReport(PrintWriter out, List<Function> functions,
        List<DataRefRecord> dataRefs, List<ScalarRecord> scalars) {
        out.println("# HP 1020 Status Mask And Constant Map");
        out.println();
        out.println("This report lists the literal-pool data words and scalar constants used by the");
        out.println("status manager, status-state updater, and engine status poller.");
        out.println();

        out.println("## Target Functions");
        out.println();
        for (Function fn : functions) {
            out.printf("- `%s` `%s`%n", fn.getEntryPoint(), displayName(fn));
        }
        out.println();

        out.println("## Data References");
        out.println();
        out.println("| Function | Instruction | Data Ref | Symbol | Value | Classification |");
        out.println("|---|---:|---:|---|---:|---|");
        for (DataRefRecord record : dataRefs) {
            out.printf(
                "| `%s` | `%s` `%s` | `%s` | `%s` | `0x%x` | %s |%n",
                displayName(record.function),
                record.instructionAddress,
                escape(record.instructionText),
                record.target,
                record.symbol,
                record.value,
                record.classification
            );
        }
        out.println();

        out.println("## Scalar Literals");
        out.println();
        out.println("| Function | Instruction | Value | Classification |");
        out.println("|---|---:|---:|---|");
        for (ScalarRecord record : scalars) {
            out.printf(
                "| `%s` | `%s` `%s` | `0x%x` | %s |%n",
                displayName(record.function),
                record.instructionAddress,
                escape(record.instructionText),
                record.value,
                record.classification
            );
        }
        out.println();

        out.println("## Current Interpretation");
        out.println();
        out.println("- The engine poller emits many full-width event words, while the status-state updater mostly compares masks and stores a normalized status word.");
        out.println("- `hp1020_status_word_to_pjl_code_candidate` is where stored status words become user-visible PJL `CODE=` numbers.");
        out.println("- Constants in this report are not fully named yet; this file narrows the next manual pass to a few literal-pool words rather than the whole firmware.");
    }

    private Function functionAt(long rawAddress) {
        Address address = addr(rawAddress);
        Function fn = currentProgram.getFunctionManager().getFunctionAt(address);
        if (fn == null) {
            fn = currentProgram.getFunctionManager().getFunctionContaining(address);
        }
        return fn;
    }

    private Address addr(long rawAddress) {
        return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(rawAddress);
    }

    private String symbolName(Address address) {
        Symbol symbol = currentProgram.getSymbolTable().getPrimarySymbol(address);
        return symbol == null ? "" : symbol.getName();
    }

    private String displayName(Function fn) {
        return labels.getOrDefault(fn, fn.getName());
    }

    private String escape(String value) {
        return value.replace("|", "\\|").replace("`", "'");
    }

    private static class DataRefRecord {
        final Function function;
        final Address instructionAddress;
        final String instructionText;
        final Address target;
        final String symbol;
        final long value;
        final String classification;

        DataRefRecord(Function function, Address instructionAddress, String instructionText,
            Address target, String symbol, long value, String classification) {
            this.function = function;
            this.instructionAddress = instructionAddress;
            this.instructionText = instructionText;
            this.target = target;
            this.symbol = symbol;
            this.value = value;
            this.classification = classification;
        }
    }

    private static class ScalarRecord {
        final Function function;
        final Address instructionAddress;
        final String instructionText;
        final long value;
        final String classification;

        ScalarRecord(Function function, Address instructionAddress, String instructionText,
            long value, String classification) {
            this.function = function;
            this.instructionAddress = instructionAddress;
            this.instructionText = instructionText;
            this.value = value;
            this.classification = classification;
        }
    }
}
