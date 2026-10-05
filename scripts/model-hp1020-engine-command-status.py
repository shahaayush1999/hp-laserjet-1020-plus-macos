#!/usr/bin/env python3
"""Model HP 1020 engine command/status flow.

This is offline analysis only. It extracts stock firmware literals and checks
the decompiled engine-status functions that sit between the print job state
machine and the printer engine command/status register pair.
"""

from __future__ import annotations

import argparse
import json
import re
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
ELF_PATH = ROOT_DIR / "analysis/sihp1020.elf"
OUT_JSON = ROOT_DIR / "analysis/hardware-boundary/engine-command-status.json"
OUT_MD = ROOT_DIR / "analysis/hardware-boundary/engine-command-status.md"

SOURCES = {
    "engine_io": ROOT_DIR / "analysis/dispatch-mmio/decompiled/10015c68_hp1020_engine_status_io_candidate.c",
    "engine_poll": ROOT_DIR / "analysis/dispatch-mmio/decompiled/10015df8_hp1020_engine_status_poll_candidate.c",
    "preflight": ROOT_DIR / "analysis/dispatch-mmio/decompiled/100160a8_hp1020_engine_preflight_candidate.c",
    "dispatch": ROOT_DIR / "analysis/dispatch-mmio/decompiled/10016164_hp1020_engine_message_dispatch_candidate.c",
}

LITERALS = {
    "engine_command_preserve_mask": 0x10005D04,
    "engine_start_status_bit": 0x10005DC8,
    "status_0x20_0x800_mask": 0x10005DDC,
    "fallback_error_event": 0x10005E34,
    "preflight_start_bit": 0x10005E74,
    "dispatch_ready_mask": 0x10005E6C,
    "engine_ready_submit_bit": 0x10005F20,
    "status_2_0x4000_mask": 0x10005F5C,
    "status_2_0x1000_mask": 0x1000605C,
    "default_primary_event": 0x1000604C,
    "low16_0x0a04": 0x10006364,
    "event_preflight_or_status_1100": 0x100063DC,
    "event_status_1607": 0x100063EC,
    "status_all_ones": 0x100068E4,
    "engine_status_register": 0x1000691C,
    "engine_state_base": 0x10006920,
    "engine_clear_mask": 0x10006924,
    "engine_command_register": 0x10006928,
    "timeout_event": 0x1000692C,
    "primary_0x4040_mask": 0x10006940,
    "event_f6000300": 0x10006944,
    "event_f6000400": 0x10006948,
    "event_e6100b0a": 0x1000694C,
    "event_e6100b0b": 0x10006950,
    "switch_table_0x13": 0x10006954,
    "event_ready_ok": 0x10006958,
    "event_e6000d03": 0x1000695C,
    "event_e6000d06": 0x10006960,
    "event_e6000d04": 0x10006964,
    "command_0x501a": 0x10006968,
    "event_e6100800": 0x1000696C,
    "event_e6100e00": 0x10006970,
    "low16_0x0a01": 0x10006974,
    "event_0x14000a04": 0x10006978,
    "command_0x5043": 0x1000697C,
    "primary_0x2e00_mask": 0x10006980,
    "state_ptr_0x48_a": 0x10006994,
    "state_ptr_0x4c_b": 0x10006998,
    "dispatch_queue_ptr": 0x1000699C,
    "command_0x3a13": 0x100069A0,
    "command_0x6012": 0x100069A4,
}

CHECKS = [
    (
        "io_stores_command_latch",
        "engine_io",
        "*(undefined2 *)(PTR_DAT_10006920 + 0x5a) = param_1",
    ),
    (
        "io_clears_status_register",
        "engine_io",
        "*puVar3 = *puVar3 & uVar5",
    ),
    (
        "io_waits_ready_submit_bit",
        "engine_io",
        "(*hp1020_engine_status_reg_table_word & uVar2) == 0",
    ),
    (
        "io_writes_command_low16",
        "engine_io",
        "*puVar6 = *puVar6 & uVar1 | (uint)*(ushort *)(puVar4 + 0x5a)",
    ),
    (
        "io_sets_submit_bit",
        "engine_io",
        "*puVar6 = *puVar6 | uVar2",
    ),
    (
        "io_timeout_emits_0x17",
        "engine_io",
        "hp1020_queue_send_candidate(1,&uStack_30)",
    ),
    (
        "poll_reads_primary_status_1",
        "engine_poll",
        "uVar4 = hp1020_engine_status_io_candidate(1)",
    ),
    (
        "poll_reads_status_0x20",
        "engine_poll",
        "uVar5 = hp1020_engine_status_io_candidate(0x20)",
    ),
    (
        "poll_reads_status_2",
        "engine_poll",
        "uVar5 = hp1020_engine_status_io_candidate(2)",
    ),
    (
        "poll_reads_substatus_0x16",
        "engine_poll",
        "uVar7 = hp1020_engine_status_io_candidate(0x16)",
    ),
    (
        "poll_reads_substatus_0x13",
        "engine_poll",
        "uVar9 = hp1020_engine_status_io_candidate(0x13)",
    ),
    (
        "poll_command_0x501a_side_effect",
        "engine_poll",
        "hp1020_engine_status_io_candidate(DAT_10006968)",
    ),
    (
        "poll_command_0x5043_side_effect",
        "engine_poll",
        "hp1020_engine_status_io_candidate(DAT_1000697c)",
    ),
    (
        "poll_stores_selected_event",
        "engine_poll",
        "*(uint *)(PTR_DAT_10006920 + 0x60) = uVar6",
    ),
    (
        "poll_stores_primary_low16",
        "engine_poll",
        "*(short *)(puVar2 + 100) = (short)uVar4",
    ),
    (
        "poll_can_reset_video",
        "engine_poll",
        "hp1020_video_reset_dispatch_candidate()",
    ),
    (
        "preflight_sets_start_bit",
        "preflight",
        "*hp1020_engine_command_reg_table_word = *hp1020_engine_command_reg_table_word | DAT_10005e74",
    ),
    (
        "preflight_timeout_event",
        "preflight",
        "uStack_2c = DAT_1000692c",
    ),
    (
        "preflight_datastore_source_0x0f",
        "preflight",
        "hp1020_datastore_get_value_candidate(0xf)",
    ),
    (
        "dispatch_command_0x6012",
        "dispatch",
        "hp1020_engine_status_io_candidate(DAT_100069a4)",
    ),
    (
        "dispatch_command_0x3a13",
        "dispatch",
        "uVar4 = hp1020_engine_status_io_candidate(DAT_100069a0)",
    ),
]


@dataclass(frozen=True)
class ElfImage:
    data: bytes
    load_segments: list[tuple[int, int, int]]

    @classmethod
    def load(cls, path: Path) -> "ElfImage":
        data = path.read_bytes()
        if data[:4] != b"\x7fELF" or data[5] != 2:
            raise ValueError(f"{path} is not a big-endian ELF")
        phoff = struct.unpack(">I", data[28:32])[0]
        phentsize = struct.unpack(">H", data[42:44])[0]
        phnum = struct.unpack(">H", data[44:46])[0]
        load_segments = []
        for index in range(phnum):
            off = phoff + index * phentsize
            p_type, p_offset, p_vaddr, _p_paddr, p_filesz, _p_memsz, _p_flags, _p_align = struct.unpack(
                ">IIIIIIII", data[off : off + 32]
            )
            if p_type == 1:
                load_segments.append((p_offset, p_vaddr, p_filesz))
        return cls(data, load_segments)

    def read_u32(self, addr: int) -> int:
        for p_offset, p_vaddr, p_filesz in self.load_segments:
            if p_vaddr <= addr <= p_vaddr + p_filesz - 4:
                off = p_offset + (addr - p_vaddr)
                return struct.unpack(">I", self.data[off : off + 4])[0]
        raise ValueError(f"address 0x{addr:08x} is not file-backed")


def fmt32(value: int) -> str:
    return f"0x{value:08x}"


def fmt_command(value: int) -> str:
    return f"0x{value:x}"


def read_sources() -> dict[str, str]:
    return {name: path.read_text(errors="replace") for name, path in SOURCES.items()}


def literal_values(elf: ElfImage) -> dict[str, str]:
    return {name: fmt32(elf.read_u32(addr)) for name, addr in LITERALS.items()}


def extract_direct_io_calls(sources: dict[str, str], literals: dict[str, str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    pattern = re.compile(r"hp1020_engine_status_io_candidate\(([^)]+)\)")
    for source_name, text in sources.items():
        for match in pattern.finditer(text):
            arg = match.group(1).strip()
            if " " in arg:
                continue
            if arg.startswith("DAT_"):
                cell = int(arg.removeprefix("DAT_"), 16)
                literal_name = next((name for name, addr in LITERALS.items() if addr == cell), None)
                value = literals.get(literal_name or "", f"0x{cell:08x}")
            else:
                literal_name = ""
                value = fmt_command(int(arg, 0))
            kind = "status_read" if source_name == "engine_poll" and arg in {"1", "0x20", "2", "0x16", "0x13"} else "engine_command"
            key = (source_name, arg, value)
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                {
                    "source": source_name,
                    "argument": arg,
                    "literal_name": literal_name or "",
                    "value": value,
                    "kind": kind,
                    "role": io_role(value, source_name),
                }
            )
    return rows


def io_role(value: str, source_name: str) -> str:
    roles = {
        "0x1": "primary engine status word",
        "0x20": "secondary status word for f600 status branch",
        "0x2": "tertiary status word for e610/20001607 branch",
        "0x16": "substatus word for e6000dxx and follow-up poll",
        "0x13": "substatus switch for e6100b0a/e6100b0b branch",
        "0x0000501a": "side-effect command used in substatus 0x16 branch",
        "0x00005043": "side-effect command used when leaving e6100800 state family",
        "0x00006012": "page/start command when no engine reset latch is active",
        "0x00003a13": "page/start command when engine reset latch is active",
    }
    return roles.get(value, f"{source_name} engine command/status operation")


def state_fields(literals: dict[str, str]) -> list[dict[str, str]]:
    base = literals["engine_state_base"]
    return [
        {"offset": "+0x24", "field": "preflight wait latch", "meaning": "breaks preflight wait loop when nonzero"},
        {"offset": "+0x28", "field": "dispatch busy flag", "meaning": "set/cleared around engine dispatch cases"},
        {"offset": "+0x2c", "field": "paper/engine latch candidate", "meaning": "used with primary status bit 0x2000 and bit 0x80"},
        {"offset": "+0x30", "field": "engine-needs-service flag candidate", "meaning": "set by normal/ready branch and reset-trigger branch"},
        {"offset": "+0x34", "field": "previous primary 0x2e00 mask flag", "meaning": "tracks whether stored primary status had any 0x2e00 bits"},
        {"offset": "+0x38", "field": "video reset / page transition latch", "meaning": "can trigger hp1020_video_reset_dispatch_candidate"},
        {"offset": "+0x3c", "field": "deferred latch clear flag", "meaning": "cleared when primary status 0x2e00 mask clears"},
        {"offset": "+0x48", "field": "active engine config pointer", "meaning": "points at preflight config or page mode config"},
        {"offset": "+0x4c", "field": "accepted config pointer", "meaning": "updated from +0x48 only when the media-setting reply has bit0x8000 clear"},
        {"offset": "+0x50", "field": "accepted scalar", "meaning": "updated from +0x54 only when the scalar-setting reply has bit0x8000 clear"},
        {"offset": "+0x54", "field": "requested scalar", "meaning": "full word is compared; low16 is shifted into command0x3300; physical meaning unresolved"},
        {"offset": "+0x58", "field": "density comparison byte", "meaning": "set to0xff during preflight; configuration helper does not update it"},
        {"offset": "+0x59", "field": "requested density byte", "meaning": "density1..5 callback maps to0/16/32/48/63"},
        {"offset": "+0x5a", "field": "command latch", "meaning": "16-bit command argument staged before register write"},
        {"offset": "+0x5c", "field": "returned status value", "meaning": "16-bit engine response returned by status IO helper"},
        {"offset": "+0x60", "field": "selected event/status word", "meaning": "last event word emitted as engine queue message 0x17"},
        {"offset": "+0x64", "field": "primary status low16", "meaning": "last primary command 1 status word"},
        {"offset": "+0x68", "field": "active page work pointer", "meaning": "current page/job work pointer used by dispatch"},
        {"offset": "+0x6c", "field": "deferred page work pointer", "meaning": "second pending work pointer if engine is busy"},
        {"offset": "base", "field": "engine state object", "meaning": f"state base pointer is {base}"},
    ]


def event_decisions(literals: dict[str, str]) -> list[dict[str, str]]:
    return [
        {
            "event": literals["default_primary_event"],
            "source": "poll",
            "condition": "primary status command 1 passes all-ones check and has mask 0x4040 set",
            "confidence": "medium",
        },
        {
            "event": literals["event_f6000300"],
            "source": "poll",
            "condition": "command 0x20 response has mask 0x800 set",
            "confidence": "medium",
        },
        {
            "event": literals["event_f6000400"],
            "source": "poll",
            "condition": "command 0x20 response has bit 0x400 set while 0x800 is clear",
            "confidence": "medium",
        },
        {
            "event": literals["event_ready_ok"],
            "source": "poll",
            "condition": "nested command 2/0x16 status checks settle into normal-looking branch",
            "confidence": "medium",
        },
        {
            "event": literals["event_e6100800"],
            "source": "poll",
            "condition": "command 2 status 0x4000 branch, or substatus 0x16 plus 0x40 transition",
            "confidence": "medium",
        },
        {
            "event": literals["event_status_1607"],
            "source": "poll",
            "condition": "command 2 response has any of mask 0x424 set",
            "confidence": "medium",
        },
        {
            "event": literals["event_preflight_or_status_1100"],
            "source": "preflight/poll",
            "condition": "preflight start event, or command 2 response has bit 0x1000 set",
            "confidence": "medium",
        },
        {
            "event": literals["event_e6100e00"],
            "source": "poll",
            "condition": "command 2 response has bit 0x2000 set",
            "confidence": "medium",
        },
        {
            "event": literals["fallback_error_event"],
            "source": "poll",
            "condition": "fallback when primary bit 0x40 is set and command 2 bit 0x200 is clear",
            "confidence": "low",
        },
        {
            "event": literals["event_e6000d03"],
            "source": "poll",
            "condition": "substatus command 0x16 bit 0x10 branch",
            "confidence": "medium",
        },
        {
            "event": literals["event_e6000d06"],
            "source": "poll",
            "condition": "substatus command 0x16 bit 0x08 branch",
            "confidence": "medium",
        },
        {
            "event": literals["event_e6000d04"],
            "source": "poll",
            "condition": "substatus command 0x16 bit 0x04 branch",
            "confidence": "medium",
        },
        {
            "event": literals["event_e6100b0a"],
            "source": "poll",
            "condition": "command 0x13 switch default for (status >> 1) & 0x3f",
            "confidence": "medium",
        },
        {
            "event": literals["event_e6100b0b"],
            "source": "poll",
            "condition": "command 0x13 switch cases 0x10, 0x14, 0x18",
            "confidence": "medium",
        },
        {
            "event": literals["event_0x14000a04"],
            "source": "poll",
            "condition": "selected event low16 0x0a01 is rewritten before storage/send",
            "confidence": "medium",
        },
        {
            "event": literals["timeout_event"],
            "source": "engine_io/preflight",
            "condition": "status I/O retries or preflight wait loop exhaust",
            "confidence": "high",
        },
    ]


def command_sequences(literals: dict[str, str]) -> list[dict[str, Any]]:
    return [
        {
            "name": "engine_status_io_handshake",
            "function": "0x10015c68 hp1020_engine_status_io_candidate",
            "registers": {
                "status": literals["engine_status_register"],
                "command": literals["engine_command_register"],
            },
            "steps": [
                "stage the 16-bit command at engine state +0x5a",
                "clear the status register with 0xfeffffff",
                "wait for status register bit 0x00010000",
                "write the staged command into the command register low 16 bits while preserving upper 16 bits",
                "set command register bit 0x00010000, enable IRQ6, and wait for event mask0x1 with option3 (AND_CLEAR) and timeout200 ticks",
                "on success, clear the command latch and return state+0x5c; four failed iterations (not necessarily four submissions) emit queue1 message0x17/event0xfe001401 and return0xffff",
            ],
        },
        {
            "name": "preflight_start",
            "function": "0x100160a8 hp1020_engine_preflight_candidate",
            "registers": {"command": literals["engine_command_register"]},
            "steps": [
                "emit queue 1 message 0x17 with event 0xe6101100",
                "OR bit 0x00020000 into the engine command register",
                "poll for that bit to clear, sleeping 0x14 ticks between checks",
                "after success, write config pointers at engine state +0x48/+0x4c and send message 0x18",
                "after 0x1e failed loops or latch +0x24, emit timeout event 0xfe001401",
            ],
        },
        {
            "name": "print_dispatch_start_commands",
            "function": "0x10016164 hp1020_engine_message_dispatch_candidate",
            "registers": {"command": literals["engine_command_register"]},
            "steps": [
                "message 0x0b/0x40 stores active page work pointer at engine state +0x68",
                "if no reset latch is active, send engine command 0x6012",
                "if reset latch is active, send engine command 0x3a13 and keep latch when returned status has 0x8000 clear",
            ],
        },
        {
            "name": "poll_transition_side_effects",
            "function": "0x10015df8 hp1020_engine_status_poll_candidate",
            "registers": {"command": literals["engine_command_register"]},
            "steps": [
                "command 0x501a is sent from the substatus 0x16 branch",
                "command 0x5043 is sent when the previous event family was e6100800 and the new event leaves that family",
                "state +0x60 is updated with the selected event and queue 1 message 0x17 is emitted when it changes",
                "primary status low16 is stored at state +0x64 after each successful poll",
            ],
        },
    ]


def evidence_checks(sources: dict[str, str]) -> list[dict[str, str]]:
    checks = []
    for name, source_name, needle in CHECKS:
        checks.append(
            {
                "name": name,
                "status": "present" if needle in sources[source_name] else "missing",
                "source": str(SOURCES[source_name].relative_to(ROOT_DIR)),
                "needle": needle,
            }
        )
    return checks


def build_report(elf_path: Path) -> dict[str, Any]:
    elf = ElfImage.load(elf_path)
    sources = read_sources()
    literals = literal_values(elf)
    checks = evidence_checks(sources)
    missing = [check for check in checks if check["status"] != "present"]
    return {
        "summary": "Engine command/status flow model for the HP 1020 print engine boundary.",
        "status": "pass" if not missing else "fail",
        "literal_values": literals,
        "status_io_calls": extract_direct_io_calls(sources, literals),
        "state_fields": state_fields(literals),
        "event_decisions": event_decisions(literals),
        "command_sequences": command_sequences(literals),
        "checks": checks,
        "open_firmware_implication": [
            "For printing, this is the critical non-USB hardware conversation: it gates page start, readiness, error state, and video reset.",
            "The model identifies the stock command IDs and event words, but it still does not name every physical condition such as exact paper, cover, fuser, toner, or jam bit.",
            "The next printer-side test should still be non-printing status/PJL calibration before any custom firmware tries to drive these commands.",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# HP 1020 Engine Command/Status Model",
        "",
        "This is a generated offline model. It does not contact the printer.",
        "",
        "## Result",
        "",
        f"- status: `{report['status']}`",
        "- scope: stock firmware engine command/status boundary for print start and status polling",
        "",
        "## Key Literal Values",
        "",
        "| Name | Value |",
        "|---|---:|",
    ]
    for name, value in report["literal_values"].items():
        lines.append(f"| `{name}` | `{value}` |")

    lines.extend(
        [
            "",
            "## Engine Status I/O Calls",
            "",
            "| Source | Argument | Value | Kind | Role |",
            "|---|---:|---:|---|---|",
        ]
    )
    for item in report["status_io_calls"]:
        lines.append(
            f"| `{item['source']}` | `{item['argument']}` | `{item['value']}` | `{item['kind']}` | {item['role']} |"
        )

    lines.extend(["", "## Event Decisions", "", "| Event | Source | Condition | Confidence |", "|---:|---|---|---|"])
    for item in report["event_decisions"]:
        lines.append(
            f"| `{item['event']}` | `{item['source']}` | {item['condition']} | `{item['confidence']}` |"
        )

    lines.extend(["", "## State Fields", "", "| Offset | Field | Meaning |", "|---:|---|---|"])
    for item in report["state_fields"]:
        lines.append(f"| `{item['offset']}` | {item['field']} | {item['meaning']} |")

    lines.extend(["", "## Command Sequences", ""])
    for sequence in report["command_sequences"]:
        lines.extend(
            [
                f"### `{sequence['name']}`",
                "",
                f"- function: `{sequence['function']}`",
                "- registers: "
                + ", ".join(f"`{name}={value}`" for name, value in sequence["registers"].items()),
                "",
            ]
        )
        for index, step in enumerate(sequence["steps"], 1):
            lines.append(f"{index}. {step}")
        lines.append("")

    lines.extend([
        "## Page settings before start", "",
        "`scripts/validate-hp1020-engine-config.py` executes the original lookup,",
        "density/media callbacks, configuration helper and page-start dispatcher",
        "in the interpreter and QEMU. `engine-config-execution.json` retains",
        "the tested sources, file-backed records and command arguments. All engine",
        "operations, status polling and datastore reads are intercepted boundaries.", "",
        "Lookup0x100162b0 scans15 eight-byte records at0x1001cd34 and returns a",
        "matching address or zero. The ten fixed keys/values are1:0,2:2,0x102:9,",
        "0x104:1,0x105:3,0x106:1,0x107:1,0x109:1,0x10b:5,0x111:0.",
        "Five mutable keys0x200..0x204 initially hold zero. Datastore callbacks",
        "16..20 copy the selected record's full value into those respective aliases.",
        "These are internal media keys; host-to-selected-media translation remains",
        "a separate PrintMgr decision. Unknown keys are not a safe default.", "",
        "Configuration0x10015d14 first requests primary status1. Low16=0xffff",
        "returns immediately; otherwise settings require `(primary & 0x6400)==0x4000`.",
        "Using that same supplied primary word, it processes these in order:", "",
        "1. Changed media-record values: `low16(0x5480 | (value_low16 << 1))`.",
        "   Reply bit0x8000 clear updates the accepted pointer at state+0x4c.",
        "2. Different density bytes+0x59/+0x58: `low16(0x5300 | (signed_byte << 1))`.",
        "   The density callback maps1..5 to0/16/32/48/63. This helper neither",
        "   checks that reply nor updates the comparison byte.",
        "3. Different scalar words+0x54/+0x50: `low16(0x3300 | (requested_low16 << 1))`.",
        "   Reply bit0x8000 clear copies the full requested word into+0x50.", "",
        "The original dispatcher calls configuration before0x6012 or0x3a13, but",
        "does not gate page-start on configuration success. Supplied timeout or",
        "rejection responses still reach a start request in the RAM experiment.",
        "This is a conditional original-code result, not an observed device fault",
        "or permission to transmit anything. The replacement should validate",
        "settings and require fresh successful replies instead of copying that",
        "error handling or treating a cached table pointer as engine acceptance.", "",
        "## Original reply interrupt and freshness boundary", "",
        "`scripts/validate-hp1020-engine-handshake.py` executes29 original RAM cuts",
        "in the interpreter and QEMU; its current source-bound result is",
        "`engine-handshake-execution.json`. All peripheral access, IRQ changes,",
        "scheduler/wait behavior and command publication are excluded.", "",
        "Initialization at0x100164f0–f8 registers0x10015bc8 for IRQ6 through",
        "0x1001716c. The handler reads0xb050000c separately at each decision:", "",
        "1. It first writes a read-modify-write value clearing bit28.",
        "2. With bit24 set, a second observation of bit27 decides acceptance.",
        "   Bit27 set only clears that bit; no response is captured or event posted.",
        "   Otherwise a third read supplies low16 to state+0x5c at0x10015c11,",
        "   then0x10017dac receives `(state,1,0)` (event OR). The hidden third",
        "   argument is zero from the earlier AND, not an omitted unknown value.",
        "   Both paths then write a value clearing bit24.",
        "3. Without bit24, bit26 selects another clear-only path.",
        "4. Every path calls0x100171b0(6) then0x100171e0(6): disable IRQ6 and",
        "   write its mask to INTCLEAR. Those CPU operations are statically read,",
        "   never executed by this experiment.", "",
        "These are values computed by the original code, not established register",
        "acknowledgement semantics or meanings of the error bits. Successive reads",
        "are independent observations; the test does not manufacture a snapshot.", "",
        "The caller stages a16-bit command, checks ready bit16, preserves the command",
        "register's upper16 bits, writes the command and sets bit16. Not-ready",
        "iterations sleep1 tick; submitted iterations enable IRQ6 then wait200 ticks.",
        "Both consume the same four-iteration budget. Tick duration is not established.", "",
        "The event core0x10019408 tests requested flags and option3 clears mask0x1 on",
        "success. The command helper does not clear a pending software event before",
        "a new command, and the IRQ producer does not tag its response with a command",
        "identity. Supplied old event-mask0x1/response RAM therefore survives a new command",
        "latch and is accepted by the success tail in the isolated cuts. This is a",
        "conditional freshness finding, not an observed printer fault: physical",
        "command submission, interrupt timing and the blocking scheduler are absent.", "",
        "The replacement need not copy ThreadX or these retries. It needs one serialized",
        "transaction with a deadline and a justified post-timeout drain/reset boundary",
        "before another command can accept an untagged response. An IRQ occurrence,",
        "a changed USB generation or a nonzero cached word alone cannot establish",
        "engine response freshness. Physical recovery and sensor calibration remain open.", "",
    ])
    lines.extend(["## Evidence Checks", "", "| Check | Status | Source | Needle |", "|---|---|---|---|"])
    for check in report["checks"]:
        needle = check["needle"].replace("|", "\\|")
        lines.append(f"| `{check['name']}` | `{check['status']}` | `{check['source']}` | `{needle}` |")

    lines.extend(["", "## Open Firmware Meaning", ""])
    for item in report["open_firmware_implication"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--elf", type=Path, default=ELF_PATH)
    parser.add_argument("--json-output", type=Path, default=OUT_JSON)
    parser.add_argument("--markdown-output", type=Path, default=OUT_MD)
    args = parser.parse_args()

    report = build_report(args.elf)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    args.markdown_output.write_text(render_markdown(report) + "\n")
    print(f"status={report['status']} checks={len(report['checks'])}")
    print(args.markdown_output)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
