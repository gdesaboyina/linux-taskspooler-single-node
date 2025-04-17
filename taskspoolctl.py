#!/usr/bin/env python3

import os
import socket
import argparse
import json

SOCKET_PATH = os.environ.get("TASKSPOOL_SOCKET", "/tmp/taskspool.sock")

parser = argparse.ArgumentParser(description="Task Spooler Client")
parser.add_argument("command", help="Command to send: 'status: all', 'status: <jobid>', or 'queue: <command>'")
args = parser.parse_args()

# Prepare the command string
msg = args.command.strip()

# Connect to the server and send the query
try:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.connect(SOCKET_PATH)
        client.sendall(msg.encode())
        response = client.recv(65536).decode()

        # Try to parse JSON response
        try:
            parsed = json.loads(response)
            print(json.dumps(parsed, indent=2))
        except json.JSONDecodeError:
            print(response)
except FileNotFoundError:
    print(f"Socket not found at {SOCKET_PATH}. Is the server running?")

