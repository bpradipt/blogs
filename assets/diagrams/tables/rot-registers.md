| Offset | Register | Width | CPU view | Meaning |
|---|---|---|---|---|
| `0x00` | `fuse_digest` | 256 | RO | SHA-256 of the firmware this chip was provisioned for. Reads 0 once locked. |
| `0x20` | `fuse_len` | 32 | RO | Length of that firmware in bytes. Reads 0 once locked. |
| `0x24` | `fuse_enforce` | 1 | RO | Policy fuse: 1 = secure boot (halt on mismatch), 0 = measured boot only. |
| `0x28` | `meas_stage` | 256 | RW | Where the ROM writes the digest it computed. |
| `0x48` | `measurement` | 256 | RO | Snapshot of meas_stage taken at lock time. Frozen until reset. |
| `0x68` | `lock` | 1 | RW | Writing 1 sets locked. Writing 0 later does nothing to locked. |
| `0x6C` | `locked` | 1 | RO | The flip-flop itself: reads 1 from the first lock write until reset. |
