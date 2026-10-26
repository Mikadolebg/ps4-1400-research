# 2. The userland chain, stage by stage

The proven pipeline, as implemented in `poc/poc.html` (distilled) and
`tools/workshop/console.html` (live). Every stage prints its verdict
markers (`data/markers.md`); every memory law cited here was measured
on console, not assumed.

## Stage 1 — arbitrary R/W (`docs/01-entry-ssv/`)

The SSV bug turns a groomed predecessor into a genuine `Uint8Array`
whose vector field we control. Pointing that vector at an address and
reading/writing byte-wise through the carrier gives:

- `ext_read8/32/64(addr)`, `ext_write8/32/64(addr, val)` — the vector
  is re-pointed before each access;
- `ext_addrof(obj)` — swap the object into two getter slots, serialize,
  read its pointer out of the captured symbol string.

Markers: `GENUINE-U8-RW-PASS`, `ARBITRARY-READ/WRITE-PASS`.

## Stage 2 — the WebKit base leak (the pair-gap door)

Two builtin natives live at a fixed delta in the frozen module
(`data/offsets/webkit-1400.md`):

```
base = s28(Math.expm1 native) - 0x2586880
delta(expm1, parseInt) = 0x24B0C20   (checked in-region, aligned, both boots)
```

The gate refuses to conclude on any deviation (clean refusal, nothing
dumped). Markers: `BASE-PAIR-GATE-PASS`, `BASE-LOCKED`.

An earlier offline approach (leak-formula via trampoline residues,
26 console samples, K28−K18 = 0xC25F8 exact) is superseded by the pair
door but corroborates the same anchor RVAs.

## Stage 3 — verified ROP

The gadget table (15 entries, RVAs + byte signatures in
`data/offsets/webkit-1400.md`) is verified **at runtime, byte by
byte**, with REX-equivalence handling for the two REX-prefixed pops;
any stale RVA triggers a bounded repair scan (±0x8000, then ±0x20000)
whose result is dumped for audit. The stub window anchor comes from
`__imp___error` (GOT deref), and the getpid stub is located by its
exact 12-byte signature at its measured offset.

Markers: `GADGET-GATE-PASS 15/15`, `FCALL-BUFADDR-SELFTEST`,
`FCALL-STUB-EXACT`.

## Stage 4 — fcall: arbitrary syscalls

The call machine (scene lineage, `jb.js`-shaped):

- a pivot object's cell is aimed at a forged stack; `m_function` of
  `Math.expm1`'s JSFunction is armed with the G0..G5 chain;
- **trigger**: calling `Math.expm1(pivotObj)` runs our chain: pops load
  the 6 argument registers, the target stub runs `syscall`, the frame
  lands in a controlled buffer we read back through the R/W primitive;
- the AMD64 orbis ABI quirk: stubs move `r9` into `rdx` — the 4th
  argument travels in `r9`.

**The law (measured):** exactly **one arm -> calls -> disarm cycle per
browser session**. Arming writes `m_function`; the finally restores
it and re-reads to prove restoration (`FCALL-SERIES-DISARMED ...
RESTORED`). The POC spends its cycle on `getpid` (`SYSCALL-PASS`); the
workshop keeps the series armed for the whole session and spends it on
hundreds of stub-verified calls.

Evidence from the live workshop: a **398-syscall series ran cleanly**
through the byte-verified stubs, including the whole aio sequence
family; the errno gadget (bare `syscall; ret` at the stub-window tail)
returns **positive errno** for gate analysis (`sysc raw=1`).

## Memory laws (all measured on 14.00)

| Law | Number | Consequence |
|---|---|---|
| Carrier size | 5M slots / 40 MB (2M failed coverage) | never shrink the carrier |
| Process ceiling | ~80 MB (success <=512 drains ~77 MB; death at 640/1024) | drain ladder caps at 512 |
| Browser cores | 2 (6-7); `cpuset_setaffinity` pins | required for per-CPU UMA reclaim |
| Scratch page | mmap **hint without MAP_FIXED** returns the exact address | `MAP_FIXED` at low addresses is refused |
| One ROP cycle | one arm/disarm per session | reload the page to re-run |

## Where the chain stops

The chain ends at **arbitrary syscalls from the browser process**.
What those syscalls meet on 14.00 — gates, kill-switches, the tar pit —
is the next document (`docs/03-syscall-surface/`).
