#!/usr/bin/env python3
import sys

sys.stdout = sys.stdout.detach()

for line in sys.stdin:
  parts = line.strip().split()
  for part in parts:
    byte = bytes.fromhex(part)
    sys.stdout.write(byte)
