| Way | How | Used by |
|---|---|---|
| ROM contents | `integrated_rom_init=` at build time | the labs' boot ROMs |
| RAM contents | `integrated_main_ram_init=` at build time (simulation) | the labs' firmware: "a loader already put it in RAM" |
| BIOS serial boot | `litex_term /dev/ttyUSB0 --kernel=app.bin` uploads to `0x4000_0000` and jumps | the normal way on an FPGA board |
| BIOS from flash, SD card or Ethernet | BIOS boot commands | Linux and other larger systems |
