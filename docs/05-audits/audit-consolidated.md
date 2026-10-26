# Audit: consolidated surface sweeps (batch_map, bughunt, sync primitives, loader TOCTOU)

**Terrain:** the long tail of the syscall surface that does not merit a
standalone write-up: the structural diff 10.50->13.52->14.00, the
ungated-stub sweep, the synchronization primitives, and the loader.
**Method:** structural diffing of the clear kernels (function
matching, 495 rewritten functions classified), instruction-level
audits of the top candidates, full audit of the 25 sync handlers.
**Status: all negative as bug sources; three durable side-findings.**

## The structural diff (the map that aimed everything)

- 96.3% of 13.52 functions have a 10.50 counterpart; **495 functions
  are genuinely new** (~318 KB of code) — zero new syscalls, all
  internal.
- Triaging the 495 against browser reachability (2,143 functions
  reachable from the 298 stubs) produced the ranked hunt list that the
  other audits consumed. The once-famous "aio family is 75% new"
  claim died here: a matching artifact (the family predates 13.52).
- The kernel syscall tables per firmware (10.50: 701 entries; 13.52:
  named + classification) ship in `data/syscalls/`.

## The ungated-stub sweep ("top 20")

231 of the 298 browser stubs showed no visible gate. The top 20 by
reachability/complexity were audited at instruction level: **no
memory-safety bug**. Two durable side-findings:

- **F2 — the unauthenticated IPC registry**: the kernel-side global
  registry of named evf/osem objects performs no authentication
  (13.52, byte-exact; ABI decoded: name-in-struct, tag 0x110 lookup,
  refcount++ at +0x50, id returned in rax). The browser's gate is at
  syscall entry — any non-gated process walks system IPC freely. Now
  lead #2 in `07-next-leads.md`.
- The "ungated" filter itself was polluted: three handlers run
  `priv_check` inside (602/603/587-class), i.e. "looks ungated" is not
  a fact until the instruction level says so.

## The sync primitives (25 handlers)

0 vulnerable, 23 clean, 2 with benign slot leaks. The setcontext/SROP
pivot data (for future exploit writers) was documented as a bonus.

## The loader (SELF) path

The suspected TOCTOU on the dynamic-loader path was **refuted** at
byte level: the flagged call is a bzero of the output struct; a single
source (kernel authmgr pool, post-SAMU); `e_phnum` capped at 72. The
row exists to keep anyone from re-suspecting it.

## The opmc finding (kept as danger, not exploit)

`opmc_set_hw/get_hw` (625/626) = raw `wrmsr`/`rdmsr` on AMD
performance MSRs, **no privilege check** (13.52). A CPL0 side-channel
surface — and a panic button if the MSR is absent. Recorded in
`data/syscalls/DANGEROUS.md`; deliberately never probed from the
browser.
