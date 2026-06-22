#!/usr/bin/env python3
"""Document the current disassembly limit for HP 1020 helper 0x1001b668.

This is offline analysis only. The helper is important for video chunk sizing,
but the available decoders do not fully decode the old Xtensa divide path.
"""

from __future__ import annotations

import json
import shutil
import struct
import subprocess
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
ELF_PATH = ROOT_DIR / "analysis/sihp1020.elf"
OUT_JSON = ROOT_DIR / "analysis/hardware-boundary/video-helper-disassembly.json"
OUT_MD = ROOT_DIR / "analysis/hardware-boundary/video-helper-disassembly.md"

HELPER_ADDR = 0x1001B668
HELPER_END = 0x1001B6C8
SIMILAR_HELPER_ADDR = 0x1001B6B0
Pcode_ERROR_ADDR = "1001b685"

SOURCES = {
    "helper_decompile": ROOT_DIR / "analysis/message-producers/producer-decompiled/1001b668_FUN_1001b668.c",
    "prepare": ROOT_DIR / "analysis/dispatch-mmio/decompiled/10014910_hp1020_video_prepare_page_candidate.c",
    "band_queue": ROOT_DIR / "analysis/zjs-parser-boundary/decompiled/10013f34_hp1020_video_band_queue_or_list_candidate.c",
    "raw_refresh": ROOT_DIR / "analysis/zjs-parser-boundary/decompiled/100140f8_hp1020_video_refresh_raw_bands_candidate.c",
}

GHIDRA_LOGS = [
    ROOT_DIR / "analysis/zjs-parser-boundary-run.txt",
    ROOT_DIR / "analysis/queue-send-census-run.txt",
    ROOT_DIR / "analysis/message-producers/message-producers-run.txt",
    ROOT_DIR / "analysis/jobmgr-producer-boundary-run.txt",
]

OBJDUMP_CANDIDATES = [
    ROOT_DIR / "tools/xtensa-fsf-elf/bin/xtensa-fsf-elf-objdump",
    Path("/tmp/hp1020-xtensa-manual-systemz/bin/xtensa-fsf-elf-objdump"),
    Path("/opt/homebrew/bin/xtensa-fsf-elf-objdump"),
    Path("/opt/homebrew/bin/objdump"),
    Path("/opt/homebrew/Cellar/binutils/2.46.0/bin/objdump"),
]


def read_text(path: Path) -> str:
    return path.read_text(errors="replace")


def elf_bytes_for_addr(addr: int, size: int) -> bytes:
    data = ELF_PATH.read_bytes()
    phoff = struct.unpack(">I", data[28:32])[0]
    phentsize = struct.unpack(">H", data[42:44])[0]
    phnum = struct.unpack(">H", data[44:46])[0]
    for index in range(phnum):
        off = phoff + index * phentsize
        p_type, p_offset, p_vaddr, _p_paddr, p_filesz, _p_memsz, _p_flags, _p_align = struct.unpack(
            ">IIIIIIII", data[off : off + 32]
        )
        if p_type == 1 and p_vaddr <= addr and addr + size <= p_vaddr + p_filesz:
            file_off = p_offset + addr - p_vaddr
            return data[file_off : file_off + size]
    raise ValueError(f"address range 0x{addr:08x}..0x{addr + size:08x} is not file-backed")


def choose_objdump() -> Path | None:
    for candidate in OBJDUMP_CANDIDATES:
        if candidate.exists() and candidate.is_file():
            return candidate
    resolved = shutil.which("xtensa-fsf-elf-objdump") or shutil.which("objdump")
    return Path(resolved) if resolved else None


def run_objdump() -> dict[str, Any]:
    objdump = choose_objdump()
    if objdump is None:
        return {
            "available": False,
            "tool": None,
            "returncode": None,
            "lines": [],
            "decoder_limit_markers": [],
        }

    command = [
        str(objdump),
        "-d",
        f"--start-address=0x{HELPER_ADDR - 8:08x}",
        f"--stop-address=0x{HELPER_END:08x}",
        str(ELF_PATH),
    ]
    proc = subprocess.run(command, capture_output=True, text=True, check=False)
    text = proc.stdout + proc.stderr
    lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    interesting = [
        line
        for line in lines
        if any(token in line for token in ("1001b668", "1001b685", "excw", "muls.ad", "1001b6b0"))
    ]
    return {
        "available": True,
        "tool": str(objdump),
        "returncode": proc.returncode,
        "command": command,
        "lines": lines[:80],
        "interesting_lines": interesting[:40],
        "decoder_limit_markers": [line for line in interesting if "excw" in line or "muls.ad" in line],
    }


def collect_ghidra_log_hits() -> list[dict[str, str]]:
    hits = []
    for path in GHIDRA_LOGS:
        if not path.exists():
            continue
        for line in read_text(path).splitlines():
            if "1001b668" in line and Pcode_ERROR_ADDR in line:
                hits.append({"path": str(path.relative_to(ROOT_DIR)), "line": line.strip()})
    return hits


def source_evidence() -> dict[str, Any]:
    sources = {name: read_text(path) for name, path in SOURCES.items()}
    return {
        "visible_exact_cases": {
            "denominator_0_returns_0": "return 0;" in sources["helper_decompile"],
            "denominator_1_returns_numerator": "return param_1;" in sources["helper_decompile"],
            "small_denominator_gate": "if (param_2 < 2)" in sources["helper_decompile"],
        },
        "decompiler_warning_markers": {
            "bad_instruction_warning": "Control flow encountered bad instruction data" in sources["helper_decompile"],
            "halt_baddata": "halt_baddata" in sources["helper_decompile"],
            "lzcount_guard": "LZCOUNT" in sources["helper_decompile"],
        },
        "caller_roles": [
            {
                "caller": "0x10014910 hp1020_video_prepare_page_candidate",
                "role": "computes stride-derived chunk cap +0xcc and a secondary chunk value",
                "snippets_present": [
                    "FUN_1001b668(uVar6,uVar19)" in sources["prepare"],
                    "FUN_1001b668(DAT_10005ddc,iVar8)" in sources["prepare"],
                ],
            },
            {
                "caller": "0x10013f34 hp1020_video_band_queue_or_list_candidate",
                "role": "encodes normal descriptor-queue raw-band counts before flag writes",
                "snippets_present": [
                    "FUN_1001b668(uVar8 >> 1,uVar11)" in sources["band_queue"],
                    "FUN_1001b668(uVar11,uVar12)" in sources["band_queue"],
                ],
            },
            {
                "caller": "0x100140f8 hp1020_video_refresh_raw_bands_candidate",
                "role": "encodes alternate raw linked-list counts before flag writes",
                "snippets_present": [
                    "FUN_1001b668(uVar1 >> 1,uVar10)" in sources["raw_refresh"],
                    "FUN_1001b668(uVar2,uVar10)" in sources["raw_refresh"],
                ],
            },
        ],
    }


def build_checks(report: dict[str, Any]) -> list[dict[str, str]]:
    raw = report["raw_bytes"]
    evidence = report["source_evidence"]
    visible = evidence["visible_exact_cases"]
    warnings = evidence["decompiler_warning_markers"]
    callers = evidence["caller_roles"]
    objdump = report["objdump"]
    checks = [
        {
            "name": "helper_bytes_extracted",
            "status": "present" if raw["helper_prefix_hex"].startswith("6c10026e3239d620056f") else "missing",
            "detail": "ELF bytes at 0x1001b668 match the current stock firmware extraction.",
        },
        {
            "name": "zero_one_cases_visible",
            "status": "present"
            if all(visible.values())
            else "missing",
            "detail": "Ghidra decompile still exposes denominator 0 -> 0 and denominator 1 -> numerator.",
        },
        {
            "name": "bad_instruction_path_visible",
            "status": "present" if all(warnings.values()) else "missing",
            "detail": "Ghidra still marks the helper's wider divide path as bad instruction data.",
        },
        {
            "name": "ghidra_logs_show_pcode_error",
            "status": "present" if report["ghidra_pcode_error_hits"] else "missing",
            "detail": "Batch decompile logs include the pcode constructor failure at 0x1001b685.",
        },
        {
            "name": "known_callers_accounted_for",
            "status": "present" if all(all(role["snippets_present"]) for role in callers) else "missing",
            "detail": "Prepare, descriptor-queue, and alternate raw-band callers still reference the helper.",
        },
        {
            "name": "local_objdump_does_not_confirm_divide_path",
            "status": "present"
            if (not objdump["available"] or objdump["decoder_limit_markers"])
            else "missing",
            "detail": "Current local objdump path is absent or emits old-Xtensa/custom-instruction-looking markers instead of a clean helper decode.",
        },
    ]
    return checks


def build_report() -> dict[str, Any]:
    raw_helper = elf_bytes_for_addr(HELPER_ADDR, HELPER_END - HELPER_ADDR)
    raw_similar = elf_bytes_for_addr(SIMILAR_HELPER_ADDR, 40)
    report: dict[str, Any] = {
        "summary": "Instruction-level status for helper 0x1001b668 used by video chunk sizing.",
        "scope": "offline static analysis; no printer contact",
        "helper": {
            "address": f"0x{HELPER_ADDR:08x}",
            "working_name": "ceil_div_or_units_encode_candidate",
            "confirmed_behavior": {
                "denominator_0": "returns 0",
                "denominator_1": "returns numerator",
            },
            "unconfirmed_behavior": {
                "denominator_ge_2": "caller-fit hypothesis remains ceil(numerator / denominator)",
                "reason": "Ghidra and local objdump do not currently provide a clean decode of the old Xtensa/custom divide path.",
            },
        },
        "raw_bytes": {
            "helper_range": f"0x{HELPER_ADDR:08x}..0x{HELPER_END:08x}",
            "helper_prefix_hex": raw_helper[:32].hex(),
            "helper_hex": raw_helper.hex(),
            "similar_helper_0x1001b6b0_prefix_hex": raw_similar[:32].hex(),
        },
        "source_evidence": source_evidence(),
        "ghidra_pcode_error_hits": collect_ghidra_log_hits(),
        "objdump": run_objdump(),
        "conclusion": {
            "status": "bounded_hypothesis",
            "plain_english": "We know this helper matters and know its no-divide edge cases. We do not yet have a clean instruction-level decode for the real divide path, so the ceil-div name is a strong model fit, not final proof.",
            "next_useful_step": "Treat this as good enough for dataflow modeling; only spend more time here if a later hardware/register formula disagrees with the ceil-div model.",
        },
    }
    report["checks"] = build_checks(report)
    report["status"] = "pass" if all(item["status"] == "present" for item in report["checks"]) else "fail"
    return report


def render_markdown(report: dict[str, Any]) -> str:
    helper = report["helper"]
    objdump = report["objdump"]
    lines = [
        "# HP 1020 Video Helper Disassembly Limit",
        "",
        "This generated report is offline only. It does not contact the printer.",
        "",
        "## Result",
        "",
        f"- status: `{report['status']}`",
        f"- helper: `{helper['address']}` `{helper['working_name']}`",
        f"- confirmed denominator 0 behavior: {helper['confirmed_behavior']['denominator_0']}",
        f"- confirmed denominator 1 behavior: {helper['confirmed_behavior']['denominator_1']}",
        f"- denominator >= 2: {helper['unconfirmed_behavior']['denominator_ge_2']}",
        f"- why not final: {helper['unconfirmed_behavior']['reason']}",
        "",
        "## Plain-English Meaning",
        "",
        report["conclusion"]["plain_english"],
        "",
        "## Raw Bytes",
        "",
        f"- range: `{report['raw_bytes']['helper_range']}`",
        f"- first 32 bytes: `{report['raw_bytes']['helper_prefix_hex']}`",
        f"- similar helper `0x1001b6b0` first 32 bytes: `{report['raw_bytes']['similar_helper_0x1001b6b0_prefix_hex']}`",
        "",
        "## Caller Impact",
        "",
        "| Caller | Role | Evidence |",
        "|---|---|---|",
    ]
    for role in report["source_evidence"]["caller_roles"]:
        present = "present" if all(role["snippets_present"]) else "missing"
        lines.append(f"| `{role['caller']}` | {role['role']} | `{present}` |")

    lines.extend(["", "## Decoder Evidence", ""])
    lines.append(f"- Ghidra pcode error hits: `{len(report['ghidra_pcode_error_hits'])}`")
    for hit in report["ghidra_pcode_error_hits"]:
        lines.append(f"  - `{hit['path']}`: `{hit['line']}`")
    lines.append("")
    if objdump["available"]:
        lines.extend(
            [
                f"- objdump tool: `{objdump['tool']}`",
                f"- objdump return code: `{objdump['returncode']}`",
                f"- decoder limit markers: `{len(objdump['decoder_limit_markers'])}`",
                "",
                "Relevant objdump lines:",
                "",
            ]
        )
        for line in objdump.get("interesting_lines", [])[:16]:
            lines.append(f"- `{line}`")
    else:
        lines.append("- objdump tool: not available")

    lines.extend(["", "## Checks", "", "| Check | Status | Detail |", "|---|---|---|"])
    for item in report["checks"]:
        lines.append(f"| `{item['name']}` | `{item['status']}` | {item['detail']} |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    OUT_MD.write_text(render_markdown(report))
    print(f"status={report['status']} checks={len(report['checks'])}")
    print(f"wrote {OUT_MD.relative_to(ROOT_DIR)}")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
