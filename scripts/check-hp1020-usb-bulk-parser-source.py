#!/usr/bin/env python3
"""Validate the source contract for the mechanically inert USB bulk/parser draft."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


REPO = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = REPO / "open-firmware/usb-bulk-parser-draft/usb-bulk-parser.S"

LABEL_RE = re.compile(r"^(?P<label>[A-Za-z_.$][A-Za-z0-9_.$]*):$")
WORD_RE = re.compile(r"^\.word\s+(?P<value>-?(?:0x)?[0-9a-f]+)$", re.IGNORECASE)
HARDWARE_LITERAL_RE = re.compile(r"(?<![0-9a-f])0x(?P<value>9[0-9a-f]{7})(?![0-9a-f])", re.IGNORECASE)
BANNED_MMIO_RE = re.compile(
    r"(?<![0-9a-f])(?:0x)?b(?:020|050|100|200|204|208)[0-9a-f]{4}(?![0-9a-f])",
    re.IGNORECASE,
)

DESCRIPTOR_PTR = "hp1020_bulk_descriptor_ptr_90021370"
BUFFER_PTR = "hp1020_bulk_buffer_ptr_900216f0"
SUBMIT_REG = "hp1020_mmio_b3000234"
STATUS_REG = "hp1020_mmio_b3000224"
ACK_REG = "hp1020_mmio_b3000220"

REQUIRED_LITERALS = {
    DESCRIPTOR_PTR: 0x90021370,
    BUFFER_PTR: 0x900216F0,
    SUBMIT_REG: 0xB3000234,
    STATUS_REG: 0xB3000224,
    ACK_REG: 0xB3000220,
    "hp1020_mmio_b3010000": 0xB3010000,
    "hp1020_bulk_completion_mask_00000400": 0x00000400,
    "hp1020_bulk_max_transfer_00000400": 0x00000400,
    "hp1020_zjs_max_chunk_01000000": 0x01000000,
    "hp1020_zjs_signature_00005a5a": 0x00005A5A,
    "hp1020_zjs_magic_jzjz_4a5a4a5a": 0x4A5A4A5A,
    "hp1020_status_descriptor_local_ptr_10003400": 0x10003400,
    "hp1020_status_descriptor_hw_ptr_90003400": 0x90003400,
    "hp1020_device_descriptor_hw_ptr_90003300": 0x90003300,
    "hp1020_config_high_speed_descriptor_hw_ptr_90003314": 0x90003314,
    "hp1020_config_full_speed_descriptor_hw_ptr_90003334": 0x90003334,
    "hp1020_lang_descriptor_hw_ptr_90003354": 0x90003354,
    "hp1020_manufacturer_descriptor_hw_ptr_90003358": 0x90003358,
}

COUNTERS = {
    "bytes_received": 0x60,
    "receive_descriptors_completed": 0x64,
    "recognized_chunks": 0x68,
    "parser_errors": 0x6C,
    "unknown_chunks": 0x70,
}

STATUS_COUNTER_CALLS = (
    (0x60, 0x14),
    (0x64, 0x2A),
    (0x68, 0x40),
    (0x6C, 0x56),
    (0x70, 0x6C),
)

HARDWARE_ALIAS_REGIONS = (
    ("marker_descriptor", 0x90003200, 0x90003225),
    ("standard_descriptors", 0x90003300, 0x90003377),
    ("status_descriptor", 0x90003400, 0x9000347B),
    ("setup_packet", 0x90021348, 0x9002134F),
    ("bulk_descriptor", 0x90021370, 0x9002137F),
    ("bulk_receive_buffer", 0x900216F0, 0x90021AEF),
    ("control_in_descriptor", 0x900226F0, 0x900226FF),
    ("control_in_staging", 0x90022BD0, 0x90022C4B),
)


@dataclass(frozen=True)
class SourceLine:
    number: int
    text: str
    canonical: str


@dataclass(frozen=True)
class Check:
    name: str
    severity: str
    detail: str
    evidence: str


@dataclass(frozen=True)
class Store:
    line: SourceLine
    source: str | int | None
    base: str | int | None
    offset: int


class AssemblySource:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.lines = self._read_lines(path)
        self.labels = {
            match.group("label").lower(): index
            for index, line in enumerate(self.lines)
            if (match := LABEL_RE.match(line.canonical))
        }
        self.literals = self._read_literals()

    @staticmethod
    def _read_lines(path: Path) -> list[SourceLine]:
        lines: list[SourceLine] = []
        for number, raw in enumerate(path.read_text().splitlines(), 1):
            text = raw.split("#", 1)[0].rstrip()
            canonical = re.sub(r"\s*,\s*", ",", re.sub(r"\s+", " ", text.strip()))
            lines.append(SourceLine(number, text.strip(), canonical))
        return lines

    def _read_literals(self) -> dict[str, int]:
        literals: dict[str, int] = {}
        for label, index in self.labels.items():
            for line in self.lines[index + 1 :]:
                if not line.canonical:
                    continue
                if LABEL_RE.match(line.canonical):
                    break
                if match := WORD_RE.match(line.canonical):
                    literals[label] = parse_number(match.group("value"))
                break
        return literals

    def block(self, start: str, end: str) -> list[SourceLine]:
        start_index = self.labels.get(start.lower())
        end_index = self.labels.get(end.lower())
        if start_index is None or end_index is None or end_index <= start_index:
            return []
        return self.lines[start_index + 1 : end_index]

    def previous_nonempty(self, label: str) -> SourceLine | None:
        index = self.labels.get(label.lower())
        if index is None:
            return None
        for line in reversed(self.lines[:index]):
            if line.canonical:
                return line
        return None


def parse_number(value: str) -> int:
    value = value.lower()
    sign = -1 if value.startswith("-") else 1
    unsigned = value[1:] if sign < 0 else value
    base = 16 if unsigned.startswith("0x") else 10
    return sign * int(unsigned, base)


def number_is(value: str, expected: int) -> bool:
    try:
        return parse_number(value) == expected
    except ValueError:
        return False


def instruction(line: SourceLine) -> tuple[str, list[str]] | None:
    text = line.canonical.lower()
    if not text or text.endswith(":") or text.startswith("."):
        return None
    parts = text.split(" ", 1)
    return parts[0], parts[1].split(",") if len(parts) == 2 else []


def instructions(lines: Iterable[SourceLine]) -> list[tuple[SourceLine, str, list[str]]]:
    parsed = []
    for line in lines:
        if item := instruction(line):
            parsed.append((line, item[0], item[1]))
    return parsed


def check(name: str, passed: bool, detail: str, evidence: str) -> Check:
    return Check(name, "pass" if passed else "fail", detail, evidence)


def line_evidence(lines: Iterable[SourceLine]) -> str:
    return "; ".join(f"line {line.number}: {line.canonical}" for line in lines)


def simulate_stores(lines: list[SourceLine]) -> tuple[list[Store], list[SourceLine]]:
    state: dict[str, str | int] = {}
    stores: list[Store] = []
    barriers: list[SourceLine] = []
    destination_ops = {
        "add",
        "add.n",
        "addi",
        "addi.n",
        "and",
        "extui",
        "l32i",
        "l32i.n",
        "l8ui",
        "or",
        "slli",
        "srli",
        "sub",
        "xor",
    }

    for line, op, args in instructions(lines):
        if op == "l32r" and len(args) == 2:
            state[args[0]] = args[1]
        elif op in {"movi", "movi.n"} and len(args) == 2:
            try:
                state[args[0]] = parse_number(args[1])
            except ValueError:
                state.pop(args[0], None)
        elif op in {"mov", "mov.n"} and len(args) == 2:
            if args[1] in state:
                state[args[0]] = state[args[1]]
            else:
                state.pop(args[0], None)
        elif op in {"s32i", "s32i.n"} and len(args) == 3:
            try:
                offset = parse_number(args[2])
            except ValueError:
                continue
            stores.append(Store(line, state.get(args[0]), state.get(args[1]), offset))
        elif op == "memw":
            barriers.append(line)
        elif op in destination_ops and args:
            state.pop(args[0], None)
    return stores, barriers


def descriptor_checks(source: AssemblySource) -> list[Check]:
    lines = source.block("hp1020_usb_bulk_rearm", "hp1020_usb_bulk_handle_completion")
    stores, barriers = simulate_stores(lines)
    descriptor_stores = [store for store in stores if store.base == DESCRIPTOR_PTR]
    expected = [
        (0, "hp1020_bulk_descriptor_initial_08000000"),
        (4, 0),
        (8, BUFFER_PTR),
        (12, 0),
    ]
    actual = [(store.offset, store.source) for store in descriptor_stores]
    construction_ok = actual == expected
    construction_evidence = line_evidence(store.line for store in descriptor_stores) or "no descriptor stores found"

    submits = [
        store
        for store in stores
        if store.base == SUBMIT_REG and store.source == DESCRIPTOR_PTR and store.offset == 0
    ]
    ordered_submit = False
    if descriptor_stores and submits:
        final_store_line = descriptor_stores[-1].line.number
        submit_line = submits[0].line.number
        ordered_submit = any(final_store_line < barrier.number < submit_line for barrier in barriers)

    descriptor_value = source.literals.get(DESCRIPTOR_PTR)
    buffer_value = source.literals.get(BUFFER_PTR)
    previous = source.previous_nonempty("hp1020_usb_bulk_rearm")
    alignment_ok = (
        descriptor_value is not None
        and buffer_value is not None
        and descriptor_value % 4 == 0
        and buffer_value % 4 == 0
        and previous is not None
        and previous.canonical.lower() == ".align 4"
    )

    return [
        check(
            "exact_16_byte_descriptor_construction",
            construction_ok,
            "bulk re-arm must construct exactly four words at offsets 0, 4, 8, and 12 "
            "with the stock initial word and buffer pointer",
            construction_evidence,
        ),
        check(
            "descriptor_alignment",
            alignment_ok,
            "the descriptor and buffer addresses must be 4-byte aligned and the re-arm "
            "routine must retain its alignment directive",
            f"descriptor={descriptor_value!r}; buffer={buffer_value!r}; "
            f"previous={previous.canonical if previous else 'missing'}",
        ),
        check(
            "descriptor_submit",
            len(submits) == 1 and ordered_submit,
            "the completed descriptor must cross a memory barrier before its pointer is written to 0xb3000234",
            line_evidence([submits[0].line]) if submits else "no matching descriptor submit found",
        ),
    ]


def find_poll_sequence(lines: list[SourceLine]) -> tuple[bool, str]:
    parsed = instructions(lines)
    for index, (status_line, op, args) in enumerate(parsed):
        if op != "l32r" or len(args) != 2 or args[1] != STATUS_REG:
            continue
        status_base = args[0]
        read: tuple[SourceLine, str] | None = None
        mask: tuple[SourceLine, str] | None = None
        masked: tuple[SourceLine, str] | None = None
        evidence = [status_line]
        for line, next_op, next_args in parsed[index + 1 :]:
            if read is None and next_op in {"l32i", "l32i.n"} and len(next_args) == 3:
                if next_args[1] == status_base and number_is(next_args[2], 0):
                    read = (line, next_args[0])
                    evidence.append(line)
                    continue
            if mask is None and next_op == "l32r" and len(next_args) == 2:
                if next_args[1] == "hp1020_bulk_completion_mask_00000400":
                    mask = (line, next_args[0])
                    evidence.append(line)
                    continue
            if read and mask and masked is None and next_op == "and" and len(next_args) == 3:
                if {next_args[1], next_args[2]} == {read[1], mask[1]}:
                    masked = (line, next_args[0])
                    evidence.append(line)
                    continue
            if masked and next_op == "bnez" and len(next_args) == 2:
                if next_args == [masked[1], "hp1020_usb_bulk_handle_completion"]:
                    evidence.append(line)
                    return True, line_evidence(evidence)
            if next_op == "l32r" and len(next_args) == 2 and next_args[1] == STATUS_REG:
                break
    return False, "no status-read, 0x400 mask, and completion-branch sequence found"


def usb_flow_checks(source: AssemblySource) -> list[Check]:
    poll_lines = source.block("hp1020_usb_marker_poll_loop", "hp1020_usb_marker_select_device")
    poll_ok, poll_evidence = find_poll_sequence(poll_lines)
    completion_lines = source.block("hp1020_usb_bulk_handle_completion", "hp1020_usb_bulk_descriptor_valid")
    rearm_lines = source.block("hp1020_usb_bulk_rearm", "hp1020_usb_bulk_handle_completion")
    init_lines = source.block("hp1020_usb_bulk_parser_probe", "hp1020_usb_bulk_rearm")
    parse_lines = source.block("hp1020_zjs_parse_transfer_loop", "hp1020_usb_marker_no_match")

    completion_text = {line.canonical.lower(): line for line in completion_lines}
    rearm_text = {line.canonical.lower(): line for line in rearm_lines}
    ack_400 = "write_mmio_const hp1020_mmio_b3000224,hp1020_value_00000400"
    ack_80 = "or_mmio_const hp1020_mmio_b3000220,hp1020_value_00000080"
    rearm_100 = "or_mmio_const hp1020_mmio_b3000220,hp1020_value_00000100"

    def targets(lines: list[SourceLine], target: str) -> list[SourceLine]:
        result = []
        for line, op, args in instructions(lines):
            if op in {"j", "beq", "bne", "beqz", "bnez", "bltu", "bgeu"} and args and args[-1] == target:
                result.append(line)
        return result

    init_rearm = targets(init_lines, "hp1020_usb_bulk_rearm")
    invalid_rearm = targets(completion_lines, "hp1020_usb_bulk_rearm")
    consumed_rearm = targets(parse_lines, "hp1020_usb_bulk_rearm")
    poll_return = targets(rearm_lines, "hp1020_usb_marker_poll_loop")
    rearm_ok = bool(init_rearm and invalid_rearm and consumed_rearm and poll_return)
    rearm_evidence = line_evidence(init_rearm + invalid_rearm + consumed_rearm + poll_return)

    ack_ok = ack_400 in completion_text and ack_80 in completion_text and rearm_100 in rearm_text
    ack_lines = [
        mapping[text]
        for mapping, text in (
            (completion_text, ack_400),
            (completion_text, ack_80),
            (rearm_text, rearm_100),
        )
        if text in mapping
    ]

    return [
        check(
            "bulk_completion_poll",
            poll_ok,
            "0xb3000224 must be polled through the exact 0x400 completion mask",
            poll_evidence,
        ),
        check(
            "bulk_completion_ack_and_control",
            ack_ok,
            "completion must clear 0xb3000224 bit 0x400 and use 0xb3000220 bits "
            "0x80/0x100 for acknowledgement and re-arm",
            line_evidence(ack_lines) or "one or more acknowledgement operations are missing",
        ),
        check(
            "bulk_rearm_paths",
            rearm_ok,
            "initialization, invalid descriptors, and consumed transfers must reach re-arm, "
            "which must return to the poll loop",
            rearm_evidence or "one or more required re-arm edges are missing",
        ),
    ]


def descriptor_alias_checks(source: AssemblySource) -> list[Check]:
    parsed = instructions(
        source.block("hp1020_usb_marker_select_config", "hp1020_usb_marker_select_string")
    )
    evidence: list[SourceLine] = []
    selection_ok = False
    for index, (speed_base_line, op, args) in enumerate(parsed):
        if op != "l32r" or len(args) != 2 or args[1] != "hp1020_mmio_b3010000":
            continue
        speed_base = args[0]
        speed_value: str | None = None
        mask_reg: str | None = None
        masked_reg: str | None = None
        branch_index: int | None = None
        evidence = [speed_base_line]
        for next_index, (line, next_op, next_args) in enumerate(parsed[index + 1 :], index + 1):
            if speed_value is None and next_op in {"l32i", "l32i.n"} and len(next_args) == 3:
                try:
                    is_base_read = next_args[1] == speed_base and parse_number(next_args[2]) == 0
                except ValueError:
                    is_base_read = False
                if is_base_read:
                    speed_value = next_args[0]
                    evidence.append(line)
                    continue
            if mask_reg is None and next_op in {"movi", "movi.n"} and len(next_args) == 2:
                try:
                    is_bit_zero = parse_number(next_args[1]) == 1
                except ValueError:
                    is_bit_zero = False
                if is_bit_zero:
                    mask_reg = next_args[0]
                    evidence.append(line)
                    continue
            if speed_value and mask_reg and masked_reg is None and next_op == "and" and len(next_args) == 3:
                if {next_args[1], next_args[2]} == {speed_value, mask_reg}:
                    masked_reg = next_args[0]
                    evidence.append(line)
                    continue
            if masked_reg and next_op == "bnez" and next_args == [
                masked_reg,
                "hp1020_usb_marker_select_full_speed_config",
            ]:
                branch_index = next_index
                evidence.append(line)
                break
        if branch_index is None:
            continue

        high_speed = next(
            (
                line
                for line, next_op, next_args in parsed[branch_index + 1 :]
                if next_op == "l32r"
                and len(next_args) == 2
                and next_args[1] == "hp1020_config_high_speed_descriptor_hw_ptr_90003314"
            ),
            None,
        )
        full_speed = next(
            (
                line
                for line, next_op, next_args in parsed[branch_index + 1 :]
                if next_op == "l32r"
                and len(next_args) == 2
                and next_args[1] == "hp1020_config_full_speed_descriptor_hw_ptr_90003334"
            ),
            None,
        )
        selection_ok = high_speed is not None and full_speed is not None
        evidence.extend(line for line in (high_speed, full_speed) if line)
        break

    return [
        check(
            "speed_specific_config_alias_selection",
            selection_ok,
            "b3010000 bit 0 must select the 0x90003314 high-speed or 0x90003334 full-speed configuration descriptor",
            line_evidence(evidence) or "no speed-specific configuration descriptor fork found",
        )
    ]


def find_counter_updates(
    lines: list[SourceLine], offset: int, increment: bool
) -> list[tuple[SourceLine, SourceLine, SourceLine]]:
    parsed = instructions(lines)
    updates: list[tuple[SourceLine, SourceLine, SourceLine]] = []
    for index, (load_line, op, args) in enumerate(parsed):
        if op not in {"l32i", "l32i.n"} or len(args) != 3:
            continue
        try:
            if parse_number(args[2]) != offset:
                continue
        except ValueError:
            continue
        value_reg, base_reg = args[0], args[1]
        arithmetic: SourceLine | None = None
        for line, next_op, next_args in parsed[index + 1 : index + 5]:
            if increment:
                if next_op in {"addi", "addi.n"} and len(next_args) == 3:
                    if next_args[:2] == [value_reg, value_reg] and number_is(next_args[2], 1):
                        arithmetic = line
                        continue
            elif next_op in {"add", "add.n"} and len(next_args) == 3:
                if next_args[0] == value_reg and value_reg in next_args[1:]:
                    arithmetic = line
                    continue
            if arithmetic and next_op in {"s32i", "s32i.n"} and len(next_args) == 3:
                try:
                    store_offset = parse_number(next_args[2])
                except ValueError:
                    continue
                if next_args[:2] == [value_reg, base_reg] and store_offset == offset:
                    updates.append((load_line, arithmetic, line))
                    break
    return updates


def prove_counter_update(lines: list[SourceLine], offset: int, increment: bool) -> tuple[bool, str]:
    updates = find_counter_updates(lines, offset, increment)
    if updates:
        return True, line_evidence(updates[0])
    return False, f"no read-modify-write update recovered for state offset 0x{offset:x}"


def counter_checks(source: AssemblySource) -> list[Check]:
    regions = {
        "bytes_received": source.block("hp1020_usb_bulk_length_valid", "hp1020_zjs_parse_transfer_loop"),
        "receive_descriptors_completed": source.block(
            "hp1020_usb_bulk_handle_completion", "hp1020_usb_bulk_descriptor_valid"
        ),
        "recognized_chunks": source.block("hp1020_zjs_known_chunk", "hp1020_zjs_chunk_counted"),
        "parser_errors": source.block("hp1020_zjs_header_error", "hp1020_usb_marker_no_match"),
        "unknown_chunks": source.block("hp1020_zjs_finish_chunk", "hp1020_zjs_known_chunk"),
    }
    checks = []
    for name, offset in COUNTERS.items():
        passed, evidence = prove_counter_update(regions[name], offset, increment=name != "bytes_received")
        checks.append(
            check(
                f"counter_update_{name}",
                passed,
                f"the {name} counter must be updated at state offset 0x{offset:x}",
                evidence,
            )
        )
    finish_start = source.labels.get("hp1020_zjs_finish_chunk")
    finish_end = source.labels.get("hp1020_zjs_chunk_counted")
    finish_range = (
        range(finish_start + 1, finish_end)
        if finish_start is not None and finish_end is not None and finish_end > finish_start
        else range(0)
    )
    finish_line_numbers = {source.lines[index].number for index in finish_range}
    recognized_updates = find_counter_updates(source.lines, COUNTERS["recognized_chunks"], True)
    unknown_updates = find_counter_updates(source.lines, COUNTERS["unknown_chunks"], True)
    updates = recognized_updates + unknown_updates
    updates_in_finish = (
        len(recognized_updates) == 1
        and len(unknown_updates) == 1
        and all(arithmetic.number in finish_line_numbers for _load, arithmetic, _store in updates)
    )

    collect_path = instructions(source.block("hp1020_zjs_collect_header", "hp1020_zjs_enter_payload"))
    zero_payload_path = any(
        op == "bnez"
        and len(args) == 2
        and args[1] == "hp1020_zjs_enter_payload"
        and index + 1 < len(collect_path)
        and collect_path[index + 1][1:] == ("j", ["hp1020_zjs_finish_chunk"])
        for index, (_line, op, args) in enumerate(collect_path)
    )

    skip_path = instructions(source.block("hp1020_zjs_skip_payload", "hp1020_zjs_finish_chunk"))
    exhausted_payload_path = False
    for index, (_line, op, args) in enumerate(skip_path):
        if op not in {"l32i", "l32i.n"} or len(args) != 3:
            continue
        try:
            if parse_number(args[2]) != 0x80:
                continue
        except ValueError:
            continue
        remaining = args[0]
        tail = skip_path[index + 1 :]
        decremented = any(
            next_op in {"addi", "addi.n"}
            and next_args[:2] == [remaining, remaining]
            and len(next_args) == 3
            and number_is(next_args[2], -1)
            for _next_line, next_op, next_args in tail
        )
        stored = any(
            next_op in {"s32i", "s32i.n"}
            and len(next_args) == 3
            and next_args[0] == remaining
            and number_is(next_args[2], 0x80)
            for _next_line, next_op, next_args in tail
        )
        branch_index = next(
            (
                tail_index
                for tail_index, (_next_line, next_op, next_args) in enumerate(tail)
                if next_op == "bnez"
                and next_args == [remaining, "hp1020_zjs_parse_transfer_loop"]
            ),
            None,
        )
        exhausted_payload_path = (
            decremented
            and stored
            and branch_index is not None
            and branch_index + 1 < len(tail)
            and tail[branch_index + 1][1:] == ("j", ["hp1020_zjs_finish_chunk"])
        )
        if exhausted_payload_path:
            break

    finish_targets = [
        line
        for line, op, args in instructions(source.lines)
        if op == "j" and args == ["hp1020_zjs_finish_chunk"]
    ]
    boundary_ok = updates_in_finish and zero_payload_path and exhausted_payload_path and len(finish_targets) == 2
    checks.append(
        check(
            "completed_payload_counter_boundary",
            boundary_ok,
            "recognized/unknown counters must update only in finish_chunk, reached after "
            "zero-payload validation or payload exhaustion",
            line_evidence(finish_targets + [item for update in updates for item in update])
            or "completion-only counter boundary is incomplete",
        )
    )
    return checks


def prove_transfer_bound(lines: list[SourceLine]) -> tuple[bool, str]:
    parsed = instructions(lines)
    for index, (extract_line, op, args) in enumerate(parsed):
        if op != "extui" or len(args) != 4 or args[2:] != ["0", "16"]:
            continue
        length_reg = args[0]
        for bound_line, bound_op, bound_args in parsed[index + 1 :]:
            if bound_op != "l32r" or len(bound_args) != 2:
                continue
            if bound_args[1] != "hp1020_bulk_max_transfer_00000400":
                continue
            bound_reg = bound_args[0]
            for branch_line, branch_op, branch_args in parsed:
                if branch_line.number <= bound_line.number:
                    continue
                if branch_op == "bltu" and branch_args == [bound_reg, length_reg, "hp1020_usb_bulk_length_invalid"]:
                    return True, line_evidence([extract_line, bound_line, branch_line])
    return False, "no unsigned descriptor-length > 0x400 rejection branch found"


def header_fields(lines: list[SourceLine]) -> tuple[dict[int, tuple[str, SourceLine]], str] | None:
    loads: dict[str, dict[int, tuple[str, SourceLine]]] = {}
    for line, op, args in instructions(lines):
        if op not in {"l32i", "l32i.n"} or len(args) != 3:
            continue
        try:
            offset = parse_number(args[2])
        except ValueError:
            continue
        loads.setdefault(args[1], {})[offset] = (args[0], line)
    for base, fields in loads.items():
        if {0, 4, 12}.issubset(fields):
            return fields, base
    return None


def parser_contract_checks(source: AssemblySource) -> list[Check]:
    transfer_lines = source.block("hp1020_usb_bulk_descriptor_valid", "hp1020_zjs_parse_transfer_loop")
    transfer_ok, transfer_evidence = prove_transfer_bound(transfer_lines)
    collect_lines = source.block("hp1020_zjs_collect_header", "hp1020_zjs_enter_payload")
    parsed = instructions(collect_lines)
    fields_result = header_fields(collect_lines)

    header_count_line: SourceLine | None = None
    lower_bound_line: SourceLine | None = None
    payload_sub: tuple[str, SourceLine] | None = None
    max_line: SourceLine | None = None
    signature_line: SourceLine | None = None
    reserved_line: SourceLine | None = None
    type_line: SourceLine | None = None

    if fields_result:
        fields, _header_base = fields_result
        size_reg, size_load = fields[0]
        _type_reg, type_load = fields[4]
        packed_reg, packed_load = fields[12]

        for index, (line, op, args) in enumerate(parsed):
            if op in {"movi", "movi.n"} and len(args) == 2 and number_is(args[1], 16):
                limit_reg = args[0]
                for branch, branch_op, branch_args in parsed[index + 1 : index + 4]:
                    if branch_op == "bltu" and len(branch_args) == 3 and branch_args[1] == limit_reg:
                        if branch_args[2] == "hp1020_zjs_parse_transfer_loop":
                            header_count_line = branch
                        elif branch_args == [size_reg, limit_reg, "hp1020_zjs_header_error"]:
                            lower_bound_line = branch

            if op in {"addi", "addi.n"} and len(args) == 3:
                if args[1] == size_reg and number_is(args[2], -16):
                    payload_sub = (args[0], line)

            if op == "l32r" and len(args) == 2 and args[1] == "hp1020_zjs_max_chunk_01000000":
                bound_reg = args[0]
                for branch, branch_op, branch_args in parsed[index + 1 : index + 4]:
                    if branch_op == "bltu" and branch_args == [bound_reg, size_reg, "hp1020_zjs_header_error"]:
                        max_line = branch

            if op == "extui" and len(args) == 4 and args[1:] == [packed_reg, "0", "16"]:
                signature_reg = args[0]
                for const_line, const_op, const_args in parsed[index + 1 : index + 5]:
                    if const_op == "l32r" and len(const_args) == 2:
                        if const_args[1] != "hp1020_zjs_signature_00005a5a":
                            continue
                        for branch, branch_op, branch_args in parsed:
                            if branch.number > const_line.number and branch_op == "bne":
                                if branch_args == [signature_reg, const_args[0], "hp1020_zjs_header_error"]:
                                    signature_line = branch
                                    break

            if op == "srli" and len(args) == 3 and args[1] == packed_reg and number_is(args[2], 16):
                reserved_reg = args[0]
                if payload_sub:
                    payload_reg, subtract_line = payload_sub
                    for branch, branch_op, branch_args in parsed:
                        if branch.number > subtract_line.number and branch_op == "bltu":
                            if branch_args == [payload_reg, reserved_reg, "hp1020_zjs_header_error"]:
                                reserved_line = branch
            if op == "extui" and len(args) == 4 and args[1:] == [packed_reg, "16", "16"]:
                reserved_reg = args[0]
                if payload_sub:
                    payload_reg, subtract_line = payload_sub
                    for branch, branch_op, branch_args in parsed:
                        if branch.number > subtract_line.number and branch_op == "bltu":
                            if branch_args == [payload_reg, reserved_reg, "hp1020_zjs_header_error"]:
                                reserved_line = branch

        field_lines = [size_load, type_load, packed_load]
    else:
        field_lines = []

    finish_parsed = instructions(source.block("hp1020_zjs_finish_chunk", "hp1020_zjs_chunk_counted"))
    for index, (_line, op, args) in enumerate(finish_parsed):
        if op not in {"l32i", "l32i.n"} or len(args) != 3:
            continue
        try:
            if parse_number(args[2]) != 0x84:
                continue
        except ValueError:
            continue
        type_reg = args[0]
        for bound_line, bound_op, bound_args in finish_parsed[index + 1 : index + 4]:
            if bound_op not in {"movi", "movi.n"} or len(bound_args) != 2:
                continue
            try:
                if parse_number(bound_args[1]) != 7:
                    continue
            except ValueError:
                continue
            bound_reg = bound_args[0]
            for branch, branch_op, branch_args in finish_parsed:
                if branch.number <= bound_line.number:
                    continue
                if branch_op == "bltu" and branch_args == [type_reg, bound_reg, "hp1020_zjs_known_chunk"]:
                    type_line = branch
                    break

    header_ok = bool(fields_result and header_count_line and lower_bound_line and payload_sub)
    header_evidence = line_evidence(
        field_lines
        + [
            line
            for line in (
                header_count_line,
                lower_bound_line,
                payload_sub[1] if payload_sub else None,
            )
            if line
        ]
    )

    return [
        check(
            "bulk_transfer_length_bound",
            transfer_ok,
            "the receive descriptor length must be extracted and rejected above 0x400",
            transfer_evidence,
        ),
        check(
            "chunk_header_16_bytes",
            header_ok,
            "the parser must collect exactly 16 header bytes, reject total sizes below 16, "
            "and subtract 16 before payload handling",
            header_evidence or "the 16-byte header flow is incomplete",
        ),
        check(
            "chunk_max_0x01000000",
            max_line is not None,
            "chunk total size must be rejected above 0x01000000",
            line_evidence([max_line]) if max_line else "no max-chunk rejection branch found",
        ),
        check(
            "chunk_signature_0x5a5a",
            signature_line is not None,
            "the low 16 bits of header word 12 must equal 0x5a5a",
            line_evidence([signature_line])
            if signature_line
            else "no signature extraction and rejection branch found",
        ),
        check(
            "reserved_not_above_payload",
            reserved_line is not None,
            "the high 16-bit reserved count must be rejected when it exceeds total_size - 16",
            line_evidence([reserved_line]) if reserved_line else "no reserved > payload rejection branch found",
        ),
        check(
            "recognized_type_bound_7",
            type_line is not None,
            "only chunk types below 7 may increment the recognized counter",
            line_evidence([type_line]) if type_line else "no type < 7 recognized-path branch found",
        ),
    ]


def status_counter_checks(source: AssemblySource) -> list[Check]:
    macro_start = next(
        (
            index
            for index, line in enumerate(source.lines)
            if line.canonical.lower()
            == ".macro write_hex_counter state_offset,descriptor_offset"
        ),
        None,
    )
    macro_end = None
    if macro_start is not None:
        macro_end = next(
            (
                index
                for index in range(macro_start + 1, len(source.lines))
                if source.lines[index].canonical.lower() == ".endm"
            ),
            None,
        )
    macro_lines = source.lines[macro_start + 1 : macro_end] if macro_start is not None and macro_end else []
    macro_text = "\n".join(line.canonical.lower() for line in macro_lines)
    macro_ok = all(
        pattern.search(macro_text)
        for pattern in (
            re.compile(r"l32i(?:\.n)? a\d+,a\d+,\\state_offset"),
            re.compile(r"l32r a\d+,hp1020_status_descriptor_local_ptr_10003400"),
            re.compile(r"addi(?:\.n)? a\d+,a\d+,\\descriptor_offset"),
            re.compile(r"movi(?:\.n)? a\d+,8"),
            re.compile(r"s8i a\d+,a\d+,0"),
        )
    )

    product_lines = source.block("hp1020_usb_marker_select_product", "hp1020_usb_marker_clip_and_dispatch")
    calls: list[tuple[int, int, SourceLine]] = []
    for line, op, args in instructions(product_lines):
        if op != "write_hex_counter" or len(args) != 2:
            continue
        try:
            calls.append((parse_number(args[0]), parse_number(args[1]), line))
        except ValueError:
            continue
    call_pairs = tuple((state_offset, descriptor_offset) for state_offset, descriptor_offset, _line in calls)
    calls_ok = call_pairs == STATUS_COUNTER_CALLS

    return [
        check(
            "dynamic_status_counter_macro",
            macro_ok,
            "the status formatter must read a runtime counter and write eight hexadecimal "
            "digits into the local status descriptor",
            line_evidence(macro_lines) if macro_lines else "write_hex_counter macro not found",
        ),
        check(
            "dynamic_product_status_counter_calls",
            calls_ok,
            "the product descriptor path must format bytes, descriptors, recognized chunks, "
            "errors, and unknown chunks at their fixed descriptor offsets",
            line_evidence(call[2] for call in calls) or "no write_hex_counter calls found",
        ),
    ]


def boundary_checks(source: AssemblySource) -> list[Check]:
    banned: list[tuple[SourceLine, str]] = []
    aliases: list[tuple[SourceLine, int]] = []
    outside: list[tuple[SourceLine, int]] = []
    xqx_lines: list[SourceLine] = []

    for line in source.lines:
        if "hp1020_zjs_magic_xqx" in line.canonical.lower() or "2c585158" in line.canonical.lower():
            xqx_lines.append(line)
        if match := BANNED_MMIO_RE.search(line.canonical):
            banned.append((line, match.group(0).lower()))
        for match in HARDWARE_LITERAL_RE.finditer(line.canonical):
            value = int(match.group("value"), 16)
            aliases.append((line, value))
            if not any(start <= value <= end for _name, start, end in HARDWARE_ALIAS_REGIONS):
                outside.append((line, value))

    banned_evidence = "; ".join(f"line {line.number}: {value}" for line, value in banned)
    outside_evidence = "; ".join(f"line {line.number}: 0x{value:08x}" for line, value in outside)
    allowed_names = ", ".join(name for name, _start, _end in HARDWARE_ALIAS_REGIONS)
    return [
        check(
            "no_alternate_xqx_magic",
            not xqx_lines,
            "the bulk/parser probe must recognize only the JZJZ framing magic",
            line_evidence(xqx_lines) or "no XQX magic literal or label found",
        ),
        check(
            "no_engine_video_mechanical_mmio",
            not banned,
            "source must not reference the b020, b050, b100, b200, b204, or b208 MMIO families",
            banned_evidence or "no banned MMIO family literals found",
        ),
        check(
            "hardware_alias_literal_allowlist",
            not outside,
            "every 0x9... source literal must stay inside the explicit endpoint-0, bulk, or status regions",
            outside_evidence or f"{len(aliases)} literals are within: {allowed_names}",
        ),
    ]


def polling_interrupt_check(source: AssemblySource) -> list[Check]:
    entry = instructions(source.block("_start", "hp1020_reset_vector"))
    rsil = [
        line
        for line, op, args in entry
        if op == "rsil" and len(args) == 2 and args[1] == "15"
    ]
    probe_jump = [
        line
        for line, op, args in entry
        if op == "jump_abs" and args == ["hp1020_usb_bulk_parser_probe"]
    ]
    ordered = bool(rsil and probe_jump and rsil[0].number < probe_jump[0].number)
    return [
        check(
            "polling_masks_cpu_interrupts_before_usb_setup",
            ordered,
            "entry must raise Xtensa INTLEVEL to 15 before the polling probe enables USB service bits, so the trap-only interrupt table cannot steal a completion",
            line_evidence([*rsil, *probe_jump]) or "missing ordered rsil/jump_abs entry sequence",
        )
    ]


def run_checks(source: AssemblySource) -> list[Check]:
    checks: list[Check] = []
    for label, expected in REQUIRED_LITERALS.items():
        actual = source.literals.get(label)
        checks.append(
            check(
                f"literal_{label}",
                actual == expected,
                f"{label} must resolve to 0x{expected:08x}",
                "missing" if actual is None else f"0x{actual & 0xFFFFFFFF:08x}",
            )
        )
    checks.extend(descriptor_checks(source))
    checks.extend(usb_flow_checks(source))
    checks.extend(descriptor_alias_checks(source))
    checks.extend(counter_checks(source))
    checks.extend(parser_contract_checks(source))
    checks.extend(status_counter_checks(source))
    checks.extend(polling_interrupt_check(source))
    checks.extend(boundary_checks(source))
    return checks


def render_markdown(source: Path, checks: list[Check]) -> str:
    fail_count = sum(item.severity == "fail" for item in checks)
    lines = [
        "# HP 1020 USB Bulk/Parser Source Check",
        "",
        f"- source: `{source}`",
        f"- status: `{'fail' if fail_count else 'pass'}`",
        f"- checks: `{len(checks)}`",
        f"- fail hits: `{fail_count}`",
        "",
        "| Severity | Check | Detail | Evidence |",
        "|---|---|---|---|",
    ]
    for item in checks:
        detail = item.detail.replace("|", "\\|")
        evidence = item.evidence.replace("|", "\\|")
        lines.append(f"| `{item.severity}` | `{item.name}` | {detail} | `{evidence}` |")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", type=Path, default=DEFAULT_SOURCE, help="usb-bulk-parser.S source")
    parser.add_argument("-o", "--output", type=Path, help="write Markdown report")
    parser.add_argument("--json", type=Path, help="write JSON check list")
    args = parser.parse_args()

    source = AssemblySource(args.source)
    checks = run_checks(source)
    report = render_markdown(args.source, checks)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report)
    else:
        print(report, end="")
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps([asdict(item) for item in checks], indent=2, sort_keys=True) + "\n")
    return 1 if any(item.severity == "fail" for item in checks) else 0


if __name__ == "__main__":
    raise SystemExit(main())
