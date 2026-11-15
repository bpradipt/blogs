| Layer | What it gives you | Used in the series as |
|---|---|---|
| **Migen** | a hardware description language embedded in Python: signals, logic, registers, memories | the Root of Trust block |
| **LiteX cores** | ready-made hardware: CPU wrappers (VexRiscv and others), Wishbone and CSR buses, UART, timer, RAM and ROM | the CPU, buses, memories, UART |
| **SoC builder** | `SoCCore` assembles cores into an SoC with a memory map; `Builder` generates everything | `make_soc()` in each lab |
| **Build backends** | Verilator for simulation; Vivado, Yosys/nextpnr and others for FPGAs | Verilator only |
| **Software** | a BIOS, `libbase` (drivers), picolibc, CPU start-up code, linker scripts, generated headers | the boot ROM and firmware build |
