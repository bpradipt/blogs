| Region | Base | Size | What it is |
|---|---|---|---|
| `rom` | `0x00000000` | 32 KiB | Boot ROM. CPU starts here. Read-only. |
| `sram` | `0x10000000` | 8 KiB | On-chip scratch RAM. Stack for the ROM. |
| `main_ram` | `0x40000000` | 64 KiB | Stands in for external flash/DRAM. Firmware here. |
| `csr` | `0xF0000000` | 64 KiB | All peripheral registers. |
