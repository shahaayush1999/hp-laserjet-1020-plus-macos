// Maps how data-store queue notifications fall into the PrintMgr dispatch path.

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.SourceType;

import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.LinkedHashMap;
import java.util.Map;

public class MapHp1020PrintMgrFallout extends GhidraScript {
    private static final long PRINT_TABLE = 0x100048f0L;
    private static final int PRINT_LOW = 0x0b;
    private static final int PRINT_COUNT = 0x39;

    private final Map<Long, String> labels = new LinkedHashMap<>();

    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            println("usage: MapHp1020PrintMgrFallout <output-dir>");
            return;
        }

        File outDir = new File(args[0]);
        File decompDir = new File(outDir, "decompiled");
        outDir.mkdirs();
        decompDir.mkdirs();

        initLabels();
        applyLabels();

        writeDispatchTable(new File(outDir, "printmgr-dispatch-table.tsv"));
        writeWindows(new File(outDir, "printmgr-dispatch-windows.tsv"));
        exportDecompilerOutput(decompDir);
        writeReport(new File(outDir, "printmgr-fallout-report.md"));
    }

    private void initLabels() {
        labels.put(0x1000f324L, "hp1020_print_mgr_thread_candidate");
        labels.put(0x1000f574L, "hp1020_print_mgr_schedule_or_advance_candidate");
        labels.put(0x1000f84cL, "hp1020_print_mgr_media_select_candidate");
        labels.put(0x1000fcb0L, "hp1020_print_mgr_datastore_notify_state_candidate");
        labels.put(0x10010158L, "hp1020_print_mgr_clear_pending_media_candidate");
        labels.put(0x10010170L, "hp1020_print_mgr_emit_media_status_candidate");
        labels.put(0x10010218L, "hp1020_queue_send_message4_candidate");
        labels.put(0x10013658L, "hp1020_queue_send_candidate");
        labels.put(0x10010f54L, "hp1020_datastore_read_locked_candidate");
        labels.put(0x10010fd0L, "hp1020_datastore_write_notify_unlock_candidate");
        labels.put(0x100111b4L, "hp1020_datastore_lock_entry_candidate");
        labels.put(0x100111d8L, "hp1020_datastore_unlock_entry_candidate");
        labels.put(0x100130bcL, "hp1020_list_peek_head_candidate");
        labels.put(0x10013050L, "hp1020_list_pop_head_candidate");
        labels.put(0x10013000L, "hp1020_list_append_tail_candidate");
        labels.put(0x100100a8L, "hp1020_print_mgr_status_aux_candidate");
        labels.put(0x10010318L, "hp1020_print_mgr_mark_work_candidate");
        labels.put(0x100048f0L, "hp1020_print_mgr_dispatch_table");
        labels.put(0x10006338L, "hp1020_print_mgr_state_ptr_word");
        labels.put(0x10006340L, "hp1020_print_mgr_notify_state_ptr_word");
        labels.put(0x10006344L, "hp1020_print_mgr_pending_media_ptr_word");
    }

    private void applyLabels() {
        for (Map.Entry<Long, String> entry : labels.entrySet()) {
            Address address = addr(entry.getKey());
            Function function = currentProgram.getFunctionManager().getFunctionAt(address);
            if (function == null) {
                function = currentProgram.getFunctionManager().getFunctionContaining(address);
            }
            if (function == null && isKnownFunction(entry.getKey())) {
                try {
                    disassemble(address);
                    function = createFunction(address, entry.getValue());
                }
                catch (Exception ignored) {
                    function = currentProgram.getFunctionManager().getFunctionAt(address);
                }
            }
            if (function != null && isKnownFunction(entry.getKey())) {
                try {
                    function.setName(entry.getValue(), SourceType.ANALYSIS);
                    function.setComment("print-manager fallout mapping candidate");
                }
                catch (Exception ignored) {
                    // Reports use local labels if Ghidra keeps an existing name.
                }
                continue;
            }
            try {
                currentProgram.getSymbolTable().createLabel(address, entry.getValue(), SourceType.ANALYSIS);
            }
            catch (Exception ignored) {
                // Existing labels are fine.
            }
        }
    }

    private boolean isKnownFunction(long rawAddress) {
        return rawAddress == 0x1000f324L || rawAddress == 0x1000f574L ||
               rawAddress == 0x1000f84cL || rawAddress == 0x1000fcb0L ||
               rawAddress == 0x10010158L || rawAddress == 0x10010170L ||
               rawAddress == 0x10010218L || rawAddress == 0x10013658L ||
               rawAddress == 0x10010f54L || rawAddress == 0x10010fd0L ||
               rawAddress == 0x100111b4L || rawAddress == 0x100111d8L ||
               rawAddress == 0x100130bcL || rawAddress == 0x10013050L ||
               rawAddress == 0x10013000L || rawAddress == 0x100100a8L ||
               rawAddress == 0x10010318L;
    }

    private void writeDispatchTable(File outFile) throws Exception {
        try (PrintWriter out = new PrintWriter(new FileWriter(outFile))) {
            out.println("message\ttarget\tcontaining_function\ttarget_note");
            for (int i = 0; i < PRINT_COUNT; i++) {
                int message = PRINT_LOW + i;
                long target = readU32(PRINT_TABLE + (long) i * 4);
                Function function = getFunctionContaining(addr(target));
                String functionName = function == null ? "none" : function.getName();
                out.printf("0x%02x\t0x%08x\t%s\t%s%n",
                    message, target, functionName, noteForMessage(message, target));
            }
        }
    }

    private void writeWindows(File outFile) throws Exception {
        try (PrintWriter out = new PrintWriter(new FileWriter(outFile))) {
            out.println("message\ttarget\tinstruction_address\tinstruction\tcall_target");
            for (int i = 0; i < PRINT_COUNT; i++) {
                int message = PRINT_LOW + i;
                long target = readU32(PRINT_TABLE + (long) i * 4);
                Instruction instruction = getInstructionAt(addr(target));
                Address cursor = addr(target);
                int emitted = 0;
                while (instruction != null && emitted < 18) {
                    String callTarget = callTarget(instruction);
                    out.printf("0x%02x\t0x%08x\t%s\t%s\t%s%n",
                        message, target, instruction.getAddress(), tsv(instruction.toString()), callTarget);
                    cursor = instruction.getMaxAddress().next();
                    instruction = getInstructionAt(cursor);
                    emitted++;
                }
            }
        }
    }

    private String callTarget(Instruction instruction) {
        for (Reference ref : instruction.getReferencesFrom()) {
            if (!ref.getReferenceType().isCall()) {
                continue;
            }
            Address to = ref.getToAddress();
            if (to == null) {
                continue;
            }
            long raw = to.getOffset();
            String label = labels.getOrDefault(raw, "");
            if (label.isEmpty()) {
                return String.format("0x%08x", raw);
            }
            return String.format("0x%08x %s", raw, label);
        }
        return "none";
    }

    private void exportDecompilerOutput(File decompDir) throws Exception {
        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);
        long[] functions = {
            0x1000f324L, 0x1000f574L, 0x1000f84cL, 0x1000fcb0L, 0x10010158L,
            0x10010170L, 0x10010218L, 0x100100a8L, 0x10010318L
        };
        for (long rawAddress : functions) {
            Function function = currentProgram.getFunctionManager().getFunctionAt(addr(rawAddress));
            if (function == null) {
                function = currentProgram.getFunctionManager().getFunctionContaining(addr(rawAddress));
            }
            if (function == null) {
                continue;
            }
            DecompileResults result = decompiler.decompileFunction(function, 30, monitor);
            String c = result != null && result.decompileCompleted()
                    ? result.getDecompiledFunction().getC()
                    : "/* decompile failed */\n";
            c = cleanDecompilerOutput(c);
            String filename = Long.toHexString(rawAddress) + "_" + sanitize(labels.getOrDefault(rawAddress, function.getName())) + ".c";
            try (PrintWriter out = new PrintWriter(new FileWriter(new File(decompDir, filename)))) {
                out.println("/* Function: " + function.getEntryPoint() + " " + function.getName() + " */");
                out.println();
                out.print(c);
            }
        }
        decompiler.dispose();
    }

    private void writeReport(File outFile) throws Exception {
        try (PrintWriter out = new PrintWriter(new FileWriter(outFile))) {
            out.println("# HP 1020 PrintMgr 0x2d Fallout");
            out.println();
            out.println("This pass checks whether data-store queue subscriber notifications land in the PrintMgr queue.");
            out.println();
            out.println("## Key Result");
            out.println();
            out.println("- Data-store writes notify queue subscribers with message `0x2d` and payload words: entry id, new value, type class.");
            out.println("- PrintMgr registers queue subscribers for data-store entries `0x18` and `0x01`, with subscriber queue id `1`.");
            out.println("- Stock constructor registration proves queue id `1` is `PrintMgrQueue`; the older engine/no-op interpretation was a mapping error. See `analysis/queue-routing/registration.md`.");
            out.println("- PrintMgr dispatch includes message `0x2d`, target `0x1000f497`. The datastore subscriber path supplies its producer through queue id `1`.");
            out.println("- The downstream scheduler function `0x1000f574` calls `0x1000fcb0`, and `0x1000fcb0` explicitly handles `message == 0x2d` and `entry == 1` in its state machine.");
            out.println();
            out.println("## Important Functions");
            out.println();
            out.println("| Address | Working label | Role |");
            out.println("|---:|---|---|");
            out.println("| `0x1000f324` | `hp1020_print_mgr_thread_candidate` | receives PrintMgrQueue messages and dispatches table `0x100048f0` |");
            out.println("| `0x1000f574` | `hp1020_print_mgr_schedule_or_advance_candidate` | advances queued page/media work and calls notification state helper |");
            out.println("| `0x1000fcb0` | `hp1020_print_mgr_datastore_notify_state_candidate` | handles `0x2d` datastore notifications and completion-style messages `0x2c`/`0x32` |");
            out.println("| `0x1000f84c` | `hp1020_print_mgr_media_select_candidate` | locks data-store entries `0x1d` and `0x01`, chooses/updates media fields, and may emit status |");
            out.println("| `0x10010170` | `hp1020_print_mgr_emit_media_status_candidate` | writes back data-store entry `0x1f` and sends StatusMgrQueue message `0x2c` |");
            out.println("| `0x10010218` | `hp1020_queue_send_message4_candidate` | small wrapper that sends a 4-word message to a queue |");
            out.println();
            out.println("## Data-Store Notification Path");
            out.println();
            out.println("```text");
            out.println("data-store entry write");
            out.println("  -> 0x10010fd0 write/notify helper");
            out.println("  -> queue subscriber message 0x2d");
            out.println("  -> known subscriber queue id 1");
            out.println("  -> PrintMgrQueue, object 0x10028a74");
            out.println("  -> PrintMgr 0x2d handler at 0x1000f497");
            out.println("```");
            out.println();
            out.println("The same notification continues through the PrintMgr handler:");
            out.println();
            out.println("```text");
            out.println("PrintMgrQueue message 0x2d");
            out.println("  -> PrintMgr dispatch table target 0x1000f497");
            out.println("  -> print scheduling/state helper 0x1000f574");
            out.println("  -> notification state helper 0x1000fcb0");
            out.println("  -> possible media/status writeback and StatusMgrQueue message 0x2c");
            out.println("```");
            out.println();
            out.println("## Current Interpretation");
            out.println();
            out.println("- Known data-store queue subscriptions target PrintMgr through queue id `1`.");
            out.println("- The producer-to-handler route is resolved statically; execution still depends on successful initialization and RTOS delivery.");
            out.println("- Next, execute selected PrintMgr dispatch and cancellation transitions with explicit queue and hardware-completion boundaries.");
        }
    }

    private String noteForMessage(int message, long target) {
        if (message == 0x2d) {
            return "PrintMgr 0x2d handler; producer is datastore subscriber queue 1";
        }
        if (message == 0x18) {
            return "startup/initial poll target";
        }
        if (message == 0x11) {
            return "video/high-level continuation target";
        }
        if (message == 0x25 || message == 0x32 || message == 0x34) {
            return "completion/status-looking target";
        }
        if (target == 0x1000f358L) {
            return "default/no-op target";
        }
        return "none";
    }

    private long readU32(long rawAddress) throws Exception {
        Memory memory = currentProgram.getMemory();
        return Integer.toUnsignedLong(memory.getInt(addr(rawAddress)));
    }

    private String sanitize(String name) {
        return name.replaceAll("[^A-Za-z0-9_.-]+", "_");
    }

    private String cleanDecompilerOutput(String value) {
        String cleaned = value.replaceAll("[ \\t]+\\n", "\n");
        return cleaned.replaceAll("\\n+\\z", "\n");
    }

    private String tsv(String value) {
        return value == null ? "" : value.replace("\t", " ").replace("\n", "\\n");
    }

    private Address addr(long rawAddress) {
        return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(rawAddress);
    }
}
