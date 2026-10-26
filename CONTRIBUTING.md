# Contributing

This repository lives on **measured truth**. Contributions are welcome
under one discipline: every claim carries its evidence.

## The evidence rules

1. **Bytes, not patterns.** An offset or gadget is only "verified" when
   its exact bytes were read and matched — at runtime for exploit
   material (the pages do this; keep it that way), offline against a
   dump for tables. A "looks like the 1304 value" file is worth
   nothing (that exact mistake produced the fakes documented in
   `docs/06-negative-results.md` — do not import them, do not repeat
   them).
2. **One unknown per console run.** Change one thing, measure one
   thing. A session that answers a question nobody asked has burned a
   browser session for nothing.
3. **Never re-test a published negative result.** The closed leads in
   `docs/06-negative-results.md` are closed with evidence; reopening
   one requires a *reason* (a firmware change, a new primitive).
4. **Respect the danger list.** `data/syscalls/DANGEROUS.md` exists
   because those calls cost real console sessions and reboots.
5. **Date your measurements.** Evidence is referenced by what ran and
   when ("measured 2026-10-16, 7 runs / 2 boots"), never by an
   internal attempt number.

## House style

- English only in the repository (the code, logs and markers are plain
  ASCII — the console browser renders it, and greps stay honest).
- Files are named functionally and are **stable forever**: no numbered
  copies, no `backup/`, no version suffixes. Git history is the only
  history; product versioning lives in `CHANGELOG.md` and git tags.
- Verdict markers are vocabulary: `UPPER-CASE`, self-describing, and
  documented in `data/markers.md`. If you add one, add the glossary
  row in the same change.
- New syscall measurements go into `data/syscalls/gates-1400.csv` with
  the evidence pointer; new leads go into `docs/07-next-leads.md`
  ranked, with a status word (OPEN / CLOSED / UNTESTED).

## Workflow

1. `node tools/qualif/selftest-repo.js` must be green before and after
   your change (it checks page syntax, table coherence, and that
   nothing internal leaked).
2. If you touched the pages: describe what changed *functionally* in
   the PR (which marker, which law); exploit-code changes that alter
   the proven sequence need explicit justification.
3. If you measured on console: include the marker log lines (redacted
   of your LAN IPs) in the PR description.
4. `python -m py_compile tools/host/*.py tools/extraction/*.py` for
   any Python change.

## Picking up the hunt

The open leads and how to attack each one are in
`docs/07-next-leads.md`; the tooling for every lead is already in this
repo (the workshop's `sysc`/`stat`/`walk`/`read` commands cover most
probing needs). Fork, measure, report with evidence — that is the whole
game until someone lands the kernel primitive.
