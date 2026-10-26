#!/usr/bin/env python3
"""
bridge.py -- real-time WebSocket bridge between the PC and the armed
workshop page (tools/workshop/console.html) running in the PS4 browser.

Architecture: a global client registry plus ONE command pump that
BROADCASTS to every live client (one pump per session would write into
dead sockets). Replies are handled per session.

Commands: one JSON object per line in bridge/commands.jsonl (lines are
consumed once). Results land in bridge/results.jsonl; the heartbeat
snapshot lives in bridge/status.json; files exported by `read` land in
bridge/files/.

Supported commands (see docs/04-terrain-map.md for recipes):
  {"t":"ping"}
  {"t":"stat","path":"/dev"}                 open + list/head of a path
  {"t":"walk","path":"/","depth":2}          recursive FS map (budgeted)
  {"t":"read","path":"/dev/random","max":256}  file export (base64)
  {"t":"sysc","num":20,"args":[],            arbitrary syscall via the
        "raw":false}                          byte-verified stub; raw=true
                                             goes through the bare
                                             `syscall; ret` gadget and
                                             returns a POSITIVE errno
                                             in rax on error
  {"t":"eval","code":"2+2"}                  remote JS evaluation
  {"t":"selftest"}                           built-in suite (devices,
                                             evf/aio errno probes)
  {"t":"arm","slots":5000000,"n":512}        to a connected boot page

Usage:
  python tools/host/bridge.py [--port 8001]
"""
import argparse
import base64
import hashlib
import json
import os
import socket
import struct
import threading
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
EXP = os.path.join(ROOT, "bridge")
CMD = os.path.join(EXP, "commands.jsonl")
RES = os.path.join(EXP, "results.jsonl")
LOG = os.path.join(EXP, "session.log")
FILES = os.path.join(EXP, "files")
for d in (EXP, FILES):
    os.makedirs(d, exist_ok=True)

WORKSHOP_ID = "workshop-console"   # the page id the death-watch tracks

CLIENTS = set()
LOCK = threading.Lock()


def log(msg):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), msg)
    print(line)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


class WS:
    """Minimal WebSocket server-side endpoint (RFC 6455, no deps)."""

    def __init__(self, conn):
        self.conn = conn

    def recv_exact(self, n):
        buf = b""
        while len(buf) < n:
            c = self.conn.recv(n - len(buf))
            if not c:
                raise ConnectionError("closed")
            buf += c
        return buf

    def handshake(self):
        data = b""
        while b"\r\n\r\n" not in data:
            c = self.conn.recv(4096)
            if not c:
                raise ConnectionError("no handshake")
            data += c
        head = data.split(b"\r\n\r\n", 1)[0].decode("latin1")
        headers = {}
        for line in head.split("\r\n")[1:]:
            if ":" in line:
                k, v = line.split(":", 1)
                headers[k.strip().lower()] = v.strip()
        key = headers.get("sec-websocket-key", "")
        accept = base64.b64encode(hashlib.sha1(
            (key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()
        ).digest()).decode()
        self.conn.sendall((
            "HTTP/1.1 101 Switching Protocols\r\n"
            "Upgrade: websocket\r\nConnection: Upgrade\r\n"
            "Sec-WebSocket-Accept: %s\r\n\r\n" % accept).encode())
        log("HANDSHAKE ok (%d clients)" % count_clients())

    def read_msg(self):
        h = self.recv_exact(2)
        op = h[0] & 0x0F
        masked = h[1] & 0x80
        ln = h[1] & 0x7F
        if ln == 126:
            ln = struct.unpack(">H", self.recv_exact(2))[0]
        elif ln == 127:
            ln = struct.unpack(">Q", self.recv_exact(8))[0]
        mask = self.recv_exact(4) if masked else None
        payload = self.recv_exact(ln) if ln else b""
        if mask:
            payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        if op == 8:
            raise ConnectionError("close frame")
        if op == 9:                      # ping -> pong
            self.send_raw(b"", 0x0A)
            return None
        return payload.decode("utf-8", "replace")

    def send_raw(self, data, op=0x01):
        ln = len(data)
        hdr = bytes([0x80 | op])
        if ln < 126:
            hdr += bytes([ln])
        elif ln < 65536:
            hdr += bytes([126]) + struct.pack(">H", ln)
        else:
            hdr += bytes([127]) + struct.pack(">Q", ln)
        self.conn.sendall(hdr + data)

    def send(self, text):
        self.send_raw(text.encode())


def count_clients():
    with LOCK:
        return len(CLIENTS)


def broadcast(text):
    with LOCK:
        live = list(CLIENTS)
    for c in live:
        try:
            c.send(text)
        except Exception:
            with LOCK:
                CLIENTS.discard(c)


HB_COUNT = [0]
LAST_HB = [0.0]


def handle_reply(obj):
    t = obj.get("t", "")
    if t == "hb":
        try:
            with open(os.path.join(EXP, "status.json"), "w", encoding="utf-8") as f:
                json.dump({"ts": time.time(),
                           "hb": time.strftime("%H:%M:%S"),
                           "syscalls": obj.get("syscalls", 0),
                           "src": obj.get("src", WORKSHOP_ID),
                           "clients": count_clients()}, f)
        except Exception:
            pass
        HB_COUNT[0] += 1
        LAST_HB[0] = time.time()
        if HB_COUNT[0] % 48 == 1:
            log("HB syscalls=%s clients=%d"
                % (obj.get("syscalls", 0), count_clients()))
        return
    with open(RES, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")
    if t == "read" and obj.get("b64"):
        safe = obj.get("path", "unknown").replace("/", "_") \
            .replace("\\", "_").lstrip("_") or "root"
        out = os.path.join(FILES, safe + ".bin")
        with open(out, "wb") as f:
            f.write(base64.b64decode(obj["b64"]))
        log("EXPORT %s -> %s (%d bytes)"
            % (obj.get("path"), out, obj.get("n", 0)))
        obj = dict(obj)
        obj["b64"] = "<exported>"
    log("REPLY " + json.dumps(obj, ensure_ascii=False)[:400])


def command_pump():
    seen = 0
    if os.path.exists(CMD):
        with open(CMD, "r", encoding="utf-8") as f:
            seen = sum(1 for _ in f)
    while True:
        try:
            if os.path.exists(CMD):
                with open(CMD, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                for line in lines[seen:]:
                    line = line.strip()
                    if not line:
                        seen += 1
                        continue
                    seen += 1
                    try:
                        json.loads(line)
                    except ValueError:
                        log("invalid command: " + line[:100])
                        continue
                    log("SEND  " + line[:200])
                    broadcast(line)
            time.sleep(0.4)
        except Exception as e:
            log("pump: " + str(e))


def session(conn, addr):
    log("CONNECTION from %s" % (addr,))
    ws = WS(conn)
    try:
        ws.handshake()
        with LOCK:
            CLIENTS.add(conn)
        while True:
            msg = ws.read_msg()
            if msg is None:
                continue
            try:
                obj = json.loads(msg)
            except ValueError:
                log("TXT  " + msg[:200])
                continue
            handle_reply(obj)
    except (ConnectionError, OSError) as e:
        log("DISCONNECT (%s)" % e)
    finally:
        with LOCK:
            CLIENTS.discard(conn)
        try:
            conn.close()
        except Exception:
            pass


def death_watch():
    import time as _t
    while True:
        _t.sleep(5)
        try:
            with open(os.path.join(EXP, "status.json"), encoding="utf-8") as f:
                st = json.load(f)
            if (st.get("src") == WORKSHOP_ID
                    and _t.time() - st.get("ts", 0) > 20):
                log("!!! PAGE DEAD (no heartbeat for %ds) - live window closed"
                    % int(_t.time() - st["ts"]))
                LAST_HB[0] = _t.time()   # avoid spam
        except FileNotFoundError:
            pass


def main():
    ap = argparse.ArgumentParser(description="PS4 14.00 workshop WebSocket bridge")
    ap.add_argument("--port", type=int, default=8001)
    ap.add_argument("--bind", default="0.0.0.0")
    args = ap.parse_args()

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((args.bind, args.port))
    srv.listen(8)
    log("workshop bridge (broadcast) on port %d" % args.port)
    log("commands: append JSON lines to bridge/commands.jsonl")
    threading.Thread(target=command_pump, daemon=True).start()
    threading.Thread(target=death_watch, daemon=True).start()
    while True:
        conn, addr = srv.accept()
        threading.Thread(target=session, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    main()
