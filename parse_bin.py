#!/usr/bin/env python3
import sys
import argparse
from packagePrinter import printPacket
from packagePrinter_dense import printPacketDense
from packagePrinter_unknown import printPacketUnknown
from message_parser import MessageParser

parser = argparse.ArgumentParser(description='Raw byte log parser.')
parser.add_argument('-d', action='store_true', dest='dense')
parser.add_argument('-u', action='store_true', dest='unknown')
args = parser.parse_args()

if args.dense:
  printer = printPacketDense
elif args.unknown:
  printer = printPacketUnknown
else:
  printer = printPacket

messageParser = MessageParser(printer)

sys.stdin = sys.stdin.detach()
while (byte := sys.stdin.read(1)):
  messageParser.feed(byte)

print("[DONE]")
