# 3. The 14.00 syscall surface (browser process)

What the browser can actually call, and what answers. Data:
`data/syscalls/` (the stub table, the per-family gates, the danger
list). This document is the narrative.

## The stub window

libkernel exports one tiny stub per syscall to the browser:

```
48 c7 c0 <nr32>    mov rax, <number>
49 89 ca           mov rdx, r9      ; the 4th argument travels in r9
0f 05              syscall
72 01 c3           jb .+1 ; ret     ; classic lazy-binding tail
```

All of them sit in a dense zone at `__error + 0x52B0..0x7A00` of
libkernel; the bare `syscall; ret` errno gadget sits at `+0x6A2A`.
Our dump of that window yields the **302 signature hits = 298 stubs +
4 inline sequences** (see `data/syscalls/README.md`); every stub the
tooling calls is resolved at its measured offset and **byte-verified
before the first call** — the workshop never dials an unverified
address.

## What the 298 map to (families that matter)

- **Working from the browser**: process ids (20), the FS set inside the
  prison (5/3/6/47/272), the socket infrastructure (97/105/118/135),
  mmap with hints (477), affinity pinning (487/488), the whole aio
  family **except its wait** (662/664/666/669).
- **Gated at entry for webkit-class processes**: named IPC — evf
  (538-546) and osem (549-556). Even creating your own named flag
  fails; 150 system names x both families = 0 opened. The kernel-side
  registry itself has no authentication (13.52 disassembly) — the gate
  is the class check at syscall entry.
- **Killed**: 622 (ipmimgr lifecycle commands) terminates the calling
  process at handler entry (`docs/05-audits/ipmimgr-622.md`).
- **The tar pit**: anything that allocates kernel-side state
  (kqueue 362, umtx 434, setuid 24, device opens...) **pends forever**
  in the browser sandbox — only getpid-class answers return. Measured
  5/5 before the gate mapping started. The direct-syscall route out of
  the sandbox is closed on 14.00; a kernel bug is required.
- **The errno discipline**: raw stubs return -1 on error; the bare
  `syscall; ret` gadget returns the **positive errno in rax** — that is
  how gate identities (EPERM vs EINVAL vs before-count failures) are
  read without side effects. The aio wait's exact errno identity is
  the one still-pending calibration (`docs/05-audits/aio-kex.md`).

## The gates table

`data/syscalls/gates-1400.csv` is the canonical per-family status
(WORKS / ALIVE / GATED / KILL-SWITCH / PENDING / UNTESTED), each row
with its evidence and measurement date. The notable **UNTESTED**
candidates — the next probes of the escape program — are 573
(`mdbg_call`: the 13.52 debugger bridge showed no gate), 572
(`virtual_query`), 482 (`shm_open`), 657 (`blockpool_batch`).

## Danger list (summary)

189 `fstat` = kernel crash (use 551). Never sweep 500-550 blindly.
625/626 (opmc) = unguarded MSR access. Full list with context:
`data/syscalls/DANGEROUS.md`.
