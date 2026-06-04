// Maps RTOS object creation/validation functions around queue and thread APIs.

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.mem.MemoryBlock;
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

public class MapHp1020ObjectCreation extends GhidraScript {
    private static final long[] TARGETS = {
        0x10017ca0L,
        0x10017cf0L,
        0x10017d28L,
        0x10017d74L,
        0x10017dacL,
        0x10017dd8L,
        0x10017e2cL,
        0x10017e64L,
        0x10017e9cL,
        0x10017ed8L,
        0x10017ef8L,
        0x10017f18L,
        0x10017f90L,
        0x10017fc8L,
        0x10018000L,
        0x10018040L,
        0x1001807cL,
        0x1001809cL,
        0x100180dcL,
        0x1001811cL,
        0x1001816cL,
        0x100181a4L,
        0x100181dcL,
        0x10018214L,
        0x10018234L,
        0x10018254L,
        0x10018274L,
        0x100199a4L,
        0x10019a30L,
        0x10019ae8L,
        0x10019b7cL,
        0x1001b98cL,
        0x1001b9b8L,
        0x1001a610L
    };

    private final Map<Function, String> labels = new LinkedHashMap<>();

    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            println("usage: MapHp1020ObjectCreation <output-dir>");
            return;
        }

        File outDir = new File(args[0]);
        File decompDir = new File(outDir, "decompiled");
        outDir.mkdirs();
        decompDir.mkdirs();

        applyLabels();
        decompileTargets(decompDir);

        try (PrintWriter out = new PrintWriter(new FileWriter(new File(outDir, "object-creation.md")))) {
            writeReport(out);
        }
    }

    private void applyLabels() {
        label(0x1001809cL, "threadx_queue_receive_wait_candidate");
        label(0x100180dcL, "threadx_queue_send_candidate");
        label(0x10018274L, "threadx_thread_create_candidate");
        label(0x1001a610L, "threadx_thread_create_core_candidate");
        label(0x10019eb4L, "threadx_queue_receive_core_candidate");
        label(0x1001a130L, "threadx_queue_send_core_candidate");
        label(0x10017f18L, "threadx_queue_create_candidate");
        label(0x100199a4L, "threadx_queue_create_core_candidate");
        label(0x10017f90L, "threadx_queue_delete_candidate");
        label(0x10019a30L, "threadx_queue_delete_core_candidate");
        label(0x1001a590L, "rtos_timer_insert_candidate");
        label(0x1001aac0L, "rtos_thread_ready_insert_candidate");
        label(0x100176c8L, "rtos_schedule_candidate");
    }

    private void label(long rawAddress, String name) {
        Function fn = functionAtOrCreate(rawAddress, name);
        if (fn == null) {
            return;
        }
        labels.put(fn, name);
        if (fn.getName().startsWith("FUN_") || fn.getName().startsWith("threadx_")) {
            try {
                fn.setName(name, SourceType.ANALYSIS);
            }
            catch (Exception ignored) {
                // Local label map is enough for reports.
            }
        }
    }

    private void writeReport(PrintWriter out) throws Exception {
        out.println("# HP 1020 RTOS Object Creation Map");
        out.println();
        out.println("This pass scans system-interface functions around queue/thread creation and validation.");
        out.println();
        out.println("## Object Magic Values");
        out.println();
        out.println("| Magic | Hex | Meaning |");
        out.println("|---|---:|---|");
        out.println("| `SEMA` | `0x53454d41` | semaphore |");
        out.println("| `MUTE` | `0x4d555445` | mutex |");
        out.println("| `QUEU` | `0x51554555` | queue |");
        out.println("| `BLOC` | `0x424c4f43` | block pool |");
        out.println("| `BYTE` | `0x42595445` | byte pool |");
        out.println("| `THRD` | `0x54485244` | thread |");
        out.println();

        out.println("## Target Function Scan");
        out.println();
        out.println("| Function | Calls | Object magic refs | Notes |");
        out.println("|---:|---|---|---|");
        List<Function> functions = new ArrayList<>();
        for (long raw : TARGETS) {
            Function fn = functionAtOrCreate(raw, "hp1020_object_target_" + Long.toHexString(raw));
            if (fn != null) {
                functions.add(fn);
            }
        }
        functions.sort(Comparator.comparing(f -> f.getEntryPoint().getOffset()));
        for (Function fn : functions) {
            FunctionScan scan = scan(fn);
            out.printf("| `0x%08x` `%s` | %s | %s | %s |%n",
                fn.getEntryPoint().getOffset(),
                displayName(fn),
                compact(String.join("<br>", first(scan.calls, 7))),
                compact(String.join("<br>", first(scan.magicRefs, 10))),
                inferNotes(scan));
        }
        out.println();

        out.println("## Current Read");
        out.println();
        out.println("- Queue receive/send wrappers at `0x1001809c` and `0x100180dc` validate `QUEU` and delegate to lower queue cores.");
        out.println("- Thread create wrapper at `0x10018274` rejects objects already marked `THRD` and delegates to `0x1001a610`.");
        out.println("- The next important proof is identifying which nearby wrapper initializes `QUEU`; this pass narrows that search to the system-interface group around `0x10017f18`-`0x1001816c`.");
        out.println("- Queue `8` should become resolvable once queue creation calls are tied back to descriptor blocks and the runtime table at `0x1002c918`.");
    }

    private String inferNotes(FunctionScan scan) {
        if (scan.magicRefs.contains("QUEU")) {
            return "queue object path";
        }
        if (scan.magicRefs.contains("THRD")) {
            return "thread object path";
        }
        if (scan.magicRefs.contains("SEMA")) {
            return "semaphore object path";
        }
        if (scan.magicRefs.contains("MUTE")) {
            return "mutex object path";
        }
        if (scan.magicRefs.contains("BLOC") || scan.magicRefs.contains("BYTE")) {
            return "memory pool object path";
        }
        return "";
    }

    private FunctionScan scan(Function fn) {
        FunctionScan scan = new FunctionScan();
        InstructionIterator instructions = currentProgram.getListing().getInstructions(fn.getBody(), true);
        while (instructions.hasNext()) {
            Instruction instruction = instructions.next();
            for (Reference ref : instruction.getReferencesFrom()) {
                Address to = ref.getToAddress();
                if (to == null) {
                    continue;
                }
                Function callee = currentProgram.getFunctionManager().getFunctionAt(to);
                if (callee != null && ref.getReferenceType().isCall()) {
                    scan.calls.add(String.format("`0x%08x` `%s`", callee.getEntryPoint().getOffset(), displayName(callee)));
                }
                addMagic(scan, to.getOffset());
            }
            for (int i = 0; i < instruction.getNumOperands(); i++) {
                for (Object obj : instruction.getOpObjects(i)) {
                    if (obj instanceof Scalar) {
                        addMagic(scan, ((Scalar) obj).getUnsignedValue());
                    }
                }
            }
        }
        return scan;
    }

    private void addMagic(FunctionScan scan, long value) {
        if (value == 0x53454d41L || value == 0x100065bcL) {
            scan.magicRefs.add("SEMA");
        }
        else if (value == 0x4d555445L || value == 0x100065d0L) {
            scan.magicRefs.add("MUTE");
        }
        else if (value == 0x51554555L || value == 0x100065e8L) {
            scan.magicRefs.add("QUEU");
        }
        else if (value == 0x424c4f43L || value == 0x10006b0cL) {
            scan.magicRefs.add("BLOC");
        }
        else if (value == 0x42595445L || value == 0x10006b10L) {
            scan.magicRefs.add("BYTE");
        }
        else if (value == 0x54485244L || value == 0x10006b14L) {
            scan.magicRefs.add("THRD");
        }
    }

    private void decompileTargets(File decompDir) throws Exception {
        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);
        for (long raw : TARGETS) {
            Function fn = functionAtOrCreate(raw, "hp1020_object_target_" + Long.toHexString(raw));
            if (fn == null) {
                continue;
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
        }
        decompiler.dispose();
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

    private Function functionAtOrCreate(long rawAddress, String fallbackName) {
        Address address = addr(rawAddress);
        Function fn = currentProgram.getFunctionManager().getFunctionAt(address);
        if (fn != null) {
            return fn;
        }
        fn = currentProgram.getFunctionManager().getFunctionContaining(address);
        if (fn != null) {
            return fn;
        }
        MemoryBlock block = currentProgram.getMemory().getBlock(address);
        if (block == null || !block.isExecute()) {
            return null;
        }
        try {
            createFunction(address, fallbackName);
            return currentProgram.getFunctionManager().getFunctionAt(address);
        }
        catch (Exception ignored) {
            return currentProgram.getFunctionManager().getFunctionAt(address);
        }
    }

    private Address addr(long value) {
        return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(value);
    }

    private String displayName(Function fn) {
        return labels.getOrDefault(fn, fn.getName());
    }

    private String compact(String value) {
        String s = value.replace("\r", "\\r").replace("\n", "\\n").replace("\t", "\\t").trim();
        return s.length() > 220 ? s.substring(0, 217) + "..." : s;
    }

    private static class FunctionScan {
        final Set<String> calls = new LinkedHashSet<>();
        final Set<String> magicRefs = new LinkedHashSet<>();
    }
}
