# Kernel 14.00 offsets and structure notes

The 14.00 kernel is not decryptable with current public tooling, so
kernel-side offsets come from two sources: the **public scene offset
files for 14.00** and **differential analysis against the clear 13.52
kernel** (14.00 is a light edit of 13.52: structural drift measured at
+0x2a0..+0x300 across matched functions).

## Public scene offsets for 14.00 (attributed)

From **Scene-Collective/ps4-hen** `offsets/1400.h` (commit `d077fb4`,
2026-09-19), as mirrored by adri22235/ps4-suid-scanner's `1400.c`
(those kernel values were verified genuine; the *WebKit* file in the
same repo is a demonstrated fake — see
`docs/06-negative-results.md`):

| Symbol | Value |
|---|---|
| PRISON0 | `0x111FA18` |
| ROOTVNODE | `0x2136E90` |
| ALLPROC | `0x1B28538` |
| SYSENT | `0x1102B70` (⚠ the 1352 value circulating in other files is `0x110A760` — the 1400 number moved; use `0x1102B70` for 1400) |
| `memcpy` | `0x2BD850` |

These are the values a future kernel payload will patch against
(kpatch-style writes: prison0/rootvnode/ucred walk — the classic
post-exploitation set, unchanged in shape from 13.04).

## What our own measurements add

- **Kernel syscall tables**: 13.52 clear-kernel tables ship in
  `data/syscalls/` (named handlers + 684 names). For 10.50, the
  complete 701-entry table. For 14.00, the browser-side stub surface
  (`stubs-1400.csv`, 302 signature hits / 298 live-verified stubs).
- **sysent syscall ABI (AMD64 orbis)**: stubs load the number in `rax`
  and move `r9` into `rdx` before `syscall` — the 4th argument travels
  in `r9`. Signature: `48 c7 c0 <nr32> 49 89 ca 0f 05`.
- **ipmimgr (622) on ≤13.52** (clear-kernel study, byte-exact):
  kid handles table at `[kid]` with `ConSx` at `+0x28` **not
  refcounted** while the kid itself is — the UAF window (readers
  0x463/0x465/0x467, two-phase destroy 0x520). Killed on 14.00 by a
  process kill-switch at handler entry (measured, see
  `docs/05-audits/ipmimgr-622.md`).
- **orbis_idt** (the generic Sony id table, 13.52): ids are
  `(seq&7)<<13 | index` — only **3 sequence bits**, so the generation
  check wraps in **8** create/destroy cycles of the same name
  (free-list is LIFO). Applies to the kid table AND the named-kqueue /
  osem tables. Live-proven on osem ids (9 cycles, id9==id1) — but the
  osem family is alias-only on 14.00, so the wrap is a tool, not an
  exploit, there. Full model: `docs/05-audits/orbis-idt-wrap8.md`.
- **Browser sandbox gates on 14.00** (measured, `gates-1400.csv`): aio
  wait gated, named IPC gated at entry, 622 kill-switch, kernel-state
  allocating syscalls pend. Sony hardened the browser's kernel frontier
  specifically.
- **The escape recipe once a kernel R/W exists** (from the 10.50/13.52
  studies, for the future 14.00 payload author): patch your own `ucred`
  — `+0x58 = 0x3801000000000013`, `+0x60 = ~0`, `+0x68 = ~0` — the
  standard PS4HEN-class credential costume; then the 594/dynlib doors
  and the device nodes open.
