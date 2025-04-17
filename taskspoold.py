#!/usr/bin/env python3

import os
import socket
import subprocess
import threading
import json
import time
import sys

# Define environment variables for socket, log and temp directories
SOCKET_PATH = os.environ.get("TASKSPOOL_SOCKET", "/tmp/taskspool.sock")
LOG_DIR = os.environ.get("TASKSPOOL_LOG_DIR", "/tmp/taskspool_logs")
TEMP_DIR = os.environ.get("TASKSPOOL_TEMP_DIR", "/tmp/taskspool_temp")

# Create log and temp directories if they don't exist
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# Max concurrent jobs and queue
MAX_CONCURRENT_JOBS = 3
job_queue = []
job_metadata = {}
job_id_counter = 1

def run_command(command, job_id):
    """Run the command and save stdout, stderr, and exit code"""
    out_file = os.path.join(TEMP_DIR, f"job-{job_id}.out")
    err_file = os.path.join(TEMP_DIR, f"job-{job_id}.err")

    with open(out_file, "w") as stdout, open(err_file, "w") as stderr:
        try:
            # Execute the command
            process = subprocess.Popen(command, shell=True, stdout=stdout, stderr=stderr)
            process.wait()
            exit_code = process.returncode
        except Exception as e:
            exit_code = 1
            stderr.write(f"Error executing command: {str(e)}")

    # Store job metadata
    job_metadata[job_id] = {
        "status": "completed" if exit_code == 0 else "failed",
        "exit": exit_code,
        "cmd": command,
        "out_file": out_file,
        "err_file": err_file
    }

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
                    "command": meta["cmd"]
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
                        "stderr": err_data
                    }
                    conn.sendall(json.dumps(job_info, indent=2).encode())
                else:
                    conn.sendall(json.dumps({"error": f"Job ID {job_id} not found"}).encode())
            except ValueError:
                conn.sendall(json.dumps({"error": "Invalid job ID"}).encode())

    elif data.startswith("queue:"):
        command = data[6:].strip()  # Remove 'queue:' prefix

        if len(job_queue) >= MAX_CONCURRENT_JOBS:
            job_queue.append(command)
            conn.sendall(json.dumps({"message": f"Job queued: {command}"}).encode())
        else:
            # Run command immediately
            job_id = job_id_counter
            job_id_counter += 1
            threading.Thread(target=run_command, args=(command, job_id)).start()
            conn.sendall(json.dumps({"message": f"Job started: {command}"}).encode())

    else:
        conn.sendall(json.dumps({"error": "Unknown command"}).encode())

def start_server():
    """Start the task spooler server"""
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
        try:
            os.remove(SOCKET_PATH)  # Remove existing socket if any
        except FileNotFoundError:
            pass

        server.bind(SOCKET_PATH)
        server.listen()

        print(f"Server listening on {SOCKET_PATH}")

        while True:
            conn, addr = server.accept()
            with conn:
                print("Connected by", addr)
                handle_client_connection(conn, addr)

if __name__ == "__main__":
    start_server()

