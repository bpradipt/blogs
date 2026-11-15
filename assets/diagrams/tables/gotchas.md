| Symptom | Cause | Fix used in the labs |
|---|---|---|
| Changes to the hardware don't take effect | `build(run=False)` skips compiling the simulator | call the compile step yourself, then run `obj_dir/Vsim` |
| Every run recompiles the simulator | LiteX re-runs Verilator on every build, and `sim.v` contains timestamps | hash `sim.v` without comments; skip the compile when the hash matches |
| Memory or fuse contents need a rebuild | values written as constants in the logic | put them in a `Memory`; LiteX loads `.init` files at start-up |
| Building without the timer fails | `libbase` uses `timer0` | keep the timer |
| Pass 1 builds a BIOS you don't want | an empty ROM means "use the BIOS" | `soc.integrated_rom_initialized = True` |
| A second UART can't reach the simulator | `serial2console` and `serial2tcp` only accept pads named `serial` | one UART, with the host telling log lines from protocol lines |
| Input sent to the chip gets corrupted | the console bridge buffers 2 KiB of input | the chip asks for each chunk (`TCP MORE`) |
| The first byte sent at boot disappears | `uart_init()` clears a pending byte | the firmware says `HELLO` before the host sends |
| FST waveforms won't open | Verilator and GTKWave versions disagree on FST | record VCD instead |
