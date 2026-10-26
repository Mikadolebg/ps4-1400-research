# extraction/ — everything captured from the console

This folder receives **every binary the console pages stream to the
host's `/dump/` endpoint**. It is local-only (git-ignored; this README
is the only tracked file in here). The logs and verdict markers live
separately in `runs/`.

## The one-click extractions (buttons on the workshop page, or
`{"t":"extract","what":...}` over the bridge)

| File | What it is | How it was produced | Size |
|---|---|---|---|
| `libkernel-window.bin` | The libkernel window `[__error, +0x6A000)` — the browser's syscall stub table lives at `+0x52B0..+0x7A00` and the bare `syscall; ret` errno gadget at `+0x6A2A`. Regenerate `data/syscalls/stubs-1400.csv` from it with `tools/extraction/extract-stubs.py`. | button `EXTRACT - libkernel window` / `{"t":"extract","what":"libkernel"}` | ~424 KB |
| `stubzone.bin` | Just the dense stub zone (`+0x52B0..+0x7A00`) — the fast version of the above. | button `EXTRACT - stub zone only` / `{"t":"extract","what":"stubzone"}` | ~9 KB |
| `webkit-text.bin` | The low 2 MB of the libSceWebKit2 text (module base = byte 0) — covers the low-RVA gadget set of `data/offsets/webkit-1400.md`. Verify offline with `tools/extraction/extract-gadgets.py webkit-text.bin --rva 0x0`. | button `EXTRACT - WebKit text slice` / `{"t":"extract","what":"webkit"}` | 2 MB |
| `anchor-expm1.bin`, `anchor-parseint.bin` | The two builtin anchors of the base-leak pair door (RVAs `0x2586880` / `0xD5C60`). | button `EXTRACT - proof anchors` | 0x100 each |
| `anchor-imp-error.bin` | The `__imp___error` GOT slot (RVA `0x3CB8CC8`) — dereferencing it gives the libkernel `__error` anchor of every stub offset. | same | 8 B |
| `anchor-base-start.bin` | The first 0x200 bytes of the WebKit module (header proof of the locked base). | same | 0x200 |
| `stub-getpid.bin`, `errno-gadget.bin` | The getpid stub (`__error+0x6CF0`) and the bare `syscall; ret` gadget (`__error+0x6A2A`), byte-proof of the two addresses the tooling calls. | same | 0x20 / 0x10 |

## The per-run evidence dumps (automatic, every session)

The pages dump their own proofs as they run — you will also find here:

- `gadg-<NAME>.bin` (0x10 each): the runtime bytes of every verified
  gadget (written by the gadget gate on each run);
- `stub-aio-*.bin`, `stub-setsockopt.bin`, `stub-socket.bin` (0x20):
  the byte-verified stubs before the aio sequence;
- `fcall-store/pivot/stack/frame.bin` (0x40): the ROP context snapshots;
- `aio-node0.bin`, `aio-arena.bin`: the sprayed/waiter structures of the
  KEX replay (`tools/workshop/kex-aio.html`);
- `expm1-anchor.bin`, `parseint-anchor.bin`, `base-start.bin`,
  `imp-error.bin`: the leak-layer anchors.

## Reminders

- Offsets inside a file are **relative to that file's start** (the
  server refuses absolute-looking offsets: > 4 MB).
- Extractions read through the armed primitive: they need the workshop
  at `WORKSHOP-READY` (see `REPRODUCE.md` §5). The libkernel window
  takes a few minutes; the status line on the page follows the progress.
- Nothing here is committed. Share a dump via a GitHub Release if you
  want others to reproduce your table (the scene norm).
