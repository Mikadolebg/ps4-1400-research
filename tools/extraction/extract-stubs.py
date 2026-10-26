#!/usr/bin/env python3
"""
extract-stubs.py -- regenerate the 14.00 browser syscall table from a
libkernel window dump.

Every syscall stub exported by libkernel to the browser is a tiny
function of the exact form:

    48 c7 c0 <nr32-le>   mov rax, <syscall number>
    49 89 ca             mov rdx, r9     (the AMD64 orbis syscall ABI
    0f 05                syscall          takes the 4th argument in r9)
    ...                  (return path / tail)

Scanning a libkernel memory dump for that 12-byte signature yields one
row per stub: the syscall number and its offset inside the window. On
the dump taken from our console (window = [__error, +0x6a000)) this
finds 302 stubs, 298 of them in the dense table zone at 0x52b0..0x7a00
- which is exactly what the live workshop resolves and calls.

Usage:
  python tools/extraction/extract-stubs.py <libkernel-window.bin> \
      [--out data/syscalls/stubs-1400.csv] \
      [--names data/syscalls/names-1352.json] [--verify-console-table]

--verify-console-table cross-checks the result against the stub table
embedded in tools/workshop/console.html (the live-measured 298-entry
table) and fails loudly on any disagreement.
"""
import argparse
import csv
import json
import os
import re
import sys

SIG_PREFIX = bytes.fromhex("48c7c0")
SIG_SUFFIX = bytes.fromhex("4989ca0f05")
TABLE_ZONE = (0x52B0, 0x7A00)   # the dense stub zone measured on console

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))


def find_stubs(data):
    """Yield (nr, offset) for every signature hit in the window."""
    out = []
    i = 0
    while True:
        i = data.find(SIG_PREFIX, i)
        if i < 0:
            break
        if data[i + 7:i + 12] == SIG_SUFFIX:
            nr = int.from_bytes(data[i + 3:i + 7], "little")
            out.append((nr, i))
        i += 1
    return out


def load_names(path):
    if not path or not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return {int(k): v for k, v in json.load(f).items()}


def console_table():
    """The live-measured stub table embedded in the workshop console."""
    table = {}
    page = os.path.join(REPO, "tools", "workshop", "console.html")
    with open(page, encoding="utf-8") as f:
        m = re.search(r'var STUB_TABLE = \{([^}]*)\}', f.read())
    if not m:
        raise SystemExit("console.html: STUB_TABLE not found")
    for part in m.group(1).split(","):
        k, v = part.split(":")
        table[int(k.strip().strip('"'))] = int(v)
    return table


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("dump", help="libkernel window dump (binary)")
    ap.add_argument("--out", default=os.path.join(
        REPO, "data", "syscalls", "stubs-1400.csv"))
    ap.add_argument("--names", default=os.path.join(
        REPO, "data", "syscalls", "names-1352.json"))
    ap.add_argument("--verify-console-table", action="store_true")
    args = ap.parse_args()

    with open(args.dump, "rb") as f:
        data = f.read()
    stubs = find_stubs(data)
    stubs.sort(key=lambda s: s[1])
    names = load_names(args.names)

    with open(args.out, "w", newline="\n", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["nr", "offset_hex", "offset_dec", "in_table_zone",
                    "classic_stub_tail", "name_1352_if_known"])
        for nr, off in stubs:
            zone = TABLE_ZONE[0] <= off <= TABLE_ZONE[1]
            # The classic exported stub continues with `72 01 c3`
            # (jb .+1 ; ret - the lazy-binding error path). A few real
            # stubs use a different tail, so this is INFORMATIONAL: on
            # our dump, 4 of the 302 signature hits are inline syscall
            # sequences inside other functions rather than table stubs
            # (see data/syscalls/README.md).
            classic = data[off + 12:off + 15] == bytes.fromhex("7201c3")
            w.writerow([nr, "0x%x" % off, off, 1 if zone else 0,
                        1 if classic else 0, names.get(nr, "")])

    print("%d stub signature hits -> %s" % (len(stubs), args.out))
    zone_n = sum(1 for _, o in stubs if TABLE_ZONE[0] <= o <= TABLE_ZONE[1])
    print("  in the dense table zone 0x%x..0x%x: %d"
          % (TABLE_ZONE[0], TABLE_ZONE[1], zone_n))

    if args.verify_console_table:
        ct = console_table()
        by_nr = {}
        for nr, off in stubs:
            by_nr.setdefault(nr, []).append(off)
        missing = []
        wrong = []
        for nr, off in ct.items():
            if nr not in by_nr:
                missing.append(nr)
            elif off not in by_nr[nr]:
                wrong.append((nr, off, by_nr[nr]))
        if missing or wrong:
            for nr in missing:
                print("  CONSOLE nr %d: not present in this dump" % nr)
            for nr, off, got in wrong:
                print("  CONSOLE nr %d at 0x%x: dump only has %s"
                      % (nr, off, [hex(g) for g in got]))
            sys.exit(1)
        dup = sorted(nr for nr, offs in by_nr.items() if len(offs) > 1)
        print("  console table: %d/%d entries verified present byte-exact"
              % (len(ct), len(ct)))
        if dup:
            print("  nrs with multiple signature hits (one is the stub, "
                  "the others are inline sequences): %s"
                  % ", ".join(map(str, dup)))


if __name__ == "__main__":
    main()
