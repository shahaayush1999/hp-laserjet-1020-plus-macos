# Reachable instruction gate

Status: pass. 21 instructions from entry and six vector roots; 6 proven constant trampolines; zero unknown/custom instructions.

Literal pools are skipped by control-flow traversal. Indirect targets require the same constant load on every incoming path. Unknown instructions, user-register access and unproven indirect transfers fail closed.

CPU instruction/control-flow gate only; existing memory and MMIO audits remain mandatory
