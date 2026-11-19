| Property | The question it answers | AMD SEV-SNP | Intel TDX | Arm CCA |
|---|---|---|---|---|
| **Isolation** | Who may access this page of memory? | Reverse Map Table (RMP) | TDX module in SEAM mode | Granule Protection Table (GPT) |
| **Memory encryption** | What does a bus probe or a DMA engine see? | AES engine, one key per VM | MKTME, one key per TD | Memory Encryption Contexts (MEC) |
| **Attestation** | How does a remote party know what runs? | Report signed by the VCEK key | Quote from the quoting enclave | Token from the RMM and the platform RoT |
