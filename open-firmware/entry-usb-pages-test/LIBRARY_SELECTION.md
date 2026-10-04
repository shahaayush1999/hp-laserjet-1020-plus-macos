# Exact compiler runtime closure for the real-page entry

Pre-build hypothesis: removing the healthy runtime's packet modulo-six removes
its sole __umodsi3 reference. Provider division still selects __udivsi3. Retain
both original pinned archive members as evidence, but admit exactly _udivsi3.o
in the new actual map and no __umodsi3 symbol. An unexpected selection stops
admission; preserve it and review the source instead of broadening silently.
The accepted reset audit supplies the unchanged archive/member/byte rules.
