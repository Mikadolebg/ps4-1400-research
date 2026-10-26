# -*- coding: utf-8 -*-
# bridge.py -- real-time WebSocket bridge between the PC and the armed
# workshop page (tools/workshop/console.html) in the PS4 browser.
#
# Architecture: one global client registry + ONE command pump that
# broadcasts to every live client (per-session pumps write into dead
# sockets). Commands: JSON lines in bridge/commands.jsonl; results:
# bridge/results.jsonl; heartbeat snapshot: bridge/status.json.

import argparse
import base64
import hashlib
import json
import os
import socket
import struct
import threading
import time