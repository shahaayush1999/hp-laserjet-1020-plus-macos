"""UNEXECUTED direct QEMU observer for the separately frozen USB pages profile.

Only the ten natural breakpoint roles differ from the accepted observer.
Transport, seed lock, 57-register/57-chunk snapshots, command/byte/time limits,
cleanup and the six-span split RAM protection policy are reused unchanged.
There is no per-call target execution, hidden breakpoint skip or post-seed write.
"""
from pathlib import Path
import re
import time
import hp1020_entry_usb_qemu as healthy
from hp1020_entry_qemu import (
    EntryQemuError, Ledger, require, sha, save_json, deadline, TOTAL_TIMEOUT,
    REGISTERS, READ_REGISTERS, CHUNK_BYTES, REGION_INTERVALS,
    snapshot, initial_piece, compare_snapshots, partial_identity,
)


# Independently frozen ten-label sequence.  The two startup roles resolve
# to the existing assembly labels; repeated functions retain one actual PC.
CHECKPOINT_ROLES = (('after-normalization', 'hp1020_entry_after_normalization'), ('pre-c', 'hp1020_entry_before_c'), ('pre-first-output', 'output'), ('pre-first-complete', 'hp1020_image_ring_complete'), ('pre-second-output', 'output'), ('pre-document-event', 'document_event'), ('pre-close', 'hp1020_tusb_adapter_close_input'), ('pre-final-service', 'hp1020_udc_publish_service'), ('pre-finish', 'hp1020_tusb_adapter_finish'), ('park', 'hp1020_entry_park'))

CORE_NAMES = ('after-normalization', 'pre-c', 'pre-close',
              'pre-final-service', 'pre-finish', 'park')
HEALTHY_OBSERVER_SHA256 = '2b16ee504abebd6f184fe2f78c035b85f16df2e4c89102bd98735c6ddb197e59'


class ObservedUSBPagesQemu(healthy.ObservedUSBQemu):
    def guard(self, command):
        # Constructor/seed and every non-execution read remain the unchanged
        # accepted command guard.  Override only its finite breakpoint count.
        if self.phase != 'observe':
            return super().guard(command)
        match = re.fullmatch(r'([Zz])0,([0-9a-f]+),1', command)
        if match:
            adding, address = match.group(1) == 'Z', int(match.group(2), 16)
            require(self.within(address, 3) and self.checkpoint_index < 10,
                    'breakpoint outside admitted pages checkpoint')
            require(address == self.checkpoints[self.checkpoint_index][1],
                    'pages breakpoint order/address')
            if adding:
                require(self.active_breakpoint is None and not self.resumed and not self.captured,
                        'one unconsumed pages breakpoint at a time')
            else:
                require(self.active_breakpoint == address and self.resumed and self.captured,
                        'only consumed observed pages breakpoint may be removed')
            return 'add-breakpoint' if adding else 'remove-breakpoint'
        if command == 'c':
            require(self.active_breakpoint is not None and not self.resumed and self.checkpoint_index < 10,
                    'continue requires the next pages breakpoint exactly once')
            self.resumed = True
            return 'continue-current-pc'
        if command == 's':
            require(self.active_breakpoint is None and self.checkpoint_index == 10 and self.steps < 2,
                    'single-step only twice after observed pages park')
            self.steps += 1
            return 'single-step-park'
        return super().guard(command)


def normalize_inputs(regions, registers, checkpoints):
    require(isinstance(checkpoints, (list, tuple)) and len(checkpoints) == 10,
            'ten ordered natural pages checkpoints')
    cp = []
    role_addresses = {}
    address_roles = {}
    for wanted, item in zip(CHECKPOINT_ROLES, checkpoints):
        require(isinstance(item, (list, tuple)) and len(item) == 2, 'pages checkpoint pair')
        name, address = item
        label, role = wanted
        require(name == label and type(address) is int, 'pages checkpoint order/name')
        require((0x10003000 <= address <= 0x1000FFE0 - 3) or
                (0x10016780 <= address <= 0x100167E0 - 3),
                'pages checkpoint outside unchanged candidate code budget')
        if role in role_addresses:
            require(role_addresses[role] == address, 'same natural role changed original PC')
        else:
            require(address not in address_roles, 'distinct natural roles alias one PC')
            role_addresses[role] = address
            address_roles[address] = role
        cp.append((name, address))
    require(all(a[1] != b[1] for a, b in zip(cp, cp[1:])),
            'successive stopped PCs require no hidden instruction skip')
    core = [(name, address) for name, address in cp if name in CORE_NAMES]
    ordered, initial, _ = healthy.normalize_inputs(regions, registers, core)
    require(len(READ_REGISTERS) == 57 and
            sum((end - start + CHUNK_BYTES - 1) // CHUNK_BYTES
                for start, end in REGION_INTERVALS) == 57,
            'unchanged complete register and memory snapshot geometry')
    return ordered, initial, cp


def copy_pages_sources(output_dir):
    require(sha(Path(healthy.__file__).read_bytes()) == HEALTHY_OBSERVER_SHA256,
            'unchanged accepted USB observer dependency')
    result = healthy.copy_usb_sources(output_dir)
    source = Path(__file__)
    raw = source.read_bytes()
    (output_dir / 'source' / source.name).write_bytes(raw)
    result[source.name] = sha(raw)
    save_json(output_dir / 'source' / 'sha256.json', result)
    return result


def execute(initial_regions, initial_registers, checkpoints, layout, output_dir):
    """Observe exactly one seed, ten next natural stops and two park steps.

    Return pass/fail and preserve partial evidence/cleanup on failure.  The root
    still owns the independent linked/input/CPU/access/semantic acceptance gate;
    these natural stops neither supply results nor prove physical settlement.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    require(not any(output_dir.iterdir()), 'output directory must be empty; no evidence overwrite')
    ledger = Ledger(output_dir / 'host-interventions.jsonl')
    report = dict(status='fail', scope='single-entry independent QEMU USB pages RAM observation',
                  snapshots=[], supplied_no_asynchronous_events=True,
                  supplied_accessible_owned_ram=True, shared_backend_modified=False,
                  resume_attempted=False, checkpoint_stop_observed=False,
                  reset_calls=0, call_helpers=0, memory_or_register_writes_after_lock=0,
                  limits='No physical CPU/loader/DMA/controller/printing proof; linked instructions and accesses require independent admission.')
    q = None
    constructor_completed = False
    fatal = None
    started = time.monotonic()
    try:
        regions, registers, cp = normalize_inputs(initial_regions, initial_registers, checkpoints)
        writable = healthy.validate_policy(layout)
        report['runtime_write_spans'] = [list(x) for x in writable]
        report['source_sha256'] = copy_pages_sources(output_dir)
        report['checkpoints'] = cp
        supplied = output_dir / 'input'
        supplied.mkdir()
        report['initial_regions'] = []
        for start, data in regions:
            name = f'input/region-{start:08x}-{len(data):08x}.bin'
            (output_dir / name).write_bytes(data)
            report['initial_regions'].append(dict(start=start, bytes=len(data), path=name, sha256=sha(data)))
        save_json(supplied / 'registers.json', registers)
        save_json(supplied / 'checkpoints.json', cp)
        ledger.add('admitted-input', region_sha256=report['initial_regions'], registers=registers, checkpoints=cp)
        with deadline(TOTAL_TIMEOUT):
            q = ObservedUSBPagesQemu.__new__(ObservedUSBPagesQemu)
            q.__init__(regions, registers, cp, ledger, output_dir)
            constructor_completed = True
            report['qemu'] = dict(version=q.version, core='test_kc705_be', machine='sim',
                                  binary=str(Path(q.binary).resolve()),
                                  binary_sha256=sha(Path(q.binary).read_bytes()), args=q.process.args)
            q.seed_once_and_lock()
            first = snapshot(q, 'initial', output_dir, regions, report)
            healthy.verify_protected(first, regions, output_dir, writable, initial=True)
            for name, value in registers.items():
                require(first['registers'][name] == value, 'initial register read-back: ' + name)
            require(q.active_breakpoint is None, 'no historical breakpoint survives initial seed')
            for name, address in cp:
                original_code = initial_piece(regions, address, 3)
                q.ok(f'Z0,{address:x},1')
                require(q.read(address, 3) == original_code, 'breakpoint insertion changed loaded code')
                report['resume_attempted'] = True
                reply = q.command('c')
                require(reply.startswith('T05'), 'unexpected continue stop: ' + reply)
                require(q.reg(0) == address, 'next natural stop differs; no occurrence may be skipped')
                report['checkpoint_stop_observed'] = True
                observed = snapshot(q, name, output_dir, regions, report)
                healthy.verify_protected(observed, regions, output_dir, writable)
                require(observed['registers']['pc'] == address, 'pages checkpoint PC capture')
                q.captured = True
                q.ok(f'z0,{address:x},1')
                require(q.read(address, 3) == original_code, 'breakpoint removal changed loaded code')
            park = report['snapshots'][-1]
            park_address = cp[-1][1]
            report['park_instruction_hex'] = q.read(park_address, 3).hex()
            for index in (1, 2):
                reply = q.command('s')
                require(reply.startswith('T05'), 'unexpected park step stop: ' + reply)
                observed = snapshot(q, f'park-step-{index}', output_dir, regions, report)
                healthy.verify_protected(observed, regions, output_dir, writable)
                require(observed['registers']['pc'] == park_address, 'terminal park is not a self-branch')
                compare_snapshots(park, observed)
            require(q.checkpoint_index == 10 and q.active_breakpoint is None and q.steps == 2 and
                    len(report['snapshots']) == 13, 'complete ten-stop pages observation plus two parks')
            report['status'] = 'pass'
    except BaseException as error:
        report['error'] = dict(type=type(error).__name__, message=str(error))
        if not isinstance(error, Exception):
            fatal = error
    finally:
        if q is not None:
            if 'qemu' not in report:
                report['qemu'] = partial_identity(q, constructor_completed)
            try:
                q.close()
                report['cleanup'] = q.cleanup
                report['gdb_commands'] = q.command_index
                report['initial_seed_commands'] = q.seed_index
                if q.cleanup and q.cleanup['errors']:
                    report['status'] = 'fail'
                    report.setdefault('error', dict(type='CleanupError', message='; '.join(q.cleanup['errors'])))
            except BaseException as error:
                report['status'] = 'fail'
                report['cleanup_error'] = type(error).__name__ + ': ' + str(error)
        report['elapsed_seconds'] = time.monotonic() - started
        try:
            ledger.add('adapter-finished', status=report['status'], error=report.get('error'))
        except Exception as error:
            report['status'] = 'fail'
            report['ledger_finalize_error'] = type(error).__name__ + ': ' + str(error)
        finally:
            ledger.close()
        report['host_intervention_ledger'] = dict(path=ledger.path.name,
            sha256=sha(ledger.path.read_bytes()), lines=ledger.lines, bytes=ledger.bytes)
        save_json(output_dir / 'result.json', report)
    if fatal is not None:
        raise fatal
    return report
