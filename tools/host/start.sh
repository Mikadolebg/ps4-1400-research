#!/bin/sh
# PS4 14.00 research host launcher (POSIX): server.py (8000) + bridge.py (8001).
# This launcher is stable: it never changes between probes.
set -e
cd "$(dirname "$0")/../.."

PY=python3
command -v "$PY" >/dev/null 2>&1 || PY=python

LANIP=$(ip -4 route get 1.1.1.1 2>/dev/null | awk '{for(i=1;i<=NF;i++)if($i=="src"){print $(i+1);exit}}')
[ -n "$LANIP" ] || LANIP=$(hostname -I 2>/dev/null | awk '{print $1}')

echo "================================================================"
echo "  PS4 14.00 RESEARCH HOST"
echo "  server.py (port 8000) + bridge.py (port 8001)"
echo "================================================================"
if [ -n "$LANIP" ]; then
    echo "  Open on the PS4:  http://$LANIP:8000/"
else
    echo "  Open on the PS4:  http://<this-PC-IP>:8000/"
fi
echo
echo "  Session log:    runs/last-session.txt + runs/last-verdicts.txt"
echo "  Bridge data:    bridge/  (commands.jsonl / results.jsonl / files/)"
echo "  Live commands:  echo '{\"t\":\"ping\"}' >> bridge/commands.jsonl"
echo "  Stop: Ctrl+C"
echo "================================================================"

"$PY" tools/host/bridge.py &
BRIDGE_PID=$!
trap 'kill $BRIDGE_PID 2>/dev/null' EXIT INT TERM
"$PY" tools/host/server.py
