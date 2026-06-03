// Extracts USB2Thread internal jump-table blocks without forcing function boundaries.

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.block.BasicBlockModel;
import ghidra.program.model.block.CodeBlock;
import ghidra.program.model.block.CodeBlockReference;
import ghidra.program.model.block.CodeBlockReferenceIterator;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.symbol.Reference;

import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.ArrayDeque;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Queue;
import java.util.Set;

public class MapHp1020UsbInternalBlocks extends GhidraScript {
    private static final long[] GET_DESCRIPTOR_BLOCKS = {
        0x10009476L,
        0x100095b3L,
        0x100095f6L,
        0x10009859L,
        0x100096afL,
        0x100096e5L
    };

    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            println("usage: MapHp1020UsbInternalBlocks <output-path>");
            return;
        }

        BasicBlockModel model = new BasicBlockModel(currentProgram);
        try (PrintWriter out = new PrintWriter(new FileWriter(new File(args[0])))) {
            out.println("# HP 1020 USB2Thread Internal Blocks");
            out.println();
            out.println("These are jump-table target blocks inside `USB2Thread`, not standalone functions.");
            out.println();

            for (long raw : GET_DESCRIPTOR_BLOCKS) {
                Address target = addr(raw);
                CodeBlock block = model.getFirstCodeBlockContaining(target, monitor);
                Function owner = currentProgram.getFunctionManager().getFunctionContaining(target);
                out.printf("## Target `%s`%n%n", target);
                out.printf("Containing function: `%s` `%s`%n%n",
                    owner == null ? "none" : owner.getEntryPoint().toString(),
                    owner == null ? "none" : owner.getName());

                if (block == null) {
                    out.println("No basic block found.");
                    out.println();
                    continue;
                }

                writeReachableBlocks(out, model, block);
            }
        }
    }

    private void writeReachableBlocks(PrintWriter out, BasicBlockModel model, CodeBlock start) throws Exception {
        Queue<BlockDepth> queue = new ArrayDeque<>();
        Set<Address> seen = new LinkedHashSet<>();
        queue.add(new BlockDepth(start, 0));

        int emitted = 0;
        while (!queue.isEmpty() && emitted < 16) {
            BlockDepth current = queue.remove();
            CodeBlock block = current.block;
            if (!seen.add(block.getFirstStartAddress())) {
                continue;
            }
            emitted++;

            out.printf("### Depth %d Block `%s` - `%s`%n%n",
                current.depth, block.getFirstStartAddress(), block.getMaxAddress());
            out.println("Outgoing block destinations:");
            CodeBlockReferenceIterator destinations = block.getDestinations(monitor);
            List<CodeBlockReference> refs = new ArrayList<>();
            while (destinations.hasNext()) {
                CodeBlockReference destination = destinations.next();
                refs.add(destination);
                out.printf("- `%s` via `%s`%n", destination.getDestinationAddress(), destination.getFlowType());
            }
            if (refs.isEmpty()) {
                out.println("- none found");
            }
            out.println();

            out.println("Instructions:");
            Address cursor = block.getFirstStartAddress();
            int count = 0;
            while (cursor != null && cursor.compareTo(block.getMaxAddress()) <= 0 && count < 80) {
                Instruction instruction = currentProgram.getListing().getInstructionAt(cursor);
                if (instruction == null) {
                    break;
                }
                out.printf("- `%s` `%s`", instruction.getAddress(), instruction);
                List<String> instructionRefs = formatRefs(instruction);
                if (!instructionRefs.isEmpty()) {
                    out.print(" refs=");
                    out.print(String.join(", ", instructionRefs));
                }
                out.println();
                cursor = instruction.getMaxAddress().next();
                count++;
            }
            out.println();

            if (current.depth >= 4) {
                continue;
            }
            for (CodeBlockReference ref : refs) {
                CodeBlock next = model.getFirstCodeBlockContaining(ref.getDestinationAddress(), monitor);
                if (next != null && !seen.contains(next.getFirstStartAddress())) {
                    queue.add(new BlockDepth(next, current.depth + 1));
                }
            }
        }
    }

    private Address addr(long raw) {
        return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(raw);
    }

    private List<String> formatRefs(Instruction instruction) {
        List<String> refs = new ArrayList<>();
        for (Reference ref : instruction.getReferencesFrom()) {
            refs.add("`" + ref.getToAddress() + "`/" + ref.getReferenceType());
        }
        return refs;
    }

    private static class BlockDepth {
        final CodeBlock block;
        final int depth;

        BlockDepth(CodeBlock block, int depth) {
            this.block = block;
            this.depth = depth;
        }
    }
}
