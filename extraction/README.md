# extraction/ — ONLY the extractions you chose

This folder receives **exactly what you picked, file by file**: every
extraction started by a workshop button or a bridge `extract` command,
and nothing else. It is local-only (git-ignored; this README is the
only tracked file in here).

**Nothing lands here on its own.** The automatic proof dumps the chain
produces during every run (the byte-verified gadgets, stubs, ROP
context...) go to a separate folder — `runs/evidence/` — so what you
see here is always the result of your own clicks.

## The one-click extractions (one button = one target, on the workshop
page; or `{"t":"extract","what":...}` over the bridge)

| File | What it is | How it was produced | Size |
|---|---|---|---|
| `libkernel-window.bin` | The libkernel window `[__error, +0x6A000)` — the browser's syscall stub table lives at `+0x52B0..+0x7A00` and the bare `syscall; ret` errno gadget at `+0x6A2A`. Regenerate `data/syscalls/stubs-1400.csv` from it with `tools/extraction/extract-stubs.py`. | button `libkernel window` / `what=libkernel` | ~424 KB |
| `stubzone.bin` | Just the dense stub zone (`+0x52B0..+0x7A00`) — the fast version of the above. | button `stub zone only` / `what=stubzone` | ~9 KB |
| `webkit-text.bin` | The low 2 MB of the libSceWebKit2 text (module base = byte 0) — covers the low-RVA gadget set of `data/offsets/webkit-1400.md`. Verify offline with `tools/extraction/extract-gadgets.py webkit-text.bin --rva 0x0`. | button `WebKit text slice` / `what=webkit` | 2 MB |
| `anchor-expm1.bin` | The `Math.expm1` builtin anchor of the base-leak pair door (RVA `0x2586880`). | button `anchor: expm1` / `what=anchor-expm1` | 0x100 |
| `anchor-parseint.bin` | The `parseInt` builtin anchor (RVA `0xD5C60`) — the pair closes at delta `0x24B0C20`. | button `anchor: parseInt` / `what=anchor-parseint` | 0x100 |
| `anchor-imp-error.bin` | The `__imp___error` GOT slot (RVA `0x3CB8CC8`) — dereferencing it gives the libkernel `__error` anchor of every stub offset. | button `anchor: __error GOT` / `what=anchor-imp-error` | 8 B |
| `anchor-base-start.bin` | The first 0x200 bytes of the WebKit module (header proof of the locked base). | button `anchor: module start` / `what=anchor-base-start` | 0x200 |
| `stub-getpid.bin` | The getpid stub (`__error+0x6CF0`) — byte-proof of the canonical first syscall call. | button `stub: getpid` / `what=stub-getpid` | 0x20 |
| `errno-gadget.bin` | The bare `syscall; ret` gadget (`__error+0x6A2A`) behind the positive-errno reads. | button `gadget: errno` / `what=errno-gadget` | 0x10 |

Each button extracts exactly one thing, whenever you press it (the
chain stays armed the whole session; nothing extracts on its own). The
buttons unlock at `WORKSHOP-READY` — the status line under them says
so.

## The automatic per-run evidence (NOT here — runs/evidence/)

The pages dump their own proofs as they run — you will find those in
**`runs/evidence/`**, not here:

- `gadg-<NAME>.bin` (0x10 each): the runtime bytes of every verified
  gadget (written by the gadget gate on each run);
- `stub-aio-*.bin`, `stub-setsockopt.bin`, `stub-socket.bin` (0x20):
  the byte-verified stubs before the aio sequence;
- `fcall-store/pivot/stack/frame.bin` (0x40): the ROP context snapshots;
- `aio-node0.bin`, `aio-arena.bin`: the sprayed/waiter structures of the
  KEX replay (`tools/workshop/kex-aio.html`);
- `expm1-anchor.bin`, `parseint-anchor.bin`, `base-start.bin`,
  `imp-error.bin`: the leak-layer anchors.

That split is deliberate: `extraction/` answers "what did I ask for",
`runs/evidence/` answers "what did the chain prove this session".

## Reminders

- Offsets inside a file are **relative to that file's start** (the
  server refuses absolute-looking offsets: > 4 MB).
- Extractions read through the armed primitive: they need the workshop
  at `WORKSHOP-READY` (see `REPRODUCE.md` §5). The libkernel window
  takes a few minutes; the status line on the page follows the progress.
- Nothing here is committed. Share a dump via a GitHub Release if you
  want others to reproduce your table (the scene norm).
