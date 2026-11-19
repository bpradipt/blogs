| AA responsibility | Lab | Why there |
|---|---|---|
| HTTP, cookies and JSON for /auth, /attest, /resource | kbs_host.py, on the host | transport only, nothing secret |
| create the TEE key pair | firmware.c | the private key must stay in the TEE |
| compute REPORT_DATA from the nonce and the TEE key | firmware.c | a host that supplied the hash could swap in its own key |
| produce evidence (the attester's job) | firmware.c and bootrom.c | the Alias key signs; the ROM's DICE chain vouches for it |
| decrypt the JWE | firmware.c | only the TEE may see the secret |
