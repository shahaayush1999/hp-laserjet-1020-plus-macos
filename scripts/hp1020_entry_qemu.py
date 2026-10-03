"""Draft direct QEMU observer for the single-entry RAM experiment.

UNEXECUTED: this source has not been imported, parsed, compiled or run by its
author. The shared hp1020_qemu_ram module remains unchanged. The caller supplies
an independently sealed/audited image, checkpoint addresses and admissible CPU
state. No candidate ELF loader, per-call CPU reset or oracle is invoked here.
"""

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import threading
import time

from hp1020_qemu_ram import QemuRAM, RETURN


VERSION = "QEMU emulator version 11.1.1"
BACKEND_SHA256 = "8fe170ab6161d47d17ef93eb6c25622878e00dc2d4747cfd70073a0fd777b5e2"
PRIMARY_SHA256 = {
    "provenance.json": "a207e83239270e8cd09763a9b96e80e733745e2e74d70cd44337ee27dc88f100",
    "target/xtensa/core-test_kc705_be/gdb-config.c.inc":
        "3bca88cfe97be52026d9e9762328f293a7892407014a775a221d2262abb0e70c",
    "target/xtensa/gdbstub.c":
        "132bb55cd6203ec5ac22f4ce2611447f225306abd6c8c4b06367b08a65ac42c1",
    "target/xtensa/core-test_kc705_be/core-isa.h":
        "449fcb676f9c05ae143749e619c4edcac3e07f590f086a58e1de0cd844f1d2cb",
    "target/xtensa/core-test_kc705_be.c":
        "9113b65e67095cd0697788530c3c1ed9d64628645828b6ec06e575f43be07a97",
}
# Exact-version primary QEMU map, not the different binutils GDB overlay.
# Register37 PREFCTL and83 DBREAKC0 are intentionally absent and never written.
REGISTERS = dict(pc=0, lbeg=33, lend=34, lcount=35, sar=36,
                 windowbase=38, windowstart=39, ps=42, intenable=110)
READ_REGISTERS = set(REGISTERS.values()) | set(range(1, 33)) | set(range(124, 140))
REGION_INTERVALS = (
    (0x10003000, 0x100351E0),
    (0x10000000, 0x10000184), (0x10000200, 0x1000023C),
    (0x10000270, 0x10000350), (0x10000370, 0x1000049C),
    (0x10100020, 0x10100304), (0x10100320, 0x1010032C),
)
MUTABLE = ((0x1000E000, 0x100114B8), (0x10012000, 0x10014000),
           (0x10014040, 0x10014440), (0x10016800, 0x10032810))
CHECKPOINT_NAMES = ("after-normalization", "pre-c", "pre-finish", "park")
CHUNK_BYTES = 4096
TOTAL_TIMEOUT = 120.0
COMMAND_TIMEOUT = 10.0
MAX_COMMANDS = 4096
MAX_LEDGER_BYTES = 16 * 1024 * 1024


class EntryQemuError(RuntimeError):
    pass


def require(ok, message):
    if not ok:
        raise EntryQemuError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save_json(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + ".partial")
    temporary.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")
    temporary.replace(path)


class Ledger:
    def __init__(self, path):
        self.path = Path(path)
        self.file = self.path.open("xb")
        self.lines = 0
        self.bytes = 0

    def add(self, kind, **fields):
        item = dict(kind=kind, ledger_index=self.lines, **fields)
        raw = (json.dumps(item, sort_keys=True, separators=(",", ":")) + "\n").encode()
        require(self.bytes + len(raw) <= MAX_LEDGER_BYTES, "host ledger byte limit")
        self.file.write(raw)
        self.file.flush()
        self.bytes += len(raw)
        self.lines += 1

    def close(self):
        self.file.close()


@contextmanager
def deadline(seconds):
    """Bound constructor/version subprocess as well as debugger traffic.

    This adapter requires a POSIX main thread with no caller ITIMER_REAL in use.
    It refuses those unsupported environments before launching QEMU, rather than
    replacing another task's alarm or relying only on a per-socket timeout.
    """
    require(threading.current_thread() is threading.main_thread(),
            "entry QEMU adapter requires the main thread")
    require(hasattr(signal, "setitimer") and hasattr(signal, "ITIMER_REAL"),
            "entry QEMU adapter requires POSIX real-time deadline support")
    old_timer = signal.getitimer(signal.ITIMER_REAL)
    require(old_timer == (0.0, 0.0), "caller already owns ITIMER_REAL")
    old_handler = signal.getsignal(signal.SIGALRM)

    def expired(_signal, _frame):
        raise EntryQemuError("entry QEMU total wall-clock deadline expired")

    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old_handler)


def normalize_inputs(regions, registers, checkpoints):
    require(isinstance(regions, (list, tuple)) and len(regions) == 7, "seven exact regions required")
    supplied = {}
    for address, data in regions:
        require(type(address) is int and isinstance(data, bytes), "immutable region tuple")
        require(address not in supplied, "duplicate initial region")
        supplied[address] = data
    require(set(supplied) == {a for a, _ in REGION_INTERVALS}, "exact admitted region starts")
    ordered = []
    for start, end in REGION_INTERVALS:
        require(len(supplied[start]) == end - start, f"exact region length at{start:#x}")
        ordered.append((start, supplied[start]))
    expected_keys = set(REGISTERS) | {"physical_ar"}
    require(isinstance(registers, dict) and set(registers) == expected_keys, "semantic register schema")
    initial = {name: registers[name] for name in REGISTERS}
    require(all(type(v) is int and 0 <= v <= 0xFFFFFFFF for v in initial.values()), "u32 special registers")
    ars = registers["physical_ar"]
    require(isinstance(ars, (list, tuple)) and len(ars) == 32 and
            all(type(v) is int and 0 <= v <= 0xFFFFFFFF for v in ars), "all32 physical ARs")
    initial["physical_ar"] = list(ars)
    require(initial["pc"] == 0x100167A8, "single admitted entry address")
    require(initial["windowbase"] < 8 and initial["windowstart"] < 256,
            "bounded32-AR window state")
    require(initial["sar"] < 64 and initial["intenable"] < (1 << 22), "selected emulator field widths")
    require((initial["ps"] & ~0x70F1F) == 0 and ((initial["ps"] >> 8) & 15) < 8,
            "supplied privileged PS with admitted fields")
    require(not initial["lcount"] or not (
        0x10007000 <= initial["lend"] < 0x1000D000 or
        0x10016780 <= initial["lend"] < 0x100167E0),
        "incoming active loop must not redirect startup/code before normalization")
    require(isinstance(checkpoints, (list, tuple)) and len(checkpoints) == 4, "four ordered checkpoints")
    cp = []
    for wanted, item in zip(CHECKPOINT_NAMES, checkpoints):
        require(isinstance(item, (list, tuple)) and len(item) == 2, "checkpoint pair")
        name, address = item
        require(name == wanted and type(address) is int, "ordered checkpoint name/address")
        require((0x10007000 <= address <= 0x1000D000 - 3) or
                (0x10016780 <= address <= 0x100167E0 - 3), "checkpoint in candidate code budget")
        cp.append((name, address))
    require(len({a for _, a in cp}) == 4, "distinct checkpoint addresses")
    return ordered, initial, cp


def seed_commands(regions, registers):
    commands = []
    for address, data in regions:
        for offset in range(0, len(data), CHUNK_BYTES):
            part = data[offset:offset + CHUNK_BYTES]
            commands.append(f"M{address + offset:x},{len(part):x}:" + part.hex())
    # QEMU's direct SR debugger write does not itself resync the logical window.
    # WB is selected first; every subsequent physical AR write resyncs it.
    for name in ("windowbase", "windowstart", "ps", "intenable", "lbeg", "lend", "lcount", "sar"):
        commands.append(f"P{REGISTERS[name]:x}={registers[name]:08x}")
    for index, value in enumerate(registers["physical_ar"], 1):
        commands.append(f"P{index:x}={value:08x}")
    commands.append(f"P0={registers['pc']:08x}")
    return commands


class ObservedQemu(QemuRAM):
    """Reuse only private sim transport, with a fail-closed command boundary."""

    def __init__(self, regions, registers, checkpoints, ledger, output_dir):
        self.ledger = ledger
        self.output_dir = output_dir
        self.regions = regions
        self.checkpoints = checkpoints
        self.seed = seed_commands(regions, registers)
        self.bootstrap = ["qSupported", "Hg0", f"Z0,{RETURN:x},1", f"z0,{RETURN:x},1"]
        self.phase = "constructor"
        self.bootstrap_index = 0
        self.seed_index = 0
        self.command_index = 0
        self.checkpoint_index = 0
        self.active_breakpoint = None
        self.resumed = False
        self.captured = False
        self.steps = 0
        self.closed = False
        self.cleanup = None
        self.expires = time.monotonic() + TOTAL_TIMEOUT
        super().__init__()
        require(self.version == VERSION, f"require exact QEMU11.1.1, found {self.version!r}")
        expected_args = [self.binary, "-M", "sim", "-cpu", "test_kc705_be", "-m", "1G",
                         "-nodefaults", "-display", "none", "-serial", "none",
                         "-monitor", "none", "-nic", "none", "-S", "-gdb"]
        require(self.process.args[:-1] == expected_args, "private sim/core launch arguments")
        self.ok(f"z0,{RETURN:x},1")
        require(self.bootstrap_index == 4, "historical RETURN breakpoint removed before seed")
        self.phase = "seed"

    def within(self, address, size):
        return type(address) is int and type(size) is int and size > 0 and any(
            start <= address and address + size <= start + len(data)
            for start, data in self.regions)

    def guard(self, command):
        if self.phase == "constructor":
            require(self.bootstrap_index < 4 and command == self.bootstrap[self.bootstrap_index],
                    "only sealed constructor bootstrap/historical breakpoint removal permitted")
            self.bootstrap_index += 1
            return "bootstrap"
        if self.phase == "seed":
            require(self.seed_index < len(self.seed) and command == self.seed[self.seed_index],
                    "initial writes must match the supplied image/register seed exactly once")
            self.seed_index += 1
            return "initial-seed"
        require(self.phase == "observe", "debugger command outside owned lifecycle")
        match = re.fullmatch(r"p([0-9a-f]+)", command)
        if match:
            require(int(match.group(1), 16) in READ_REGISTERS, "unadmitted debugger register read")
            return "read-register"
        match = re.fullmatch(r"m([0-9a-f]+),([0-9a-f]+)", command)
        if match:
            address, size = (int(value, 16) for value in match.groups())
            require(size <= CHUNK_BYTES and self.within(address, size), "read outside exact supplied regions")
            return "read-memory"
        if command in ("qSupported", "qC", "qAttached", "?"):
            return "read-query"
        match = re.fullmatch(r"([Zz])0,([0-9a-f]+),1", command)
        if match:
            adding, address = match.group(1) == "Z", int(match.group(2), 16)
            require(self.within(address, 3) and self.checkpoint_index < 4,
                    "breakpoint outside admitted checkpoint")
            require(address == self.checkpoints[self.checkpoint_index][1], "breakpoint order/address")
            if adding:
                require(self.active_breakpoint is None and not self.resumed and not self.captured,
                        "one unconsumed breakpoint at a time")
            else:
                require(self.active_breakpoint == address and self.resumed and self.captured,
                        "only consumed observed breakpoint may be removed")
            return "add-breakpoint" if adding else "remove-breakpoint"
        if command == "c":
            require(self.active_breakpoint is not None and not self.resumed and self.checkpoint_index < 4,
                    "continue requires the next ordered breakpoint, once")
            self.resumed = True
            return "continue-current-pc"
        if command == "s":
            require(self.active_breakpoint is None and self.checkpoint_index == 4 and self.steps < 2,
                    "single-step only twice after observed park")
            self.steps += 1
            return "single-step-park"
        raise EntryQemuError("post-seed GDB mutation or unadmitted command rejected: " + command[:80])

    def command(self, command):
        number = self.command_index
        self.command_index += 1
        try:
            require(number < MAX_COMMANDS, "GDB command count limit")
            action = self.guard(command)
        except BaseException as error:
            self.ledger.add("gdb-rejected", command_index=number, phase=self.phase,
                            command=command, error=str(error))
            raise
        self.ledger.add("gdb-request", command_index=number, phase=self.phase,
                        action=action, command=command)
        try:
            remaining = self.expires - time.monotonic()
            require(remaining > 0, "total QEMU deadline")
            self.socket.settimeout(min(COMMAND_TIMEOUT, remaining))
            reply = super().command(command)
            require(len(reply) <= 16384, "bounded debugger reply")
        except BaseException as error:
            self.ledger.add("gdb-error", command_index=number, error=type(error).__name__ + ": " + str(error))
            raise
        self.ledger.add("gdb-reply", command_index=number, reply=reply)
        if action == "add-breakpoint" and reply == "OK":
            self.active_breakpoint = self.checkpoints[self.checkpoint_index][1]
        elif action == "remove-breakpoint" and reply == "OK":
            self.active_breakpoint = None
            self.resumed = self.captured = False
            self.checkpoint_index += 1
        return reply

    def seed_once_and_lock(self):
        require(self.phase == "seed" and self.seed_index == 0, "single initial seed")
        for command in self.seed:
            self.ok(command)
        require(self.seed_index == len(self.seed), "complete initial seed")
        self.phase = "observe"
        self.ledger.add("initial-state-locked", seed_commands=len(self.seed),
                        gdb_commands=self.command_index)

    def close(self):
        if self.closed:
            return
        result = dict(terminated=False, killed=False, returncode=None,
                      still_running=False, errors=[])
        # A constructor deadline can interrupt this call. Do not mark closed
        # before cleanup completes: execute's finally can safely retry after
        # restoring the alarm handler, retaining partial evidence meanwhile.
        self.cleanup = result
        sock = getattr(self, "socket", None)
        if sock is not None:
            try:
                sock.close()
            except Exception as error:
                result["errors"].append("socket: " + repr(error))
        process = getattr(self, "process", None)
        if process is not None:
            result["pid"] = process.pid
            try:
                if process.poll() is None:
                    process.terminate()
                    result["terminated"] = True
                try:
                    _, stderr = process.communicate(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    result["killed"] = True
                    _, stderr = process.communicate(timeout=2)
                (self.output_dir / "qemu-stderr.bin").write_bytes(stderr or b"")
                result["returncode"] = process.returncode
            except Exception as error:
                result["errors"].append("process: " + repr(error))
            result["still_running"] = process.poll() is None
            # A constructor's total deadline may interrupt communicate before
            # its TimeoutExpired handler. Still attempt one bounded kill while
            # retaining the original failure, and never mark a live child closed.
            if result["still_running"] and not result["killed"]:
                try:
                    process.kill()
                    result["killed"] = True
                    _, stderr = process.communicate(timeout=2)
                    (self.output_dir / "qemu-stderr.bin").write_bytes(stderr or b"")
                    result["returncode"] = process.returncode
                except Exception as error:
                    result["errors"].append("forced process cleanup: " + repr(error))
                result["still_running"] = process.poll() is None
            if result["still_running"]:
                result["errors"].append("QEMU process remains alive after bounded cleanup")
        temp = getattr(self, "temp", None)
        if temp is not None and not result["still_running"]:
            try:
                temp.cleanup()
            except Exception as error:
                result["errors"].append("private temporary directory: " + repr(error))
        self.closed = not result["still_running"]
        try:
            self.ledger.add("process-cleanup", **result)
        except Exception as error:
            result["errors"].append("cleanup ledger: " + repr(error))


def partial_identity(q, constructor_completed):
    """Preserve available constructor evidence without a new process or query."""
    result = dict(partial=True, constructor_completed=constructor_completed,
                  requested_binary=os.environ.get("HP1020_QEMU", "qemu-system-xtensaeb"),
                  requested_core="test_kc705_be", requested_machine="sim",
                  binary=None, binary_sha256=None, version=getattr(q, "version", None),
                  args=None, errors=[])
    binary = getattr(q, "binary", None)
    if binary:
        try:
            result["binary"] = str(Path(binary).resolve())
            result["binary_sha256"] = sha(Path(binary).read_bytes())
        except Exception as error:
            result["errors"].append("binary identity: " + repr(error))
    process = getattr(q, "process", None)
    if process is not None:
        result["args"] = process.args
    return result


def copy_sources(output_dir):
    module = sys.modules[QemuRAM.__module__]
    backend = Path(module.__file__).resolve()
    require(sha(backend.read_bytes()) == BACKEND_SHA256, "sealed unchanged QemuRAM source")
    primary = Path(os.environ.get("HP1020_ENTRY_QEMU_PRIMARY",
                                  str(Path(__file__).parent / "references" / "qemu-primary")))
    source_dir = output_dir / "source"
    source_dir.mkdir()
    sources = {}
    for name, source in (("hp1020_entry_qemu.py", Path(__file__)), ("hp1020_qemu_ram.py", backend)):
        raw = source.read_bytes()
        (source_dir / name).write_bytes(raw)
        sources[name] = sha(raw)
    for relative, wanted in PRIMARY_SHA256.items():
        raw = (primary / relative).read_bytes()
        require(sha(raw) == wanted, "sealed exact-version QEMU primary source: " + relative)
        destination = source_dir / "qemu-primary" / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(raw)
        sources["qemu-primary/" + relative] = wanted
    save_json(source_dir / "sha256.json", sources)
    return sources


def initial_piece(regions, address, size):
    for start, data in regions:
        if start <= address and address + size <= start + len(data):
            return data[address - start:address - start + size]
    raise EntryQemuError("initial byte slice outside supplied regions")


def read_registers(q, partial):
    for name, number in REGISTERS.items():
        partial[name] = q.reg(number)
    partial["physical_ar"] = []
    for number in range(1, 33):
        partial["physical_ar"].append(q.reg(number))
    partial["logical_a"] = []
    for number in range(124, 140):
        partial["logical_a"].append(q.reg(number))
    wb = partial["windowbase"]
    require(0 <= wb < 8, "observed WINDOWBASE field width")
    aliases = [partial["physical_ar"][(4 * wb + i) % 32] for i in range(16)]
    require(partial["logical_a"] == aliases, "actual current-window aliases match physical ARs")


def snapshot(q, name, output_dir, regions, report):
    folder = output_dir / name
    folder.mkdir()
    item = dict(name=name, status="partial", registers={}, regions=[])
    report["snapshots"].append(item)
    q.ledger.add("snapshot-start", name=name)
    try:
        read_registers(q, item["registers"])
        for start, original in regions:
            relative = name + f"/region-{start:08x}-{len(original):08x}.bin"
            path = output_dir / relative
            region = dict(start=start, bytes=len(original), captured_bytes=0, path=relative)
            item["regions"].append(region)
            try:
                with path.open("xb") as destination:
                    for offset in range(0, len(original), CHUNK_BYTES):
                        count = min(CHUNK_BYTES, len(original) - offset)
                        actual = q.read(start + offset, count)
                        destination.write(actual)
                        destination.flush()
                        region["captured_bytes"] += len(actual)
            finally:
                if path.exists():
                    region["sha256"] = sha(path.read_bytes())
        item["status"] = "complete"
        return item
    finally:
        save_json(folder / "registers.json", item["registers"])
        save_json(folder / "snapshot.json", item)
        q.ledger.add("snapshot-end", name=name, status=item["status"])


def verify_protected(snapshot_item, regions, output_dir, initial=False):
    require(snapshot_item["status"] == "complete", "complete capture before validation")
    for record, (start, original) in zip(snapshot_item["regions"], regions):
        actual = (output_dir / record["path"]).read_bytes()
        require(record["start"] == start and len(actual) == len(original), "capture identity/length")
        for offset, (before, after) in enumerate(zip(original, actual)):
            address = start + offset
            writable = not initial and any(low <= address < high for low, high in MUTABLE)
            require(before == after or writable, f"immutable loaded byte changed at{address:#x}")


def compare_snapshots(first, second):
    require(first["registers"] == second["registers"], "park step changed observed registers")
    require([(r["start"], r["bytes"], r["sha256"]) for r in first["regions"]] ==
            [(r["start"], r["bytes"], r["sha256"]) for r in second["regions"]],
            "park step changed supplied memory regions")


def execute(initial_regions, initial_registers, checkpoints, output_dir):
    """Return a report with status pass/fail; preserve partial evidence on failure.

    output_dir must be a new or empty directory. Operational/input failures
    after it is accepted produce result.json and a ledger. KeyboardInterrupt
    and SystemExit are recorded and re-raised after cleanup. Root must treat
    status!=pass as failure. This observer does not replace root's instruction,
    memory-access, CPU/workload oracle or stack audits.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    require(not any(output_dir.iterdir()), "output directory must be empty; no evidence overwrite")
    ledger = Ledger(output_dir / "host-interventions.jsonl")
    report = dict(status="fail", scope="single-entry independent QEMU RAM observation",
                  snapshots=[], supplied_no_asynchronous_events=True,
                  supplied_accessible_owned_ram=True, shared_backend_modified=False,
                  resume_attempted=False, checkpoint_stop_observed=False,
                  reset_calls=0, call_helpers=0,
                  memory_or_register_writes_after_lock=0,
                  limits="No physical CPU/loader/DMA/controller proof; root separately audits all linked instructions and concrete accesses.")
    q = None
    constructor_completed = False
    fatal = None
    started = time.monotonic()
    try:
        regions, registers, cp = normalize_inputs(initial_regions, initial_registers, checkpoints)
        report["source_sha256"] = copy_sources(output_dir)
        report["checkpoints"] = cp
        supplied = output_dir / "input"
        supplied.mkdir()
        report["initial_regions"] = []
        for start, data in regions:
            name = f"input/region-{start:08x}-{len(data):08x}.bin"
            (output_dir / name).write_bytes(data)
            report["initial_regions"].append(dict(start=start, bytes=len(data), path=name, sha256=sha(data)))
        save_json(supplied / "registers.json", registers)
        save_json(supplied / "checkpoints.json", cp)
        ledger.add("admitted-input", region_sha256=report["initial_regions"], registers=registers, checkpoints=cp)
        with deadline(TOTAL_TIMEOUT):
            # Allocate first so partial-constructor resources remain reachable.
            q = ObservedQemu.__new__(ObservedQemu)
            q.__init__(regions, registers, cp, ledger, output_dir)
            constructor_completed = True
            report["qemu"] = dict(version=q.version, core="test_kc705_be", machine="sim",
                                  binary=str(Path(q.binary).resolve()),
                                  binary_sha256=sha(Path(q.binary).read_bytes()), args=q.process.args)
            q.seed_once_and_lock()
            first = snapshot(q, "initial", output_dir, regions, report)
            verify_protected(first, regions, output_dir, initial=True)
            for name, value in registers.items():
                require(first["registers"][name] == value, "initial register read-back: " + name)
            require(q.active_breakpoint is None, "no historical breakpoint survives initial seed")
            for name, address in cp:
                original_code = initial_piece(regions, address, 3)
                q.ok(f"Z0,{address:x},1")
                require(q.read(address, 3) == original_code, "breakpoint insertion changed loaded code bytes")
                report["resume_attempted"] = True
                reply = q.command("c")
                require(reply.startswith("T05"), "unexpected continue stop: " + reply)
                require(q.reg(0) == address, "stop at exact next checkpoint without PC repair")
                report["checkpoint_stop_observed"] = True
                observed = snapshot(q, name, output_dir, regions, report)
                verify_protected(observed, regions, output_dir)
                require(observed["registers"]["pc"] == address, "checkpoint PC capture")
                q.captured = True
                q.ok(f"z0,{address:x},1")
                require(q.read(address, 3) == original_code, "breakpoint removal changed loaded code bytes")
            park = report["snapshots"][-1]
            park_address = cp[-1][1]
            report["park_instruction_hex"] = q.read(park_address, 3).hex()
            for index in (1, 2):
                reply = q.command("s")
                require(reply.startswith("T05"), "unexpected park step stop: " + reply)
                observed = snapshot(q, f"park-step-{index}", output_dir, regions, report)
                verify_protected(observed, regions, output_dir)
                require(observed["registers"]["pc"] == park_address, "park is a self-branch")
                compare_snapshots(park, observed)
            require(q.checkpoint_index == 4 and q.active_breakpoint is None and q.steps == 2,
                    "complete ordered observation with park breakpoint removed")
            report["status"] = "pass"
    except BaseException as error:
        report["error"] = dict(type=type(error).__name__, message=str(error))
        if not isinstance(error, Exception):
            fatal = error
    finally:
        if q is not None:
            if "qemu" not in report:
                report["qemu"] = partial_identity(q, constructor_completed)
            try:
                q.close()
                report["cleanup"] = q.cleanup
                report["gdb_commands"] = q.command_index
                report["initial_seed_commands"] = q.seed_index
                if q.cleanup and q.cleanup["errors"]:
                    report["status"] = "fail"
                    report.setdefault("error", dict(type="CleanupError", message="; ".join(q.cleanup["errors"])))
            except BaseException as error:
                report["status"] = "fail"
                report["cleanup_error"] = type(error).__name__ + ": " + str(error)
        report["elapsed_seconds"] = time.monotonic() - started
        try:
            ledger.add("adapter-finished", status=report["status"], error=report.get("error"))
        except Exception as error:
            report["status"] = "fail"
            report["ledger_finalize_error"] = type(error).__name__ + ": " + str(error)
        finally:
            ledger.close()
        report["host_intervention_ledger"] = dict(path=ledger.path.name,
                                                  sha256=sha(ledger.path.read_bytes()),
                                                  lines=ledger.lines, bytes=ledger.bytes)
        save_json(output_dir / "result.json", report)
    if fatal is not None:
        raise fatal
    return report
