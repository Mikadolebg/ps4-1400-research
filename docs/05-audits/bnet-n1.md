# Audit: bnet `raise` — the write-UAF (N1), never tested on console

**Terrain:** the bnet error-raising path (network stack), 13.52 clear
kernel; browser-reachable through 4 real stubs (97 `socket`, 98, 99
`netcontrol`, 114).
**Method:** instruction-level audit of the network+GPU stacks; the
finding was confirmed byte-exact at the disassembly level and
cross-checked against the live reachability measurements.
**Status: OPEN — designed, never played on hardware. The strongest
untested in-browser kernel lead, and the hardest to land.**

## The bug (byte-exact)

The error-raising routine at `raise @ 0x1e02e0`:

1. captures its **owner** (a socket struct — UMA zone 0x478) under
   locks;
2. releases the locks;
3. **then writes** through the captured pointer, unreferenced:
   - word `4` at `owner + 0x70`,
   - word `0xa5` at `[owner + 0x360] + 0x70`.

If the socket is freed between (1) and (3) — or if `+0x360` can be
made to point into attacker-controlled memory — this is a **kernel
write primitive from the browser**, with fixed values at fixed
offsets.

## The honest cost

The window between lock release and the writes is **~15 bytes of
code** — a preemption lottery, not a schedule-friendly race. The
design doc rates it exactly that: high value, low probability per
attempt, deterministic *proof* available before any exploitation
attempt.

## The KASLR-free proof of touch (the first probe, never run)

Command shape `0x10000002` on a socket we own: if the write lands in
**our own** socket's field (no race, no free needed), the proof reads
back the touched value through normal socket state — establishing the
write path exists and is reachable from the browser's 4 stubs, with
zero crash risk. Only after that proof does the race (free the socket
under the window, spray the UMA zone) make any sense.

## Why it survived the 14.00 gates

The 4 stubs it needs are **not gated** (the socket infrastructure
works — the aio sequence uses it heavily). The hardened frontier on
14.00 (gates table) does not cover this path; only hardware time
does.
