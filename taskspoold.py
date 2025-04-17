#!/usr/bin/env python3

import os
import socket
import subprocess
import threading
import json
import time
import sys
from datetime import datetime
from zoneinfo import ZoneInfo  # Python 3.9+

# Define environment variables for socket, log and temp directories
SOCKET_PATH = os.environ.get("TASKSPOOL_SOCKET", "/tmp/taskspool.sock")
LOG_DIR = os.environ.get("TASKSPOOL_LOG_DIR", "/tmp/taskspool_logs")
TEMP_DIR = os.environ.get("TASKSPOOL_TEMP_DIR", "/tmp/taskspool_temp")
TIMEZONE_NAME = os.environ.get("TASKSPOOL_TZ", "America/New_York")
LOCAL_ZONE = ZoneInfo(TIMEZONE_NAME)

# Create log and temp directories if they don't exist
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# Max concurrent jobs and queue
MAX_CONCURRENT_JOBS = 3
job_queue = []
job_metadata = {}
job_id_counter = 1

def current_time():
    return datetime.now(LOCAL_ZONE).strftime("%Y-%m-%dT%H:%M:%S %Z")

def run_command(command, job_id):
    """Run the command and save stdout, stderr, and exit code"""
    out_file = os.path.join(TEMP_DIR, f"job-{job_id}.out")
    err_file = os.path.join(TEMP_DIR, f"job-{job_id}.err")

    run_time = current_time()
    print(f"[{run_time}] [Job {job_id}] Command: {command}")

    with open(out_file, "w") as stdout_file, open(err_file, "w") as stderr_file:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=stdout_file,
            stderr=stderr_file,
            text=True
        )
        process.wait()
        exit_code = process.returncode

    # Update job metadata
    if job_id in job_metadata:
        job_metadata[job_id]["run_time"] = run_time
        job_metadata[job_id]["status"] = "completed" if exit_code == 0 else "failed"
        job_metadata[job_id]["exit"] = exit_code
        job_metadata[job_id]["out_file"] = out_file
        job_metadata[job_id]["err_file"] = err_file

def handle_client_connection(conn, addr):
    """Handle commands from clients"""
    global job_id_counter

    data = conn.recv(65536).decode()
    if data.startswith("status:"):
        query = data[7:].strip()

        if query == "all":
            result = {
                "queue_length": len(job_queue),
                "active_workers": threading.active_count() - 2,
                "max_concurrent_jobs": MAX_CONCURRENT_JOBS,
                "load_avg": list(os.getloadavg()),
                "last_job_id": job_id_counter,
                "jobs": []
            }

            for jid in sorted(job_metadata):
                meta = job_metadata[jid]
                result["jobs"].append({
                    "job_id": jid,
                    "status": meta["status"],
                    "exit_code": meta["exit"],
                    "command": meta["cmd"],
                    "queued_time": meta.get("queued_time"),
                    "run_time": meta.get("run_time")
                })

            conn.sendall(json.dumps(result, indent=2).encode())

        else:
            try:
                job_id = int(query)
                if job_id in job_metadata:
                    meta = job_metadata[job_id]
                    out_data = ""
                    err_data = ""
                    try:
                        with open(meta["out_file"], "r") as out_file:
                            out_data = out_file.read()
                        with open(meta["err_file"], "r") as err_file:
                            err_data = err_file.read()
                    except FileNotFoundError:
                        pass  # Might not have run yet

                    job_info = {
                        "job_id": job_id,
                        "status": meta["status"],
                        "exit_code": meta["exit"],
                        "command": meta["cmd"],
                        "stdout": out_data,
                        "stderr": err_data,
                        "queued_time": meta.get("queued_time"),
                        "run_time": meta.get("run_time")
                    }
                    conn.sendall(json.dumps(job_info, indent=2).encode())
                else:
                    conn.sendall(json.dumps({"error": f"Job ID {job_id} not found"}).encode())
            except ValueError:
                conn.sendall(json.dumps({"error": "Invalid job ID"}).encode())

    elif data.startswith("queue:"):
        command = data[6:].strip()  # Remove 'queue:' prefix

        job_id = job_id_counter
        job_id_counter += 1
        queued_time = current_time()
        job_metadata[job_id] = {
            "status": "queued",
            "exit": None,
            "cmd": command,
            "queued_time": queued_time,
            "run_time": None,
            "out_file": None,
            "err_file": None
        }

        if len(job_queue) >= MAX_CONCURRENT_JOBS:
            job_queue.append((command, job_id))
            conn.sendall(json.dumps({"message": f"Job queued: {command}"}).encode())
        else:
            threading.Thread(target=run_command, args=(command, job_id)).start()
            conn.sendall(json.dumps({"message": f"Job started: {command}"}).encode())

    else:
        conn.sendall(json.dumps({"error": "Unknown command"}).encode())


# === Main Server Loop ===
def start_server():
    if os.path.exists(SOCKET_PATH):
        os.remove(SOCKET_PATH)

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(SOCKET_PATH)
    server.listen()
    print(f"Task Spooler is listening on {SOCKET_PATH}")

    try:
        while True:
            conn, addr = server.accept()
            threading.Thread(target=handle_client_connection, args=(conn,addr), daemon=True).start()
    finally:
        server.close()
        if os.path.exists(SOCKET_PATH):
            os.remove(SOCKET_PATH)

if __name__ == "__main__":
    start_server()

