| Check in verifier.py | Where it lives in Trustee |
|---|---|
| 1. the DeviceID key belongs to a genuine chip | AS policy rule, against a value in the RVPS |
| 2. the chip's ROM signed the Alias certificate | the TEE's verifier |
| 3. the certified measurement is the vendor's firmware | AS policy rule, against a reference value in the RVPS |
| 4. the report carries our nonce and the Alias key signed it | the TEE's verifier, plus KBS's nonce handling |
| release the secret, encrypted to the firmware's key | KBS resource policy, and a JWE encrypted to the TEE's public key |
