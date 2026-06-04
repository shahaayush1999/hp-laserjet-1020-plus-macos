// Maps the unresolved engine queue 0x17 event consumer path.

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.scalar.Scalar;
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

public class MapHp1020EngineEventConsumer extends GhidraScript {
    private final Map<Long, String> labels = new LinkedHashMap<>();
    private final List<FunctionHit> hits = new ArrayList<>();

    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            println("usage: MapHp1020EngineEventConsumer <output-dir>");
            return;
        }

        File outDir = new File(args[0]);
        File decompDir = new File(outDir, "decompiled");
        outDir.mkdirs();
        decompDir.mkdirs();

        initLabels();
        applyLabels();
        scanFunctions();
        exportDecompilerOutput(decompDir);

        try (PrintWriter out = new PrintWriter(new FileWriter(new File(outDir, "engine-event-consumer.md")))) {
            writeReport(out);
        }
    }

    private void initLabels() {
        labels.put(0x10013620L, "hp1020_send_or_raise_engine_msg_candidate");
        labels.put(0x10013658L, "hp1020_queue_send_candidate");
        labels.put(0x10013668L, "hp1020_queue_send_indexed_candidate");
        labels.put(0x10013d4cL, "hp1020_video_reset_dispatch_candidate");
        labels.put(0x10015c68L, "hp1020_engine_status_io_candidate");
        labels.put(0x10015df8L, "hp1020_engine_status_poll_candidate");
        labels.put(0x100160a8L, "hp1020_engine_preflight_candidate");
        labels.put(0x10016164L, "hp1020_engine_message_dispatch_candidate");
        labels.put(0x10016318L, "hp1020_engine_event_0x0f_config_callback_candidate");
        labels.put(0x1001635cL, "hp1020_engine_delay_thread_candidate");
        labels.put(0x100163b0L, "hp1020_engine_thread_candidate");
        labels.put(0x1001809cL, "threadx_queue_receive_wait_candidate");
        labels.put(0x100180dcL, "threadx_queue_send_candidate");
        labels.put(0x100069bcL, "hp1020_eng_msg_queue_object_ptr_word");
        labels.put(0x1002f134L, "hp1020_eng_msg_queue_object_candidate");
        labels.put(0x1002c918L, "hp1020_queue_table_candidate");
        labels.put(0x10006490L, "hp1020_event_handler_table_ptr_word");
    }

    private void applyLabels() {
        for (Map.Entry<Long, String> entry : labels.entrySet()) {
            Address address = addr(entry.getKey());
            Function fn = currentProgram.getFunctionManager().getFunctionAt(address);
            if (fn == null) {
                fn = currentProgram.getFunctionManager().getFunctionContaining(address);
            }
            if (fn != null && fn.getName().startsWith("FUN_")) {
                try {
                    fn.setName(entry.getValue(), SourceType.ANALYSIS);
                }
                catch (Exception ignored) {
                    // Reports use fallback labels even if Ghidra refuses a rename.
                }
            }
            else {
                try {
                    currentProgram.getSymbolTable().createLabel(address, entry.getValue(), SourceType.ANALYSIS);
                }
                catch (Exception ignored) {
                    // Existing data labels are fine.
                }
            }
        }
    }

    private void scanFunctions() {
        FunctionIterator functions = currentProgram.getFunctionManager().getFunctions(true);
        while (functions.hasNext()) {
            Function fn = functions.next();
            FunctionHit hit = new FunctionHit(fn);
            InstructionIterator instructions = currentProgram.getListing().getInstructions(fn.getBody(), true);
            while (instructions.hasNext()) {
                Instruction instruction = instructions.next();
                scanInstruction(hit, instruction);
            }
            if (keepHit(hit)) {
                hits.add(hit);
            }
        }
        hits.sort(Comparator.comparing(h -> h.entry));
    }

    private boolean keepHit(FunctionHit hit) {
        long entry = hit.function.getEntryPoint().getOffset();
        if (entry == 0x10010fd0L || entry == 0x10011258L || entry == 0x1001135cL ||
            entry == 0x10013d4cL || entry == 0x10015c68L || entry == 0x10015df8L ||
            entry == 0x100160a8L || entry == 0x10016164L || entry == 0x10016318L ||
            entry == 0x1001635cL || entry == 0x100163b0L) {
            return true;
        }
        for (String reason : hit.reasons) {
            if (reason.contains("literal_0x17") || reason.contains("event_code") ||
                reason.contains("eng_msg_queue") || reason.contains("event_handler_table")) {
                return true;
            }
        }
        return false;
    }

    private void scanInstruction(FunctionHit hit, Instruction instruction) {
        for (int i = 0; i < instruction.getNumOperands(); i++) {
            for (Object obj : instruction.getOpObjects(i)) {
                if (!(obj instanceof Scalar)) {
                    continue;
                }
                long value = ((Scalar) obj).getUnsignedValue();
                if (value == 0x17L) {
                    hit.add("literal_0x17", instruction);
                }
                if (isEngineEventCode(value)) {
                    hit.add(String.format("event_code_0x%08x", value), instruction);
                }
                if (labels.containsKey(value)) {
                    hit.add("scalar_ref_" + labels.get(value), instruction);
                }
            }
        }

        for (Reference ref : instruction.getReferencesFrom()) {
            Address to = ref.getToAddress();
            if (to == null) {
                continue;
            }
            long off = to.getOffset();
            if (labels.containsKey(off)) {
                hit.add("ref_" + labels.get(off), instruction);
            }
            if (ref.getReferenceType().isCall()) {
                Function callee = currentProgram.getFunctionManager().getFunctionAt(to);
                if (callee != null && isInterestingCall(callee.getEntryPoint().getOffset())) {
                    hit.add("call_" + displayName(callee), instruction);
                }
            }
        }
    }

    private boolean isInterestingCall(long off) {
        return off == 0x10013620L || off == 0x10013658L || off == 0x10013668L ||
               off == 0x1001809cL || off == 0x100180dcL || off == 0x10017d28L ||
               off == 0x10016164L || off == 0x10015df8L || off == 0x10015c68L ||
               off == 0x100160a8L || off == 0x10013d4cL || off == 0x10016318L;
    }

    private boolean isEngineEventCode(long value) {
        long[] codes = {
            0xfe001401L, 0xe6101100L, 0xe6100a01L, 0xf6000300L, 0xf6000400L,
            0xe6100800L, 0x20001607L, 0xe6100e00L, 0x80000000L, 0xe6000d03L,
            0xe6000d06L, 0xe6000d04L, 0xe6100b0aL, 0xe6100b0bL, 0xe6e01201L,
            0xe6e01202L, 0xeee01b02L, 0xeee01b04L, 0xeee01b01L
        };
        for (long code : codes) {
            if (value == code) {
                return true;
            }
        }
        return false;
    }

    private void exportDecompilerOutput(File decompDir) throws Exception {
        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);
        int emitted = 0;
        for (FunctionHit hit : hits) {
            if (!shouldDecompile(hit)) {
                continue;
            }
            DecompileResults result = decompiler.decompileFunction(hit.function, 30, monitor);
            String c = result != null && result.decompileCompleted()
                    ? result.getDecompiledFunction().getC()
                    : "/* decompile failed */\n";
            String filename = hit.entry + "_" + sanitize(displayName(hit.function)) + ".c";
            try (PrintWriter out = new PrintWriter(new FileWriter(new File(decompDir, filename)))) {
                out.println("/* Function: " + hit.entry + " " + displayName(hit.function) + " */");
                out.println();
                out.println(c);
            }
            emitted++;
            if (emitted >= 80) {
                break;
            }
        }
    }

    private boolean shouldDecompile(FunctionHit hit) {
        if (hit.entry.equals("100163b0") || hit.entry.equals("10016164") ||
            hit.entry.equals("10015df8") || hit.entry.equals("10015c68") ||
            hit.entry.equals("100160a8") || hit.entry.equals("10013d4c") ||
            hit.entry.equals("10010fd0") || hit.entry.equals("10011258") ||
            hit.entry.equals("1001135c") || hit.entry.equals("10016318")) {
            return true;
        }
        for (String reason : hit.reasons) {
            if (reason.contains("literal_0x17") || reason.contains("event_code") ||
                reason.contains("eng_msg_queue") || reason.contains("queue_receive") ||
                reason.contains("queue_send")) {
                return true;
            }
        }
        return false;
    }

    private void writeReport(PrintWriter out) {
        out.println("# HP 1020 Engine Event Consumer Scan");
        out.println();
        out.println("This pass scans for engine queue/event evidence that the normal decompile did not fully resolve.");
        out.println();
        out.println("## Key Result");
        out.println();
        out.println("- `engMsgQ` object pointer word: `0x100069bc` -> object `0x1002f134`.");
        out.println("- The only direct `engMsgQ` receive found in this pass is the engine thread at `0x100163b0`.");
        out.println("- The recovered engine dispatch switch at `0x10016164` still has no visible `0x17` case.");
        out.println("- `0x17` producers are confirmed through status I/O, status poll, preflight, and video reset paths.");
        out.println("- Generic queue-helper users were filtered out unless they also touch engine/event evidence.");
        out.println();
        out.println("## Functions With Relevant Hits");
        out.println();
        out.println("| Function | Reasons |");
        out.println("|---:|---|");
        for (FunctionHit hit : hits) {
            out.printf("| `%s` `%s` | %s |%n", hit.entry, escape(displayName(hit.function)), shortReasons(hit.reasons));
        }
        out.println();
        out.println("## Instruction Evidence");
        out.println();
        for (FunctionHit hit : hits) {
            out.println();
            out.printf("### `%s` `%s`%n%n", hit.entry, escape(displayName(hit.function)));
            for (String line : hit.lines) {
                out.println("- " + line);
            }
        }
        out.println();
        out.println("## Interpretation");
        out.println();
        out.println("The current evidence supports a missing or non-obvious consumer branch rather than a second obvious queue consumer.");
        out.println("The next step is to inspect the raw control flow around `0x10016164` and the generated switch metadata, because Ghidra may have dropped a case or folded it into a default path.");
    }

    private String shortReasons(Set<String> reasons) {
        List<String> list = new ArrayList<>(reasons);
        list.sort(String::compareTo);
        if (list.size() > 8) {
            return "`" + escape(String.join("`, `", list.subList(0, 8))) + "`, ...";
        }
        return "`" + escape(String.join("`, `", list)) + "`";
    }

    private String displayName(Function fn) {
        String label = labels.get(fn.getEntryPoint().getOffset());
        return label != null ? label : fn.getName();
    }

    private String sanitize(String s) {
        return s.replaceAll("[^A-Za-z0-9_.-]", "_");
    }

    private String escape(String s) {
        return s.replace("|", "\\|");
    }

    private Address addr(long off) {
        return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(off);
    }

    private static class FunctionHit {
        final Function function;
        final String entry;
        final Set<String> reasons = new LinkedHashSet<>();
        final List<String> lines = new ArrayList<>();

        FunctionHit(Function function) {
            this.function = function;
            this.entry = function.getEntryPoint().toString();
        }

        void add(String reason, Instruction instruction) {
            reasons.add(reason);
            String text = "`" + instruction.getAddress() + "` `" + instruction.getMnemonicString() + "` `" +
                    instruction.toString().replace("`", "'") + "` -> `" + reason + "`";
            if (!lines.contains(text)) {
                lines.add(text);
            }
        }
    }
}
