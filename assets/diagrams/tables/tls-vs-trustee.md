| Step | trustee-lab (third post) | tls-lab (this post) |
|---|---|---|
| TCP connection to Trustee | host | host |
| TLS | none (plain HTTP) | **firmware**, with the KBS key pinned |
| HTTP, cookies and JSON for /auth, /attest, /resource | host (kbs_host.py) | **firmware** |
| TEE key, REPORT_DATA, evidence | firmware | firmware |
| JWE decryption | firmware | firmware |
