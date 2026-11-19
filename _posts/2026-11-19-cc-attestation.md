---
title: "Proving What Runs: DICE, Attestation and Confidential Computing on a Simulated SoC"
tags: [soc, security, confidential-computing, attestation]
---

You've already read [Foundations of Trust in System-on-Chip (SoC)]({{ '/2026-11-17/soc-root-of-trust/' | relative_url }}) (the first post in the series), and you know what a boot ROM is, what OTP fuses and a lock bit do. You've heard of confidential computing and attestation and want a mental model you can check on real hardware. We'll take the lab SoC from the first post and extend it so it can prove to a remote server what firmware it's running and receive a secret if the answer is correct. This is the essence of remote attestation in confidential computing: the hardware generates cryptographic evidence about the running firmware, which a remote verifier can trust to decide whether to release secrets or services. By tying the ability to prove its state to secure hardware mechanisms, the SoC demonstrates the same principles that underpin confidential computing systems.

---

## Where the first post stopped

The lab in the first post concluded with a measured boot. The boot ROM hashed the firmware and then froze that hash in a register which the firmware itself couldn't change. The bad firmware would boot, but its measurement would be obvious and the post would say "a remote verifier would refuse".

That sentence completely skipped the hard bit. The verifier is sitting somewhere else (on a remote server). It can't read the chip's registers at all. All it sees are the bytes that get transmitted over the network and the firmware it's trying to verify is the one that's transmitting those bytes. A malicious firmware could read the frozen register and then transmit whatever value it wanted.

So the verifier needs more than a hash. It needs a statement about the firmware signed with a key that:

1. only this chip holds, and
2. the firmware can't be used to sign false statements.

This post builds that key (the statement and the verifier). In the process, it explains what confidential computing is, since confidential computing is based on the same mechanism.

---

## A quick primer on Confidential computing

In a normal cloud server, you trust the people who run it. They can read your VM's memory via the hypervisor and their admin staff can dump it. Confidential computing removes that trust completely. The host OS, hypervisor, and cloud operator are now the attacker. The tenant trusts only the CPU's hardware and a small amount of firmware and nothing else on the machine.

Three hardware features make that possible:

![Confidential computing hardware features across AMD SEV-SNP, Intel TDX, and Arm CCA]({{ '/assets/diagrams/cc-properties.png' | relative_url }})

The diagram shows where those pieces sit in an SoC that supports confidential computing:

![Block diagram of an SoC with confidential computing: CPU cores running an untrusted hypervisor and a confidential VM, an interconnect, an access check and a memory encryption engine in front of the memory controller, and a security processor with its own boot ROM, fuses and key engine. The security processor installs per-VM keys, manages the page-ownership table and sends signed reports to a remote verifier. DRAM off-chip holds ciphertext.]({{ '/assets/diagrams/cc-soc-architecture.png' | relative_url }})

Green blocks are part of the tenant's trusted computing base, blue blocks are the workloads that they protect, and red blocks are the ones that may be hostile. That's the design:

* **Every memory access goes through the access check and encryption engine.** The hypervisor still does VM scheduling and memory management but can't read or write the VM's pages. If it reads them, it sees only ciphertext.
* **The security processor is the root of everything.** It boots first from its own ROM, from its own fuses. It installs the per-VM keys, and it signs the attestation report. In AMD's design, that's the AMD Secure Processor (a separate Arm core on the CPU die). The Arm CCA reference designs also have the root of trust on their own core.

Isolation and encryption keep the hypervisor out. A tenant who uploads a disk key to a cloud VM must prove the VM is a confidential VM on real hardware running the correct code before they'll send the key. That's attestation, and the rest of this post is about it. The lab covers the attestation bit. It briefly mentions isolation and encryption at the end.

For an in-depth tutorial on CC, you can refer to the following material: https://cc-book.github.io/cc-book/

---

## Identity: a key that depends on the firmware

Attestation needs a signing key with two properties:

1. **It belongs to this chip.** A verifier must be able to tell a genuine chip from a simulator that’s just making up the answers.
2. **It changes when the firmware changes.** Otherwise, an malicious firmware could sign “I am the official firmware” with the same key the official firmware uses.

The Trusted Computing Group's **DICE** (Device Identifier Composition Engine) design gets both properties from three steps:

1. **UDS.** The Unique Device Secret is a random secret written into the chip's fuses during manufacturing. Nothing external to the chip ever sees it. In our accompanying lab, a script runs the fab and writes it.
2. **CDI.** The Compound Device Identifier, which is calculated at every boot. The ROM measures the firmware and then combines that measurement with the UDS to produce the CDI: `CDI = HMAC(UDS, measurement)`. 
3. **Keys from the CDI.** The ROM turns the CDI into a signing key pair, the *Alias* key, and hands it to the firmware.

Change one byte of the firmware and the measurement changes. The CDI changes with it and so does the Alias key, all without the ROM having any knowledge of what's going on.

The ROM also derives a second key from the UDS alone, the **DeviceID** key. It stays the same on every boot and acts as the chip’s long-term identity. The manufacturer records the DeviceID public key at the fab and publishes it, so verifiers can recognise genuine chips. The DeviceID private key never leaves the ROM’s run. The ROM uses it once to sign a certificate for the Alias key, and then wipes it.

![DICE key derivation: UDS, firmware measurement, CDI, DeviceID and Alias keys, and the Alias certificate]({{ '/assets/diagrams/dice-keys.png' | relative_url }})

The green items exist only inside the ROM's run. The orange items are what the ROM hands to the firmware: the Alias key pair and its certificate. The firmware never sees the UDS, the CDI or the DeviceID private key.

Real chips follow the same pattern with more layers. Each boot stage measures the next one and derives the next CDI, so a chain of keys covers ROM, firmware, bootloader and kernel. Caliptra, an open-source root of trust for datacenter SoCs, implements DICE in its ROM. AMD's VCEK follows the same idea. AMD derives it from a chip-unique secret and the version numbers of the security processor's firmware, so the key changes when that firmware changes.

---

## A chain of signatures

The verifier now receives three things and can check them in order:

![The chain of signatures: manufacturer's list, DeviceID key, Alias certificate, report]({{ '/assets/diagrams/signature-chain.png' | relative_url }})

Each link answers one question:

![Each link in the chain of signatures, the question it answers, and what breaks it]({{ '/assets/diagrams/signature-chain-links.png' | relative_url }})

The **nonce** in the report is important. The verifier picks a fresh random number for each attestation. Without it, an attacker could record the evidence from one official boot and replay it forever.

The report also carries a **key-release public key**, an X25519 key the firmware creates for this attestation. When the verifier approves, it encrypts the secret to that key. Only the firmware that signed the report holds the matching private key, so the host that relays the messages can't read the secret.

The TPM world uses the same structure under different names: an *Endorsement Key* certified by the manufacturer plays the DeviceID role, and an *Attestation Key* signs quotes over measurements and a nonce.

---

## The attestation protocol

Following is a high level overview of the attestation protocol.

![The attestation protocol: firmware, host, and verifier exchanging nonce, evidence, and the released secret]({{ '/assets/diagrams/attestation-protocol.png' | relative_url }})

Every message passes through the host, and the host may be hostile. The design doesn't need to trust it:

- It can't forge a certificate, because it has no DeviceID private key.
- It can't sign a fresh report, because it has no Alias private key.
- It can't read the secret, because it has no key-release private key.

It can drop messages and stop the attestation. Confidential computing accepts that risk. A hostile host can create a denial of service, but it can't steal the secret or fake the evidence.

In production, this pattern shows up as a key broker. In the Confidential Containers project, for example, a confidential VM sends its attestation evidence to a service called Trustee, which checks it against reference values and then releases keys to the VM.

---

## Hands-on: an SoC that attests

### What changed from the first lab

The lab lives in [`cc-attest-lab/`](https://github.com/bpradipt/soc/tree/main/cc-attest-lab), a separate copy of the first lab:

```
cc-attest-lab/
├── Containerfile     toolchain: LiteX 2026.08, Verilator, RISC-V GCC, Python cryptography
├── cc_soc.py         the SoC, the fab and vendor steps, and the host relay
├── verifier.py       the remote verifier: four checks, then key release
└── sw/
    ├── bootrom.c     DICE boot ROM
    ├── firmware.c    firmware that attests and receives a secret
    ├── handoff.h     what the ROM leaves in RAM for the firmware
    ├── sha256.c      the measurement hash, unchanged from the first lab
    └── monocypher/   Monocypher 4.0.2: Ed25519, X25519, HMAC, HKDF (BSD-2 or CC0)
```

The lab SoC is the first post's chip with a new ROM and a new fuse layout. The same VexRiscv CPU, interconnect and memory map carry over:

![Block diagram of the lab SoC: a VexRiscv CPU on a Wishbone interconnect with a 64 KiB DICE boot ROM, 16 KiB SRAM, 64 KiB main RAM holding the firmware partition and the DICE handoff, and a CSR space with the Root of Trust (UDS fuses and lock), a UART and a timer. Off-chip, an untrusted host relays messages between the UART and the verifier. A dashed box marks the access check and memory encryption the lab leaves out.]({{ '/assets/diagrams/cc-lab-soc.png' | relative_url }})

Compare it with the generic SoC picture in the beginning of the post. In the lab, the main CPU does the security processor's job by running ROM code, as in the first post. The dashed box marks where a real CC chip puts its access check and encryption engine.

The hardware changes are small:

![What changed from the first lab to this one]({{ '/assets/diagrams/lab-changes.png' | relative_url }})

The RoT block shrinks. The first lab needed a measurement register so the firmware couldn't change the hash. DICE puts the measurement into the Alias certificate instead, signed with a key the firmware never sees, so this lab drops the register.

```python
class RootOfTrust(LiteXModule):
    def __init__(self, uds_words):
        self.uds    = CSRStatus(256, description="Unique Device Secret (OTP). Reads 0 once locked.")
        self.lock   = CSRStorage(1)
        self.locked = CSRStatus(1)
        ...
        self.sync += If(self.lock.re & self.lock.storage[0], locked.eq(1))
        self.comb += [
            self.locked.status.eq(locked),
            self.uds.status.eq(Mux(locked, 0, Cat(*reversed([port.dat_r for port in ports])))),
        ]
```

The same `Mux(locked, 0, …)` from the first post hides the UDS after the lock. Everything else happens in software, in the ROM.

The crypto comes from [Monocypher](https://monocypher.org), a small C library: Ed25519 for signatures, X25519 for the key exchange, HMAC and HKDF with SHA-512 for key derivation. On the simulated CPU, generating one Ed25519 key pair takes about 1.6 million cycles, and one signature about 1.7 million. A full boot and attestation takes around 15 seconds of wall time.

`cc_soc.py` plays four roles before the chip powers on, and prints a line for each:

- **fab:** gives the chip a random UDS once (`build/fab/uds.bin`) and computes the DeviceID public key the way the ROM will. Real chips create the UDS on the die, for example with a Physical Unclonable Function [PUC](https://en.wikipedia.org/wiki/Physical_unclonable_function), and only the public key ever leaves.
- **vendor:** publishes the reference measurement, the SHA-256 of the official 32 KiB firmware partition.
- **attacker:** with `--tamper`, patches the firmware in RAM before boot.
- **host:** runs the simulator and relays messages. Lines that start with `[` go to your terminal. Protocol lines go to the verifier. With `--replay`, the host turns hostile and rewrites the evidence.

### Setup

Same as the first lab, with a new image name:

```bash
cd cc-attest-lab
podman build -t cc-attest-lab .
alias lab='podman run --rm -it -v "$PWD":/lab:Z -w /lab cc-attest-lab'
```

The primary change from the first lab is the additon of the Python `cryptography` package to the lab's tool list.

Your keys and nonces will differ from the ones below: your chip gets its own random UDS, and the verifier picks a new nonce on every run. Delete `build/` to make a new chip.

### The DICE boot ROM

The core of `sw/bootrom.c`, after measuring the firmware:

```c
/* 2. Copy the UDS out of the fuses, then lock: from here on the fuses read as zero. */
for (int i = 0; i < 8; i++)
	words[i] = csr_read_simple(CSR_ROT_UDS_ADDR + 4 * i);
words_to_bytes(words, uds, 8);
rot_lock_write(1);

/* 3. DeviceID key: depends only on the UDS, so it is the same every boot. */
crypto_sha512_hkdf(seed, 32, uds, 32, NULL, 0, (const uint8_t *)"DeviceID", 8);
crypto_ed25519_key_pair(device_priv, h->device_id_pub, seed);

/* 4. CDI: depends on the UDS and on the measurement. */
crypto_sha512_hmac(cdi, uds, 32, h->cert.measurement, 32);

/* 5. Alias key: derived from the CDI, so it changes whenever the firmware changes. */
crypto_sha512_hkdf(seed, 32, cdi, 64, NULL, 0, (const uint8_t *)"Alias", 5);
crypto_ed25519_key_pair(h->alias_priv, h->cert.alias_pub, seed);

/* 6. Certify: "this Alias key belongs to firmware with this measurement", signed by DeviceID. */
crypto_ed25519_sign(h->cert.signature, device_priv, tbs, sizeof tbs);
```

Then it wipes `uds`, `cdi`, `seed` and `device_priv`, and jumps to the firmware.

Notice the order in step 2. The ROM copies the UDS and locks the RoT before any key derivation, so the fuses stay readable for a few instructions only. The secret then exists in one place, the ROM's stack, until the wipe.

The ROM leaves its results in RAM above the firmware partition, in the layout from `sw/handoff.h`:

```c
struct alias_cert {
	uint8_t alias_pub[32];
	uint8_t measurement[32];   /* SHA-256 of the firmware partition */
	uint8_t signature[64];     /* Ed25519 by DeviceID over alias_pub || measurement */
};

struct dice_handoff {
	uint32_t magic;
	uint8_t  device_id_pub[32];  /* the chip's long-term identity */
	uint8_t  alias_priv[64];     /* the firmware's own signing key */
	struct alias_cert cert;
};
```

The firmware gets the Alias private key, the certificate and the DeviceID *public* key. The struct has no field for anything the firmware must not know.

### The verifier

`verifier.py` trusts two published facts: the manufacturer's list of DeviceID keys and the vendor's reference measurement. Its four checks map one-to-one onto the chain in §4:

```python
checks = [
    (device_id.hex() in endorsed,
     "the DeviceID key belongs to a genuine chip (manufacturer's list)"),
    (signed_by(device_id, cert_sig, alias_pub + measurement),
     "that chip's ROM signed the Alias certificate"),
    (measurement.hex() == reference,
     f"the certified measurement {measurement.hex()[:16]}... is the vendor's firmware"),
    (report_nonce == nonce and signed_by(alias_pub, report_sig, report),
     "the report carries our nonce and is signed by the certified Alias key"),
]
```

If all four pass, the verifier generates its own X25519 key, computes a shared secret with the key from the report, and uses it to encrypt the secret. The firmware repeats the computation on its side and decrypts.

### Run 1: official firmware, secret released

```bash
lab ./cc_soc.py
```

```
[fab] chip provisioned, DeviceID public key a6e2bcd02f28b90165a2ba42b64b448f9a5a8a5bce98a717ec0a77a466b48329
[vendor] reference measurement f31e21ed845a7cf24cf213aeaa61c50a3cb2faa5b2b2f314a581fa71e9203a67

[rom] reset vector reached, DICE boot ROM running
[rom] firmware measurement : f31e21ed845a7cf24cf213aeaa61c50a3cb2faa5b2b2f314a581fa71e9203a67
[rom] UDS copied, RoT locked
[rom] DeviceID public key  : a6e2bcd02f28b90165a2ba42b64b448f9a5a8a5bce98a717ec0a77a466b48329
[rom] Alias public key     : e037da5c35868ffc0a864ec2ffb21cebdd537eb608b46eb038f16acc02f644b5
[rom] Alias certificate signed with the DeviceID key
[rom] UDS, CDI and DeviceID private key wiped, jumping to firmware @ 0x40000000
[fw] hello from the official firmware
[fw] the ROM left me an Alias key and its certificate
[verifier] chip said HELLO, sent nonce 3d196ab244d138e6...
[verifier] got evidence, appraising:
[verifier]   ok   the DeviceID key belongs to a genuine chip (manufacturer's list)
[verifier]   ok   that chip's ROM signed the Alias certificate
[verifier]   ok   the certified measurement f31e21ed845a7cf2... is the vendor's firmware
[verifier]   ok   the report carries our nonce and is signed by the certified Alias key
[verifier] secret released, encrypted to the key in the report
[fw] unwrapped the secret: "tenant-42 disk key: open sesame!"
```

Compare the `[fab]` line with the ROM's DeviceID line. Python computed the key at the fab, and the C code in the ROM computed it again from the fuses. Both give `a6e2bc…`. The verifier never learns the UDS. It only checks that `a6e2bc…` appears on the manufacturer's list.

### Run 2: modified firmware, secret refused

```bash
lab ./cc_soc.py --tamper
```

```
[attacker] patched firmware, it now measures f9958c81a0959a87a0eaa02c525d4cc60b08c0ef016f82055503547685ecdc8c
[build] RTL unchanged, reusing the compiled simulator

[rom] reset vector reached, DICE boot ROM running
[rom] firmware measurement : f9958c81a0959a87a0eaa02c525d4cc60b08c0ef016f82055503547685ecdc8c
[rom] UDS copied, RoT locked
[rom] DeviceID public key  : a6e2bcd02f28b90165a2ba42b64b448f9a5a8a5bce98a717ec0a77a466b48329
[rom] Alias public key     : 6a4dcc3b2582d5e0002667a024a51716b7405b0eaf389f085b9dcf3a579a9f5e
[rom] Alias certificate signed with the DeviceID key
[rom] UDS, CDI and DeviceID private key wiped, jumping to firmware @ 0x40000000
[fw] hello from the EVIL  firmware!!!
[fw] the ROM left me an Alias key and its certificate
[verifier] chip said HELLO, sent nonce 0105db8a6ddf768f...
[verifier] got evidence, appraising:
[verifier]   ok   the DeviceID key belongs to a genuine chip (manufacturer's list)
[verifier]   ok   that chip's ROM signed the Alias certificate
[verifier]   FAIL the certified measurement f9958c81a0959a87... is the vendor's firmware
[verifier] secret NOT released
[fw] verifier said: DENIED evidence failed appraisal
```

Look at the two key lines from the ROM:

- **DeviceID** stays `a6e2bc…`. Same chip, same UDS.
- **Alias** changes from `e037da…` to `6a4dcc…`. The CDI mixes in the measurement, so new firmware gets a new key.

The malicious firmware runs and talks to the verifier, and it even tells the truth: it sends the certificate the ROM gave it. The ROM put the real measurement into that certificate and signed it, so check 3 fails. The malicious firmware can't produce a certificate with the official measurement, because that needs the DeviceID private key, which the ROM wiped before the firmware started.

### Run 3: a hostile host replays an official certificate

The malicious firmware can't forge a certificate, but the host can copy one. Run 1 sent a valid certificate for the official firmware across the host, and the host recorded it. Now the host swaps that recording into the malicious firmware's evidence:

```bash
lab ./cc_soc.py --tamper --replay
```

```
[fw] hello from the EVIL  firmware!!!
[fw] the ROM left me an Alias key and its certificate
[verifier] chip said HELLO, sent nonce b14a52cc22903bad...
[host] swapped in the Alias certificate recorded from an official boot
[verifier] got evidence, appraising:
[verifier]   ok   the DeviceID key belongs to a genuine chip (manufacturer's list)
[verifier]   ok   that chip's ROM signed the Alias certificate
[verifier]   ok   the certified measurement f31e21ed845a7cf2... is the vendor's firmware
[verifier]   FAIL the report carries our nonce and is signed by the certified Alias key
[verifier] secret NOT released
[fw] verifier said: DENIED evidence failed appraisal
```

Three checks pass: the replayed certificate is genuine. Check 4 catches the swap. The certificate vouches for Alias key `e037da…`, but the malicious firmware signed the fresh nonce with its own key, `6a4dcc…`. To pass check 4, the attacker needs the official firmware's Alias private key, and only the ROM can derive it, from a UDS the attacker can't read.

So a verifier needs two things: the certificate, and a fresh signature from the key it certifies.

---

## What this lab leaves out

The lab covers the attestation chain only. Real confidential computing includes additional capabilities which the lab skips:

- **Isolation and memory encryption.** The lab's firmware keeps its Alias private key in ordinary RAM. A real host could read it there, sign anything, and break the whole scheme. A RISC-V version of isolation uses PMP (Physical Memory Protection) registers, which LiteX's `secure` VexRiscv variant supports. That's a good topic for a follow-on lab.
- **Real certificate formats.** The lab uses a 128-byte custom certificate. Real chips use X.509 certificates and token formats such as EAT, and chain the DeviceID key up to a manufacturer CA, which verifiers fetch from a service like AMD's Key Distribution Service.
- **Firmware versions and rollback.** A verifier should refuse old firmware with known bugs even when the vendor signed it. AMD mixes firmware version numbers into the VCEK for this. The lab compares one exact hash.
- **More DICE layers.** The lab's ROM acts as the DICE engine and as the first layer at once. Real chips derive a new CDI at every boot stage.
- **Randomness.** The lab SoC has no random number generator, so the firmware derives its key-release key from the Alias key and the nonce. Real TEEs use a hardware RNG.
- **Real encryption for key release.** The lab XORs the secret with a hash of the X25519 shared secret. Production systems use an authenticated scheme such as HPKE.
- **Revocation.** If a chip's keys leak, the manufacturer must be able to withdraw its endorsement. The lab's list never changes.

---

## Exercises

1. **Forget to wipe the DeviceID key.** Comment out `crypto_wipe(device_priv, …)` in `bootrom.c` and copy `device_priv` into the handoff struct. Then make the malicious firmware sign its own Alias certificate that claims the official measurement. Which check still catches it?
2. **Make a new chip.** Change `cc_soc.py` so the verifier reads a fixed manufacturer list from a file, then delete `build/fab/uds.bin`. Which check fails, and why?
3. **Add a version number.** Put a firmware version in the image header, mix it into the CDI, and make the verifier refuse versions below a minimum. Compare your design with AMD's VCEK.
4. **Bind a session key.** Real reports often carry the hash of a TLS public key, so the verifier knows its TLS connection ends inside the attested firmware. Replace the X25519 key in the report with a hash of a key the firmware would use for TLS.
5. **Move the Alias key out of reach.** Switch the CPU to the `secure` VexRiscv variant and use PMP to stop user-mode code from reading the handoff area. This is the first step from attestation toward confidential computing.

