# Changelog

All notable changes to this project are documented here.
Versioning follows the repo as a whole — individual files never carry
version numbers (git history is the only file history).

## [Unreleased]

- **One-click extraction from the workshop**: EXTRACT buttons on the
  console page (libkernel stub table, stub zone, WebKit text slice,
  proof anchors) and a matching `{"t":"extract","what":...}` bridge
  command. All captures now land in the dedicated `extraction/` folder
  on the PC (git-ignored, self-documenting via its README), replacing
  the old `runs/dumps/` location. New markers: `EXT-START`, `EXT-DONE`,
  `EXT-FAIL`.

## v1.0.0 — 2026-10-26

Initial public release. State of the research at this date:

- **POC**: the full 14.00 userland chain (SSV entry → arbitrary R/W →
  WebKit base leak → byte-verified ROP → arbitrary syscalls) as a single
  distilled page (`poc/poc.html`), plus the host server with marker
  logging and binary dump capture (`tools/host/server.py`).
- **Workshop**: the live remote workshop (thin boot page + console page +
  WebSocket bridge) used to drive the armed chain from the PC without
  reloading the console browser (`tools/workshop/`, `tools/host/bridge.py`).
- **Data**: the 302-stub browser syscall table for 14.00 (regenerable via
  `tools/extraction/extract-stubs.py`), 13.52 kernel syscall tables, the
  10.50 reference table, 684 syscall names extracted from the 13.52
  kernel, measured gate status per interesting syscall family, WebKit and
  kernel offset notes, and the danger list.
- **Docs**: the SSV entry write-up and the frozen-engine proof; the
  userland chain; the 14.00 syscall surface; the browser terrain map;
  eight audit distillations (aio, ipmimgr 622, orbis_idt wrap-8, bnet N1,
  sandbox, dmem gates, consolidated surface audits, Remote Play); the
  consolidated negative-results table; and the ranked open leads.
