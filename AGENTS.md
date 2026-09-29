# Agent instructions

## Owner and communication

Aayush delegates repository maintenance and technical decisions to the agents.
He does not intend to read notes, inspect reports, or learn printer internals.
Documentation is agent memory, never a deliverable he must review.

- Answer progress questions in plain language: is the replacement working yet,
  what changed, what matters next, and whether anything is needed from him.
- Distinguish the already-working HP-based printing setup from the unfinished
  open firmware replacement. Never call the overall task done because tests pass.
- Sustain autonomous work across multiple research checkpoints. A passing suite
  or a commit is not a reason to yield while a concrete productive avenue remains.
  Keep chat updates short during the longer run; do not ask the owner to restart work.
- Default to short updates. Omit addresses, instruction counts, commit hashes,
  document links and jargon unless requested or needed for a decision.
- Do not invent percentage-complete estimates or promise a completion date.
- Make routine technical/maintenance choices autonomously. Ask only for missing
  physical actions, consequential decisions or authorization actually needed.
- Use focused parallel agents when investigations or reviews are independently
  useful. Keep one lead responsible for shared context, integration and claims;
  avoid duplicate work and coordinate all validation sequentially.
- Keep these preferences across new tasks. Do not ask him to maintain context.

## Startup

1. Read `CURRENT_STATUS.md` for the current state, next action and restrictions.
2. Check `git status --short --branch`; preserve work already present.
3. Use `analysis/README.md` to find only the evidence relevant to the task.
   Do not load the entire report collection or repeat completed investigations.
4. For installed printing support, read `README.md` instead of research plans.

## Objective and authority

The target is a practical working replacement, with suitable open-source
components reused wherever they reduce the work. Functional compatibility and
reliable printing matter; reproducing HP's binary, internal architecture or bugs
does not. Use the original program to discover necessary hardware/protocol
contracts and as an independent reference. Do not make matching its internal
queues, object layouts or scheduling a requirement of an independent replacement.

The current execution scope remains offline development and capability
evaluation, without the owner's assistance or a printer. Revisit claimed
blockers and pursue useful offline experiments tied to that working path.
Missing hardware limits live proof, but does not rule out meaningful offline
implementation, binary analysis or differential execution.

Work toward feature parity with the closed driver for normal use of the HP
LaserJet 1020 Plus: reliable pages/documents, copies, supported media/quality
options, useful status, cancellation and recovery. Build the open firmware
replacement in narrow, independently verified stages using host-generated
ZjStream; current restricted profiles are milestones, not the final feature
target. Keep the working macOS/foo2zjs setup intact. Other models, networking,
scanning and unrelated features are out of scope.

Completion requires observed, repeatable physical printing with the replacement
firmware, including recovery after a power cycle. Models, uploads, quiet LEDs
and stock USB identity alone do not establish this. Record the tested scope and
remaining limitations; never substitute a test count for device evidence.

Offline research, local tools, reversible cleanup, coherent commits and pushes
to this repository's `main` are authorized. Repository maintenance does
not authorize changing installed printing files or contacting the printer.

- Do not enumerate/contact USB, send queries or upload firmware during offline work.
- Hardware tests require Aayush to explicitly request the specific test with the
  printer connected and freshly power-cycled. Use the existing guarded harness
  and its matching opt-ins; do not bypass them with direct backend commands.
- Follow the selected hardware test plan and its safer prerequisite stages.
  Descriptor reads also contact the device, even though they do not print.
- Do not introduce print-driving video/engine/mechanical MMIO without explicit
  permission. Unknown custom instructions are not assumed mechanically inert.
- Do not alter the installed queue, daemon, firmware or user runtime as research
  cleanup. Use the installer/uninstaller only for authorized printing maintenance.
- The repository is public at Aayush's request. Do not change its visibility
  without a new owner request. Retain stock assets, licenses and provenance.

## Evidence and validation

Verify important claims against stock bytes and control flow. Saved decompilation
can omit switch arms or arguments. Generated reports and passing consistency
checks establish agreement with a model, not correctness on hardware. Distinguish
observations, instruction-derived facts, hypotheses and device-tested behavior.

- Edit generators before regenerating derived reports; do not patch generated
  conclusions by hand. Preserve raw captures, source snapshots and byte fixtures.
- Run focused checks for the change. Run `scripts/validate.sh` before a research
  checkpoint or changes to shared validation; it is offline-only. For prose-only
  edits, check references and `git diff --check` instead of rebuilding firmware.
- Toolchains under `/tmp` are disposable. Recover them using the pinned build
  scripts referenced in `analysis/README.md`; do not trust old tool inventories.
- Review diffs, commit coherent checkpoints, push `main`, and verify sync.
  Do not commit unrelated user changes. Never run validation suites concurrently:
  they regenerate shared outputs.

## Documentation maintenance

- `CURRENT_STATUS.md` is the single current handoff: state, next action, blockers,
  latest validation and material corrections. Keep it roughly one page.
- `analysis/README.md` is a topic map and recovery guide, not a growing changelog.
- `analysis/open-firmware-model/next-evidence.md` owns the detailed unresolved
  questions and the observations needed to resolve them.
- Put durable technical evidence beside its implementation or generator. Add a
  new note only for a distinct question that existing notes cannot hold clearly.
- Update existing summaries; remove superseded planning duplicates after checking
  references. Git retains narrative history. Keep evidence and stable generated
  paths that validators consume; do not shuffle them for cosmetic organization.
- Revisit blockers when new evidence arrives. Do not busywork on duplicate models
  or declare all conceivable offline research impossible.
