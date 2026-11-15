| Way | Example | Good for |
|---|---|---|
| **The CLI tools** | `litex_sim --cpu-type=vexriscv` | trying LiteX: a ready-made SoC with a BIOS prompt, configured by flags |
| **A litex-boards target** | `python3 -m litex_boards.targets.digilent_arty --build --load` | running a standard SoC on a real FPGA board |
| **Your own SoC script** | `rot_soc.py`, `cc_soc.py`, `trustee_soc.py`, `tls_soc.py` | custom hardware, custom boot flow |
