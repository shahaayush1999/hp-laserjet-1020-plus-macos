# Original USB GET_PORT_STATUS boundary

28 original-byte cases agree between the interpreter and QEMU. Zero completed control transfers or page lifecycles.

Original GET_PORT_STATUS dispatch prepares a zero byte at stack+80, a response pointer and length one, independent of supplied unrelated status RAM. Unsupported request pairs select stall intent. Both stop before their control/peripheral handlers.

The two zero-definition instructions are isolated by explicit PC cuts; surrounding initialization, setup admission, event waiting and all hardware are omitted. No claim of a continuous boot or USB lifecycle is made. Numeric status/global fixtures are not physical calibration. Noncanonical field acceptance describes original response preparation only, not recommended policy or bytes actually transferred. The replacement should retain explicit unknown status until a real sensor/status adapter exists.
