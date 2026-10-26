#!/usr/bin/env python3
"""
extract-gadgets.py -- verify (and, on a drifted build, re-locate) the
ROP gadget set inside a WebKit memory dump.

The exploit's gadget table (15 gadgets, `data/offsets/webkit-1400.md`)
is expected to hold as-is on the frozen engine; the workshop verifies
it AT RUNTIME before every use. This tool does the same check offline,
on a dump you took of your own console's WebKit text, and scans a
window around any stale RVA to repair it (the same ±0x8000/±0x20000
ladder the page uses).

Usage:
  python tools/extraction/extract-gadgets.py <webkit-dump.bin> --rva 0x0
      [--out gadgets-verified.csv]

`--rva` is the module RVA of byte 0 of the dump (so a window starting
at text+0x1000 would pass --rva 0x1000).
"""
import argparse
import csv
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

# name, expected RVA, byte signature (REX-prefixed ones are matched
# with REX-equivalence on the first byte, as the runtime gate does)
GADGETS = [
    ("POP_RDI_RET", 0x5c480, [0x5f, 0xc3]),
    ("POP_RSI_RET", 0x6e45e, [0x5e, 0xc3]),
    ("POP_RDX_RET", 0x12c5ba, [0x5a, 0xc3]),
    ("POP_RCX_RET", 0x1bade, [0x59, 0xc3]),
    ("POP_R8_RET", 0x9b311, [0x41, 0x58, 0xc3]),
    ("POP_R9_RET", 0x1dcfb1, [0x41, 0x59, 0xc3]),
    ("POP_RAX_RET", 0x10504, [0x58, 0xc3]),
    ("LEAVE_RET", 0x182f7, [0xc9, 0xc3]),
    ("MOV_RDI_RAX_RET", 0x548b, [0x48, 0x89, 0x07, 0xc3]),
    ("G0", 0x295f948, [0x48, 0x8b, 0x7e, 0x30]),
    ("G1", 0x1d989e3, [0x58, 0x48, 0x8b, 0x07]),
    ("G2", 0x25bae0, [0x55, 0x48, 0x89, 0xe5]),
    ("G3", 0x4a0406, [0x48, 0x8b, 0x78, 0x08]),
    ("G4", 0x1ec3ada, [0x48, 0x8b, 0x50, 0x38]),
    ("G5", 0x2abccaa, [0x52, 0x5c, 0xc3]),
]

WIN1, WIN2 = 0x8000, 0x20000


def rex_equiv(expected, actual):
    if actual == expected:
        return True
    if (expected & 0xf8) != 0x40:
        return False
    return ((actual & 0xf8) == 0x40
            and (actual & 0x08) == (expected & 0x08))


def matches(data, at, pat):
    rex_head = (pat[0] & 0xf8) == 0x40
    b0 = data[at]
    if not (rex_equiv(pat[0], b0) if rex_head else b0 == pat[0]):
        return False
    return all(data[at + k] == pat[k] for k in range(1, len(pat)))


def scan(data, lo, hi, pat):
    for a in range(lo, hi):
        if matches(data, a, pat):
            return a
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dump")
    ap.add_argument("--rva", required=True,
                    help="module RVA of byte 0 of the dump")
    ap.add_argument("--out",
                    default=os.path.join(REPO, "runs", "gadgets-verified.csv"))
    args = ap.parse_args()

    base = int(args.rva, 0)
    with open(args.dump, "rb") as f:
        data = f.read()

    rows = []
    bad = 0
    for name, rva, pat in GADGETS:
        off = rva - base
        verdict = "EXACT"
        found = rva
        if off < 0 or off + len(pat) > len(data) or not matches(data, off, pat):
            verdict = "DRIFT"
            lo = max(off - WIN1, 0)
            hi = min(off + WIN1, len(data) - len(pat))
            hit = scan(data, lo, hi, pat)
            used = 1
            if not hit:
                lo = max(off - WIN2, 0)
                hi = min(off + WIN2, len(data) - len(pat))
                hit = scan(data, lo, hi, pat)
                used = 2
            if hit:
                found = base + hit
                verdict = "REPAIRED-window%d" % used
            else:
                found = 0
                verdict = "NOT-FOUND"
                bad += 1
        rows.append([name, "0x%x" % rva, "0x%x" % found if found else "",
                     verdict, bytes(pat).hex()])

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", newline="\n", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["gadget", "expected_rva", "found_rva", "verdict",
                    "signature_hex"])
        w.writerows(rows)
    for r in rows:
        print("  %-16s expected %-10s -> %-10s %s"
              % (r[0], r[1], r[2] or "-", r[3]))
    print("%d/%d verified -> %s" % (len(rows) - bad, len(rows), args.out))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
