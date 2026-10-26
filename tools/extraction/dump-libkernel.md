# Dumping your own libkernel window (14.00 browser)

The browser syscall table (`data/syscalls/stubs-1400.csv`) and the
errno gadget live in a window of **libkernel** starting at its `__error`
function. This document is the recipe that produced our dump from a
stock 14.00 console — the same dump you can regenerate with the armed
workshop. No kernel access is involved: it is userland memory of the
browser process, read through the proven R/W primitive.

## The easy way: one click (or one command)

The workshop console ships the extraction built in. Once armed
(`WORKSHOP-READY`):

- on the **PlayStation page**: the `EXTRACT - libkernel window` button
  (progress on the status line; the file assembles in
  `extraction/libkernel-window.bin` on the PC);
- from the **PC**, over the bridge:

```sh
echo {"t":"extract","what":"libkernel"} >> bridge/commands.jsonl
```

The other buttons / `what` values, **one per target** (press when you
want, nothing runs on its own): `stubzone` (just the dense zone, fast),
`webkit` (the low 2 MB of WebKit text — the gadget set), and each proof
anchor separately (`anchor-expm1`, `anchor-parseint`, `anchor-imp-error`,
`anchor-base-start`, `stub-getpid`, `errno-gadget`). The full file map
of `extraction/` lives in `extraction/README.md`.

## How the window is located at runtime

1. The chain runs (see `REPRODUCE.md`) with the **workshop console**
   armed (`tools/workshop/console.html`).
2. WebKit's `__imp___error` GOT slot (RVA `0x3CB8CC8` in
   libSceWebKit2) is dereferenced → the address of `__error` **inside
   libkernel**. That address is the anchor; every stub offset in the
   table is relative to it.
3. The window of interest is `[anchor, anchor + 0x6A000)` (~424 KB):
   the dense stub table zone sits at `+0x52B0..+0x7A00`, the bare
   `syscall; ret` errno gadget at `+0x6A2A`.

## The manual way (the eval recipe, equivalent to the button)

With `bridge.py` running and the workshop armed, push this through the
bridge (one JSON line per command in `bridge/commands.jsonl`):

```json
{"t":"eval","code":"(function(){var s=0x6a000,ch=0x400,n=0;for(var o=0;o<s;o+=ch){var h='';for(var i=0;i<ch;i++)h+=('0'+ext_read8(LIBK_ERRORFN+o+i).toString(16)).slice(-2);(function(off,hh){var x=new XMLHttpRequest();x.open('GET','/dump/libkernel-window/'+off.toString(16)+'/'+hh,true);x.send()})(o,h);n++}return 'chunks='+n})()"}
```

What it does: walks the window in 1 KB chunks, hex-encodes each chunk
through `ext_read8` (the R/W primitive) and streams it to the server's
`/dump/` endpoint, which assembles `extraction/libkernel-window.bin`
(offsets are relative — the server guards against absolute-address
mistakes). ~424 chunks, a few minutes at heartbeat cadence.

Notes:

- `LIBK_ERRORFN` is already defined by the armed console page (the
  anchor from step 2). In a fresh `eval` context use `window.LAB` /
  the page's globals as shipped.
- The XHRs are async and lossless-by-offset: chunks may arrive out of
  order; each carries its own offset.
- Keep the page armed: the read primitive is the carrier — do not
  reload mid-dump.

## Then: regenerate the table

```sh
python tools/extraction/extract-stubs.py extraction/libkernel-window.bin \
    --verify-console-table
```

produces the stub CSV from **your** dump and cross-checks the 298
live-verified entries (see `data/syscalls/README.md` for the
302-hits / 298-stubs story and the 4 inline-sequence duplicates).

## Dumping the WebKit gadget set

The gadget verification happens at runtime on every run
(`GADGET-GATE`). To audit it offline, dump a slice of WebKit text the
same way (the base is known from `BASE-LOCKED`; e.g. window
`[base+0x0, base+0x400000)` via the same `/dump/` streaming with the
anchor changed to the module base), then:

```sh
python tools/extraction/extract-gadgets.py extraction/webkit-text.bin --rva 0x0
```
