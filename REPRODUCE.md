# Reproducing the POC on your console

What you need:

- a PS4 on **firmware 14.00** (stock — the whole point is that nothing
  is jailbroken yet), web browser usable, on the same LAN as your PC;
- a PC with **Python 3** (and, for the offline selftests, Node.js);
- 15 minutes.

## 1. Start the host

```
tools\host\start.bat          (Windows)
sh tools/host/start.sh        (Linux/macOS)
```

The launcher auto-detects your LAN IP, starts the WebSocket bridge
(port 8001) and the server (port 8000), and prints the URL.
Manual alternative: `python tools/host/server.py` alone is enough for
the POC (the bridge is only used by the workshop).

Optional pre-flight: `node tools/qualif/selftest-repo.js` — every unit
must be green before a console session.

## 2. Open the menu on the console

On the PS4 browser, open the printed URL (`http://<pc-ip>:8000/`).
You get the menu: **POC**, **WORKSHOP**, **KEX AIO**.

Ritual (it matters — see the memory laws below): **clean browser**
(close old tabs first), menu, click. A miss = reload the page. A crash
= close the browser entirely, reopen, come back.

## 3. Run the POC

Pick **POC**. The page runs the chain stage by stage; each verdict
marker appears on the console screen AND in the server log. Expect, in
order (glossary: `data/markers.md`):

```
1-BOOT ...                       session start
SSV-BUILD / SSV-STORED / SSV-RETURNED-CLEARED
ADDROF-RETURNED / ADDROF-POINTERS
GENUINE-U8-RW-PASS               <- arbitrary R/W works
ARBITRARY-READ-PASS / ARBITRARY-WRITE-PASS
LEAK-BOOT ...
BASE-PAIR-GATE-PASS              <- the pair delta matched
BASE-LOCKED webkit=0x...         <- exact WebKit base (delta 0x24B0C20)
FCALL-BOOT / GADGET-GATE-PASS 15/15
FCALL-STUB-EXACT ...
FCALL-SERIES-ARMED
FCALL-SERIES-DISARMED mf=RESTORED pivot=RESTORED
SYSCALL-PASS getpid(20)=...      <- THE PROOF: a syscall ran
FCALL-EXPM1-RESTORED
FCALL-DONE verdict=FCALL-GETPID-OK
```

On the PC side the same lines land in `runs/last-verdicts.txt`, and
binary evidence (stub bytes, gadget bytes, the anchors) in
`runs/dumps/`.

**That is the userland chain reproduced: entry, R/W, base leak, ROP,
arbitrary syscall.** From here, `SYSCALL-PASS` for any number in
`data/syscalls/stubs-1400.csv` follows the same pattern — which is
what the workshop does interactively.

## 4. The operating laws (measured — breaking them wastes sessions)

- **One arm->calls->disarm cycle per browser session.** The ROP series
  is armed once; a second series in the same session is refused. To
  re-run anything: reload the page. After a crash: close and reopen
  the browser (the auto-ladder reloads benign misses for you).
- **The carrier is 5M slots / 40 MB, never less.** If the page hits an
  out-of-memory loop: close and reopen the browser.
- **The browser gets ~80 MB and cores 6-7.** Big allocations belong to
  the carrier, not to spray experiments.
- **Read `data/syscalls/DANGEROUS.md` before probing numbers by hand.**

## 5. The live workshop (optional, recommended)

1. Start the host with the bridge running (`start.bat` does both).
2. On the console menu pick **WORKSHOP** -> the thin boot page appears,
   connects to the PC (`CONNECTED`), then arm with the button (or from
   the PC: `{"t":"arm","slots":5000000,"n":512}` appended to
   `bridge/commands.jsonl`).
3. The console page takes over: expect `ERRNO-GADGET-OK`,
   `BRIDGE-OPEN`, `WORKSHOP-READY`, then a heartbeat every 5 s.
4. Drive it from the PC (one JSON line per command):

```
echo {"t":"ping"} >> bridge/commands.jsonl
echo {"t":"selftest"} >> bridge/commands.jsonl
echo {"t":"walk","path":"/dev"} >> bridge/commands.jsonl
echo {"t":"sysc","num":20,"args":[],"raw":true} >> bridge/commands.jsonl
```

Results stream back into `bridge/results.jsonl`; file exports land in
`bridge/files/`. The page stays armed for the whole session — leave it
open and work from the PC.

5. **One-click extraction.** The workshop page has EXTRACT buttons
(the libkernel stub table, the stub zone only, the WebKit text slice,
the proof anchors): each streams the memory range through the armed
primitive and assembles the file in **`extraction/` on the PC**
(progress on the page status line; the same targets work over the
bridge: `echo {"t":"extract","what":"libkernel"} >>
bridge/commands.jsonl`). What each file is and what to run on it:
`extraction/README.md`.

## 6. The aio KEX reproduction (optional)

Pick **KEX AIO** on the menu. The page plays the scene's exact P1->P5
sequence. On 14.00 the deterministic outcome is
`AIO-WALK`-absent -> **`AIO-LIVE-NO-RECLAIM`** with
`AIO-WAIT-CALIB` showing the wait returning instantly (the gate
evidence — `docs/05-audits/aio-kex.md`). The page exists so that the
day a firmware round re-enables the wait, the same file becomes the
kernel exploit unchanged.
