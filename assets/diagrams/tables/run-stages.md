| Stage | Printed by | Example | What happens |
|---|---|---|---|
| 1. Assembly | Python (`SoCCore`, `Builder`) | `INFO:SoC:CPU vexriscv setting reset address to 0x00000000.` | LiteX assembles the SoC and writes `sim.v`, the `.init` files and the headers |
| 2. Compile | `make`, Verilator, C compiler | `verilator -Wno-fatal -O3 --cc …` (or `[build] RTL unchanged…`) | `sim.v` becomes `obj_dir/Vsim`; each simulation module becomes a `.so` |
| 3. Starting of the simulator | `Vsim` and its modules | `[gmii_ethernet] loaded`, `[clocker] sys_clk: freq_hz=1000000` | modules load, `sim_config.js` picks the ones to attach |
| 4. Power on  | simulated SoC | `[rom] reset vector reached` | memories fill from `.init` files, reset releases, the CPU fetches from `0x0` |
