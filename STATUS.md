# PS4 14.00 — Exploit Status: Userland WORKING, Kernel is the Missing Link

**TL;DR:** The public SSV WebKit entry gives full userland R/W + arbitrary syscalls on 14.00, proven repeatedly on console. The scene's aio (663) kernel exploit is closed on 14.00 — deterministic evidence below. Several unexplored kernel doors remain open (device ioctls visible from the browser). What's missing for a 14.00 jailbreak is exactly one thing: a kernel primitive.

> This file is the canonical status declaration of this repository.
> Everything it claims is backed by a tool or a document shipped here:
> evidence pointers inline. Last updated: 2026-10-26.

## 1. Userland — complete and proven (15+ full boots on console)

**Entry: the SSV (SerializedScriptValue) bug** (public since 13.04/13.52, Jordy/zecoxao family). The WebKit serializer does not pool BigInts; the deserializer does. A duplicated reference makes the pool index get written on 2 bytes but read on 4 → `-2` signed in `MarkedVector::at()` → `m_buffer[-2]` = groomed predecessor → fake `Uint8Array` cell in raw-fields mode → **arbitrary userland R/W**.

**Why it works on 14.00:** the engine is frozen. Sony's last LGPL source drop is the 13.00-era WebKit (616.1.27.211.1); zero browser changes after. 13.00 → 14.00 share the same engine — Sony patched the kernel side, not the entry. (Full documentary proof: `docs/01-entry-ssv/frozen-engine.md`.)

**Chain proven live on 14.00** (reproduce it yourself: `poc/poc.html` + `REPRODUCE.md`):
- addrof / fakeobj (host/target pointer leak)
- WebKit base leak via the pair-gap door (delta `0x24B0C20`, stable across boots)
- ROP: 15 gadgets, byte-verified at runtime
- **Arbitrary syscalls**: 302 libkernel stubs mapped from a live console dump (`48 c7 c0 <num> 49 89 ca 0f 05` signature — regenerate the table with `tools/extraction/extract-stubs.py`); a 398-syscall series ran cleanly
- `mmap` hint trick: a hint **without** `MAP_FIXED` returns the exact address if the range is free (the scene's scratch page at `0x04000000` is obtainable this way — `MAP_FIXED` itself is refused)
- UMA pinning works: `cpuset_setaffinity` (487/488) ungated; browser thread restricted to cores 6–7

## 2. Kernel — the aio (663) KEX is closed on 14.00

Ported the scene's exact P1→P5 sequence (scratch page, immortal group, rthdr spray, timing, even the per-CPU UMA pinning from `jb.js`). Result, deterministic across 7 runs / 2 boots (replay it: `tools/workshop/console.html`, verdict markers `AIO-*`):

- `aio_submit_cmd` (669), `aio_multi_cancel` (666), `poll` (664), `delete` (662) → all return 0. **Handlers are alive.**
- `aio_multi_wait` (663) → **immediate error, never sleeps**. Tested with 1 ms and 100 ms timeouts: returns in ~4–6 ms (pure ROP overhead), statuses stay 0. No waiter is ever created → no UAF lifetime → the reclaim can never land.
- Conclusion: the wait — the exact syscall that builds the vulnerable waiter — is gated on 14.00. This is consistent with the scene never porting its 13.52 host to 14.00. (Exact errno identity — EPERM vs context-init failure — readable with the raw `syscall;ret` errno gadget exposed by the workshop's `sysc {raw:1}` command.)

## 3. Other measured gates (browser process, 14.00)

- **Named IPC is closed**: `evf_*` (538–546) and `osem_*` (549–556) fail at entry — even creating your **own** named event flag fails; 150 system-object names x both families = 0 opened. Note: the kernel-side global registry itself has **no authentication** (13.52 disassembly) — the gate is at syscall entry for webkit-class processes. It would still work from any non-gated process.
- Devices: classic nodes EPERM, **but see §4 — `/dev` is not fully blind.**
- Full per-family measured status: `data/syscalls/gates-1400.csv`.

## 4. Open doors (untested publicly — leads)

- **`/dev` visible nodes**: `dipsw`, `random`, `urandom` (LNK), **`dmem0`**, **`dce`**, `rng`. **`open("/dev/dipsw")` succeeds** (fd obtained; read fails — ioctl-only device). Its ioctl entry check, decoded from the 13.52 kernel: proceeds when `cred+0x60` bit 62 == 0 — i.e. **non-system processes, including the browser**. Command window: `0x80028800..0x80108804`. Never tested anywhere.
- **`/system_tmp`** contains live UNIX sockets: `mdbg0_dbgp`, `GnmCompositor`, `GnmCompositorRestricted`, `gpvdec_arbitrator`, `gpvdec_proxy`, `gpvenc_proxy`.
- Browser prison FS = root + 5 mounts (`/dev`, `/system_tmp`, `/user`, `/av_contents`, + one random-named dir); ~31 standard paths invisible.
- Facts for payload authors: browser memory ceiling ≈ **80 MB** (5M-slot carrier = 40 MB + groom drain); browser gets **2 cores** (6,7); `random`/`urandom` readable **and writable** from the prison.

## 5. Bottom line

14.00 needs **one kernel primitive**. Everything above it — entry, R/W, leak, ROP, syscalls, tooling — is done and reproducible. The gated paths (aio wait, evf/osem) show Sony hardened the browser's kernel frontier on 14.00; the untested device doors (`dipsw` ioctl window, `dmem0`, `dce`, the `/system_tmp` sockets) are where we're looking next. Ranked list with everything we know per lead: `docs/07-next-leads.md`. Closed leads and why: `docs/06-negative-results.md`.
