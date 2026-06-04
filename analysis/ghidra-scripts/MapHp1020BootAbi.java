// Maps HP 1020 boot/runtime ABI anchors: reset vector, ELF entry, and system interface table.

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

public class MapHp1020BootAbi extends GhidraScript {
    private static final long RESET_VECTOR = 0x10100020L;
    private static final long ELF_ENTRY = 0x100167a8L;
    private static final long SYS_INTERFACE_TABLE = 0x10000370L;
    private static final int SYS_INTERFACE_WORDS = 0x12c / 4;

    private static final long[] EARLY_TARGETS = {
        RESET_VECTOR,
        ELF_ENTRY,
        0x10006bb0L,
        0x10010f54L,
        0x10010fd0L,
        0x10011258L,
        0x1001135cL,
        0x100116ecL,
        0x100131b8L,
        0x10013408L,
        0x100175c0L,
        0x1001766cL,
        0x10017af4L,
        0x10017b64L,
        0x1001809cL,
        0x100180dcL,
        0x100181a4L
    };

    private final Map<Function, String> labels = new LinkedHashMap<>();

    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            println("usage: MapHp1020BootAbi <output-dir>");
            return;
        }

        File outDir = new File(args[0]);
        File decompDir = new File(outDir, "decompiled");
        outDir.mkdirs();
        decompDir.mkdirs();

        applyLabels();
        labelSystemInterfaceEntries();
        decompileTargets(decompDir);

        try (PrintWriter out = new PrintWriter(new FileWriter(new File(outDir, "boot-abi.md")))) {
            writeReport(out);
        }
    }

    private void applyLabels() {
        label(RESET_VECTOR, "hp1020_reset_vector_candidate");
        label(ELF_ENTRY, "hp1020_elf_entry_candidate");
        label(0x10006bb0L, "hp1020_early_boot_or_init_candidate");
        label(0x10010f54L, "hp1020_datastore_read_locked_candidate");
        label(0x10010fd0L, "hp1020_datastore_write_notify_unlock_candidate");
        label(0x10011258L, "hp1020_register_event_handler_candidate");
        label(0x1001135cL, "hp1020_register_or_signal_message_candidate");
        label(0x100116ecL, "hp1020_system_service_candidate");
        label(0x100131b8L, "hp1020_runtime_service_candidate");
        label(0x10013408L, "hp1020_runtime_service_2_candidate");
        label(0x100175c0L, "threadx_or_timer_service_candidate");
        label(0x1001766cL, "threadx_sleep_candidate");
        label(0x1001809cL, "threadx_queue_receive_wait_candidate");
        label(0x100180dcL, "threadx_queue_send_candidate");
        label(0x100181a4L, "threadx_memory_or_copy_candidate");
    }

    private void labelSystemInterfaceEntries() throws Exception {
        for (int i = 0; i < SYS_INTERFACE_WORDS; i++) {
            long value = readU32(SYS_INTERFACE_TABLE + (long) i * 4);
            if (value < 0x10000000L || value >= 0x10200000L) {
                continue;
            }
            labelIfUnnamed(value, String.format("hp1020_sys_interface_%02d_candidate", i));
        }
    }

    private void label(long rawAddress, String name) {
        Function fn = functionAtOrCreate(rawAddress, name);
        if (fn == null) {
            return;
        }
        labels.put(fn, name);
        if (fn.getName().startsWith("FUN_") || fn.getName().startsWith("hp1020_sys_interface_")) {
            try {
                fn.setName(name, SourceType.ANALYSIS);
            }
            catch (Exception ignored) {
                // Report labels still use the local map.
            }
        }
    }

    private void labelIfUnnamed(long rawAddress, String name) {
        Function fn = functionAtOrCreate(rawAddress, name);
        if (fn == null || labels.containsKey(fn)) {
            return;
        }
        label(rawAddress, name);
    }

    private void writeReport(PrintWriter out) throws Exception {
        out.println("# HP 1020 Boot ABI Map");
        out.println();
        out.println("This pass maps the firmware startup and runtime interface anchors relevant to any custom firmware experiment.");
        out.println();
        writeMemoryBlocks(out);
        writeBootAnchors(out);
        writeSystemInterfaceTable(out);
        writeEarlyTargetSummary(out);
        writeResetVectorReferences(out);
        writeInterpretation(out);
    }

    private void writeMemoryBlocks(PrintWriter out) {
        out.println("## Loaded Memory Blocks");
        out.println();
        out.println("| Block | Start | End | Size | Permissions |");
        out.println("|---|---:|---:|---:|---|");
        MemoryBlock[] blocks = currentProgram.getMemory().getBlocks();
        for (MemoryBlock block : blocks) {
            String perms = (block.isRead() ? "R" : "-") + (block.isWrite() ? "W" : "-") + (block.isExecute() ? "X" : "-");
            out.printf("| `%s` | `%s` | `%s` | `%d` | `%s` |%n",
                block.getName(), block.getStart(), block.getEnd(), block.getSize(), perms);
        }
        out.println();
    }

    private void writeBootAnchors(PrintWriter out) {
        out.println("## Boot Anchors");
        out.println();
        out.println("| Anchor | Address | Notes |");
        out.println("|---|---:|---|");
        out.printf("| Reset vector section | `0x%08x` | `.ResetVector.text`, 736 bytes |%n", RESET_VECTOR);
        out.printf("| ELF entry point | `0x%08x` | ELF header entry |%n", ELF_ENTRY);
        out.printf("| System interface table | `0x%08x` | 75 function-pointer entries in `.sys_interface_table` |%n", SYS_INTERFACE_TABLE);
        out.println();
    }

    private void writeSystemInterfaceTable(PrintWriter out) throws Exception {
        out.println("## System Interface Table");
        out.println();
        out.println("The `.sys_interface_table` is a boot/runtime ABI-looking function pointer table. Queue, sleep, event, and helper functions used by tasks appear here.");
        out.println();
        out.println("| Index | Table address | Function pointer | Label / description |");
        out.println("|---:|---:|---:|---|");
        for (int i = 0; i < SYS_INTERFACE_WORDS; i++) {
            long tableAddress = SYS_INTERFACE_TABLE + (long) i * 4;
            long value = readU32(tableAddress);
            out.printf("| `%02d` | `0x%08x` | `0x%08x` | %s |%n", i, tableAddress, value, describeAddress(value));
        }
        out.println();
    }

    private void writeEarlyTargetSummary(PrintWriter out) {
        out.println("## Early Function Summary");
        out.println();
        out.println("| Function | Size | Calls | Referenced strings / MMIO |");
        out.println("|---:|---:|---|---|");
        for (long raw : EARLY_TARGETS) {
            Function fn = functionAtOrCreate(raw, "hp1020_early_target_" + Long.toHexString(raw));
            if (fn == null) {
                out.printf("| `0x%08x` | | | function not created by Ghidra |%n", raw);
                continue;
            }
            FunctionScan scan = scan(fn);
            out.printf("| `0x%08x` `%s` | `%d` | %s | %s |%n",
                raw, displayName(fn), fn.getBody().getNumAddresses(),
                compact(String.join("<br>", first(scan.calls, 8))),
                compact(String.join("<br>", first(scan.refs, 8))));
        }
        out.println();
    }

    private void writeResetVectorReferences(PrintWriter out) {
        out.println("## Reset/Entry Reference Notes");
        out.println();
        out.println("Direct references found from the reset vector and ELF entry candidates:");
        out.println();
        out.println("| Function | References |");
        out.println("|---:|---|");
        for (long raw : new long[] { RESET_VECTOR, ELF_ENTRY }) {
            Function fn = functionAtOrCreate(raw, "hp1020_reference_target_" + Long.toHexString(raw));
            if (fn == null) {
                continue;
            }
            FunctionScan scan = scan(fn);
            out.printf("| `0x%08x` `%s` | %s |%n",
                raw, displayName(fn), compact(String.join("<br>", first(scan.refs, 20))));
        }
        out.println();
    }

    private void writeInterpretation(PrintWriter out) {
        out.println("## Interpretation");
        out.println();
        out.println("Current boot/runtime ABI read:");
        out.println();
        out.println("- The ELF is not a freestanding flat binary. It carries Xtensa vectors, a reset vector section, a system interface table, `.data`, and `.bss`.");
        out.println("- `.sys_interface_table` is likely part of the boot ROM / firmware ABI boundary. It contains the queue primitives and task/runtime services used throughout the firmware.");
        out.println("- A custom firmware experiment needs to preserve enough of this ABI shape for the boot ROM to load and jump correctly.");
        out.println("- The immediate next unknown is whether the boot ROM uses only the ELF program headers and entry point, or also validates/uses HP-specific interface table slots.");
        out.println();
        out.println("Practical implication: the safest prototype target is a minimal ELF that keeps the same section/header/interface-table shape and changes behavior only after early startup is understood.");
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
                addReference(scan, to.getOffset());
            }
            for (int i = 0; i < instruction.getNumOperands(); i++) {
                for (Object obj : instruction.getOpObjects(i)) {
                    if (obj instanceof Scalar) {
                        addReference(scan, ((Scalar) obj).getUnsignedValue());
                    }
                }
            }
        }
        return scan;
    }

    private void addReference(FunctionScan scan, long value) {
        if (isMmio(value)) {
            scan.refs.add(String.format("MMIO `0x%08x`", value));
            return;
        }
        if (value >= 0x10000000L && value < 0x10200000L) {
            scan.refs.add(String.format("program `0x%08x` %s", value, describeAddress(value)));
            return;
        }
        if (value >= 0x90000000L && value < 0x90100000L) {
            scan.refs.add(String.format("SRAM `0x%08x`", value));
        }
    }

    private void decompileTargets(File decompDir) throws Exception {
        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);
        for (long raw : EARLY_TARGETS) {
            Function fn = functionAtOrCreate(raw, "hp1020_decompile_target_" + Long.toHexString(raw));
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

    private String describeAddress(long value) {
        if (value == 0) {
            return "zero";
        }
        if (isMmio(value)) {
            return "MMIO-looking address";
        }
        if (value >= 0x10000000L && value < 0x10200000L) {
            Address address = addr(value);
            Function fn = currentProgram.getFunctionManager().getFunctionAt(address);
            if (fn != null) {
                return "`" + displayName(fn) + "`";
            }
            fn = currentProgram.getFunctionManager().getFunctionContaining(address);
            if (fn != null) {
                return "inside `" + displayName(fn) + "` + `0x" + Long.toHexString(address.subtract(fn.getEntryPoint())) + "`";
            }
            Data data = currentProgram.getListing().getDataAt(address);
            if (data != null) {
                StringDataInstance s = StringDataInstance.getStringDataInstance(data);
                if (s != null && s.getStringValue() != null) {
                    return "string `" + compact(s.getStringValue()) + "`";
                }
            }
            MemoryBlock block = currentProgram.getMemory().getBlock(address);
            if (block != null) {
                return "block `" + block.getName() + "`";
            }
        }
        return "constant";
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

    private long readU32(long rawAddress) throws Exception {
        return Integer.toUnsignedLong(currentProgram.getMemory().getInt(addr(rawAddress)));
    }

    private boolean isMmio(long value) {
        return value >= 0xb0000000L && value < 0xb4000000L;
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
        final Set<String> refs = new LinkedHashSet<>();
    }
}
