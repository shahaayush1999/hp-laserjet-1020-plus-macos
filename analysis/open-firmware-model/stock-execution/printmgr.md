# Original PrintMgr execution

40 cases agree between the instruction interpreter, QEMU and explicit routing/ownership expectations.

- Original PrintMgr startup creates 20-byte circular subscriber records for entries 1 and 24, queue 1, null callback.
- Cancel message 15 enters state 1 and forwards the reason to engine queue 0. First injected acknowledgement 37 drains both PrintMgr node lists, enters state 2 and sends stop 15 to Video queue 8. Second acknowledgement returns state 0 and forwards 37 to JobMgr queue 3.
- PrintMgr frees only its 16-byte list nodes in these stop paths; referenced 148-byte work allocations remain byte-identical and owned elsewhere.
- Engine/video event 23 is consumed by PrintMgr and selected numeric events produce StatusMgr queue 10 message 44. The old default-engine-consumer interpretation was wrong.

Both stop acknowledgements are injected queue inputs. Engine stop, Video reset, real queue scheduling and work-buffer retirement are outside this test. Empty/seeded RAM list and media-state fixtures are explicit. RTOS locks/startup and allocator share host services across engines. QEMU independently executes the selected CPU instructions, original register-window vectors and critical-mask helpers; it is not the printer CPU or hardware proof.
