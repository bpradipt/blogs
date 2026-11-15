| Class | Hardware side | CPU side | In the series |
|---|---|---|---|
| `CSRStatus(n)` | drives `.status` | reads | `fuse_digest`, `locked`, `uds` |
| `CSRStorage(n)` | reads `.storage`; `.re` pulses for one cycle on each CPU write | writes, reads back | `lock`, `meas_stage` |
| `CSR(n)` | sees `.r` and `.re` (write strobe), drives `.w` | writes and reads, no storage | `sim_finish` |
