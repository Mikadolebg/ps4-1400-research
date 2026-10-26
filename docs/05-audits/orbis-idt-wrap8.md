# Audit: orbis_idt — the generic Sony id table and its 3-bit wrap

**Terrain:** Sony's generic id-table service in the kernel (used by the
ipmimgr kid table, the named-kqueue table, and the osem table),
13.52 clear kernel.
**Method:** full decode of the id allocator + all consumers; an exact
simulator of the scheme (deterministic model); live confirmation on
14.00 via the osem family.
**Status: the wrap is REAL and live-proven; on 14.00's browser-reachable
tables it is alias-only (no type confusion) — a tool, not an exploit,
there. One untested branch remains (see the end).**

## The scheme

```
id (16 bits) = (seq & 7) << 13 | index
```

- **only 3 bits of sequence** are exposed: the generation check
  (`seq` mismatch = stale id) **wraps after 8 remove cycles** of the
  same slot;
- the free list is **LIFO** — after 8 create/destroy rounds of the
  *same name*, the 9th create returns an id whose generation equals
  the 1st's: `id9 == id1` byte-for-byte;
- per-process tables (osem) and global tables (kid) both use it; 8
  consumers identified in the kernel.

## Proof chain

1. **Model:** the simulator reproduces the allocator exactly (period 8,
   LIFO reuse) — deterministic, no hardware.
2. **Live (14.00, browser):** the osem family executes the 9-cycle
   dance cleanly — 9 create/destroy pairs, `id9 == id1` observed,
   18 syscalls, process alive (`cpuset`-pinned thread). The wrap is
   confirmed on the shipping kernel.

## Why it stops there on 14.00

- The **osem** table is per-process and strictly typed at all 59 call
  sites: a stale id aliases an object of the *same* type. No confusion.
- The **kid** table (where the ipmimgr UAF lived) is unreachable since
  the 622 kill-switch (`ipmimgr-622.md`).
- The **named-kqueue** table (kqueueex, syscall 141) exists on 13.52 —
  its 14.00 behavior is unmeasured (kqueue-class calls pend in the
  browser tar pit, so the browser cannot reach it either).

## The open branch

The decode found that the destroy path of one consumer family never
marks the slot dying (a "zombie" branch) — a candidate for a
**deterministic** stale-id read (no race) on whichever table a future
non-browser process can reach. That branch is modelled but was never
probed on hardware: the probe requires a caller class the browser
cannot provide (same wall as everywhere else: the gates).
