# Portable page and band plan

Status: pass. 1398 native ASan/UBSan cases and 5394344 band partitions checked.

RAM arithmetic only; complete page, bounded stock metadata, NBIE1, 600dpi BPP1/2, height divisible by four, RET0, ECONOMODE0/1; no hardware authorization.

A4 default: stride/window 1200, four rows per band, 1706 bands, 8,188,800 row bytes per copy. BPP4 and the inconsistent logical-clip metadata fixture are rejected by this deliberately narrow planning policy. The semantic parser can still retain those inputs for analysis.

Custom callback transformations, asynchronous buffer ownership, USB/device execution, and physical engine/video sequencing remain outside this component.
