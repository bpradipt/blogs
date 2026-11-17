| Property | Why | How silicon gets it |
|---|---|---|
| **Immutable** | If it can be modified, it can be modified by an attacker. | Mask ROM: code fixed in the metal layers at fab. |
| **Minimal** | reduced blast radius. | ROMs are typically a few KiB to a few tens of KiB. |
| **Holds a reference** | It must know what "good" looks like. | One-time-programmable **fuses** (OTP), burned at manufacturing. |
| **Can protect itself** | less-trusted code must not reach the secrets. | **Lock** bits: write-once registers that close a door until next reset. |
| **Can report** | Others (a remote server) need evidence of what booted. | **Measurement** registers that later code can read but not forge. |
