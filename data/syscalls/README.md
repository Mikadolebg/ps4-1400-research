# Syscall data

| File | What it is |
|---|---|
| `stubs-1400.csv` | The **14.00 browser syscall table**: every syscall stub exported by libkernel to the browser process, mapped from a live console memory dump (regenerate with `tools/extraction/extract-stubs.py`). |
| `syscalls-1352.csv` | The named syscall handlers of the **13.52 kernel** (clear-kernel ground truth: nr → handler name → file offset). |
| `names-1352.json` | 684 syscall **names** extracted from the strings of the 13.52 kernel itself — the best name source for the Sony number space. Used to annotate `stubs-1400.csv`. |
| `syscalls-1050.csv` | The full **10.50 kernel syscall table** (701 entries) produced by disassembly of the clear 10.50 kernel: nr, handler offset, arg count, name, status. The long-term reference for what each number *is*. |
| `freebsd9-syscalls.master` | The official FreeBSD 9 `syscalls.master` (© The FreeBSD Project, BSD license) — the upstream numbering Sony's table derives from. |
| `gates-1400.csv` | **Measured gate status** per syscall family on the 14.00 browser process: what works, what is gated, what kills, with evidence pointers. |
| `DANGEROUS.md` | Calls that crash or kill. Read before probing. |

## About `stubs-1400.csv` (the 302 vs 298 numbers)

The 12-byte stub signature (`48 c7 c0 <nr32> 49 89 ca 0f 05`) occurs
**302 times** in the libkernel window dump. **298** of those are the
exported stub table (each one live-verified byte-exact by the workshop
console before any call — see `tools/workshop/console.html`,
`STUB_TABLE`). The other **4** hits (syscall numbers 1, 59, 340, 454)
are the same byte sequence occurring *inline* inside other functions;
the `classic_stub_tail` column (the `72 01 c3` lazy-binding tail) marks
the classic stubs — 293 of the 298 carry it, a handful of real stubs
use a different return path, so treat that column as informational.

Offsets are relative to the start of the dump window, i.e. relative to
the `__error` function of libkernel (`__imp___error` dereferenced from
WebKit — see `data/offsets/webkit-1400.md`).
