// Maps PJL-visible status/fault strings, status tables, and related code paths.

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.data.StringDataInstance;
import ghidra.program.model.listing.Data;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.SourceType;

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

public class MapHp1020StatusPath extends GhidraScript {
    private static final long STATUS_TABLE_PTR_WORD = 0x10006148L;
    private static final long STATUS_CODE_TABLE_PTR_WORD = 0x10006014L;

    private static final String[] STATUS_NEEDLES = {
        "FUSER",
        "PAPERLESS",
        "SETERROR",
        "TONEREXP",
        "JAMRECOVERY",
        "USTATUS",
        "CODE=",
        "DISPLAY=",
        "DISPLAY",
        "BUSY",
        "PARSEERROR",
        "CANCELED",
        "USER CANCELED"
    };

    private static final long[] SEED_FUNCTIONS = {
        0x1000a280L,
        0x1000a2a4L,
        0x1000b2a8L,
        0x1000b3f8L,
        0x1000b520L,
        0x1000b870L,
        0x1000bd04L,
        0x1000c8fcL,
        0x1000cd44L,
        0x1000d2a8L,
        0x10010590L,
        0x10010838L,
        0x10010a3cL,
        0x10010a8cL,
        0x10010f54L,
        0x10010fd0L,
        0x10011178L,
        0x10015c68L,
        0x10015df8L,
        0x100160a8L
    };

    private final Map<Function, String> labels = new LinkedHashMap<>();

    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            println("usage: MapHp1020StatusPath <output-dir>");
            return;
        }

        File outDir = new File(args[0]);
        File decompDir = new File(outDir, "status-decompiled");
        outDir.mkdirs();
        decompDir.mkdirs();

        applyLabels();

        List<StringRecord> strings = collectStatusStrings();
        Map<Address, List<Address>> pointerRefs = scanPointerReferences(strings);
        List<TableEntry> statusTable = readStatusTable();
        List<CodeOffsetEntry> codeTable = readStatusCodeOffsetTable();
        Set<Function> functions = collectRelatedFunctions(strings, pointerRefs);
        decompile(functions, decompDir);

        writeStatusTableTsv(statusTable, new File(outDir, "status-command-table.tsv"));
        writeStatusCodeTableTsv(codeTable, new File(outDir, "status-code-offset-table.tsv"));
        try (PrintWriter out = new PrintWriter(new FileWriter(new File(outDir, "status-path.md")))) {
            writeReport(out, strings, pointerRefs, statusTable, codeTable, functions);
        }
    }

    private void applyLabels() {
        label(0x1000a280L, "hp1020_status_code_offset_lookup_candidate");
        label(0x1000a2a4L, "hp1020_status_word_to_pjl_code_candidate");
        label(0x1000b2a8L, "hp1020_pjl_status_notify_builder_candidate");
        label(0x1000b3f8L, "hp1020_pjl_ustatus_result_builder");
        label(0x1000b520L, "hp1020_pjl_ustatus_cancel_builder_candidate");
        label(0x1000b870L, "hp1020_pjl_status_table_get_candidate");
        label(0x1000bd04L, "hp1020_pjl_info_capabilities_builder");
        label(0x1000c8fcL, "hp1020_pjl_status_table_set_candidate");
        label(0x1000cd44L, "hp1020_pjl_response_send_candidate");
        label(0x1000d2a8L, "hp1020_pjl_command_dispatch_candidate");
        label(0x10010590L, "hp1020_status_mgr_thread_candidate");
        label(0x10010838L, "hp1020_status_state_update_candidate");
        label(0x10010a3cL, "hp1020_status_notify_pending_candidate");
        label(0x10010a8cL, "hp1020_status_event_store_candidate");
        label(0x10010f54L, "hp1020_datastore_read_locked_candidate");
        label(0x10010fd0L, "hp1020_datastore_write_notify_unlock_candidate");
        label(0x10011178L, "hp1020_datastore_get_value_candidate");
        label(0x10015c68L, "hp1020_engine_status_io_candidate");
        label(0x10015df8L, "hp1020_engine_status_poll_candidate");
        label(0x100160a8L, "hp1020_engine_preflight_candidate");
        label(0x100169d4L, "hp1020_strlen_like");
        label(0x1001b544L, "hp1020_append_string_to_buffer_candidate");
        label(0x10007430L, "hp1020_format_into_buffer_candidate");
        label(0x1000dc00L, "hp1020_alloc_buffer_candidate");
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
                // The report uses the local label if the database rename is rejected.
            }
        }
    }

    private List<StringRecord> collectStatusStrings() {
        List<StringRecord> result = new ArrayList<>();
        var data = currentProgram.getListing().getDefinedData(true);
        while (data.hasNext()) {
            Data item = data.next();
            StringDataInstance s = StringDataInstance.getStringDataInstance(item);
            if (s == null || s.getStringValue() == null) {
                continue;
            }
            String value = s.getStringValue();
            if (!matchesNeedle(value)) {
                continue;
            }
            StringRecord record = new StringRecord(item.getAddress(), value);
            for (Reference ref : getReferencesTo(item.getAddress())) {
                record.directRefs.add(ref.getFromAddress());
            }
            result.add(record);
        }
        result.sort(Comparator.comparing(r -> r.address.toString()));
        return result;
    }

    private boolean matchesNeedle(String value) {
        String upper = value.toUpperCase();
        for (String needle : STATUS_NEEDLES) {
            if (upper.contains(needle)) {
                return true;
            }
        }
        return false;
    }

    private Map<Address, List<Address>> scanPointerReferences(List<StringRecord> records) throws Exception {
        Map<Address, List<Address>> result = new LinkedHashMap<>();
        Memory memory = currentProgram.getMemory();
        for (StringRecord record : records) {
            List<Address> refs = new ArrayList<>();
            byte[] needle = intBytes((int) record.address.getOffset());
            for (MemoryBlock block : memory.getBlocks()) {
                if (!block.isInitialized() || !block.isRead()) {
                    continue;
                }
                int size = (int) Math.min(block.getSize(), 0x400000);
                byte[] bytes = new byte[size];
                block.getBytes(block.getStart(), bytes);
                for (int i = 0; i + 4 <= bytes.length; i++) {
                    if (bytes[i] == needle[0] && bytes[i + 1] == needle[1] &&
                        bytes[i + 2] == needle[2] && bytes[i + 3] == needle[3]) {
                        refs.add(block.getStart().add(i));
                    }
                }
            }
            result.put(record.address, refs);
        }
        return result;
    }

    private byte[] intBytes(int value) {
        return new byte[] {
            (byte) ((value >>> 24) & 0xff),
            (byte) ((value >>> 16) & 0xff),
            (byte) ((value >>> 8) & 0xff),
            (byte) (value & 0xff)
        };
    }

    private List<TableEntry> readStatusTable() throws Exception {
        List<TableEntry> entries = new ArrayList<>();
        Address ptrWord = addr(STATUS_TABLE_PTR_WORD);
        long tableBaseRaw = Integer.toUnsignedLong(currentProgram.getMemory().getInt(ptrWord));
        Address tableBase = addr(tableBaseRaw);
        for (int i = 0; i < 0x20; i++) {
            Address entryAddress = tableBase.add(i * 0x24L);
            if (!currentProgram.getMemory().contains(entryAddress)) {
                break;
            }
            List<Long> words = new ArrayList<>();
            for (int j = 0; j < 9; j++) {
                words.add(Integer.toUnsignedLong(currentProgram.getMemory().getInt(entryAddress.add(j * 4L))));
            }
            long kind = words.get(0);
            String name = safeAscii(words.get(1));
            TableEntry entry = new TableEntry(i, entryAddress, kind, words.get(1), name, words);
            entries.add(entry);
            if (kind == 0x14) {
                break;
            }
        }
        return entries;
    }

    private List<CodeOffsetEntry> readStatusCodeOffsetTable() throws Exception {
        List<CodeOffsetEntry> entries = new ArrayList<>();
        Address ptrWord = addr(STATUS_CODE_TABLE_PTR_WORD);
        long tableBaseRaw = Integer.toUnsignedLong(currentProgram.getMemory().getInt(ptrWord));
        Address tableBase = addr(tableBaseRaw);
        for (int i = 0; i < 20; i++) {
            Address entryAddress = tableBase.add(i * 4L);
            if (!currentProgram.getMemory().contains(entryAddress.add(3))) {
                break;
            }
            int input = Short.toUnsignedInt(currentProgram.getMemory().getShort(entryAddress));
            int offset = Short.toUnsignedInt(currentProgram.getMemory().getShort(entryAddress.add(2)));
            entries.add(new CodeOffsetEntry(i, entryAddress, input, offset, 0xa028 + offset));
        }
        return entries;
    }

    private String safeAscii(long rawAddress) {
        Address address = addr(rawAddress);
        if (!currentProgram.getMemory().contains(address)) {
            return "";
        }
        StringBuilder out = new StringBuilder();
        try {
            for (int i = 0; i < 160; i++) {
                int b = currentProgram.getMemory().getByte(address.add(i)) & 0xff;
                if (b == 0) {
                    break;
                }
                if (b < 0x20 || b > 0x7e) {
                    out.append(String.format("\\x%02x", b));
                }
                else {
                    out.append((char) b);
                }
            }
        }
        catch (Exception ignored) {
            return "";
        }
        return out.toString();
    }

    private Set<Function> collectRelatedFunctions(List<StringRecord> strings, Map<Address, List<Address>> pointerRefs) {
        Set<Function> functions = new LinkedHashSet<>();
        for (long seed : SEED_FUNCTIONS) {
            Function fn = functionAt(seed);
            if (fn != null) {
                functions.add(fn);
            }
        }
        for (StringRecord record : strings) {
            for (Address ref : record.directRefs) {
                addContainingFunction(functions, ref);
            }
            for (Address pointerRef : pointerRefs.getOrDefault(record.address, List.of())) {
                addContainingFunction(functions, pointerRef);
                for (Reference ref : getReferencesTo(pointerRef)) {
                    addContainingFunction(functions, ref.getFromAddress());
                }
                for (Function fn : scanInstructionRefsTo(pointerRef)) {
                    functions.add(fn);
                }
            }
        }
        return functions;
    }

    private void addContainingFunction(Set<Function> functions, Address address) {
        Function fn = currentProgram.getFunctionManager().getFunctionContaining(address);
        if (fn != null) {
            functions.add(fn);
        }
    }

    private Set<Function> scanInstructionRefsTo(Address target) {
        Set<Function> result = new LinkedHashSet<>();
        InstructionIterator instructions = currentProgram.getListing().getInstructions(true);
        while (instructions.hasNext()) {
            Instruction instruction = instructions.next();
            for (Reference ref : instruction.getReferencesFrom()) {
                if (ref.getToAddress().equals(target)) {
                    Function fn = currentProgram.getFunctionManager().getFunctionContaining(instruction.getAddress());
                    if (fn != null) {
                        result.add(fn);
                    }
                }
            }
        }
        return result;
    }

    private void decompile(Set<Function> functions, File decompDir) throws Exception {
        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);
        List<Function> sorted = new ArrayList<>(functions);
        sorted.sort(Comparator.comparing(f -> f.getEntryPoint().toString()));
        for (Function fn : sorted) {
            DecompileResults results = decompiler.decompileFunction(fn, 30, monitor);
            File outFile = new File(decompDir, fn.getEntryPoint() + "_" + displayName(fn) + ".c");
            try (PrintWriter out = new PrintWriter(new FileWriter(outFile))) {
                out.println("/* Function: " + fn.getEntryPoint() + " " + displayName(fn) + " */");
                out.println();
                if (results.decompileCompleted() && results.getDecompiledFunction() != null) {
                    out.println(results.getDecompiledFunction().getC());
                }
                else {
                    out.println("/* Decompilation failed: " + results.getErrorMessage() + " */");
                }
            }
        }
        decompiler.dispose();
    }

    private void writeStatusTableTsv(List<TableEntry> entries, File file) throws Exception {
        try (PrintWriter out = new PrintWriter(new FileWriter(file))) {
            out.println("# index\tentry_address\tkind\tname_pointer\tname\twords");
            for (TableEntry entry : entries) {
                out.printf(
                    "%d\t%s\t0x%x\t0x%x\t%s\t%s%n",
                    entry.index,
                    entry.address,
                    entry.kind,
                    entry.namePointer,
                    entry.name,
                    formatWords(entry.words)
                );
            }
        }
    }

    private void writeStatusCodeTableTsv(List<CodeOffsetEntry> entries, File file) throws Exception {
        try (PrintWriter out = new PrintWriter(new FileWriter(file))) {
            out.println("# index\tentry_address\tinput_value\toffset\tpjl_code_base_0xa028_plus_offset");
            for (CodeOffsetEntry entry : entries) {
                out.printf(
                    "%d\t%s\t0x%x\t0x%x\t%d%n",
                    entry.index,
                    entry.address,
                    entry.inputValue,
                    entry.offset,
                    entry.pjlCode
                );
            }
        }
    }

    private void writeReport(PrintWriter out, List<StringRecord> strings,
        Map<Address, List<Address>> pointerRefs, List<TableEntry> statusTable,
        List<CodeOffsetEntry> codeTable, Set<Function> functions) {
        out.println("# HP 1020 Status And PJL Fault Path");
        out.println();
        out.println("This report maps PJL-visible status/fault strings, the status command table,");
        out.println("and the functions that bridge firmware state into status responses.");
        out.println();

        out.println("## Status Command Table");
        out.println();
        out.printf("- Table pointer word: `%s`%n", addr(STATUS_TABLE_PTR_WORD));
        if (!statusTable.isEmpty()) {
            out.printf("- Table base: `%s`%n", statusTable.get(0).address);
        }
        out.println("- Entry size: `0x24` bytes");
        out.println();
        out.println("| Index | Entry | Kind | Name Pointer | Name | Words |");
        out.println("|---:|---:|---:|---:|---|---|");
        for (TableEntry entry : statusTable) {
            out.printf(
                "| `%d` | `%s` | `0x%x` | `0x%x` | `%s` | `%s` |%n",
                entry.index,
                entry.address,
                entry.kind,
                entry.namePointer,
                compact(entry.name),
                formatWords(entry.words)
            );
        }
        out.println();

        out.println("## Status Code Offset Table");
        out.println();
        out.printf("- Table pointer word: `%s`%n", addr(STATUS_CODE_TABLE_PTR_WORD));
        if (!codeTable.isEmpty()) {
            out.printf("- Table base: `%s`%n", codeTable.get(0).address);
        }
        out.println("- Entry shape: two big-endian halfwords: input/status index, PJL-code offset");
        out.println("- Code base used by `hp1020_status_word_to_pjl_code_candidate`: `0xa028`");
        out.println();
        out.println("| Index | Entry | Input Value | Offset | Base `0xa028` + Offset |");
        out.println("|---:|---:|---:|---:|---:|");
        for (CodeOffsetEntry entry : codeTable) {
            out.printf(
                "| `%d` | `%s` | `0x%x` | `0x%x` | `%d` |%n",
                entry.index,
                entry.address,
                entry.inputValue,
                entry.offset,
                entry.pjlCode
            );
        }
        out.println();

        out.println("## Status/Fault Strings");
        out.println();
        out.println("| Address | String | Direct Refs | Pointer Refs |");
        out.println("|---:|---|---|---|");
        for (StringRecord record : strings) {
            out.printf(
                "| `%s` | `%s` | %s | %s |%n",
                record.address,
                compact(record.value),
                formatAddresses(record.directRefs),
                formatAddresses(pointerRefs.getOrDefault(record.address, List.of()))
            );
        }
        out.println();

        out.println("## Related Functions");
        out.println();
        List<Function> sorted = new ArrayList<>(functions);
        sorted.sort(Comparator.comparing(f -> f.getEntryPoint().toString()));
        for (Function fn : sorted) {
            out.printf("- `%s` `%s`%n", fn.getEntryPoint(), displayName(fn));
        }
        out.println();

        out.println("## Current Interpretation");
        out.println();
        out.println("- The visible words `FUSER`, `PAPERLESS`, `TONEREXP`, and `JAMRECOVERY` are PJL/status table names, not direct engine event-code names.");
        out.println("- `hp1020_pjl_status_table_set_candidate` walks the table and updates event/config slots based on the matched string name.");
        out.println("- `hp1020_pjl_status_table_get_candidate` reads the same table and converts rows into stored status/config values.");
        out.println("- `hp1020_status_mgr_thread_candidate` consumes `StatusMgrQueue` messages and calls USTATUS/result builders after state transitions.");
        out.println("- `hp1020_status_state_update_candidate` is the current bridge between numeric firmware state words and StatusMgr/PJL-visible notifications.");
        out.println("- `hp1020_status_word_to_pjl_code_candidate` converts an internal status word into the numeric PJL `CODE=` value used by USTATUS DEVICE messages; mapped fault/status values use base `0xa028` plus the offset table above.");
        out.println("- The next useful connection is to name the bit masks used by `hp1020_status_state_update_candidate` and the engine poller, then map those masks to the table rows above.");
    }

    private String formatAddresses(List<Address> addresses) {
        if (addresses.isEmpty()) {
            return "";
        }
        List<String> parts = new ArrayList<>();
        for (Address address : addresses) {
            parts.add("`" + address + "`");
        }
        return String.join("<br>", parts);
    }

    private String formatWords(List<Long> words) {
        List<String> parts = new ArrayList<>();
        for (Long word : words) {
            parts.add(String.format("0x%x", word));
        }
        return String.join(" ", parts);
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

    private String displayName(Function fn) {
        return labels.getOrDefault(fn, fn.getName());
    }

    private String compact(String value) {
        String s = value.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t");
        return s.length() > 120 ? s.substring(0, 117) + "..." : s;
    }

    private static class StringRecord {
        final Address address;
        final String value;
        final List<Address> directRefs = new ArrayList<>();

        StringRecord(Address address, String value) {
            this.address = address;
            this.value = value;
        }
    }

    private static class TableEntry {
        final int index;
        final Address address;
        final long kind;
        final long namePointer;
        final String name;
        final List<Long> words;

        TableEntry(int index, Address address, long kind, long namePointer, String name, List<Long> words) {
            this.index = index;
            this.address = address;
            this.kind = kind;
            this.namePointer = namePointer;
            this.name = name;
            this.words = words;
        }
    }

    private static class CodeOffsetEntry {
        final int index;
        final Address address;
        final int inputValue;
        final int offset;
        final int pjlCode;

        CodeOffsetEntry(int index, Address address, int inputValue, int offset, int pjlCode) {
            this.index = index;
            this.address = address;
            this.inputValue = inputValue;
            this.offset = offset;
            this.pjlCode = pjlCode;
        }
    }
}
