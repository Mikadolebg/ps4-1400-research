# Open leads — ranked, with the next probe for each

Status legend: **OPEN** (measured alive somewhere, 14.00 unknown),
**UNTESTED** (never probed anywhere, per our knowledge), each with the
tool in this repo that takes you there. Read `06-negative-results.md`
first — several intuitive leads there are closed.

## 1. `/dev/dipsw` ioctl window — UNTESTED, highest value-per-unknown

**What is proven already:** `open("/dev/dipsw")` **succeeds** from the
browser (an fd comes back; reads fail — ioctl-only device). The 13.52
kernel's ioctl entry check is decoded: it proceeds when
`cred+0x60` bit 62 == 0, i.e. **non-system processes — the browser
included**. Command window `0x80028800..0x80108804`.

**Why it is first:** it is the only measured-open device door for the
browser class, and dipsw (dip-switch emulation) is a privileged
control surface. Nothing about its ioctls has ever been published.

**Next probe** (workshop armed, one command per session):
`{"t":"sysc","num":54,"args":[fd,0x80028800,0,0,0],"raw":true}` —
ioctl via the stub with errno readout, sweeping the documented command
window one command at a time (DANGER list rules apply: never blind-loop).

## 2. The unauthenticated IPC registry from a non-gated process — OPEN (F2)

**What is proven:** the kernel-side global registry of named evf/osem
objects has **no authentication** (13.52 disassembly); the browser is
blocked at *syscall entry*, not at the registry. Any process that is
not webkit-class can open/operate system IPC objects by name. The
browser can also **see** the relevant namespaces (`/system_tmp`).

**Why it matters:** a confused-deputy path (a system daemon doing
IPC-by-name on the browser's behalf) becomes an immediate primitive
the day any such deputy is found; also the ABI decode gives
refcount++ (+0x50) and id-return-in-rax — a clean object-grab
primitive from the right context.

**Next probe:** map which system daemons speak evf/osem by name
(strings of NPXS21006.elf and friends are already in hand); the
Remote Play registration surface (below) is the closest
browser-influenceable daemon.

## 3. `mdbg_call` (573) and the debugger bridge — UNTESTED on 14.00

**What is known:** the 13.52 kernel exposes the mdbg (debugger
backdoor) call with VA->phys translation and **no gate seen**; the
`/system_tmp/mdbg0_dbbp` socket is alive on 14.00. Stub present in
the browser table.

**Next probe:** `sysc 573` with minimal args + `raw:true` for the
errno identity (before anything else — DANGER discipline), then the
documented ABI shapes from the 13.52 study.

## 4. The `/system_tmp` sockets (GnmCompositor, gpvdec/gpvenc arbiters) — UNTESTED

Live UNIX sockets of graphics system processes, reachable by name
from the prison's mount set. Protocol unknown = surface unknown.
`connect()` from the browser needs measuring first (the gates table
has no row yet for AF_UNIX connects to these).

**Next probe:** `socket`+`connect` via the workshop (one syscall pair,
errno read), then `stat`/`read` on the socket files.

## 5. The bnet `raise` write-UAF (N1) — OPEN, high risk / high value

**What is proven (byte-exact, 13.52 kernel):** the bnet error-raising
path captures its owner (a socket struct, UMA zone 0x478) under locks,
then **writes** `word 4` at `owner+0x70` and `word 0xa5` at
`[owner+0x360]+0x70` **after releasing the locks, without taking a
reference** — reachable from the browser through 4 real stubs
(97/98/99/114). No KASLR needed for a proof-of-touch (command
0x10000002 path).

**Honest cost:** the race window is ~15 bytes of code wide — "a
preemption lottery". Never tested on console. Full design:
`05-audits/bnet-n1.md`.

**Next probe:** the KASLR-free touch proof first (does the write land
in our own socket's field?), concurrency only after.

## 6. Remote Play parsers (TCP 9295 / UDP 987, console side) — OPEN

The console-side daemon (`NPXS21006`) accepts discovery (UDP 987) and
registration (TCP 9295) **without pairing**, from the LAN. Our fuzz
harness ran 576 cases / 13 minutes with **0 crashes** (deterministic
403 + `RP-Application-Reason: 80108bff`, 15.0 s server timeout) — the
bench works, the ctrl/takion channels need the console in PIN mode to
open. That is a non-browser process class with its own heap — a real
second front.

**Next probe:** console into Remote Play PIN-pairing mode, rerun the
fuzzer against ctrl; the harness recipe is in `05-audits/remote-play.md`.

## 7. Untested stub families (batch probes, cheap) — UNTESTED

572 (`virtual_query`), 482 (`shm_open` — its gate passed the browser
in the 13.52 bt-gate decode), 657 (`blockpool_batch`, zero gates in
13.52), 533/534 (jitshm create/alias — RWX question). Each is one
`sysc` + errno read; do them one per session, DANGER list first.

## What NOT to do (closed — see 06)

The aio wait, 622, evf/osem creation from the browser, dmem/aout
opens, blind 500-550 sweeps, the fake 1400 offset files. All closed
with evidence; reopening any of them requires a firmware change or a
new primitive.
