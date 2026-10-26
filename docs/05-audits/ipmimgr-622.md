# Audit: sys_ipmimgr_call (622) — the UAF that was, and the kill-switch that is

**Terrain:** syscall 622, the ipmimgr IPC gateway (~35 commands),
kernel side, 10.50 (clear) / 13.52 (clear) / 14.00 (live behavior).
**Method:** full Ghidra+capstone decode of the gateway on the clear
kernels; live probes on 14.00 (clean Lua via an existing loader, then
ROP calls with positive controls).
**Status: CLOSED on 14.00 — the handler kills the calling process.
The bug class was real and unhardened through 13.52.**

## The command surface (decoded, 10.50 == 13.52)

- Calling convention and status codes measured: `0x800E0001` size
  guard, `0x8002004E` credential gate, `0x80020002` lookup failure.
- Handles ("kid"): types 0x8001 server / 0x8002 eventflag / 0x8004
  client; creation command **2** was **ungated** on <=13.52 (a struct
  of 0x150 zeroed, `+0x18 >= 0xfc00` or refuse 0x16).
- A **blacklist of panic commands** was established before any live
  probing (0x302, 0x490, 3, 4, 0x310/0x320, destroyers 1/3/5/0x520).

## The UAF (byte-exact, <=13.52)

The kid is refcounted — but the **ConSx ([kid+0x28]) and the channels
are not**. Destroy runs in two phases (markDying / release, command
0x520 zfreeing the ConSx after the kid's release): readers 0x463 /
0x465 / 0x467 (sub=kid) can walk a freed ConSx. This was the top
H1-pending candidate of the period ("the kernel bug" most likely used
by the private 14.00 chain demoed in the scene, 2026-10-05).

## The 14.00 verdict

The lifecycle commands (**0, 1, 2, 3, 5, 0x400, 0x465**) **terminate
the calling process at handler entry**, input-independently:

- first measured with clean Lua (2026-09-27): the caller dies, zero
  bytes answered;
- re-measured through the ROP chain (2026-10-15) with **positive
  controls in the same session**: getpid 7/7, osem 549/550 18 calls —
  the ROP chain is blameless; the handler itself kills.

Conclusion: Sony rewrote the module's entry between 13.52 and 14.00 —
a kill-switch, not a gate. No probing strategy around it from the
browser; the only future for this surface is a different caller class
or a firmware change.

## What survives from this audit

- The orbis_idt wrap-8 discovery (the kid table shares Sony's generic
  id scheme) -> `orbis-idt-wrap8.md`.
- The measured status-code map and the panic blacklist (safety data
  for any future ipmimgr work on older firmwares).
- The methodological pattern that closed it: *positive controls in the
  same session as the fatal call* — the reason the kill-switch was
  proven rather than blamed on the chain.
