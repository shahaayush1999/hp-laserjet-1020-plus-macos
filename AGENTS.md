# Agent instructions

## Hard rule: paid effort must advance reverse engineering

Aayush is paying for reverse engineering that leads to a working replacement.
Nothing that does not contribute to that goal is welcome. This is a binding
project rule for every session, continuation and delegated agent until he
explicitly changes it.

Before spending effort, identify the concrete unknown, missing capability or
relevant regression the work will resolve. If there is no direct contribution,
skip it. Make that decision internally; do not create another justification
document or ask the owner to manage priorities. Necessary tooling, tests and
notes must be the minimum useful support for the implementation. No cosmetic
polish, speculative infrastructure, audit bureaucracy or repeated proof of
settled facts. Reports, test counts and commits are not progress by themselves.
Prefer the next missing capability; stop investigating once there is enough
evidence to implement or reject an approach. Treat time, tokens and agent usage
as the owner's money, not a budget to exhaust.

## Goal and working style

Build a practical open firmware replacement for the HP LaserJet 1020 Plus.
Reuse open components where useful. Functional printing, copies, normal media/
quality options, status, cancellation and recovery matter; reproducing HP's
internal architecture or bugs does not. The existing HP-based Mac driver is a
separate working product and must remain intact.

Aayush delegates technical decisions and repository maintenance. He will not
read reports or maintain context. Give brief plain-language updates; distinguish
offline findings from working physical printing. Do not invent percentages or
dates. Tests passing does not mean the replacement is complete.

- Keep working across useful checkpoints when asked to continue; stop when asked.
- Make routine decisions autonomously. Ask only for missing physical actions or
  consequential authorization. Use agents only for genuinely independent work
  that shortens the task; avoid routine duplicate reviews.
- Read `CURRENT_STATUS.md`, check `git status --short --branch`, then consult only
  the relevant topic in `analysis/README.md`. Read root `README.md` for driver work.
- No new audit diaries, per-session archives, duplicate source snapshots, progress
  matrices or reports about reports. Git preserves history. Keep current code,
  necessary fixtures/raw evidence, and concise actionable findings.

## Authorization and boundaries

Offline research, local tools, reversible pruning, commits and pushes to `main`
are authorized. Preserve unrelated user changes, original assets, licenses and
required provenance. The repository is public; do not change its visibility.

- Do not enumerate/contact USB, query a printer or upload firmware during offline
  work. Descriptor reads also contact the device.
- Hardware tests require the owner's explicit request for that specific test,
  with the printer connected and freshly power-cycled. Use the existing guarded
  harness and matching opt-ins, following its prerequisite stages.
- Do not add print-driving video/engine/mechanical MMIO without permission.
  Unknown custom instructions are not assumed mechanically inert.
- Do not change installed queues, daemons, firmware or printing files as research
  cleanup. Installer/uninstaller use requires printing-maintenance authorization.
- Completion requires repeatable physical output from the replacement, including
  recovery after a power cycle. Offline execution, uploads or stock identity do
  not establish this. Record the actual tested scope.

## Evidence and proportionate validation

Verify important hardware/protocol claims against original bytes and control
flow; decompilation can omit arguments and switch arms. Distinguish observations,
conditional models, hypotheses and device-tested behavior.

- Edit generators before regenerating reports. Never patch reported source hashes
  to make changed code look tested. Retain current reproducible fixtures and raw
  evidence needed by active checks; obsolete runs can remain in Git history.
- Run checks for the changed behavior and its affected callers. Broaden testing
  when shared code, new failures or unresolved concerns justify it. A commit or
  handoff alone is not a reason to rerun every historical experiment.
- `scripts/validate.sh` remains the complete offline suite for broad integration
  changes or a release candidate. Do not run it for prose/archive cleanup. Use
  reference/source checks and `git diff --check` for those changes.
- Never run validators concurrently: they regenerate shared outputs. Stop after
  relevant checks pass; do not repeat them to increase test counts.
- Recover disposable tools through the pinned scripts in `analysis/README.md`.
  Preserve their source, checksum and instruction-encoding checks.
- Review the diff, commit coherent work, push `main`, and verify sync.

## Minimal memory

`CURRENT_STATUS.md` holds only current capability, validation limits and next
work. `analysis/README.md` is a short navigation/tool-recovery map.
`analysis/open-firmware-model/next-evidence.md` holds concrete unresolved contracts
and implementation decisions. Put durable findings beside their code; replace
superseded summaries instead of appending dated run histories. Do not require the
owner to review or maintain any of these files.
