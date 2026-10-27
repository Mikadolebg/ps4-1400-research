# Audit: bnet `raise` — the write-UAF (N1)

**Terrain:** the bnet error-raising path (network stack), 13.52 clear
kernel; browser-reachable through 4 real stubs (97 `socket`, 98, 99
`netcontrol`, 114 `close`).
**Method:** instruction-level audit of the network+GPU stacks, confirmed
byte-exact; then — **2026-10-27 — the entry chain was proven LIVE on a
stock 14.00 console** through the armed workshop (probe driven over the
bridge; sequence below).
**Status: OPEN — the netevent chain is armed from the browser on 14.00
(the prerequisite of the UAF is in place); the race itself remains to be
played (accepted panic risk).**

## On-device proof (2026-10-27, stock 14.00 browser)

Corrected ABI (the original internal design had it swapped — this was
why the earlier on-device attempt failed): `netcontrol(id, cmd, ptr,
len)`, and the voluntary-raise command is **0x20000010** (not
0x10000010):

| Step | Call | Result |
|---|---|---|
| socket | `sysc(97,[2,1,0])` | fd=6 |
| id sweep | `netcontrol(i, 0x20000010, buf, 4)` — NULL-safe raise | **ids 1-4 alive (raise ran); 5-8 absent** |
| REGISTER | `netcontrol(1, 0x20000003, {fd}, 8)` | **0 — our queue registered, owner = our socket, no reference taken** |
| RAISE | `netcontrol(1, 0x20000010, buf, 4)` | 0 |
| SENSOR | `netcontrol(1, 0x10000002, kbuf{fd}, 0x20)` | **0; events = 0x4, qid = 6** |

`events = 4` is the literal mask the raise handler writes when
`ifnet+0xa4 == 2` (`mov esi,4` @+0x1e1046): **the raise ran on OUR
queue with OUR socket as the owner — on 14.00, from the browser.**
No gate anywhere on the path (unlike the aio wait / named IPC / 622).

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

## The KASLR-free proof of touch (played 2026-10-27 — see above)

The register + voluntary raise + sensor sequence just played on 14.00 IS
that proof: the sensor read back the accumulated event mask of OUR queue
(`events = 0x4`), establishing that the write path exists and is
reachable from the browser's stubs, with zero crash risk. The race (free
the socket under the window, spray the UMA zone) is the remaining step.

## Session 2 (2026-10-27, later) — the close path measured, the lottery quantified

Follow-up probes the same night settled the remaining questions:

- **The purge DOES run at close.** After `close(fd)`, the registered
  queue no longer accumulates events under heavy traffic (sensor reads
  stay 0) — Sony's double-free fix works as designed. The earlier
  static suspicion ("purge never runs because nothing writes the
  +0x76 marker") was wrong: the marker is set by a path my byte scans
  (no REX/SIB encodings) missed. **There is no deterministic dangling
  owner** — the preemption lottery is the only door, exactly as the
  original design rated it.
- **The notification's indirect call is NULL-gated**: the raise's
  post-write notify only does `call rax` when `[owner+0x180] != 0`
  (verified at +0x1e66bd). Bare, never-selected sockets have it NULL
  -> a race WON on our own throwaway blocks would be benign by
  construction (word 4 at +0x70, cmpxchg at +0xf8, no indirect call).
- **Measured loop rate**: ~3000 socket/register/close iterations per
  second through the armed ROP series (500 iterations in 169 ms).
- **Measured raise pressure**: traffic XHR bursts drove masks like
  `0x2010000d` into our queue (many distinct event sources).
- **Lottery odds, honestly computed**: the raise's [owner-read ->
  write] gap is ~1 ns; the free needs the raise thread descheduled
  exactly there -> ~1e-6 per overlapping raise, ~1e-8 per iteration.
  At 3000 iter/s that is ~1e-4 wins/s — hours of tight looping per
  coin flip, and only on the traffic-bearing ifnet.
- **New phenomenon — ifnet slot wedging**: after intensive
  register/close churn, ifnet 1's three queue slots stopped accepting
  registrations (every `REGISTER` returns the impl's literal -1),
  while ifnets 2-4 still accept and cleanly unregister. Recovery
  requires a console reboot; root mechanism not yet isolated (open
  question, next session).
- **Clean UNREGISTER proven on device**: `netcontrol(id, 0x20000007,
  {fd}, 8)` round-trips 0/0 on a fresh ifnet — the hygiene call for
  any future race harness.

## Next-session plan (measured, not guessed)

1. Reboot the console (clears the wedged ifnet-1 slots).
2. Volume lottery on ifnet 1: in-page tight loop (3000 iter/s
   measured) with traffic bursts, batches with health checks between.
   Odds ~1e-8/iter — decide the time budget with the numbers above; a
   win on our own blocks is benign (NULL-gated notify) and the signal
   is a state-dependent errno anomaly on the reoccupied socket.
3. In parallel, isolate the slot-wedging mechanism (a second bug
   candidate in itself: a resource-exhaustion / refcount path in the
   netcontrol register machinery).
