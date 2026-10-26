# Audit: the PS4 sandbox — five layers, and why the browser needs a kernel bug

**Terrain:** the sandbox architecture around the browser process,
10.50/13.52 clear kernels + live measurements on 14.00.
**Method:** structural analysis of the credential/prison machinery
(byte-exact localization of the sceSblACMgr family), live probes of
every escape-adjacent door.
**Status: no syscall-level escape exists from the browser class on
14.00 — by measurement. The canonical escape recipe (for whoever
lands the kernel primitive) is fully documented.**

## The five layers

1. **Sony credential class** — the `ucred`-attached class fields
   (`ucred+0x58/0x60/0x68`); the sceSblACMgr check family localized
   byte-exact (`0x3b2ce0..0x3b3560` on 13.52). The browser holds the
   webkit class.
2. **The FreeBSD prison** — the mount table wall
   (`docs/04-terrain-map/`: 5 visible mounts, ~31 invisible paths).
3. **Per-syscall gates** — the class check at entry (named IPC, the
   aio wait, ...): `data/syscalls/gates-1400.csv`.
4. **Per-device permissions** — devfs visibility + open/ioctl checks
   (dipsw's decoded ioctl door is the surviving exception).
5. **The tar pit** — anything allocating kernel state from the browser
   pends forever (kqueue/umtx/setuid/device opens; 5/5 measured).

## What was measured live (no escape found)

- 7/7 classic device-node opens: EPERM.
- AF_UNIX connects to non-prison sockets: EPERM.
- The dynlib doors (594 load_prx): -1 sandboxed (and on a *jailed*
  10.50 the same call passes with a credential costume — proof the
  refusal is the class check, not a missing handler).
- The loader TOCTOU that would have bypassed layer 1: refuted
  (`06-negative-results.md`).

## The escape recipe (post-kernel-primitive, the classic)

Once a kernel R/W exists, the standard PS4HEN-class credential patch
on 14.00 (offsets in `data/offsets/kernel-1400.md`):

```
ucred+0x58 = 0x3801000000000013
ucred+0x60 = ~0
ucred+0x68 = ~0
```

That single write dissolves layers 1/3/4 for the process; the prison
mounts then fall to the standard rootvnode/prison0 walk. Everything
above the missing kernel primitive is, on 14.00, ready: offsets,
patch set, payload contract (the classic loader ports 9020/9021).
