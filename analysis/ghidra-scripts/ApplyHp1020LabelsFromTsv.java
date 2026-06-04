// Applies HP 1020 firmware labels from a tab-separated data file.

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.SourceType;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.List;

public class ApplyHp1020LabelsFromTsv extends GhidraScript {
    private int appliedFunctions = 0;
    private int appliedDataLabels = 0;
    private final List<String> warnings = new ArrayList<>();

    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length < 1 || args.length > 2) {
            println("usage: ApplyHp1020LabelsFromTsv <labels.tsv> [report.md]");
            return;
        }

        File labelsFile = new File(args[0]);
        File reportFile = args.length == 2 ? new File(args[1]) : null;

        List<LabelRecord> labels = readLabels(labelsFile);
        for (LabelRecord label : labels) {
            apply(label);
        }

        if (reportFile != null) {
            File parent = reportFile.getParentFile();
            if (parent != null) {
                parent.mkdirs();
            }
            try (PrintWriter out = new PrintWriter(new FileWriter(reportFile))) {
                writeReport(out, labelsFile, labels);
            }
        }

        println("labels=" + labels.size() + " functions=" + appliedFunctions + " data=" + appliedDataLabels + " warnings=" + warnings.size());
    }

    private List<LabelRecord> readLabels(File labelsFile) throws Exception {
        List<LabelRecord> labels = new ArrayList<>();
        try (BufferedReader reader = new BufferedReader(new FileReader(labelsFile))) {
            String line;
            int lineNumber = 0;
            while ((line = reader.readLine()) != null) {
                lineNumber++;
                if (line.isBlank() || line.startsWith("#")) {
                    continue;
                }
                String[] parts = line.split("\t", 5);
                if (parts.length < 5) {
                    warnings.add("line " + lineNumber + ": expected 5 tab-separated fields");
                    continue;
                }
                labels.add(new LabelRecord(
                    lineNumber,
                    Long.decode(parts[0]),
                    parts[1],
                    parts[2],
                    parts[3],
                    parts[4]
                ));
            }
        }
        return labels;
    }

    private void apply(LabelRecord label) {
        Address address = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(label.address);
        if (address == null) {
            warnings.add("line " + label.lineNumber + ": invalid address " + Long.toHexString(label.address));
            return;
        }
        if (!isValidSymbolName(label.name)) {
            warnings.add("line " + label.lineNumber + ": invalid symbol name " + label.name);
            return;
        }

        if (label.kind.equals("function")) {
            Function function = currentProgram.getFunctionManager().getFunctionAt(address);
            if (function == null) {
                function = currentProgram.getFunctionManager().getFunctionContaining(address);
            }
            if (function == null) {
                function = createKnownFunction(address, label.name);
            }
            if (function == null) {
                warnings.add("line " + label.lineNumber + ": could not create function at " + address + " for " + label.name);
                return;
            }
            try {
                function.setName(label.name, SourceType.ANALYSIS);
                function.setComment(label.confidence + " confidence: " + label.note);
                appliedFunctions++;
            }
            catch (Exception exc) {
                warnings.add("line " + label.lineNumber + ": could not rename function at " + address + ": " + exc.getMessage());
            }
            return;
        }

        if (label.kind.equals("data")) {
            try {
                currentProgram.getSymbolTable().createLabel(address, label.name, SourceType.ANALYSIS);
                setPlateComment(address, label.confidence + " confidence: " + label.note);
                appliedDataLabels++;
            }
            catch (Exception exc) {
                warnings.add("line " + label.lineNumber + ": could not label data at " + address + ": " + exc.getMessage());
            }
            return;
        }

        warnings.add("line " + label.lineNumber + ": unknown kind " + label.kind);
    }

    private Function createKnownFunction(Address address, String name) {
        try {
            disassemble(address);
            Function function = createFunction(address, name);
            if (function != null) {
                return function;
            }
        }
        catch (Exception ignored) {
            // Fall through to a normal warning with the original label context.
        }
        return currentProgram.getFunctionManager().getFunctionAt(address);
    }

    private boolean isValidSymbolName(String name) {
        if (name == null || name.isBlank()) {
            return false;
        }
        return name.matches("[A-Za-z_][A-Za-z0-9_]*");
    }

    private void writeReport(PrintWriter out, File labelsFile, List<LabelRecord> labels) {
        out.println("# Ghidra Label Application Report");
        out.println();
        out.println("This report records an offline label replay against the HP 1020 firmware Ghidra import.");
        out.println();
        out.println("- Program: `" + currentProgram.getName() + "`");
        out.println("- Language: `" + currentProgram.getLanguageID() + "`");
        out.println("- Label file: `" + labelsFile.getPath() + "`");
        out.println("- Labels read: `" + labels.size() + "`");
        out.println("- Function labels applied: `" + appliedFunctions + "`");
        out.println("- Data labels applied: `" + appliedDataLabels + "`");
        out.println("- Warnings: `" + warnings.size() + "`");
        out.println();
        if (!warnings.isEmpty()) {
            out.println("## Warnings");
            out.println();
            for (String warning : warnings) {
                out.println("- " + warning);
            }
            out.println();
        }
        out.println("## Meaning");
        out.println();
        out.println("The TSV file is the portable label source of truth. The Java script lets a fresh Ghidra project");
        out.println("recover the current function/data names before running deeper manual analysis.");
        out.println();
    }

    private static class LabelRecord {
        final int lineNumber;
        final long address;
        final String name;
        final String kind;
        final String confidence;
        final String note;

        LabelRecord(int lineNumber, long address, String name, String kind, String confidence, String note) {
            this.lineNumber = lineNumber;
            this.address = address;
            this.name = name;
            this.kind = kind;
            this.confidence = confidence;
            this.note = note;
        }
    }
}
