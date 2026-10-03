"""UNEXECUTED reset-profile observation extension of the accepted USB model.

No new instruction, memory, stack or CPU permission.  The inherited six core
guards and their evidence remain unchanged.  The additional observations see
only natural instruction transitions; they never call a target API or read
target data through the modeled load/access path.
"""
from hp1020_entry_usb_machine import EntryUSBMachine
from hp1020_entry_machine import require


# Exact order from the independently frozen reset literal-addendum.py.  Its
# pre-c role is the existing before-C assembly checkpoint, not the C entry.
CHECKPOINT_ROLES = (
    ('after-normalization', 'hp1020_entry_after_normalization'),
    ('pre-c', 'hp1020_entry_before_c'),
    ('pre-initial-status', 'hp1020_udc_ep0_take_submission'),
    ('pre-reset-offer', 'hp1020_udc_setup_offer'),
    ('pre-cancel-mark', 'hp1020_udc_out_request_cancel'),
    ('pre-receive-owned', 'hp1020_tusb_adapter_ack_reset'),
    ('pre-late-service', 'hp1020_udc_publish_service'),
    ('pre-receive-drained', 'hp1020_tusb_adapter_ack_reset'),
    ('pre-restart', 'hp1020_usb_document_restart'),
    ('pre-reset-status', 'hp1020_udc_ep0_take_submission'),
    ('pre-fresh-arm', 'hp1020_udc_publish_arm_out'),
    ('pre-fresh-service', 'hp1020_udc_publish_service'),
    ('pre-reuse-arm', 'hp1020_udc_publish_arm_out'),
    ('pre-stale-acquire', 'hp1020_udc_acquire_packet'),
    ('pre-stale-cancel', 'hp1020_udc_out_request_cancel'),
    ('post-stale-pair', 'hp1020_usb_runtime_ram_install_bulk'),
    ('pre-close', 'hp1020_tusb_adapter_close_input'),
    ('pre-final-service', 'hp1020_udc_publish_service'),
    ('pre-finish', 'hp1020_tusb_adapter_finish'),
    ('park', 'hp1020_entry_park'),
)
CORE_NAMES = ('after-normalization', 'pre-c', 'pre-close',
              'pre-final-service', 'pre-finish', 'park')
ADDITIONAL_ENTRIES = (
    'hp1020_udc_out_request_cancel',
    'hp1020_usb_runtime_ram_reset_observation',
    'hp1020_usb_runtime_ram_install_bulk',
    'hp1020_usb_runtime_ram_check',
    'hp1020_usb_receive_complete_data',
    'hp1020_usb_receive_release',
    'hp1020_image_output_feed',
    'hp1020_image_ring_accept',
    'hp1020_image_ring_complete',
    'dcd_edpt0_status_complete',
    'driver_xfer', 'document_out', 'request_cancel', 'output', 'document_event',
)
MAX_INSTRUCTIONS = 10000000


class EntryUSBResetMachine(EntryUSBMachine):
    def __init__(self, program, regions, initial, checkpoints, trace_dir, observe):
        require(isinstance(checkpoints, (list, tuple)) and len(checkpoints) == 20,
                'reset profile requires exactly twenty natural checkpoints')
        ordered = []
        for item, (label, symbol) in zip(checkpoints, CHECKPOINT_ROLES):
            require(isinstance(item, (tuple, list)) and len(item) == 2,
                    'reset checkpoint pair')
            supplied_label, address = item
            require(supplied_label == label and type(address) is int and
                    address == program.symbols[symbol],
                    'reset checkpoint name/original linked symbol mismatch')
            ordered.append((label, address))
        require(all(a[1] != b[1] for a, b in zip(ordered, ordered[1:])),
                'successive natural checkpoints must not need a hidden skip')
        self.reset_checkpoint_pairs = tuple(ordered)
        self.reset_checkpoint_order = [label for label, _ in ordered]
        self.reset_seen = []
        self.reset_observations = []
        self.reset_api_events = []
        self._reset_frames = []
        self._core_observations = []
        self._reset_observe = observe
        self._reset_run_started = False
        self._reset_transfer = None
        # Pass only the unchanged accepted six guards to the accepted parent.
        # Do not overwrite its checkpoints, seen, calls, entry_names or ledgers.
        core = [(label, address) for label, address in ordered if label in CORE_NAMES]
        super().__init__(program, regions, initial, core, trace_dir,
                         self._defer_core_observation)
        try:
            require(tuple(self.checkpoint_order) == CORE_NAMES, 'inherited core guard order')
            self._bind_reset_entries(program)
        except BaseException as error:
            # The successful parent constructor owns open trace streams.  A
            # later symbol/guard rejection must close those resources even
            # though no complete instance is returned to the runner.
            try:
                self.close()
            except BaseException as cleanup:
                raise error from cleanup
            raise

    def _bind_reset_entries(self, program):
        # A name->address dictionary collapses duplicate local request_cancel
        # definitions.  Keep every actual audited nonempty function record;
        # the independent gate binds callback provenance by original pointers.
        records = program.entry_symbol_records
        watched_names = set(self.entry_names.values()) | set(ADDITIONAL_ENTRIES)
        found = set()
        self._reset_entry_names = {}
        for row in records:
            if row['type'] != 2 or not row['size'] or row['name'] not in watched_names:
                continue
            address = row['address']
            require(address in program.entry_function_starts and
                    address in program.instructions, 'observed entry is not admitted code')
            names = self._reset_entry_names.setdefault(address, [])
            require(row['name'] not in names, 'duplicate identical observed symbol record')
            names.append(row['name'])
            found.add(row['name'])
        require(found == watched_names, 'missing linked reset observation function')
        for names in self._reset_entry_names.values():
            names.sort()

    def _defer_core_observation(self, label, registers, regions):
        # The parent already established every core guard.  Defer only the
        # external file observation until this same transition's call ledger
        # has been recorded.  No target instruction executes in between.
        self._core_observations.append((label, registers, regions))

    def span(self, address, size, execute=False):
        # The unchanged engine calls this once for the actual instruction
        # fetch, before incrementing steps or changing any target register.
        # In particular CALLX0 a0 overwrites a0 with its return address later.
        # First preserve every inherited backing/fetch permission check.
        result = super().span(address, size, execute=execute)
        if execute:
            op, args, encoded = self.program.instructions[address]
            require(address == self.pc and size == len(encoded),
                    'indirect observation requires the exact actual fetch')
            self._reset_transfer = None
            if op in ('jx', 'callx0'):
                require(len(args) == 1 and type(args[0]) is int and
                        0 <= args[0] < 16, 'audited indirect register operand')
                register = args[0]
                self._reset_transfer = (address, self.steps, register,
                                        self.registers[register])
        # The base run loop still compares every fetched byte with the audited
        # instruction immediately after this returns. No load/access is added.
        return result

    def _observe_reset(self, label, registers, regions):
        index = len(self.reset_seen)
        require(index < 20 and self.reset_checkpoint_order[index] == label,
                'reset natural checkpoint order changed')
        address = self.reset_checkpoint_pairs[index][1]
        require(registers['pc'] == address, 'reset observation PC mismatch')
        self.reset_seen.append(label)
        self.reset_observations.append(dict(label=label, address=address,
            instruction=self.steps,
            access_index=self.access_count['read'] + self.access_count['write']))
        self._reset_observe(label, registers, regions)

    def after_instruction(self, pc, next_pc):
        op, args, _encoded = self.program.instructions[pc]
        base = op.removesuffix('.n')
        transfer_register = transfer_value = None
        if base in ('jx', 'callx0'):
            require(self._reset_transfer is not None and
                    self._reset_transfer[:3] == (pc, self.steps - 1, args[0]) and
                    self._reset_transfer[3] == next_pc,
                    'indirect transfer differs from its original fetch operand')
            transfer_register, transfer_value = self._reset_transfer[2:]
        else:
            require(self._reset_transfer is None,
                    'indirect operand leaked into another instruction')
        self._reset_transfer = None
        require(len(self._reset_frames) == len(self.call_stack),
                'observational call-frame depth differs from guarded caller stack')
        # The accepted parent performs all state changes, instruction/access
        # traces, normalized CPU/SP guards, close/finish rules and park checks.
        result = super().after_instruction(pc, next_pc)
        access_index = self.access_count['read'] + self.access_count['write']
        if base in ('call0', 'callx0'):
            caller = self.call_stack[-1]
            self._reset_frames.append(dict(call_ledger_index=len(self.calls) - 1,
                call_pc=caller['pc'], return_pc=caller['return_pc'], sp=caller['sp'],
                depth=len(self.call_stack), entries=[]))
        elif base == 'ret':
            require(self._reset_frames, 'observation return without original frame')
            frame = self._reset_frames.pop()
            require(next_pc == frame['return_pc'] and self.registers[1] == frame['sp'],
                    'observed return differs from already-guarded original frame')
            # Tail-entered functions can share this one real physical frame.
            # Each row refers to its actual entry and this actual RET; none is
            # an invented return, extra call, completion or target transition.
            for entry_index in reversed(frame['entries']):
                entry = self.reset_api_events[entry_index]
                self.reset_api_events.append(dict(kind='return',
                    entry_event_index=entry_index, name=entry['name'], pc=pc,
                    target=next_pc, instruction=self.steps, access_index=access_index,
                    result=self.registers[2], sp=self.registers[1],
                    call_ledger_index=frame['call_ledger_index'], depth=frame['depth']))
        require(len(self._reset_frames) == len(self.call_stack),
                'observational frame tracking changed guarded call depth')
        if next_pc in self._reset_entry_names:
            require(self._reset_frames, 'selected API entry without an original call frame')
            frame = self._reset_frames[-1]
            for name in self._reset_entry_names[next_pc]:
                event_index = len(self.reset_api_events)
                self.reset_api_events.append(dict(kind='entry', name=name, pc=pc,
                    target=next_pc, instruction=self.steps, access_index=access_index,
                    arguments=self.registers[2:8].copy(), sp=self.registers[1],
                    return_pc=frame['return_pc'], call_pc=frame['call_pc'],
                    call_ledger_index=frame['call_ledger_index'], depth=frame['depth'],
                    transfer=op, transfer_register=transfer_register,
                    transfer_value=transfer_value))
                frame['entries'].append(event_index)
        require(len(self._core_observations) <= 1, 'multiple core observations in one transition')
        if self._core_observations:
            label, registers, regions = self._core_observations.pop()
            self._observe_reset(label, registers, regions)
        elif len(self.reset_seen) < 20:
            label, address = self.reset_checkpoint_pairs[len(self.reset_seen)]
            if label not in CORE_NAMES and next_pc == address:
                self._observe_reset(label, self.registers_at(address), self.regions_at())
        return result

    def run(self, args=(), budget=MAX_INSTRUCTIONS):
        require(not self._reset_run_started and args == () and
                type(budget) is int and 0 < budget <= MAX_INSTRUCTIONS,
                'one reset lifecycle, no argument injection or budget expansion')
        self._reset_run_started = True
        return super().run(args=(), budget=budget)

    def evidence(self):
        result = super().evidence()
        require(self.reset_seen == self.reset_checkpoint_order and
                len(self.reset_observations) == 20 and not self._reset_frames and
                not self._core_observations and self._reset_transfer is None,
                'incomplete reset observation lifecycle')
        result.update(reset_checkpoints=list(self.reset_seen),
            reset_observations=self.reset_observations,
            reset_api_events=self.reset_api_events,
            reset_observation_schema='hp1020-entry-usb-reset-observation-v1',
            reset_cursor_convention='completed instructions/accesses before target; causing PC at instruction-1',
            reset_host_target_calls=0, reset_host_target_mutations=0)
        return result
