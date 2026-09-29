# TinyUSB protocol execution

Locally patched TinyUSB generic device/EP0 core plus the existing class/document component and a synthetic event/DCD fixture. Actual descriptor parsing, control packetization and application-driver dispatch execute; all controller and cancellation observations are supplied.

160 host scenarios; 160 target scenarios. 0 routing/result observations and 0 target wire mismatches remain explicit limitations.

This is a synthetic protocol fixture, not a production controller adapter. Packet captures represent submissions, including cancelled transfers, not USB wire delivery. Unchanged upstream limitations remain in the separate baseline. No controller port, bulk data, physical reset, sensor status, boot or printing is established.
