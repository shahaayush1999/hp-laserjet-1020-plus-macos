# Original engine decision execution

Status: pass. 133,941 cases, 12,508,027 instructions, 203 distinct instructions.

Original decision code only; all MMIO forbidden. Exhaustive status_2 and substatus_16 axes are not exhaustive joint inputs or physical calibration.

Compares stored event, event emissions, status-read order, command intents and state latches. Every instruction and both outcomes of every conditional branch are reached. Each 16-bit status_2 value and each 16-bit substatus_16 value is exercised in a fixed qualifying context; substatus_13, mixed random inputs, prior events and latch transitions add branch coverage.

The original status-I/O, queue, datastore and reset helpers are intercepted, never executed. No engine/video/MMIO implementation is added to open firmware. Physical meanings and timing remain unknown.
