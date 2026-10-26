# Audit: the dmem/dce/aout doors — what they would give, and why the browser cannot have them

**Terrain:** the direct-memory device family (`/dev/dmem0`, the dce
GPU command encoder, `/dev/aout`), 13.52 clear kernel + live 14.00
measurements.
**Method:** disassembly of the device entry paths (open checks, mmap
routines); live open attempts from the armed browser.
**Status: CLOSED for the browser class on 14.00 (opens refused) — the
capability itself is documented for post-escape or other process
classes.**

## What dmem0 actually is (13.52, byte-level)

Its mmap handler **translates a user offset to a physical address**
and maps it — with **no owner filter** on the translation itself. The
door is guarded by credentials + an AuthID check at open time. In
other words: whoever passes the open gate gets a physical-memory
window. That is why it was worth auditing to the last byte even after
the browser could not open it.

## The live 14.00 verdict

- `open("/dev/dmem0")`: **refused** (browser class), measured
  repeatedly (marker trail `DMEM-OPEN-REFUSE`-class verdicts).
- `open("/dev/aout")`: **refused**.
- The GPU-side surface (`/dev/dce`, gc/gic command paths): opens
  behave the same for the browser; the audit of the submit paths
  (from the network+GPU stack study) found the historical double-free
  (<12.00 era) **fixed** — the cleanup chain is locked. The surviving
  GPU finding is the bnet `raise` write-UAF (`bnet-n1.md`), which is
  network-side, not device-side.

## Why this row exists in a negative-results-heavy repo

Two reasons: (a) it documents that the *interesting* capability
(physical memory windows) sits one credential check away — so any
confused-deputy or credential trick that ever lands re-opens it
instantly; (b) it closes the "just mmap physical memory from the
browser" family of ideas with evidence instead of folklore.

## Related closed rows

The same measurement round closed: ptrace PT_LWPINFO (fixed in 13.52),
the audio mmap CVE (device node EPERM for the browser — the bug lives
on in the kernel, unreachable from this class), and the loader TOCTOU
(refuted outright).
