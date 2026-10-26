# 4. The terrain: the browser sandbox on 14.00

What the browser process actually sees, mapped with the live workshop
(`stat`/`walk`/`read`/`sysc` over the bridge). The sandbox has five
layers (Sony credential class -> prison -> mounts -> per-syscall gates
-> per-device permissions); the workshop probes mapped the visible
ones from inside.

## The filesystem prison

The browser's root is a prison whose visible tree is:

```
/              (the prison root)
/dev           <- devfs, partially populated (see below)
/system_tmp    <- live UNIX sockets
/user          <- user data
/av_contents   <- AV content mount
/<random-named dir>
```

~31 standard system paths are **invisible** (not EPERM — simply not in
the prison's mount set). The FS syscalls themselves work (open/read/
getdirenitories/lseek/close all return cleanly on visible paths) — the
wall is the mount table, not the syscall layer.

## /dev as seen from the browser

Visible nodes: `dipsw`, `random`, `urandom` (symlink), **`dmem0`**,
**`dce`**, `rng`, `bt`. Measured:

- `random`/`urandom` are readable **and writable** from the prison.
- **`open("/dev/dipsw")` succeeds** (an fd comes back; reads fail — it
  is an ioctl-only device). Its ioctl entry check, decoded from the
  13.52 kernel: proceeds when `cred+0x60` bit 62 == 0 — i.e. for
  **non-system processes, the browser included**. Command window
  `0x80028800..0x80108804`. **Never tested anywhere** — the top open
  lead (`docs/07-next-leads.md`).
- `dmem0` / `dce` / `aout`: opens are **refused** for the browser class
  (measured; the 13.52 study shows dmem0 mmap would translate user
  offsets to physical addresses behind a creds+AuthID gate — the gate,
  not the capability, is what 14.00 tightened).

## /system_tmp — the live sockets

Walking `/system_tmp` shows live UNIX domain sockets:
`mdbg0_dbbp`, `GnmCompositor`, `GnmCompositorRestricted`,
`gpvdec_arbitrator`, `gpvdec_proxy`, `gpvenc_proxy`. These are the
debugger and graphics-compositor IPC endpoints of system processes —
reachable name-space-wise from the prison. Untested (the second open
lead family).

## The process terrain around the browser

- The browser gets **2 cores (6, 7)** of the 8; affinity calls are
  ungated (that is a tool, not a threat).
- The memory budget is ~**80 MB** (see the laws in
  `docs/02-userland-chain/`).
- Named IPC (evf/osem) is gated at entry for the browser class — but
  the **kernel-side registry has no authentication** (13.52 kernel),
  so any *other* non-gated process (a system daemon, a confused deputy)
  can walk it. F2 in `docs/05-audits/audit-consolidated.md`.
- Remote Play: the console-side daemon (`NPXS21006`) exposes
  UDP 987 (discovery) and TCP 9295 (registration/control) **without
  pairing**, from the LAN — a different process class with its own
  parser surface (`docs/05-audits/remote-play.md`).

## Bridge recipes (the probing cookbook)

With the workshop armed (`REPRODUCE.md` §5):

```
{"t":"walk","path":"/","depth":3}                       the prison map
{"t":"stat","path":"/dev/dipsw"}                        open + head
{"t":"read","path":"/system_tmp/...","max":256}         export a file
{"t":"sysc","num":573,"args":[0,0,0],"raw":true}        probe + errno
{"t":"eval","code":"window.LAB.G.POP_RDI_RET.toString(16)"}  sanity
```

Every probe above is side-effect-free by construction except the sysc
line — check `data/syscalls/DANGEROUS.md` before dialing a number.
