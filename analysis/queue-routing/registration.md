# Stock queue registration audit

All seven annotated direct CALL8 registration sites. Conservative control-flow constant propagation, with explicit CALL8 preservation of a0..a7. Registration helper separately agrees with a table-update oracle in both interpreter and QEMU.

| ID | Original queue name | Object | Constructor | Registration call |
|---:|---|---|---|---|
| 0 | engMsgQ | `0x1002f134` | `0x100164a8` | `0x1001653a` |
| 1 | PrintMgrQueue | `0x10028a74` | `0x1000f294` | `0x1000f2f1` |
| 3 | Job Mgr Queue | `0x10023e40` | `0x1000e3ac` | `0x1000e3cc` |
| 4 |  | `0x1002c9f8` | `0x10013688` | `0x100136aa` |
| 8 | Video Queue | `0x1002ee38` | `0x10013cfc` | `0x10013d1e` |
| 10 | StatusMgrQueue | `0x10028adc` | `0x10010504` | `0x10010540` |
| 15 | DelayMgr Msg Queue | `0x1001d694` | `0x10010aac` | `0x10010ade` |

Registration bounds and occupied-slot behavior agree in 48 independent QEMU/interpreter cases.

Correction: older queue maps reversed IDs 0 and 1 and mistook the JobMgr task object for its queue. Queue 1 is PrintMgr; queue 0 is engine. Datastore notifications to queue 1 therefore do reach the PrintMgr dispatch path.

Constructors and their MMIO are never executed. This does not prove boot order, successful RTOS creation, indirect registrations or queue delivery on hardware.
