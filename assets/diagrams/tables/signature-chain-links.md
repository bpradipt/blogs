| Link | Question | What breaks it |
|---|---|---|
| Manufacturer → DeviceID | Is this a genuine chip? | A simulator or a clone that invents its own keys |
| DeviceID → certificate | Did this chip's ROM issue this certificate? | Firmware that writes its own certificate |
| certificate → measurement | Does the chip run the vendor's firmware? | Modified firmware: the ROM certifies its real measurement |
| Alias key → report | Did the certified firmware produce this answer, for this request? | Replaying an old certificate, or answering from a different firmware |
