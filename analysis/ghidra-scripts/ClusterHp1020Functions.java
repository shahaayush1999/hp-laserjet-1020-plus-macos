// Exports a coarse function/call cluster map for the HP LaserJet 1020 firmware.

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSetView;
import ghidra.program.model.data.StringDataInstance;
import ghidra.program.model.listing.Data;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.RefType;
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

public class ClusterHp1020Functions extends GhidraScript {
    private final Map<Function, String> labels = new LinkedHashMap<>();

    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            println("usage: ClusterHp1020Functions <output-dir>");
            return;
        }

        File outDir = new File(args[0]);
        File decompDir = new File(outDir, "seed-decompiled");
        outDir.mkdirs();
        decompDir.mkdirs();

        applyLabels();

        List<FunctionRecord> records = collectFunctionRecords();
        Map<String, List<FunctionRecord>> clusters = cluster(records);
        decompileSeeds(records, decompDir);

        try (PrintWriter out = new PrintWriter(new FileWriter(new File(outDir, "call-clusters.md")))) {
            writeReport(out, records, clusters);
        }
    }

    private void applyLabels() {
        label(0x10007430L, "hp1020_format_into_buffer_candidate");
        label(0x10007c00L, "hp1020_usb_register_transfer_candidate");
        label(0x10008c24L, "hp1020_usb_control_tx_data_stage_candidate");
        label(0x10008fb0L, "hp1020_usb_drain_pending_queue_candidate");
        label(0x10008ff0L, "hp1020_usb2_thread");
        label(0x10009934L, "hp1020_usb2_idle_thread");
        label(0x1000ad44L, "hp1020_acl_download");
        label(0x1000b3f8L, "hp1020_pjl_ustatus_result_builder");
        label(0x1000bd04L, "hp1020_pjl_info_capabilities_builder");
        label(0x1000cdb0L, "hp1020_pjl_echo_matcher");
        label(0x1000d6b0L, "hp1020_pjl_read_or_poll_candidate");
        label(0x1000dc00L, "hp1020_alloc_buffer_candidate");
        label(0x10011178L, "hp1020_datastore_get_value_candidate");
        label(0x1001693cL, "hp1020_copy_string_candidate");
        label(0x100169d4L, "hp1020_strlen_like");
        label(0x10017d28L, "threadx_queue_receive_candidate");
        label(0x10018274L, "threadx_thread_create_candidate");
        label(0x1001b544L, "hp1020_append_string_to_buffer_candidate");
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
                // The report uses local labels even if Ghidra rejects a rename.
            }
        }
    }

    private List<FunctionRecord> collectFunctionRecords() {
        List<FunctionRecord> records = new ArrayList<>();
        var functions = currentProgram.getFunctionManager().getFunctions(true);
        while (functions.hasNext()) {
            Function fn = functions.next();
            FunctionRecord record = new FunctionRecord(fn);
            scanFunction(record);
            records.add(record);
        }
        records.sort(Comparator.comparing(r -> r.entry));
        return records;
    }

    private void scanFunction(FunctionRecord record) {
        AddressSetView body = record.function.getBody();
        record.size = body.getNumAddresses();
        InstructionIterator instructions = currentProgram.getListing().getInstructions(body, true);
        while (instructions.hasNext()) {
            Instruction instruction = instructions.next();
            for (Reference ref : instruction.getReferencesFrom()) {
                Address to = ref.getToAddress();
                if (to == null) {
                    continue;
                }
                Function callee = currentProgram.getFunctionManager().getFunctionAt(to);
                if (callee != null && ref.getReferenceType().isCall()) {
                    record.calls.add(displayName(callee) + "@" + callee.getEntryPoint());
                }
                Data data = currentProgram.getListing().getDataAt(to);
                if (data != null) {
                    StringDataInstance s = StringDataInstance.getStringDataInstance(data);
                    if (s != null && s.getStringValue() != null) {
                        record.strings.add(compact(s.getStringValue()));
                    }
                }
                long off = to.getOffset();
                if ((off & 0xffff0000L) == 0xb3000000L || (off & 0xffff0000L) == 0xb3010000L) {
                    record.mmioRefs.add(to.toString());
                }
                if (off >= 0x90000000L && off < 0x90100000L) {
                    record.sramRefs.add(to.toString());
                }
            }
            for (Object obj : instruction.getOpObjects(0)) {
                classifyOperand(record, obj);
            }
            for (Object obj : instruction.getOpObjects(1)) {
                classifyOperand(record, obj);
            }
            for (Object obj : instruction.getOpObjects(2)) {
                classifyOperand(record, obj);
            }
        }

        for (Reference ref : getReferencesTo(record.function.getEntryPoint())) {
            if (ref.getReferenceType().isCall()) {
                Function caller = currentProgram.getFunctionManager().getFunctionContaining(ref.getFromAddress());
                if (caller != null) {
                    record.callers.add(displayName(caller) + "@" + caller.getEntryPoint());
                }
            }
        }
    }

    private void classifyOperand(FunctionRecord record, Object obj) {
        if (!(obj instanceof ghidra.program.model.scalar.Scalar)) {
            return;
        }
        long value = ((ghidra.program.model.scalar.Scalar) obj).getUnsignedValue();
        if ((value & 0xffff0000L) == 0xb3000000L || (value & 0xffff0000L) == 0xb3010000L) {
            record.mmioRefs.add(String.format("0x%08x", value));
        }
        if (value >= 0x90000000L && value < 0x90100000L) {
            record.sramRefs.add(String.format("0x%08x", value));
        }
    }

    private Map<String, List<FunctionRecord>> cluster(List<FunctionRecord> records) {
        Map<String, List<FunctionRecord>> clusters = new LinkedHashMap<>();
        clusters.put("USB control and enumeration", new ArrayList<>());
        clusters.put("PJL, ACL, and printer identity/status", new ArrayList<>());
        clusters.put("Memory/string/runtime helpers", new ArrayList<>());
        clusters.put("RTOS/threading/scheduler candidates", new ArrayList<>());
        clusters.put("Hardware register or SRAM touch points", new ArrayList<>());
        clusters.put("Other or unresolved", new ArrayList<>());

        for (FunctionRecord record : records) {
            String name = displayName(record.function);
            String text = (name + " " + String.join(" ", record.strings) + " " + String.join(" ", record.calls)).toLowerCase();
            long entry = record.function.getEntryPoint().getOffset();
            String cluster = "Other or unresolved";
            if (name.contains("usb") || (entry >= 0x10007c00L && entry <= 0x10009b00L) ||
                text.contains("get_descriptor") || text.contains("usb2")) {
                cluster = "USB control and enumeration";
            }
            else if (name.contains("pjl") || name.contains("acl") || text.contains("@pjl") ||
                text.contains("ustatus") || text.contains("paper") || text.contains("fuser") ||
                text.contains("toner") || text.contains("mfg:") || text.contains("fwver")) {
                cluster = "PJL, ACL, and printer identity/status";
            }
            else if (name.contains("strlen") || name.contains("append_string") || name.contains("alloc") ||
                name.contains("format") || text.contains("append_string") || text.contains("strlen")) {
                cluster = "Memory/string/runtime helpers";
            }
            else if (name.contains("threadx") || name.contains("thread") || entry >= 0x10017600L) {
                cluster = "RTOS/threading/scheduler candidates";
            }
            else if (!record.mmioRefs.isEmpty() || !record.sramRefs.isEmpty()) {
                cluster = "Hardware register or SRAM touch points";
            }
            clusters.get(cluster).add(record);
        }
        return clusters;
    }

    private void decompileSeeds(List<FunctionRecord> records, File decompDir) throws Exception {
        Set<Function> seeds = new LinkedHashSet<>();
        for (FunctionRecord record : records) {
            String name = displayName(record.function);
            if (labels.containsKey(record.function) || name.contains("usb") || name.contains("pjl") ||
                name.contains("acl") || !record.mmioRefs.isEmpty()) {
                seeds.add(record.function);
            }
        }
        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);
        int emitted = 0;
        for (Function fn : seeds) {
            if (emitted >= 60) {
                break;
            }
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
            emitted++;
        }
        decompiler.dispose();
    }

    private void writeReport(PrintWriter out, List<FunctionRecord> records, Map<String, List<FunctionRecord>> clusters) {
        out.println("# HP 1020 Function Call Clusters");
        out.println();
        out.println("This is a coarse automated clustering pass over Ghidra functions. It is intended to guide manual reverse engineering, not to be treated as final naming.");
        out.println();
        out.printf("- Total functions: `%d`%n", records.size());
        out.println("- Known labels are seeded from earlier USB/PJL/identity passes.");
        out.println("- Hardware references are partial because many MMIO addresses are loaded through literal tables.");
        out.println();

        out.println("## Cluster Counts");
        out.println();
        for (Map.Entry<String, List<FunctionRecord>> entry : clusters.entrySet()) {
            out.printf("- %s: `%d`%n", entry.getKey(), entry.getValue().size());
        }
        out.println();

        for (Map.Entry<String, List<FunctionRecord>> entry : clusters.entrySet()) {
            out.printf("## %s%n%n", entry.getKey());
            List<FunctionRecord> sorted = new ArrayList<>(entry.getValue());
            sorted.sort(Comparator
                .comparing((FunctionRecord r) -> !labels.containsKey(r.function))
                .thenComparing((FunctionRecord r) -> -r.size)
                .thenComparing(r -> r.entry));
            int limit = entry.getKey().equals("Other or unresolved") ? 40 : 80;
            int count = 0;
            for (FunctionRecord record : sorted) {
                if (count++ >= limit) {
                    out.printf("- ... `%d` more%n", sorted.size() - limit);
                    break;
                }
                out.printf("### `%s` `%s`%n%n", record.entry, displayName(record.function));
                out.printf("- size: `%d` bytes/addresses%n", record.size);
                out.printf("- callers: `%d`; calls: `%d`%n", record.callers.size(), record.calls.size());
                if (!record.calls.isEmpty()) {
                    out.printf("- calls: `%s`%n", compact(String.join("`, `", first(record.calls, 8))));
                }
                if (!record.strings.isEmpty()) {
                    out.printf("- strings: `%s`%n", compact(String.join("`, `", first(record.strings, 8))));
                }
                if (!record.mmioRefs.isEmpty()) {
                    out.printf("- MMIO refs: `%s`%n", compact(String.join("`, `", first(record.mmioRefs, 10))));
                }
                if (!record.sramRefs.isEmpty()) {
                    out.printf("- SRAM refs: `%s`%n", compact(String.join("`, `", first(record.sramRefs, 10))));
                }
                out.println();
            }
        }
    }

    private List<String> first(Set<String> values, int limit) {
        List<String> result = new ArrayList<>();
        int count = 0;
        for (String value : values) {
            if (count++ >= limit) {
                break;
            }
            result.add(value);
        }
        return result;
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
        return s.length() > 160 ? s.substring(0, 157) + "..." : s;
    }

    private static class FunctionRecord {
        final Function function;
        final String entry;
        long size;
        final Set<String> callers = new LinkedHashSet<>();
        final Set<String> calls = new LinkedHashSet<>();
        final Set<String> strings = new LinkedHashSet<>();
        final Set<String> mmioRefs = new LinkedHashSet<>();
        final Set<String> sramRefs = new LinkedHashSet<>();

        FunctionRecord(Function function) {
            this.function = function;
            this.entry = function.getEntryPoint().toString();
        }
    }
}
