# Verdict markers — the vocabulary of the tooling

The pages emit marker lines to the screen, to the host server
(`/log/`, captured in `runs/last-verdicts.txt`), and evidence dumps
(`/dump/` → `runs/dumps/*.bin`). Markers are the product's
vocabulary — stable, functional, and self-describing. This glossary
tells you what each one *proves*.

## Session

| Marker | Meaning |
|---|---|
| `SESSION-BOOT` (printed as `1-BOOT …`) | a fresh exploit session started (the server rotates its session files on this line) |

## Stage 1 — SSV entry (arbitrary R/W)

| Marker | Meaning |
|---|---|
| `GENUINE-U8-RW-PASS` | the fake `Uint8Array` cell works: genuine R/W over a live cell, carrier vector restored |
| `ARBITRARY-READ-PASS` / `ARBITRARY-WRITE-PASS` | read/write proofs on a live target (a5→5a→a5 restored) |
| `ADDROF-*` (`RETURNED`, `POINTERS`, `CARRIER-DONE`…) | the addrof primitive captured host/target pointers (repeated, distinct, plausible) |
| `SSV-BUILD` / `SSV-STORED` / `SSV-RETURNED-CLEARED` | the serialized graph built, stored via `history.replaceState`, and reloaded with the duplicate index cleared |
| `HEADER-MISMATCH` / `NORMAL-CLONE-MISS` / `LOAD-THREW` | benign placement misses — reload and retry (the auto-ladder does it for you) |

## Stage 2 — base leak

| Marker | Meaning |
|---|---|
| `BASE-PAIR-GATE-PASS` | the expm1/parseInt pair matched the fixed delta `0x24B0C20` in-range, same-region, aligned |
| `BASE-LOCKED` | the exact WebKit module base is derived and dumped (`webkit=0x…`) |
| `BASE-PAIR-FAIL` / `EXE-NOT-FOUND` | the pair did not close — clean refusal, nothing read |

## Stage 3 — ROP

| Marker | Meaning |
|---|---|
| `GADGET-GATE-PASS n/15 [-repaired=…]` | all 15 gadgets verified byte-by-byte at runtime (repairs are re-scans around the stale RVA, dumped for audit) |
| `FCALL-BUFADDR-SELFTEST` | the addrof→backing-store walk (`0x10/0x10`) reads back the planted magic |
| `FCALL-STUB-EXACT` | the getpid stub found at the measured offset, signature-checked byte-exact |

## Stage 4 — syscalls

| Marker | Meaning |
|---|---|
| `FCALL-SERIES-ARMED` / `FCALL-SERIES-DISARMED` | the one arm→disarm cycle of the session (mf RESTORED / pivot RESTORED on the way out) |
| `SYSCALL-PASS` | **the proof**: getpid(20) executed through the byte-verified stub, sane return value in the ROP frame |
| `SYSCALL-FAIL` | the cycle ran but the return was not a sane pid — dump and inspect |

## The aio KEX sequence (`kex-aio.html`)

| Marker | Meaning |
|---|---|
| `AIO-STUB-EXACT` (x~20) | every stub of the sequence resolved and byte-verified before a single call |
| `AIO-PIN-SET` … `AIO-PIN-RESTORED` | the thread pinned to one core (UMA bucket discipline), always restored in the finally |
| `AIO-SCRATCH-HINT` / `AIO-SCRATCH-OK` | the scratch page obtained at an exact hinted address, confirmed **by the mmap return value**, then reread |
| `AIO-P1-*` … `AIO-P5-*` | the scene's exact sequence: free (P1), submit (P2), wait (P3), spray (P4), the cancel walk (P5) |
| `AIO-P5-PROOF` | the sink counters after the walk (dum/n0/scratch/whoHasF) — `-WALK-ATTESTED` if the reclaim landed |
| **`AIO-WALK-PROVEN`** | the UAF is alive and walked — the kernel exploit works (this is the success verdict a future firmware may give you) |
| **`AIO-LIVE-NO-RECLAIM`** | the sequence ran (submit ok, hundreds of syscalls) but **no waiter was ever created** — the wait is gated; the current deterministic 14.00 verdict |
| `AIO-WAIT-CALIB` | the two side-effect-free probes separating EPERM-gate from EINVAL/before-count failure |

## The live workshop (`console.html` + `bridge.py`)

| Marker | Meaning |
|---|---|
| `ERRNO-GADGET-OK` | the bare `syscall; ret` gadget found at the stub-window tail — positive errno reads available (`sysc raw=1`) |
| `BRIDGE-OPEN` | the WebSocket bridge to the PC is up |
| `WORKSHOP-READY` | the armed live console is taking commands (ping/stat/walk/read/sysc/eval/selftest), heartbeat every 5 s |
| `EVF-REGISTRY-OPEN/CLOSED`, `PRISON-*` | verdicts of the named-IPC and FS-map probes driven over the bridge |
