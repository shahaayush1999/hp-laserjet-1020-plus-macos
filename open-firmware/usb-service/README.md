# Shared controller and command service

This coordinator joins the existing controller programming, OUT publication,
IN publication and command pump. It owns no buffers, allocates no identifiers
and supplies no physical backend. Initialize its stationary graph once after
the components. All components must refer to the same adapter/document.

Use its control, pump, OUT-arm and IN-publication wrappers for ordinary work.
Every DCD submission must check `hp1020_usb_service_submission_allowed`; the IN
publisher's `io.ready` must include `hp1020_usb_service_in_ready` as well as any
independent platform readiness conditions. Before programming selection/grant,
check `hp1020_usb_service_program_allowed` and retain that operation's own
checks. Require all three combined progress bits before close/finish,
finish-reset and independent EP0 publication. Do not call the ordinary document
pump alongside the command pump.

A failed IN publication stops new controller programming and OUT work just as
an OUT failure stops IN work. Binding readiness and captured-but-undispatched
control requests remain gates. Only an already admitted, inactive actual bus
reset can permit service behind a publication failure. An unready binding's
SERVICE-only permission is not that exception. Terminal command ownership
errors also stop ordinary work.

Pump first reaps any returned original reply; this can proceed behind a failure
without consuming input or submitting another reply. Exact-cookie completion/
cancellation and actual-reset admission remain separate, available operations.
Each publisher's existing cleanup still requires its own original identity and
independently supplied physical cleanup. Clearing one failure cannot clear
another, manufacture quiescence or authorize new work with an old binding.

This is software coordination. CPU/DMA mapping, cache visibility, captures,
controller cleanup, FIFO readiness, status observations and page output still
need real providers. Existing entry RAM experiments are not hardware firmware.

`python3 scripts/validate-hp1020-usb-service.py --target` exercises real
programming, OUT/IN descriptors, TinyUSB and the command pump with supplied RAM
observations. It checks ECHO/status and exact two-page pixels, failures in both
directions and programming, original-result collection behind closed gates,
actual reset drainage and interface re-selection. The current result is
`analysis/usb-path/usb-service-validation.json`. Busy/graph checks are explicit
software-state mutations, not physical failure evidence.
