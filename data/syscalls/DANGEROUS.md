# DANGER list — read before probing

Measured on live consoles (10.50 / 13.52 / 14.00). Everything here was
learned the hard way; do not relearn it.

## Instant process kill (14.00)

- **622 `sys_ipmimgr_call`** — the module's lifecycle commands
  (0, 1, 2, 3, 5, 0x400, 0x465) **kill the calling process at handler
  entry, input-independently**. Not an error return: the process dies.
  Verified twice (clean Lua, then ROP with positive controls). The
  browser tab closes. Nothing persistent — but the session is gone.

## Kernel crash (console reboot)

- **189 `fstat`** — live 13.52 console, stock browser context: **kernel
  crash**. Use **551** (the STD variant) instead: clean `-1`.
- **Sweeping the 500-550 number range** — a blind scan of 500..550
  crashed the console (measured once, never repeated). Probe syscall
  numbers ONE at a time, never in a loop over that range.
- **625/626 `opmc_set_hw`/`opmc_get_hw`** — raw `wrmsr`/`rdmsr` with no
  gate (13.52 audit). `wrmsr` on an absent MSR is a plausible panic.
  Do not touch from the browser.
- **Reading an address you have not confirmed mapped** — a speculative
  read of an unmapped page (`0x04000800` before the mmap returned) is a
  SIGSEGV the page's try/catch cannot catch; two crashes taught this.
  Verify by return value first, read second.

## Session-burners (not crashes, but you lose the armed chain)

- **More than one arm→calls→disarm cycle per browser session** —
  `m_function` is armed once; the whole session gets ONE series
  (`docs/02-userland-chain/`). Reload the page for a new session.
- **`MAP_FIXED` at the low scratch addresses** — refused on 14.00; use
  the hint-without-`MAP_FIXED` door instead.
- **Named IPC creation from the browser** (538-546, 549-556) — fails at
  entry on 14.00; do not burn a ROP series retrying it (the gates table
  is already measured, `gates-1400.csv`).
