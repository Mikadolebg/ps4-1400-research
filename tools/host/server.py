#!/usr/bin/env python3
"""
server.py -- the PC-side host for the PS4 14.00 research pages.

Serves the repository root (the POC, the workshop, the docs) to the
console browser, captures every verdict marker the pages emit, and
stores the binary evidence dumps they send.

Endpoints beyond static files:
  /log/<marker>            records one verdict marker (sent by the pages)
  /extract/<name>/<off-hex>/<hex-bytes>
                           a CHOSEN extraction (workshop button or bridge
                           command) -> assembles extraction/<name>.bin.
                           This is the only writer of extraction/: the
                           folder contains exactly what YOU picked.
  /dump/<name>/<off-hex>/<hex-bytes>
                           the AUTOMATIC per-run proof dumps of the chain
                           (gadgets verified, stubs, anchors, ROP context)
                           -> assembles runs/evidence/<name>.bin.
                           Both take RELATIVE offsets (< 4 MB guard).

Output (all git-ignored except extraction/README.md):
  runs/                    the logs: journal_YYYY-MM-DD.log (everything,
                           timestamped, with the client IP),
                           last-session.txt (full trace of the latest
                           session), last-verdicts.txt (verdict lines),
                           evidence/ (the automatic proof dumps)
  extraction/              ONLY the extractions you chose, file by file
                           (see extraction/README.md).

Usage:
  python tools/host/server.py [--port 8000] [--bind 0.0.0.0]
"""
import argparse
import os
import sys
import threading
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

# Lines kept in the verdict file (substring match).
VERDICT_KEYS = (
    "PASS", "FAIL", "THREW", "BOOT", "DONE", "SURVIVED", "UNSUPPORTED",
    "LOCKED", "BASE-", "GADGET-GATE", "SYSCALL-", "FCALL-", "AIO-",
    "BRIDGE-", "WORKSHOP", "ERRNO-", "PRISON-", "EVF-REGISTRY",
    "NO-BASE", "SCAN-MISS", "AUTO-",
)

_write_lock = threading.Lock()


class HostHandler(SimpleHTTPRequestHandler):

    # Nothing is ever cached on the console side: every page load serves
    # the fresh file (an exploit page must never be replayed stale).
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Pragma", "no-cache")
        SimpleHTTPRequestHandler.end_headers(self)

    # -- marker journal ---------------------------------------------------
    def _journal(self, marker):
        now = datetime.now()
        ip = self.client_address[0]
        line = now.strftime("[%H:%M:%S] ") + ip + " " + marker
        journal = os.path.join(RUNS_DIR, "journal_" + now.strftime("%Y-%m-%d") + ".log")
        last_run = os.path.join(RUNS_DIR, "last-session.txt")
        verdict = os.path.join(RUNS_DIR, "last-verdicts.txt")
        new_session = marker.startswith("1-BOOT")
        with _write_lock:
            with open(journal, "a", encoding="utf-8") as f:
                f.write(line + "\n")
            with open(last_run, "w" if new_session else "a", encoding="utf-8") as f:
                if new_session:
                    f.write(now.strftime("# session %Y-%m-%d %H:%M:%S from ") + ip + "\n")
                f.write(line + "\n")
            if any(k in marker for k in VERDICT_KEYS):
                with open(verdict, "w" if new_session else "a", encoding="utf-8") as f:
                    f.write(line + "\n")
        print(line, flush=True)

    # -- binary captures (chosen extractions + automatic evidence) --------
    def _capture(self, rest, dest_dir, label):
        try:
            parts = rest.split("/")
            if len(parts) < 3:
                return
            name = parts[0][:64].replace("\\", "_").replace(".", "_")
            offset = int(parts[1], 16)
            # Guard: offsets are RELATIVE to the capture start (< 4 MB -
            # the largest legitimate extraction is the 2 MB WebKit slice).
            # A huge value means a page bug (an absolute address was
            # sent) -> refuse, never grow a file to gigabytes.
            if offset > 0x400000:
                print("[%s] %s-REFUSED offset=0x%x too large (relative expected)"
                      % (datetime.now().strftime("%H:%M:%S"), label, offset),
                      flush=True)
                return
            data = bytes.fromhex(parts[2])
            os.makedirs(dest_dir, exist_ok=True)
            fp = os.path.join(dest_dir, name + ".bin")
            with _write_lock:
                size = os.path.getsize(fp) if os.path.exists(fp) else 0
                with open(fp, "r+b" if os.path.exists(fp) else "wb") as f:
                    if offset > size:
                        f.seek(0, 2)
                        f.write(b"\x00" * (offset - size))
                    else:
                        f.seek(offset)
                    f.write(data)
            print("[%s] %s %s +0x%x (%d bytes)"
                  % (datetime.now().strftime("%H:%M:%S"), label, name,
                     offset, len(data)), flush=True)
        except Exception as exc:
            print("[%s-ERR] %s" % (label, exc), flush=True)

    # -- routing ------------------------------------------------------------
    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path.startswith("/log/"):
            marker = unquote(path[len("/log/"):]).strip()
            if marker:
                self._journal(marker)
            self.send_response(200)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if path.startswith("/extract/"):
            self._capture(path[len("/extract/"):], EXTRACTION_DIR, "EXTRACT")
            self.send_response(200)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if path.startswith("/dump/"):
            self._capture(path[len("/dump/"):], EVIDENCE_DIR, "DUMP")
            self.send_response(200)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        return SimpleHTTPRequestHandler.do_GET(self)

    def log_message(self, fmt, *args):
        try:
            if "/log/" not in (args[0] if args else ""):
                print("[%s] %s" % (datetime.now().strftime("%H:%M:%S"),
                                   fmt % args), flush=True)
        except Exception:
            pass


def main():
    global RUNS_DIR, EXTRACTION_DIR, EVIDENCE_DIR
    ap = argparse.ArgumentParser(description="PS4 14.00 research host server")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--bind", default="0.0.0.0")
    args = ap.parse_args()

    RUNS_DIR = os.path.join(REPO_ROOT, "runs")
    os.makedirs(RUNS_DIR, exist_ok=True)

    EVIDENCE_DIR = os.path.join(RUNS_DIR, "evidence")
    os.makedirs(EVIDENCE_DIR, exist_ok=True)

    EXTRACTION_DIR = os.path.join(REPO_ROOT, "extraction")
    os.makedirs(EXTRACTION_DIR, exist_ok=True)
    readme = os.path.join(EXTRACTION_DIR, "README.md")
    if not os.path.exists(readme):
        with open(readme, "w", encoding="utf-8", newline="\n") as f:
            f.write("# extraction/ - binary captures from the console\n\n"
                    "This folder receives everything the console pages "
                    "stream to /dump/.\nIt is git-ignored; the committed "
                    "explanation lives next to it in the repository\n"
                    "(re-run tools/host/server.py from a checkout to get "
                    "the full README).\n")

    # serve the repository root
    os.chdir(REPO_ROOT)

    server = ThreadingHTTPServer((args.bind, args.port), HostHandler)
    print("Serving %s on port %d" % (REPO_ROOT, args.port), flush=True)
    print("Logs + automatic proof dumps -> runs/ ; chosen extractions -> extraction/",
          flush=True)
    print("Open on the console: http://<this-PC-IP>:%d/  (menu)" % args.port,
          flush=True)
    print("Ctrl+C to stop.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.", flush=True)


if __name__ == "__main__":
    main()
