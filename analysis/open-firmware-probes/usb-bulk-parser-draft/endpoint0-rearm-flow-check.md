# HP 1020 Marker Rearm Flow Check

- fail hits: `0`

| Severity | Check | Detail |
|---|---|---|
| `watch` | `response_enters_rearm_wait` | after submitting one descriptor response, marker should enter a gate-clear wait path |
| `watch` | `no_idle_after_successful_response` | successful marker response must not immediately park in the idle loop |
| `watch` | `rearm_state_recorded` | rearm wait should leave a RAM breadcrumb for postmortem diagnosis |
| `watch` | `waits_for_both_setup_gates` | rearm wait must read and mask both USB setup/status gates before polling again |
| `watch` | `rearm_returns_to_poll_loop` | after both gates clear, marker should return to the setup polling loop |
