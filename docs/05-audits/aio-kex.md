# Audit: the scene's aio kernel exploit (KEX) on 14.00

**Terrain:** the `aio_multi_*` syscall family (662-670), AMD64 orbis
ABI, browser process, firmware 14.00.
**Method:** decode of the public KEX (relapse / jb.js lineage,
13.02-13.52), instruction-level audit of the clear 13.52 kernel, then
the exact sequence replayed live on a stock 14.00 console
(`tools/workshop/kex-aio.html`).
**Status: the family is alive on 14.00; the exploit is CLOSED — the
wait (663) is gated.**

## The mechanism, decoded

Not a bounds bug — a **lifetime bug on the waiter list**:

1. `aio_multi_wait` (663) builds a waiter node linked into the group's
   list; the waiter holds raw pointers (status buffer, mutex, next).
2. When the waited jobs die *during the sleep*, completion frees the
   group's chunks — including memory the waiter still references.
3. An `IPV6_RTHDR` setsockopt spray of `0x48`-byte options (same malloc
   zone 0x60) **reclaims** the freed chunk: the attacker now owns the
   "waiter" the kernel will walk.
4. `aio_multi_cancel` (666) walks the list without validation: per node
   it writes a status (+0x20), stores `curthread` into a fake mutex
   owner field (+0x10 — a **kernel pointer leak**), decrements a
   dword (+0x00 — a **kernel arbitrary decrement**), and conditionally
   decrements again (+0x08).
5. Leak + decrement = the classic ladder to kernel R/W (sysctl route)
   and to the ucred patch.

The engineering constraints that make it deterministic rather than a
race: UMA per-CPU buckets (pin the thread with 487/488 so free and
malloc share one bucket), the scratch-page door (a hint without
`MAP_FIXED` returns the exact address — `MAP_FIXED` is refused), and
proof sinks in the browser's own ArrayBuffers read *after* the syscall
returns (no concurrency needed to prove the walk).

## The 14.00 measurement (deterministic, 7 runs / 2 boots, 2026-10-16)

| Call | Result on 14.00 |
|---|---|
| `aio_submit_cmd` (669) | 0 — groups are created |
| `aio_multi_cancel` (666) | 0 |
| `aio_multi_poll` (664) | 0 |
| `aio_multi_delete` (662) | 0 |
| **`aio_multi_wait` (663)** | **immediate error, never sleeps** — at 1 ms and 100 ms timeouts it returns in ~4-6 ms (pure ROP overhead) with statuses untouched |

No waiter is ever created -> step 2 never happens -> the reclaim has
nothing to reclaim. The verdict marker is `AIO-LIVE-NO-RECLAIM`; the
success verdict (on a firmware that re-enables the wait) would be
`AIO-WALK-PROVEN`.

The one open calibration: the wait's exact errno identity (EPERM vs
context-init failure). The raw `syscall; ret` gadget reads positive
errno without side effects (`sysc raw=1` in the workshop); the page's
`AIO-WAIT-CALIB` probes (invalid count 0x90 -> EINVAL expected; bogus
id -> lookup code) separate the hypotheses.

## Earlier audit of the same family (for completeness)

The instruction-level audit of all six handlers on 13.52 found the
family hardened *except* this lifetime window — the "75% new code in
13.52" premise was a function-matching artifact (the family exists
since 10.50). Only the wait bug was real; 14.00 gates exactly it.
