// Labels obvious HP 1020 firmware functions from string references and exports call clusters.

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.data.StringDataInstance;
import ghidra.program.model.listing.Data;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.SourceType;

import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Queue;
import java.util.Set;
import java.util.TreeMap;

public class LabelHp1020Firmware extends GhidraScript {
    private final Map<Function, LinkedHashSet<String>> functionStrings = new LinkedHashMap<>();
    private final Map<Function, LinkedHashSet<Function>> outgoing = new LinkedHashMap<>();
    private final Map<Function, LinkedHashSet<Function>> incoming = new LinkedHashMap<>();
    private final Map<Function, String> assignedNames = new LinkedHashMap<>();
    private final List<TableDescriptor> tableDescriptors = new ArrayList<>();
    private final Map<Address, LinkedHashSet<String>> unownedCodeRefs = new TreeMap<>();

    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            println("usage: LabelHp1020Firmware <output-dir>");
            return;
        }

        File outDir = new File(args[0]);
        File decompDir = new File(outDir, "decompiled");
        outDir.mkdirs();
        decompDir.mkdirs();

        collectStringReferences();
        renameSeedFunctions();
        applyKnownHelperLabels();
        buildCallGraph();

        List<Function> seeds = new ArrayList<>(functionStrings.keySet());
        seeds.sort(Comparator.comparing(f -> f.getEntryPoint().toString()));

        try (PrintWriter out = new PrintWriter(new FileWriter(new File(outDir, "labeled-functions.md")))) {
            writeReport(out, seeds);
        }

        exportDecompilerOutput(seeds, decompDir);
    }

    private void collectStringReferences() {
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

            String compact = compact(value);
            for (Reference ref : getReferencesTo(item.getAddress())) {
                Address from = ref.getFromAddress();
                Instruction instruction = currentProgram.getListing().getInstructionAt(from);
                if (instruction == null) {
                    collectTableDescriptor(from, compact);
                    continue;
                }

                Function fn = currentProgram.getFunctionManager().getFunctionContaining(from);
                if (fn == null) {
                    fn = nearestFunctionBefore(from, 0x500);
                }
                if (fn == null) {
                    unownedCodeRefs.computeIfAbsent(from, k -> new LinkedHashSet<>()).add(compact);
                    continue;
                }
                functionStrings.computeIfAbsent(fn, k -> new LinkedHashSet<>()).add(compact);
            }
        }
    }

    private void collectTableDescriptor(Address refAddress, String stringValue) {
        TableDescriptor descriptor = new TableDescriptor(refAddress, stringValue);
        descriptor.words = readWords(refAddress, 8);
        if (descriptor.words.size() > 1) {
            Function candidate = functionFromWord(descriptor.words.get(1), stringValue);
            if (candidate != null) {
                descriptor.handler = candidate;
                functionStrings.computeIfAbsent(candidate, k -> new LinkedHashSet<>())
                    .add("descriptor:" + stringValue);
            }
        }
        tableDescriptors.add(descriptor);
    }

    private void renameSeedFunctions() {
        for (Map.Entry<Function, LinkedHashSet<String>> entry : functionStrings.entrySet()) {
            Function fn = entry.getKey();
            String name = "hp1020_" + classify(entry.getValue()) + "_" + fn.getEntryPoint();
            name = name.replace(':', '_');
            assignedNames.put(fn, name);
            if (fn.getName().startsWith("FUN_")) {
                try {
                    fn.setName(name, SourceType.ANALYSIS);
                }
                catch (Exception ignored) {
                    // Duplicate or protected names are not important for this report.
                }
            }
        }
    }

    private void buildCallGraph() {
        FunctionIterator functions = currentProgram.getFunctionManager().getFunctions(true);
        while (functions.hasNext()) {
            Function fn = functions.next();
            LinkedHashSet<Function> callees = outgoing.computeIfAbsent(fn, k -> new LinkedHashSet<>());
            InstructionIterator instructions = currentProgram.getListing().getInstructions(fn.getBody(), true);
            while (instructions.hasNext()) {
                Instruction ins = instructions.next();
                for (Reference ref : ins.getReferencesFrom()) {
                    if (!ref.getReferenceType().isCall()) {
                        continue;
                    }
                    Function target = currentProgram.getFunctionManager().getFunctionAt(ref.getToAddress());
                    if (target == null) {
                        target = currentProgram.getFunctionManager().getFunctionContaining(ref.getToAddress());
                    }
                    if (target == null || target.equals(fn)) {
                        continue;
                    }
                    callees.add(target);
                    incoming.computeIfAbsent(target, k -> new LinkedHashSet<>()).add(fn);
                }
            }
        }
    }

    private void applyKnownHelperLabels() {
        labelAddress(0x10007430L, "hp1020_format_into_buffer_candidate");
        labelAddress(0x100169d4L, "hp1020_strlen_like");
        labelAddress(0x1001693cL, "hp1020_copy_string_candidate");
        labelAddress(0x1001b544L, "hp1020_append_string_to_buffer_candidate");
        labelAddress(0x1000dc00L, "hp1020_alloc_buffer_candidate");
        labelAddress(0x1000d6b0L, "hp1020_pjl_read_or_poll_candidate");
    }

    private void labelAddress(long rawAddress, String name) {
        Address address = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(rawAddress);
        Function fn = currentProgram.getFunctionManager().getFunctionAt(address);
        if (fn == null) {
            fn = currentProgram.getFunctionManager().getFunctionContaining(address);
        }
        if (fn == null) {
            return;
        }
        assignedNames.put(fn, name);
        if (fn.getName().startsWith("FUN_")) {
            try {
                fn.setName(name, SourceType.ANALYSIS);
            }
            catch (Exception ignored) {
                // Report labels still use assignedNames even if Ghidra refuses the rename.
            }
        }
    }

    private void writeReport(PrintWriter out, List<Function> seeds) {
        out.println("# HP 1020 Labeled Firmware Functions");
        out.println();
        out.println("Program: " + currentProgram.getName());
        out.println("Language: " + currentProgram.getLanguageID());
        out.println("Seed functions from interesting string references: " + seeds.size());
        out.println("Total functions: " + currentProgram.getFunctionManager().getFunctionCount());
        out.println();

        out.println("## Labeled Seed Functions");
        out.println();
        for (Function fn : seeds) {
            out.printf("### `%s` `%s`%n%n", fn.getEntryPoint(), displayName(fn));
            out.println("Referenced strings:");
            for (String s : functionStrings.getOrDefault(fn, new LinkedHashSet<>())) {
                out.println("- `" + escapeMd(s) + "`");
            }
            writeFunctionLinks(out, "Direct callees", outgoing.get(fn), 12);
            writeFunctionLinks(out, "Direct callers", incoming.get(fn), 12);
            out.println();
        }

        out.println("## Conservative Helper Labels");
        out.println();
        out.println("- `10007430` `hp1020_format_into_buffer_candidate`: used with destination buffer plus format/data arguments.");
        out.println("- `100169d4` `hp1020_strlen_like`: return value is used as a string/buffer offset.");
        out.println("- `1001693c` `hp1020_copy_string_candidate`: called after allocation/buffer preparation in PJL response construction.");
        out.println("- `1001b544` `hp1020_append_string_to_buffer_candidate`: heavily used to append literal strings to response buffers.");
        out.println("- `1000dc00` `hp1020_alloc_buffer_candidate`: called with computed output length before buffer population.");
        out.println("- `1000d6b0` `hp1020_pjl_read_or_poll_candidate`: used inside the `@PJL ECHO` scanning loop.");
        out.println();

        out.println("## Descriptor Table Anchors");
        out.println();
        if (tableDescriptors.isEmpty()) {
            out.println("No descriptor-table string references found.");
        }
        for (TableDescriptor descriptor : tableDescriptors) {
            out.printf("- `%s` string=`%s`", descriptor.refAddress, escapeMd(descriptor.stringValue));
            if (descriptor.handler != null) {
                out.printf(" handler=`%s` `%s`", descriptor.handler.getEntryPoint(), displayName(descriptor.handler));
            }
            out.print(" words=");
            out.println(formatWords(descriptor.words));
        }
        out.println();

        out.println("## Unowned Code String References");
        out.println();
        if (unownedCodeRefs.isEmpty()) {
            out.println("All instruction string references were associated with a function or nearby function.");
        }
        for (Map.Entry<Address, LinkedHashSet<String>> entry : unownedCodeRefs.entrySet()) {
            out.printf("- `%s` strings=%s%n", entry.getKey(), shortStringList(entry.getValue(), 4));
        }
        out.println();

        out.println("## Subsystem Clusters");
        writeCluster(out, "USB/Download", seedsMatching(seeds, "USB", "ACL", "DOWNLOAD"), 2);
        writeCluster(out, "PJL/Status", seedsMatching(seeds, "PJL", "FWVER", "USTATUS", "MFG", "MDL"), 2);
        writeCluster(out, "Device State", seedsMatching(seeds, "FUSER", "PAPER", "TONER", "JAM", "ERROR"), 2);
        writeCluster(out, "ThreadX/RTOS Diagnostics", seedsMatching(seeds, "THREAD", "TX_", "SEMAPHORE", "MUTEX", "QUEUE", "TIMER"), 2);
    }

    private void writeFunctionLinks(PrintWriter out, String title, Set<Function> fns, int limit) {
        out.println();
        out.println(title + ":");
        if (fns == null || fns.isEmpty()) {
            out.println("- none found");
            return;
        }

        List<Function> sorted = new ArrayList<>(fns);
        sorted.sort(Comparator.comparing(f -> f.getEntryPoint().toString()));
        int count = 0;
        for (Function fn : sorted) {
            if (count >= limit) {
                out.println("- ... " + (sorted.size() - limit) + " more");
                break;
            }
            out.printf("- `%s` `%s`%n", fn.getEntryPoint(), displayName(fn));
            count++;
        }
    }

    private void writeCluster(PrintWriter out, String title, List<Function> seeds, int depth) {
        out.println();
        out.println("### " + title);
        out.println();
        if (seeds.isEmpty()) {
            out.println("No seed functions found.");
            return;
        }

        LinkedHashSet<Function> cluster = expandCluster(seeds, depth);
        out.println("Seed count: " + seeds.size());
        out.println("Cluster size through call depth " + depth + ": " + cluster.size());
        out.println();
        for (Function fn : cluster) {
            out.printf("- `%s` `%s`", fn.getEntryPoint(), displayName(fn));
            LinkedHashSet<String> strings = functionStrings.get(fn);
            if (strings != null && !strings.isEmpty()) {
                out.print(" strings=");
                out.print(shortStringList(strings, 3));
            }
            out.println();
        }
    }

    private LinkedHashSet<Function> expandCluster(List<Function> seeds, int depth) {
        LinkedHashSet<Function> seen = new LinkedHashSet<>();
        Queue<FunctionDepth> queue = new ArrayDeque<>();
        for (Function seed : seeds) {
            seen.add(seed);
            queue.add(new FunctionDepth(seed, 0));
        }

        while (!queue.isEmpty()) {
            FunctionDepth current = queue.remove();
            if (current.depth >= depth) {
                continue;
            }
            List<Function> neighbors = new ArrayList<>();
            neighbors.addAll(outgoing.getOrDefault(current.function, new LinkedHashSet<>()));
            neighbors.addAll(incoming.getOrDefault(current.function, new LinkedHashSet<>()));
            neighbors.sort(Comparator.comparing(f -> f.getEntryPoint().toString()));
            for (Function next : neighbors) {
                if (seen.add(next)) {
                    queue.add(new FunctionDepth(next, current.depth + 1));
                }
            }
        }
        return seen;
    }

    private List<Function> seedsMatching(List<Function> seeds, String... terms) {
        List<Function> matches = new ArrayList<>();
        for (Function fn : seeds) {
            String haystack = String.join(" ", functionStrings.getOrDefault(fn, new LinkedHashSet<>())).toUpperCase(Locale.ROOT);
            for (String term : terms) {
                if (haystack.contains(term)) {
                    matches.add(fn);
                    break;
                }
            }
        }
        return matches;
    }

    private Function functionFromWord(long word, String stringValue) {
        if (word < 0x10000000L || word > 0x10200000L) {
            return null;
        }
        Address address = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(word);
        MemoryBlock block = currentProgram.getMemory().getBlock(address);
        if (block == null || !block.isExecute()) {
            return null;
        }

        Function fn = currentProgram.getFunctionManager().getFunctionAt(address);
        if (fn == null) {
            fn = currentProgram.getFunctionManager().getFunctionContaining(address);
        }
        if (fn == null) {
            try {
                String name = "hp1020_" + classify(Collections.singleton("descriptor:" + stringValue)) + "_" + address;
                createFunction(address, name);
                fn = currentProgram.getFunctionManager().getFunctionAt(address);
                if (fn != null) {
                    assignedNames.put(fn, name);
                }
            }
            catch (Exception ignored) {
                fn = currentProgram.getFunctionManager().getFunctionAt(address);
            }
        }
        return fn;
    }

    private Function nearestFunctionBefore(Address address, long maxDistance) {
        Function best = null;
        FunctionIterator functions = currentProgram.getFunctionManager().getFunctions(true);
        while (functions.hasNext()) {
            Function fn = functions.next();
            if (fn.getEntryPoint().compareTo(address) > 0) {
                break;
            }
            best = fn;
        }
        if (best == null) {
            return null;
        }
        long distance = address.subtract(best.getEntryPoint());
        if (distance >= 0 && distance <= maxDistance) {
            return best;
        }
        return null;
    }

    private List<Long> readWords(Address address, int count) {
        List<Long> words = new ArrayList<>();
        for (int i = 0; i < count; i++) {
            try {
                int raw = currentProgram.getMemory().getInt(address.add((long) i * 4));
                words.add(Integer.toUnsignedLong(raw));
            }
            catch (Exception e) {
                break;
            }
        }
        return words;
    }

    private void exportDecompilerOutput(List<Function> seeds, File decompDir) throws Exception {
        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);

        int exported = 0;
        for (Function fn : seeds) {
            if (exported >= 40) {
                break;
            }
            DecompileResults results = decompiler.decompileFunction(fn, 30, monitor);
            File outFile = new File(decompDir, fn.getEntryPoint() + "_" + displayName(fn) + ".c");
            try (PrintWriter out = new PrintWriter(new FileWriter(outFile))) {
                out.println("/*");
                out.println("Function: " + fn.getEntryPoint() + " " + displayName(fn));
                out.println("Strings:");
                for (String s : functionStrings.getOrDefault(fn, new LinkedHashSet<>())) {
                    out.println("- " + s);
                }
                out.println("*/");
                out.println();
                if (results.decompileCompleted() && results.getDecompiledFunction() != null) {
                    out.println(results.getDecompiledFunction().getC());
                }
                else {
                    out.println("/* Decompilation failed: " + results.getErrorMessage() + " */");
                }
            }
            exported++;
        }
        decompiler.dispose();
    }

    private String displayName(Function fn) {
        return assignedNames.getOrDefault(fn, fn.getName());
    }

    private boolean isInteresting(String value) {
        String upper = value.toUpperCase(Locale.ROOT);
        return upper.contains("PJL")
            || upper.contains("ACL")
            || upper.contains("USB")
            || upper.contains("THREAD")
            || upper.contains("TX_")
            || upper.contains("FUSER")
            || upper.contains("PAPER")
            || upper.contains("TONER")
            || upper.contains("FWVER")
            || upper.contains("MANGUSTA")
            || upper.contains("JAM")
            || upper.contains("ERROR")
            || upper.contains("SEMAPHORE")
            || upper.contains("MUTEX")
            || upper.contains("QUEUE")
            || upper.contains("TIMER");
    }

    private String classify(Set<String> strings) {
        String joined = String.join(" ", strings).toUpperCase(Locale.ROOT);
        String label;
        if (joined.contains("USB2IDLETHREAD")) {
            label = "usb2_idle_thread";
        }
        else if (joined.contains("USB2THREAD") || joined.contains("USB")) {
            label = "usb2_thread";
        }
        else if (joined.contains("AGIACLDOWNLOAD") || joined.contains("ACL")) {
            label = "acl_download";
        }
        else if (joined.contains("PJL") || joined.contains("FWVER") || joined.contains("MFG")) {
            label = "pjl_status";
        }
        else if (joined.contains("FUSER") || joined.contains("PAPER") || joined.contains("TONER") || joined.contains("JAM")) {
            label = "device_state";
        }
        else if (joined.contains("THREAD") || joined.contains("TX_") || joined.contains("SEMAPHORE") || joined.contains("MUTEX") || joined.contains("QUEUE") || joined.contains("TIMER")) {
            label = "threadx_diag";
        }
        else if (joined.contains("ERROR")) {
            label = "error_diag";
        }
        else {
            label = "string_ref";
        }
        return label;
    }

    private String compact(String value) {
        String s = value.replace("\r", "\\r").replace("\n", "\\n").replace("\t", "\\t").trim();
        if (s.length() > 140) {
            return s.substring(0, 137) + "...";
        }
        return s;
    }

    private String escapeMd(String value) {
        return value.replace("`", "'");
    }

    private String shortStringList(Set<String> strings, int limit) {
        List<String> items = new ArrayList<>(strings);
        List<String> shown = items.subList(0, Math.min(limit, items.size()));
        String suffix = items.size() > limit ? ", ..." : "";
        return "`" + escapeMd(String.join("`, `", shown)) + "`" + suffix;
    }

    private String formatWords(List<Long> words) {
        List<String> formatted = new ArrayList<>();
        for (Long word : words) {
            formatted.add(String.format("`0x%08x`", word));
        }
        return String.join(", ", formatted);
    }

    private static class FunctionDepth {
        final Function function;
        final int depth;

        FunctionDepth(Function function, int depth) {
            this.function = function;
            this.depth = depth;
        }
    }

    private static class TableDescriptor {
        final Address refAddress;
        final String stringValue;
        List<Long> words = new ArrayList<>();
        Function handler;

        TableDescriptor(Address refAddress, String stringValue) {
            this.refAddress = refAddress;
            this.stringValue = stringValue;
        }
    }
}
