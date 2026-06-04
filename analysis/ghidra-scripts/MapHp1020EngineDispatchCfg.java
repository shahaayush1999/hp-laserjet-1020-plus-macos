// Exports Ghidra's instruction and block view for the HP 1020 engine dispatcher.

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressRange;
import ghidra.program.model.block.BasicBlockModel;
import ghidra.program.model.block.CodeBlock;
import ghidra.program.model.block.CodeBlockIterator;
import ghidra.program.model.block.CodeBlockReference;
import ghidra.program.model.block.CodeBlockReferenceIterator;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.symbol.Reference;

import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

public class MapHp1020EngineDispatchCfg extends GhidraScript {
    private static final long ENGINE_DISPATCH = 0x10016164L;

    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            println("usage: MapHp1020EngineDispatchCfg <output-dir>");
            return;
        }

        File outDir = new File(args[0]);
        outDir.mkdirs();

        Function fn = currentProgram.getFunctionManager().getFunctionAt(addr(ENGINE_DISPATCH));
        if (fn == null) {
            fn = currentProgram.getFunctionManager().getFunctionContaining(addr(ENGINE_DISPATCH));
        }
        if (fn == null) {
            println("engine dispatch function not found");
            return;
        }

        try (PrintWriter out = new PrintWriter(new FileWriter(new File(outDir, "engine-dispatch-cfg.md")))) {
            writeReport(out, fn);
        }
    }

    private void writeReport(PrintWriter out, Function fn) throws Exception {
        out.println("# HP 1020 Engine Dispatch CFG");
        out.println();
        out.println("This report records Ghidra's raw instruction and basic-block view for the engine dispatcher.");
        out.println("It is meant to check whether decompilation lost a branch such as engine message `0x17`.");
        out.println();
        out.printf("- Function: `%s` `%s`%n", fn.getEntryPoint(), fn.getName());
        out.printf("- Body addresses: `%d`%n", fn.getBody().getNumAddresses());
        out.println();

        writeBlocks(out, fn);
        writeSwitchTable(out);
        writeInstructions(out, fn);
        writeScalarSummary(out, fn);
    }

    private void writeBlocks(PrintWriter out, Function fn) throws Exception {
        out.println("## Basic Blocks");
        out.println();
        out.println("| Block | Range | Destinations |");
        out.println("|---:|---|---|");

        BasicBlockModel model = new BasicBlockModel(currentProgram);
        CodeBlockIterator blocks = model.getCodeBlocksContaining(fn.getBody(), monitor);
        List<CodeBlock> blockList = new ArrayList<>();
        while (blocks.hasNext()) {
            blockList.add(blocks.next());
        }
        blockList.sort(Comparator.comparing(b -> b.getFirstStartAddress().toString()));

        int index = 0;
        for (CodeBlock block : blockList) {
            List<String> ranges = new ArrayList<>();
            for (AddressRange range : block) {
                ranges.add("`" + range.getMinAddress() + ".." + range.getMaxAddress() + "`");
            }
            List<String> dests = new ArrayList<>();
            CodeBlockReferenceIterator refs = block.getDestinations(monitor);
            while (refs.hasNext()) {
                CodeBlockReference ref = refs.next();
                dests.add("`" + ref.getDestinationAddress() + "` " + ref.getFlowType());
            }
            out.printf("| `%d` | %s | %s |%n", index++, String.join("<br>", ranges), String.join("<br>", dests));
        }
        out.println();
    }

    private void writeSwitchTable(PrintWriter out) throws Exception {
        out.println("## Switch Table");
        out.println();
        out.println("The dispatcher subtracts `0x0b` from message word 0, accepts indexes `0..0x35`,");
        out.println("and jumps through the table at `0x10005a10`.");
        out.println();
        out.println("| Message | Target | Working meaning |");
        out.println("|---:|---:|---|");
        long table = 0x10005a10L;
        for (int i = 0; i <= 0x35; i++) {
            int message = 0x0b + i;
            long target = Integer.toUnsignedLong(currentProgram.getMemory().getInt(addr(table + i * 4L)));
            out.printf("| `0x%02x` | `%s` | %s |%n", message, addr(target), meaning(message, target));
        }
        out.println();
        out.println("Message `0x17` maps to `0x100162aa`, the default return block. That means the");
        out.println("engine thread receives `0x17` messages, but this recovered dispatcher does not consume");
        out.println("their payload directly.");
        out.println();
    }

    private String meaning(int message, long target) {
        if (target == 0x100162aaL) {
            return "default return/no-op";
        }
        switch (message) {
            case 0x0b:
                return "page/engine work";
            case 0x0d:
                return "rewrite to `0x0e` and resend queue `1`";
            case 0x0f:
                return "engine reset/clear; sends `0x25`";
            case 0x11:
                return "drain deferred engine/page work";
            case 0x18:
                return "status poll";
            case 0x19:
                return "send startup/ready message `0x16`";
            case 0x1a:
                return "preflight/status refresh";
            case 0x40:
                return "force/start page path; falls through to `0x0b`";
            default:
                return "non-default target";
        }
    }

    private void writeInstructions(PrintWriter out, Function fn) {
        out.println("## Instructions");
        out.println();
        out.println("| Address | Instruction | References |");
        out.println("|---:|---|---|");

        InstructionIterator instructions = currentProgram.getListing().getInstructions(fn.getBody(), true);
        while (instructions.hasNext()) {
            Instruction ins = instructions.next();
            List<String> refs = new ArrayList<>();
            for (Reference ref : ins.getReferencesFrom()) {
                refs.add("`" + ref.getToAddress() + "` " + ref.getReferenceType());
            }
            out.printf(
                "| `%s` | `%s` | %s |%n",
                ins.getAddress(),
                escape(ins.toString()),
                refs.isEmpty() ? "" : String.join("<br>", refs)
            );
        }
        out.println();
    }

    private void writeScalarSummary(PrintWriter out, Function fn) {
        out.println("## Scalar Literals");
        out.println();
        out.println("This lists small scalar literals seen in operands. It is a quick check for visible case IDs.");
        out.println();
        out.println("| Address | Literal | Instruction |");
        out.println("|---:|---:|---|");

        InstructionIterator instructions = currentProgram.getListing().getInstructions(fn.getBody(), true);
        while (instructions.hasNext()) {
            Instruction ins = instructions.next();
            for (int i = 0; i < ins.getNumOperands(); i++) {
                for (Object obj : ins.getOpObjects(i)) {
                    if (!(obj instanceof ghidra.program.model.scalar.Scalar)) {
                        continue;
                    }
                    long value = ((ghidra.program.model.scalar.Scalar) obj).getUnsignedValue();
                    if (value <= 0x50 || value == 0xffffffffL) {
                        out.printf("| `%s` | `0x%x` | `%s` |%n", ins.getAddress(), value, escape(ins.toString()));
                    }
                }
            }
        }
        out.println();
    }

    private Address addr(long off) {
        return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(off);
    }

    private String escape(String s) {
        return s.replace("|", "\\|").replace("`", "'");
    }
}
