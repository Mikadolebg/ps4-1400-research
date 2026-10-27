# Open leads — ranked, with the next probe for each

Status legend: **OPEN** (measured alive somewhere, 14.00 unknown),
**UNTESTED** (never probed anywhere, per our knowledge), each with the
tool in this repo that takes you there. Read `06-negative-results.md`
first — several intuitive leads there are closed.

## 1b. The `aio_multi_delete` TOCTOU (Lapse family) — REOPENED, strongest shape

**Why it is the top candidate (2026-10-27 cross-evidence):**
- The 13.52 kernel shows the exact shape the PS5 scene says Sony fixed
  in **PS5 14.20**: a lock upgrade (drop-and-reacquire) on the AIO
  group inside `sys_aio_multi_delete`, then sub-object frees with no
  generation-ID revalidation. The fix landed AFTER our 14.00 build.
- On-device: delete (662) is alive and ungated on 14.00 (gates table).
- The window is the lock-upgrade span (microseconds), not a 1 ns
  preemption lottery — a real TOCTOU, winnable with timing control.
- **The public Lapse chain (11.00-12.02) is in hand and documents the
  full recipe**: the browser's Web Workers are in-process kernel
  threads on this same frozen WebKit engine — the chain arms a worker
  from the main thread's R/W (walk into worker memory, hijack its
  context) and RPCs syscalls into it, giving TWO concurrent syscall
  streams plus nanosleep/sched_yield for race timing.

**Next probe:** port the Lapse worker-arming to our 14.00 workshop
(verify workers on the frozen engine first — one eval), then replay
the delete race against our measured-alive handler with the group
teardown timed into the upgrade window.

## 2. `/dev/dipsw` ioctl window — UNTESTED, highest value-per-unknown

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

## 3. The unauthenticated IPC registry from a non-gated process — OPEN (F2)

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

## 4. The `/system_tmp` sockets (GnmCompositor, gpvdec/gpvenc arbiters) — UNTESTED

Live UNIX sockets of graphics system processes, reachable by name
from the prison's mount set. Protocol unknown = surface unknown.
`connect()` from the browser needs measuring first (the gates table
has no row yet for AF_UNIX connects to these).

**Next probe:** `socket`+`connect` via the workshop (one syscall pair,
errno read), then `stat`/`read` on the socket files.

## 1. The bnet `raise` write-UAF (N1) — OPEN, entry chain PROVEN LIVE on 14.00

**What is proven (2026-10-27, stock 14.00 console, through the armed
workshop):** the whole netevent chain runs from the browser with zero
gates — socket, REGISTER (owner = our socket, no reference), voluntary
RAISE, and the sensor read back `events = 0x4` (the raise's literal
mask) from OUR queue. Live interfaces: ids 1-4. Corrected ABI:
`netcontrol(id, cmd, ptr, len)`; raise trigger `0x20000010`.

**What remains (the hard part, honestly rated):** the race — close the
socket while a raise sits in the ~15-byte post-unlock window, then
reoccupy the freed 0x478 socket block. Per-event probability is tiny
(the incoming-HTTP traffic raises continuously; each attempt is a
preemption lottery), and a lost attempt in a bad state is a kernel
panic (accepted, documented, reboot). The winning signal without KASLR:
the reoccupied socket's connect() returning an abnormal errno.

**Next probe (measured 2026-10-27):** the purge at close is CONFIRMED
on device (no deterministic dangling — the lottery stands), the notify
indirect call is NULL-gated (wins on our own throwaway blocks are
benign), the in-page loop runs at 3000 iter/s, and the honest odds are
~1e-8/iteration. Plan: reboot (clears the wedged ifnet-1 slots), then a
volume lottery with health-checked batches — or bank the hours and work
the slot-wedging mechanism (a fresh bug candidate found by the same
session: ifnet queue slots stop accepting registrations after intensive
churn; ifnets 2-4 unaffected; clean-unregister command identified).

## 5. Remote Play parsers (TCP 9295 / UDP 987, console side) — OPEN

The console-side daemon (`NPXS21006`) accepts discovery (UDP 987) and
registration (TCP 9295) **without pairing**, from the LAN. Our fuzz
harness ran 576 cases / 13 minutes with **0 crashes** (deterministic
403 + `RP-Application-Reason: 80108bff`, 15.0 s server timeout) — the
bench works, the ctrl/takion channels need the console in PIN mode to
open. That is a non-browser process class with its own heap — a real
second front.

**Next probe:** console into Remote Play PIN-pairing mode, rerun the
fuzzer against ctrl; the harness recipe is in `05-audits/remote-play.md`.

## 6. Untested stub families (batch probes, cheap) — UNTESTED

572 (`virtual_query`), 482 (`shm_open` — its gate passed the browser
in the 13.52 bt-gate decode), 657 (`blockpool_batch`, zero gates in
13.52), 533/534 (jitshm create/alias — RWX question). Each is one
`sysc` + errno read; do them one per session, DANGER list first.

## What NOT to do (closed — see 06)

The aio wait, 622, evf/osem creation from the browser, dmem/aout
opens, mdbg_call 573 (gated by credential class — proven in the 13.52
disassembly), blind 500-550 sweeps, the fake 1400 offset files. All closed
with evidence; reopening any of them requires a firmware change or a
new primitive.
