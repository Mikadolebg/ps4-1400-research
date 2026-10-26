# The frozen engine (why a 13.x bug is a 14.00 bug)

**Claim:** 13.00, 13.50, 13.52 and 14.00 ship the **same WebKit
engine**, so the public 13.52 userland entry works on 14.00 unchanged.
Proven live (the POC runs on 14.00) and provable from public sources:

## The LGPL paper trail

Sony's OSS source page for PS4 lists WebKit drops per firmware. The
**last WebKit entry is "13.00 -"**: there is no source archive for
13.50, 13.52 or 14.00. Under Sony's LGPL obligation the sources are
republished when the shipped binary changes — the standard reading is
that the binary has not changed since.

The last archive itself (`WebKit-616-1300.zip`, 1.62 GB, md5
`6f2a5b0f16bc944fdd584f6fe6201bc9`):

- engine version **616.1.27.211.1** (`safari-7616-branch`, forked
  around October 2023);
- **699 Sony-specific changes** in the tree: 651 in 2023, 38 in 2024,
  10 in 2025 — the **last one dated 2025-07-18** (DOMURL);
- **zero changes in 2026**, i.e. nothing between 13.52 (spring 2026)
  and 14.00 (September 2026).

## The runtime corroborations (14.00, live)

- The base-leak pair door uses **RVAs measured from the 13.00-era
  build** and closes exactly on 14.00 (`delta 0x24B0C20`, both anchors
  aligned — `BASE-PAIR-GATE-PASS`).
- The 15 ROP gadgets verify byte-exact at those same RVAs on 14.00
  (`GADGET-GATE-PASS 15/15`), zero repairs needed across sessions.
- The `__imp___error` GOT slot sits at its 13.00 RVA.

If Sony had rebuilt the engine, none of that would line up.

## Consequence for the 14.00 hunt

What Sony actually hardened on 14.00 is the **kernel frontier of the
browser process** (the gates in `data/syscalls/gates-1400.csv`: the
aio wait, named IPC, the 622 kill-switch, kernel-state allocations) —
not the entry. That asymmetry defines the whole research program of
this repository: the userland side is a solved, frozen platform; the
missing link is exactly one kernel primitive.
