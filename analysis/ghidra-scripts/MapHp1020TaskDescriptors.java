// Maps thread/task/queue descriptor tables anchored by human-readable names.

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.data.StringDataInstance;
import ghidra.program.model.listing.Data;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
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

public class MapHp1020TaskDescriptors extends GhidraScript {
    private static final String[] TASK_NAME_NEEDLES = {
        "USB2IdleThread",
        "usbIoFlags",
        "USB2Thread",
        "agiACLDownload",
        "Job Mgr Queue",
        "PrintMgrQueue",
        "PrintMgr",
        "StatusMgrQueue",
        "DelayMgr Semaphore",
        "DelayMgr Msg Queue",
        "tDelayMgrRcvMsg",
        "?Video Queue",
        "tEngine",
        "tEngineDelay",
        "initTimer",
        "System Timer Thread"
    };

    private final Map<Function, String> labels = new LinkedHashMap<>();

    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            println("usage: MapHp1020TaskDescriptors <output-dir>");
            return;
        }

        File outDir = new File(args[0]);
        File decompDir = new File(outDir, "task-decompiled");
        outDir.mkdirs();
        decompDir.mkdirs();

        applyLabels();

        List<TaskAnchor> anchors = collectTaskAnchors();
        Set<Function> relatedFunctions = collectRelatedFunctions(anchors);
        decompile(relatedFunctions, decompDir);

        try (PrintWriter out = new PrintWriter(new FileWriter(new File(outDir, "task-descriptors.md")))) {
            writeReport(out, anchors, relatedFunctions);
        }
    }

    private void applyLabels() {
        label(0x10007cd0L, "hp1020_usb2_start_thread_candidate");
        label(0x10008ff0L, "hp1020_usb2_thread");
        label(0x10009934L, "hp1020_usb2_idle_thread");
        label(0x1000ad44L, "hp1020_acl_download");
        label(0x1000e414L, "hp1020_job_mgr_thread_candidate");
        label(0x1000f324L, "hp1020_print_mgr_thread_candidate");
        label(0x10010590L, "hp1020_status_mgr_thread_candidate");
        label(0x10010b0cL, "hp1020_delay_mgr_receive_thread_candidate");
        label(0x1001146cL, "hp1020_data_store_thread_candidate");
        label(0x1001215cL, "hp1020_queue_receive_wrapper_candidate");
        label(0x100138fcL, "hp1020_init_timer_candidate");
        label(0x100139e4L, "hp1020_control_panel_thread_candidate");
        label(0x10013c18L, "hp1020_video_thread_candidate");
        label(0x1001635cL, "hp1020_engine_delay_thread_candidate");
        label(0x100163b0L, "hp1020_engine_thread_candidate");
        label(0x1001788cL, "hp1020_system_timer_thread_candidate");
        label(0x10017d28L, "threadx_queue_receive_candidate");
        label(0x10018274L, "threadx_thread_create_candidate");
    }

    private void label(long rawAddress, String name) {
        Function fn = functionAtOrCreate(rawAddress, name);
        if (fn == null) {
            return;
        }
        labels.put(fn, name);
        if (fn.getName().startsWith("FUN_")) {
            try {
                fn.setName(name, SourceType.ANALYSIS);
            }
            catch (Exception ignored) {
                // The report uses local labels even if the program DB keeps the old name.
            }
        }
    }

    private List<TaskAnchor> collectTaskAnchors() throws Exception {
        List<TaskAnchor> anchors = new ArrayList<>();
        var data = currentProgram.getListing().getDefinedData(true);
        while (data.hasNext()) {
            Data item = data.next();
            StringDataInstance s = StringDataInstance.getStringDataInstance(item);
            if (s == null || s.getStringValue() == null || !matchesTaskName(s.getStringValue())) {
                continue;
            }

            TaskAnchor anchor = new TaskAnchor(item.getAddress(), s.getStringValue());
            for (Reference ref : getReferencesTo(item.getAddress())) {
                anchor.pointerRefs.add(ref.getFromAddress());
            }
            for (Address pointerRef : anchor.pointerRefs) {
                readWindow(anchor, pointerRef.subtract(16), 28);
            }
            anchors.add(anchor);
        }
        anchors.sort(Comparator.comparing(a -> a.stringAddress.toString()));
        return anchors;
    }

    private boolean matchesTaskName(String value) {
        for (String needle : TASK_NAME_NEEDLES) {
            if (value.equals(needle) || value.contains(needle)) {
                return true;
            }
        }
        return false;
    }

    private void readWindow(TaskAnchor anchor, Address start, int wordCount) throws Exception {
        for (int i = 0; i < wordCount; i++) {
            Address wordAddress = start.add((long) i * 4);
            MemoryBlock block = currentProgram.getMemory().getBlock(wordAddress);
            if (block == null || !block.isInitialized()) {
                continue;
            }
            long value = Integer.toUnsignedLong(currentProgram.getMemory().getInt(wordAddress));
            anchor.words.add(new WordRecord(wordAddress, value, classifyWord(value)));
        }
    }

    private String classifyWord(long value) {
        if (value == 0) {
            return "zero";
        }
        if (value >= 0x10000000L && value < 0x10200000L) {
            Address address = addr(value);
            Function fn = currentProgram.getFunctionManager().getFunctionAt(address);
            if (fn != null) {
                return "function " + displayName(fn);
            }
            fn = currentProgram.getFunctionManager().getFunctionContaining(address);
            if (fn != null) {
                return "inside function " + displayName(fn) + "+" + Long.toHexString(address.subtract(fn.getEntryPoint()));
            }
            Data data = currentProgram.getListing().getDataAt(address);
            if (data != null) {
                StringDataInstance s = StringDataInstance.getStringDataInstance(data);
                if (s != null && s.getStringValue() != null) {
                    return "string \"" + compact(s.getStringValue()) + "\"";
                }
            }
            MemoryBlock block = currentProgram.getMemory().getBlock(address);
            if (block != null) {
                return "program " + block.getName();
            }
            return "program address";
        }
        if (value >= 0x90000000L && value < 0x90100000L) {
            return "SRAM/DMA-looking address";
        }
        if ((value & 0xffff0000L) == 0xb3000000L || (value & 0xffff0000L) == 0xb3010000L ||
            (value & 0xffff0000L) == 0xb0300000L || (value & 0xffff0000L) == 0xb0700000L ||
            (value & 0xffff0000L) == 0xb0800000L) {
            return "MMIO-looking address";
        }
        if (value > 0xffffL && value < 0x10000000L) {
            return "constant/flags";
        }
        return "small value";
    }

    private Set<Function> collectRelatedFunctions(List<TaskAnchor> anchors) {
        Set<Function> functions = new LinkedHashSet<>();
        for (TaskAnchor anchor : anchors) {
            for (WordRecord word : anchor.words) {
                Function fn = functionFromWord(word.value);
                if (fn != null) {
                    functions.add(fn);
                }
            }
            for (Address pointerRef : anchor.pointerRefs) {
                for (Reference ref : getReferencesTo(pointerRef)) {
                    Function fn = currentProgram.getFunctionManager().getFunctionContaining(ref.getFromAddress());
                    if (fn != null) {
                        functions.add(fn);
                    }
                }
                functions.addAll(scanInstructionRefsTo(pointerRef));
            }
        }
        functions.add(functionAt(0x10008ff0L));
        functions.add(functionAt(0x10009934L));
        functions.add(functionAt(0x1001215cL));
        functions.add(functionAt(0x100138fcL));
        functions.add(functionAt(0x1001788cL));
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
        List<Function> sorted = new ArrayList<>(functions);
        sorted.sort(Comparator.comparing(f -> f.getEntryPoint().toString()));
        int emitted = 0;
        for (Function fn : sorted) {
            if (emitted >= 80) {
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

    private void writeReport(PrintWriter out, List<TaskAnchor> anchors, Set<Function> relatedFunctions) {
        out.println("# HP 1020 Task And Queue Descriptor Map");
        out.println();
        out.println("This maps string-anchored task/queue/semaphore descriptor tables. The word windows are intentionally wider than a single struct because the firmware uses adjacent descriptor tables and literal pools.");
        out.println();

        out.println("## Anchors");
        out.println();
        for (TaskAnchor anchor : anchors) {
            out.printf("### `%s` `%s`%n%n", anchor.stringAddress, compact(anchor.name));
            out.println("Pointer references:");
            if (anchor.pointerRefs.isEmpty()) {
                out.println("- none found");
            }
            for (Address ref : anchor.pointerRefs) {
                out.printf("- `%s`%n", ref);
            }
            out.println();
            out.println("Nearby words:");
            for (WordRecord word : anchor.words) {
                if (word.kind.equals("zero") || word.kind.equals("small value")) {
                    continue;
                }
                out.printf("- `%s`: `0x%08x` %s%n", word.address, word.value, word.kind);
            }
            out.println();
        }

        out.println("## Related Functions");
        out.println();
        List<Function> sorted = new ArrayList<>(relatedFunctions);
        sorted.sort(Comparator.comparing(f -> f.getEntryPoint().toString()));
        for (Function fn : sorted) {
            out.printf("- `%s` `%s`%n", fn.getEntryPoint(), displayName(fn));
        }
        out.println();

        out.println("## Interpretation");
        out.println();
        out.println("- `USB2Thread` and `USB2IdleThread` are directly resolved through descriptor-table function pointers.");
        out.println("- `System Timer Thread` also has a direct handler candidate at `0x1001788c`.");
        out.println("- `tJobMgr`, `PrintMgr`, `StatusMgr`, `tDelayMgrRcvMsg`, `tVideo`, `tEngineDelay`, and `tEngine` now have direct handler candidates from descriptor-table function pointers.");
        out.println("- The next pass should trace each queue ID/message code into the dispatch functions, especially `PrintMgr` and `tEngine`.");
        out.println("- Many descriptor words point into `0x1002....`/`0x1003....` BSS-like memory. These are probably ThreadX control blocks, stacks, queues, or engine buffers rather than executable code.");
    }

    private Function functionFromWord(long value) {
        if (value < 0x10000000L || value >= 0x10200000L) {
            return null;
        }
        Address address = addr(value);
        MemoryBlock block = currentProgram.getMemory().getBlock(address);
        if (block == null || !block.isExecute()) {
            return null;
        }
        if (block.getName().contains("Vectors")) {
            return null;
        }
        Function fn = currentProgram.getFunctionManager().getFunctionAt(address);
        if (fn == null) {
            fn = currentProgram.getFunctionManager().getFunctionContaining(address);
        }
        if (fn == null) {
            if ((value & 0x3L) != 0) {
                return null;
            }
            try {
                createFunction(address, "hp1020_task_entry_" + address);
                fn = currentProgram.getFunctionManager().getFunctionAt(address);
            }
            catch (Exception ignored) {
                fn = currentProgram.getFunctionManager().getFunctionAt(address);
            }
        }
        return fn;
    }

    private Function functionAtOrCreate(long rawAddress, String name) {
        Address address = addr(rawAddress);
        Function fn = currentProgram.getFunctionManager().getFunctionAt(address);
        if (fn == null) {
            fn = currentProgram.getFunctionManager().getFunctionContaining(address);
        }
        if (fn == null) {
            MemoryBlock block = currentProgram.getMemory().getBlock(address);
            if (block == null || !block.isExecute()) {
                return null;
            }
            if (block.getName().contains("Vectors")) {
                return null;
            }
            try {
                createFunction(address, name);
                fn = currentProgram.getFunctionManager().getFunctionAt(address);
            }
            catch (Exception ignored) {
                fn = currentProgram.getFunctionManager().getFunctionAt(address);
            }
        }
        return fn;
    }

    private Function functionAt(long rawAddress) {
        Function fn = currentProgram.getFunctionManager().getFunctionAt(addr(rawAddress));
        if (fn == null) {
            fn = currentProgram.getFunctionManager().getFunctionContaining(addr(rawAddress));
        }
        return fn;
    }

    private Address addr(long value) {
        return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(value);
    }

    private String displayName(Function fn) {
        return labels.getOrDefault(fn, fn.getName());
    }

    private String compact(String value) {
        String s = value.replace("\r", "\\r").replace("\n", "\\n").replace("\t", "\\t").trim();
        return s.length() > 140 ? s.substring(0, 137) + "..." : s;
    }

    private static class TaskAnchor {
        final Address stringAddress;
        final String name;
        final List<Address> pointerRefs = new ArrayList<>();
        final List<WordRecord> words = new ArrayList<>();

        TaskAnchor(Address stringAddress, String name) {
            this.stringAddress = stringAddress;
            this.name = name;
        }
    }

    private static class WordRecord {
        final Address address;
        final long value;
        final String kind;

        WordRecord(Address address, long value, String kind) {
            this.address = address;
            this.value = value;
            this.kind = kind;
        }
    }
}
