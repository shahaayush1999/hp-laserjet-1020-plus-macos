"""Draft independent direct-QEMU observer for the new continuous USB RAM profile.

The old direct observer and shared transport remain unchanged. This profile
owns its six actual component-entry breakpoints and split memory policy. It
never invokes a per-call helper, repairs registers, or writes after one seed.
"""
from pathlib import Path
import re
import time
from hp1020_entry_qemu import (
    ObservedQemu, EntryQemuError, Ledger, require, sha, save_json, deadline,
    REGISTERS, READ_REGISTERS, REGION_INTERVALS, CHUNK_BYTES, TOTAL_TIMEOUT,
    copy_sources, snapshot, initial_piece, compare_snapshots, partial_identity,
)
CHECKPOINT_NAMES=('after-normalization','pre-c','pre-close','pre-final-service','pre-finish','park')

class ObservedUSBQemu(ObservedQemu):
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
            require(self.within(address, 3) and self.checkpoint_index < 6,
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
            require(self.active_breakpoint is not None and not self.resumed and self.checkpoint_index < 6,
                    "continue requires the next ordered breakpoint, once")
            self.resumed = True
            return "continue-current-pc"
        if command == "s":
            require(self.active_breakpoint is None and self.checkpoint_index == 6 and self.steps < 2,
                    "single-step only twice after observed park")
            self.steps += 1
            return "single-step-park"
        raise EntryQemuError("post-seed GDB mutation or unadmitted command rejected: " + command[:80])


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
        0x10003000 <= initial["lend"] < 0x1000FFE0 or
        0x10016780 <= initial["lend"] < 0x100167E0),
        "incoming active loop must not redirect startup/code before normalization")
    require(isinstance(checkpoints, (list, tuple)) and len(checkpoints) == 6, "six ordered checkpoints")
    cp = []
    for wanted, item in zip(CHECKPOINT_NAMES, checkpoints):
        require(isinstance(item, (list, tuple)) and len(item) == 2, "checkpoint pair")
        name, address = item
        require(name == wanted and type(address) is int, "ordered checkpoint name/address")
        require((0x10003000 <= address <= 0x1000FFE0 - 3) or
                (0x10016780 <= address <= 0x100167E0 - 3), "checkpoint in candidate code budget")
        cp.append((name, address))
    require(len({a for _, a in cp}) == 6, "distinct checkpoint addresses")
    return ordered, initial, cp


def validate_policy(layout):
    require(isinstance(layout,dict) and set(layout)=={'zero_spans','owned_stack','initialized_data_span'},
            'closed USB observer memory-policy schema')
    zero=layout['zero_spans']
    require(isinstance(zero,(list,tuple)) and len(zero)==4,'four actual zero spans')
    zero=[tuple(x) for x in zero]
    require(all(len(x)==2 and all(type(v) is int for v in x) for x in zero),'integer zero ranges')
    require(zero[0][0]==0x10010000 and 13512<=zero[0][1]<=16352 and not(zero[0][1]&3) and
            zero[1:]==[(0x10016060,1024),(0x10016800,114704),(0x10032830,9216)],
            'exact bounded split-object zero policy')
    stack=tuple(layout['owned_stack']);data=tuple(layout['initialized_data_span'])
    require(stack==(0x10014020,8192),'exact8192-byte owned stack')
    require(len(data)==2 and all(type(x) is int for x in data) and data[0]==0x100164a0 and 0<data[1]<=96,
            'actual linked initialized-data extent')
    return [(a,a+n) for a,n in zero+[stack,data]]


def copy_usb_sources(output_dir):
    result=copy_sources(output_dir)
    source=Path(__file__);raw=source.read_bytes()
    (output_dir/'source'/source.name).write_bytes(raw)
    result[source.name]=sha(raw)
    save_json(output_dir/'source'/'sha256.json',result)
    return result


def verify_protected(snapshot_item, regions, output_dir, mutable, initial=False):
    require(snapshot_item["status"] == "complete", "complete capture before validation")
    for record, (start, original) in zip(snapshot_item["regions"], regions):
        actual = (output_dir / record["path"]).read_bytes()
        require(record["start"] == start and len(actual) == len(original), "capture identity/length")
        for offset, (before, after) in enumerate(zip(original, actual)):
            address = start + offset
            writable = not initial and any(low <= address < high for low, high in mutable)
            require(before == after or writable, f"immutable loaded byte changed at{address:#x}")


def execute(initial_regions, initial_registers, checkpoints, layout, output_dir):
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
        writable=validate_policy(layout)
        report["runtime_write_spans"]=[list(x) for x in writable]
        report["source_sha256"] = copy_usb_sources(output_dir)
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
            q = ObservedUSBQemu.__new__(ObservedUSBQemu)
            q.__init__(regions, registers, cp, ledger, output_dir)
            constructor_completed = True
            report["qemu"] = dict(version=q.version, core="test_kc705_be", machine="sim",
                                  binary=str(Path(q.binary).resolve()),
                                  binary_sha256=sha(Path(q.binary).read_bytes()), args=q.process.args)
            q.seed_once_and_lock()
            first = snapshot(q, "initial", output_dir, regions, report)
            verify_protected(first, regions, output_dir, writable, initial=True)
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
                verify_protected(observed, regions, output_dir, writable)
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
                verify_protected(observed, regions, output_dir, writable)
                require(observed["registers"]["pc"] == park_address, "park is a self-branch")
                compare_snapshots(park, observed)
            require(q.checkpoint_index == 6 and q.active_breakpoint is None and q.steps == 2,
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
