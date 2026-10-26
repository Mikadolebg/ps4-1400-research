# Negative results (closed leads, with evidence)

The most valuable page of this repository: what has been tried on the
road to a 14.00 kernel primitive, what closed it, and why nobody should
burn time reopening it without new input. Status words: **CLOSED**
(proven dead on 14.00), **CLOSED <13.x** (dead on the studied range,
14.00 already covered by another row), **REFUTED** (the premise itself
was wrong).

| # | Lead | Status | The evidence that closed it |
|---|---|---|---|
| 1 | The scene's aio KEX (`aio_multi_wait` 663 UAF) | **CLOSED on 14.00** (the wait is gated) | The exact P1->P5 sequence ported and replayed (7 runs / 2 boots, 2026-10-16): submit/cancel/poll/delete return 0, the wait errors instantly without sleeping at 1 ms and 100 ms — no waiter is ever created, so the reclaim cannot land. Details: `05-audits/aio-kex.md`. Re-test trigger: a firmware that re-enables the wait. |
| 2 | `sys_ipmimgr_call` (622) UAF — the H1-pending candidate | **CLOSED on 14.00** (kill-switch) | Lifecycle commands kill the calling process at handler entry, input-independently (clean-Lua 2026-09-27, then ROP with positive controls 2026-10-15). The UAF itself was alive and unhardened 10.50->13.52 (ConSx/canals non-refcounted). Details: `05-audits/ipmimgr-622.md`. |
| 3 | Named IPC gating (evf 538-546 / osem 549-556) from the browser | **CLOSED for the browser class** | Creation of your own named flag fails at entry; 150 system names x 2 families = 0 opened (2026-10-16). Note the asymmetry: the registry itself is unauthenticated — the door is open for any non-gated process, which is a *lead*, not a closure (see 07). |
| 4 | `dmem0` / `aout` device doors for the browser | **CLOSED for the browser class** | Opens refused, measured live twice (2026-10-16). The 13.52 study shows what they *would* give (physical-address translation mmap) behind the creds+AuthID gate. |
| 5 | osem id-table wrap-8 as a confusion primitive | **CLOSED (alias-only)** | The 3-bit sequence wrap is real and live-proven (9 cycles, id9==id1) — but all 59 call sites are strictly typed: the stale id only ever aliases the same type. No confusion surface. `05-audits/orbis-idt-wrap8.md`. |
| 6 | SELF-loader TOCTOU (dynamic loader path) | **REFUTED** | Full disassembly of the suspected path: the flagged call is a bzero of the output struct; a single source (the kernel authmgr pool), e_phnum capped at 72. The "TOCTOU" never existed. |
| 7 | The aio family as a fresh bug source (audit of all 6 handlers) | **CLOSED** | Instruction-level audit of submit/wait/cancel/poll/delete/init on the clear 13.52 kernel: hardened, refcounted, no memory-safety bug found (the earlier "75% new code" premise was a matching artifact — the family already existed in 10.50). Only the *wait lifetime* bug (row 1) was real, and it is gated. |
| 8 | `sys_batch_map` (548) | **CLOSED** | Full audit: dmem-type and deferred-entry types both validate cleanly; count is unbounded but the error path unwinds correctly. No bug. |
| 9 | Top-20 ungated syscall sweep (231-candidate triage) | **CLOSED (negative)** | Structured triage of the 231 stubs without visible gates -> top 20 audited at instruction level: no memory-safety bug. Two side-findings kept: opmc 625/626 (unguarded MSR — danger, not exploit) and the polluted "ungated" filter (priv_check hidden inside three handlers). |
| 10 | Synchronization primitives (25 handlers) | **CLOSED (negative)** | Full audit: 0 vulnerable, 23 clean, 2 with benign slot leaks. The unauthenticated global registry (F2) is the surviving observation -> lead, not bug. |
| 11 | `ptrace` PT_LWPINFO (CVE-2017-1086 family) | **CLOSED <13.x** | Fixed in the 13.52 kernel (byte-level: the lwpinfo path is hardened). Dead before 14.00. |
| 12 | PPPwn / CVE-2006-4304 (network, remote play adjacent) | **CLOSED <13.52** | The ICMP-era fix is backported into 13.52 — binary proof in the console-side parser. |
| 13 | SA-26:27 sound (CVE-2026-45258, audio mmap) from the browser | **CLOSED for the browser** | The audio device node is EPERM for the browser class (the mmap bug itself lives on in 13.52 — a post-escape or non-browser-process surface only). |
| 14 | CVE-2019-5606 (pts/ SIGIO family) | **CLOSED <13.x** | Fixed-form in 13.52. |
| 15 | "webkit_gadgets_1400.js" circulating files (adri22235 commit 349e4c1) | **REFUTED (fake)** | All 17 "1400" gadget values byte-identical to the 1304 file; the repo's own later commit admits synthetic generation "PENDING_DUMP". Never import. (The *kernel* 1400 offsets in that repo are genuine - Scene-Collective's - and are what we reuse.) |
| 16 | "1400 kpatch binaries" (XEMIXJB family) | **REFUTED (fake)** | md5 of `patches/1400.bin` == md5 of the 1352 kpatch == the file zecoxao serves for 1352. Renamed, not ported. |
| 17 | Direct syscall escape from the sandbox (state-allocating calls) | **CLOSED** | The tar pit: kqueue/umtx/setuid/device-opens pend forever in the browser (5/5 measured). Escaping the browser class requires a kernel bug, not a syscall trick. |
| 18a | `mdbg_call` (573) from the browser | **CLOSED (gated by credential class)** | The 13.52 handler calls the sceSblACMgr family (0x3b2ce0) at entry via td+0x130 and returns 0x4e when the class is wrong — the earlier "no gate" audit note was incorrect. Disassembly 2026-10-27. |
| 18 | KEX Lapse (`aio_multi_delete`, 11.00-12.02 family) / KEX Poops (12.50-13.00) as-is | **CLOSED (superseded by row 1)** | Those chains call into the same gated wait-side family; the 14.00 closure of the wait covers them. |

**The pattern across all rows:** 14.00 did not add bugs — it added
**gates at the browser's kernel frontier**. The leads that remain open
(`07-next-leads.md`) are exactly the surfaces the gates do not cover:
ioctl-only device doors, unauthenticated IPC (from the right process
class), and other processes' parsers.
