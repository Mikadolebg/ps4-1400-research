# WebKit 14.00 offsets (browser process)

All offsets are RVAs inside `libSceWebKit2` (the browser's WebKit
module). The engine is **frozen**: 13.00, 13.50, 13.52 and 14.00 ship
the same WebKit build (`616.1.27.211.1`, Sony's last LGPL drop being
the 13.00-era source; see `docs/01-entry-ssv/frozen-engine.md`), so
these hold across that whole range — verified live on 14.00.

## Module base leak — the pair-gap door

The base is derived from two JS builtins whose native executable cells
sit at a **fixed delta** from each other:

| Anchor | RVA | How it is reached |
|---|---|---|
| `Math.expm1` builtin executable | `0x2586880` | addrof(`Math.expm1`) → cell +0x18/+0x10 → native executable → +0x28 |
| `parseInt` builtin executable | `0x2586880 − 0x24B0C20` = `0xD5C60` | a holder object leaks the cell by slot (`core.js` holder shape) |

Measured invariant (live, both boots): `delta = s28(expm1) −
s28(parseInt) = 0x24B0C20` exactly, both anchors in the same 4 GB
region, base 0x4000-aligned → **base = s28(expm1) − 0x2586880**.
The POC prints this as `BASE-PAIR-GATE-PASS` / `BASE-LOCKED`.
(An earlier offline study pinned the same pair through the residues:
s18 trampoline residue `0x5e8 mod 0x4000`, K28−K18 = 0xC25F8 across 26
console samples — superseded by the direct pair door.)

## Key module offsets

| Offset (RVA) | Meaning |
|---|---|
| `0x3CB8CC8` | `__imp___error` GOT slot — dereference gives `__error` in libkernel, the anchor of the stub window |
| `+0x28` (JSFunction cell) | `m_function` field — the fcall trigger slot (`Math.expm1`'s cell is armed with the gadget chain) |
| `+0x18` / `+0x10` (JSFunction cell) | native-executable links used by the leak probes |

## The verified ROP gadget set (15)

Gadget RVAs and their byte signatures — every one is **verified at
runtime, byte by byte**, through the R/W primitive before use (the
`GADGET-GATE` marker; the REX-prefixed gadgets additionally accept the
REX-equivalence class, hardened against encoding variants). If a byte
fails, the gadget is repaired by scanning ±0x8000/±0x20000 around the
old RVA for the signature — and dumped for audit.

| Gadget | RVA | Bytes |
|---|---|---|
| POP_RDI_RET | `0x5C480` | `5f c3` |
| POP_RSI_RET | `0x6E45E` | `5e c3` |
| POP_RDX_RET | `0x12C5BA` | `5a c3` |
| POP_RCX_RET | `0x1BADE` | `59 c3` |
| POP_R8_RET | `0x9B311` | `41 58 c3` (REX-verified, hardened) |
| POP_R9_RET | `0x1DCFB1` | `41 59 c3` (REX-verified, hardened) |
| POP_RAX_RET | `0x10504` | `58 c3` |
| LEAVE_RET | `0x182F7` | `c9 c3` |
| MOV_RDI_RAX_RET | `0x548B` | `48 89 07 c3` |
| G0 | `0x295F948` | `48 8b 7e 30` (mov rdi,[rsi+0x30]; call …) |
| G1 | `0x1D989E3` | `58 48 8b 07` (pop rax; mov rax,[rax]; jmp [rax+0x18]) |
| G2 | `0x25BAE0` | `55 48 89 e5` (push rbp; mov rbp,rsp …) |
| G3 | `0x4A0406` | `48 8b 78 08` (mov rdi,[rax+8]; call [rax+0x20]) |
| G4 | `0x1EC3ADA` | `48 8b 50 38` (mov rdx,[rax+0x38]; call [rax+0x10]) |
| G5 | `0x2ABCCAA` | `52 5c c3` (push rdx; pop rsp; ret) |

The fcall machinery (pivot/stack/frame layout built from G0..G5,
argument marshalling through the POP_* gadgets) is documented in
`docs/02-userland-chain/` and lives in `poc/poc.html`.

## Facts for exploit/payload authors (measured on console)

- Browser memory ceiling ≈ **80 MB** (the 5M-slot carrier = 40 MB, plus
  groom drain; full success at n≤512 drains ≈ 77 MB total, death at
  640/1024). The carrier is **never** reduced below 5M.
- The browser runs on **cores 6-7**; `cpuset_setaffinity` (487/488)
  pins a thread to one core — required for per-CPU UMA reclaim work.
- A `mmap` **hint without `MAP_FIXED`** returns the exact requested
  address when the range is free (`0x04000000` scratch page door);
  `MAP_FIXED` at those addresses is refused.
