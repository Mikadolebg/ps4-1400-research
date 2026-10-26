# Notices and attribution

## License split

- **Code** in this repository (`poc/`, `tools/`) is released under the MIT
  license (see `LICENSE`).
- **Documentation** (`docs/`, `data/`, `STATUS.md`, `REPRODUCE.md`) is released
  under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

## Scene attribution

This project builds directly on the public PS4/PS5 exploit scene. The
userland entry and several kernel-exploit designs studied here are **not our
inventions**. Specifically:

- **Jordy** (`jordyidk`) — the SerializedScriptValue (SSV) userland bug used
  as the entry point on 13.04/13.52, and its public stage-2 patterns.
- **zecoxao** — the public scene chain family (slopkit builds, offset
  verification protocol), served publicly up to 13.52; our offset-verification
  discipline follows the standard that author established (verify gadgets by
  bytes, never by pattern).
- **GamerHack (g2all/slopkit)** — the public reference chain (userland SSV +
  `jb.js` kernel orchestrator + `ps4_offsets.js`) covering 11.00–13.52. The
  aio P1→P5 kernel-exploit sequence reproduced by our workshop page is a port
  of that orchestrator's exact syscall series.
- **ntfargo / Relapse-Exploit** — the PS5 7.00–13.60 public chain that uses
  the `aio_multi_wait` UAF; our audit of the aio family on 14.00 started
  from that published mechanism.
- **Scene-Collective / ps4-hen** — the public kernel offset files for 14.00
  (`offsets/1400.h`, commit d077fb4, 2026-09-19), reused verbatim as
  reference data in `data/offsets/kernel-1400.md`.
- **adri22235 / ps4-suid-scanner** — public repo that mirrored the 14.00
  kernel offsets; useful as corroboration (its "webkit_gadgets_1400.js" was
  demonstrated to be a byte-identical copy of the 1304 file and is **not**
  used here — see `docs/06-negative-results.md`).

## Our contribution

What this repository adds on top of the above:

- The measured proof that the SSV entry still works on firmware **14.00**
  (frozen-engine argument + 15+ full boots on console), and the complete
  userland chain (R/W, base leak, verified ROP, arbitrary syscalls).
- The **browser syscall table for 14.00** (302 libkernel stubs mapped from a
  live console) and the measured per-syscall gate status of the interesting
  families (`data/syscalls/`).
- The negative results: which public kernel leads are **closed** on 14.00
  (aio wait gated, ipmimgr kill-switch, evf/osem gated, dmem/aout refused)
  with the evidence for each.
- The tooling: the distilled POC, the live workshop, the dump/extraction
  pipeline that lets anyone regenerate our data from their own console.

## Sony material

No Sony proprietary code, firmware images, or decrypted binaries are
committed to this repository. Memory dumps referenced by the extraction
tools must be produced by the user from their own console. The FreeBSD 9
`syscalls.master` reference file redistributed in `data/syscalls/` is from
the official FreeBSD source tree (BSD license, © The FreeBSD Project).
