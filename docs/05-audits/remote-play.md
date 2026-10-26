# Audit: Remote Play — the second front (non-browser process class)

**Terrain:** the console-side Remote Play daemon (`NPXS21006`, whose
clear ELF we hold), its LAN-facing channels: UDP 987 (discovery) and
TCP 9295 (registration/control), plus the streaming stack (takion).
**Method:** protocol reconstruction from the daemon's disassembly and
the reference open-source client (chiaki family) as semantic
corroboration; a purpose-built fuzz harness run against the live
console.
**Status: the bench works (576 cases, 0 crashes); the deep channels
need the console in PIN-pairing mode. A genuinely open front.**

## What is exposed without pairing (measured)

- **UDP 987 wakeup/discovery** — broadcast-reachable, parser on the
  daemon side.
- **TCP 9295 registration** — accepts connections pre-pairing. Our
  fuzz round produced a **deterministic 403** with
  `RP-Application-Reason: 80108bff` on every malformed/registered
  probe; server-side timeout measured at **15.0 s**; the daemon stayed
  alive through all 576 cases (22/22 liveness probes).
- The **ctrl/takion** channels refuse pre-login (PIN wall) — that is
  where the fat parsers (session control, video stream setup) live.

## The fuzz bench (reusable)

`python rp_fuzzer.py --host <console-ip> --seed 20261015` style
invocation against a console in Remote Play mode; deterministic
seeds, liveness probing between rounds, JSONL case log. Run 1 (13
minutes, 576 cases): zero crashes, zero resets — a negative result
that validates the harness rather than closing the surface.

## Why this front matters strategically

Every closed browser-class gate (`06-negative-results.md`) leaves the
same question: *what about other processes?* The Remote Play daemon
is: reachable from the LAN (no pairing for two of its channels), a
different credential class, and a heap full of parsing. A bug here is
a foothold outside the browser entirely — and its IPC-by-name habits
(F2, the unauthenticated registry) could then chain back into system
objects.

## Historical note (closed rows that this audit owns)

PPPwn / CVE-2006-4304: **dead on 13.52+** — the old ICMP-era fix is
backported (binary proof in the console-side parser). Do not revisit.
