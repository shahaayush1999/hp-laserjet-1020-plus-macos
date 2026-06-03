// Maps identity/device-ID strings and their nearby tables/functions.

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

public class MapHp1020IdentityData extends GhidraScript {
    private static final String[] NEEDLES = {
        "Hewlett-Packard",
        "HP LaserJet 1020",
        "ACL.PRINTER",
        "xxMFG:%s;MDL:%s;CMD:%s;CLS:%s;DES:%s;FWVER:%s;",
        "20050309",
        "HPBOISEID",
        "@PJL",
        "@PJL ECHO",
        "%-12345X"
    };

    private final Map<Function, String> labels = new LinkedHashMap<>();

    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            println("usage: MapHp1020IdentityData <output-dir>");
            return;
        }

        File outDir = new File(args[0]);
        File decompDir = new File(outDir, "identity-decompiled");
        outDir.mkdirs();
        decompDir.mkdirs();

        applyLabels();

        List<StringRecord> strings = collectStrings();
        Map<Address, List<Address>> pointerRefs = scanPointerReferences(strings);
        Set<Function> functions = collectFunctions(strings, pointerRefs);
        decompile(functions, decompDir);

        try (PrintWriter out = new PrintWriter(new FileWriter(new File(outDir, "identity-map.md")))) {
            writeReport(out, strings, pointerRefs, functions);
        }
    }

    private void applyLabels() {
        label(0x1000b3f8L, "hp1020_pjl_ustatus_result_builder");
        label(0x1000bd04L, "hp1020_pjl_info_capabilities_builder");
        label(0x1000cdb0L, "hp1020_pjl_echo_matcher");
        label(0x10007430L, "hp1020_format_into_buffer_candidate");
        label(0x100169d4L, "hp1020_strlen_like");
        label(0x1001b544L, "hp1020_append_string_to_buffer_candidate");
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
                // The report uses the local label even if Ghidra rejects the rename.
            }
        }
    }

    private List<StringRecord> collectStrings() {
        List<StringRecord> result = new ArrayList<>();
        var data = currentProgram.getListing().getDefinedData(true);
        while (data.hasNext()) {
            Data item = data.next();
            StringDataInstance s = StringDataInstance.getStringDataInstance(item);
            if (s == null || s.getStringValue() == null) {
                continue;
            }
            String value = s.getStringValue();
            if (!matches(value)) {
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

    private boolean matches(String value) {
        for (String needle : NEEDLES) {
            if (value.contains(needle)) {
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
                byte[] bytes = new byte[(int) Math.min(block.getSize(), 0x400000)];
                block.getBytes(block.getStart(), bytes);
                for (int i = 0; i + 4 <= bytes.length; i += 4) {
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

    private Set<Function> collectFunctions(List<StringRecord> strings, Map<Address, List<Address>> pointerRefs) {
        Set<Function> functions = new LinkedHashSet<>();
        for (StringRecord record : strings) {
            for (Address ref : record.directRefs) {
                Function fn = currentProgram.getFunctionManager().getFunctionContaining(ref);
                if (fn != null) {
                    functions.add(fn);
                }
            }
            for (Address pointerRef : pointerRefs.getOrDefault(record.address, List.of())) {
                for (Reference ref : getReferencesTo(pointerRef)) {
                    Function fn = currentProgram.getFunctionManager().getFunctionContaining(ref.getFromAddress());
                    if (fn != null) {
                        functions.add(fn);
                    }
                }
                functions.addAll(scanInstructionRefsTo(pointerRef));
            }
        }
        functions.add(functionAt(0x1000b3f8L));
        functions.add(functionAt(0x1000bd04L));
        functions.add(functionAt(0x1000cdb0L));
        functions.remove(null);
        return functions;
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
        for (Function fn : functions) {
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

    private void writeReport(PrintWriter out, List<StringRecord> strings,
        Map<Address, List<Address>> pointerRefs, Set<Function> functions) {
        out.println("# HP 1020 Identity Data Map");
        out.println();
        out.println("This maps product/manufacturer/PJL identity strings and pointer tables around them.");
        out.println();

        out.println("## Strings");
        out.println();
        for (StringRecord record : strings) {
            out.printf("### `%s` `%s`%n%n", record.address, compact(record.value));
            out.println("Direct code/data references:");
            if (record.directRefs.isEmpty()) {
                out.println("- none found");
            }
            for (Address ref : record.directRefs) {
                Function fn = currentProgram.getFunctionManager().getFunctionContaining(ref);
                out.printf("- `%s`", ref);
                if (fn != null) {
                    out.printf(" in `%s` `%s`", fn.getEntryPoint(), displayName(fn));
                }
                out.println();
            }
            out.println();
            out.println("Pointer-table references:");
            List<Address> refs = pointerRefs.getOrDefault(record.address, List.of());
            if (refs.isEmpty()) {
                out.println("- none found");
            }
            for (Address ref : refs) {
                out.printf("- `%s`%n", ref);
            }
            out.println();
        }

        out.println("## Related Functions");
        out.println();
        List<Function> sorted = new ArrayList<>(functions);
        sorted.sort(Comparator.comparing(f -> f.getEntryPoint().toString()));
        for (Function fn : sorted) {
            out.printf("- `%s` `%s`%n", fn.getEntryPoint(), displayName(fn));
        }
        out.println();

        out.println("## Interpretation");
        out.println();
        out.println("- ASCII identity strings live in `.data`, not USB UTF-16 descriptor form.");
        out.println("- Static USB descriptors separately contain string indexes; the actual string response path likely builds runtime strings from these ASCII values or related buffers.");
        out.println("- PJL/IEEE1284 identity construction is centered around the `xxMFG:%s;MDL:%s;CMD:%s;CLS:%s;DES:%s;FWVER:%s;` format string and the status/capability builder functions.");
    }

    private Function functionAt(long rawAddress) {
        Address address = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(rawAddress);
        Function fn = currentProgram.getFunctionManager().getFunctionAt(address);
        if (fn == null) {
            fn = currentProgram.getFunctionManager().getFunctionContaining(address);
        }
        return fn;
    }

    private String displayName(Function fn) {
        return labels.getOrDefault(fn, fn.getName());
    }

    private String compact(String value) {
        String s = value.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t");
        return s.length() > 140 ? s.substring(0, 137) + "..." : s;
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
}
