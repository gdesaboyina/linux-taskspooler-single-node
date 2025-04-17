TaskSpooler
===========

TaskSpooler is a lightweight UNIX domain socket-based task queue and runner.
It enables you to submit shell commands for asynchronous execution and monitor their status easily.
Ideal for simple distributed job execution scenarios.

Features
--------

- Minimalistic, self-contained Python3-based task runner
- Queue shell commands via a UNIX socket
- View job status, output, error, and exit code
- Includes timestamps with timezone support (e.g., EST)
- Simple JSON protocol for communication
- Configurable via environment variables

Components
----------

- taskspoold — Server daemon that listens on a UNIX socket and runs commands
- taskspoolctl — Client utility to queue commands and check status

Installation
------------

You can clone and run directly:

    git clone https://github.com/your-org/taskspooler.git
    cd taskspooler
    chmod +x taskspoold taskspoolctl

Configuration
-------------

You can override these environment variables:

| Variable Name         | Description                            | Default Value            |
|-----------------------|----------------------------------------|--------------------------|
| TASKSPOOL_SOCKET      | Unix socket path used by server/client | /tmp/taskspool.sock      |
| TASKSPOOL_LOG_DIR     | Directory for job logs (future use)    | /tmp/taskspool_logs      |
| TASKSPOOL_TEMP_DIR    | Temp directory for stdout/stderr files | /tmp/taskspool_temp      |
| TASKSPOOL_TZ          | Timezone used for timestamps (e.g., EST) |   America/New_York                |

Usage
-----

1. Start the Server

```bash
./taskspoold.py
```

Server listens on the socket and accepts task or status queries.

2. Queue a Command

```bash
./taskspoolctl.py "queue: ls -lh /var"
./taskspoolctl.py "queue: cd /var && ls -ltr"
./taskspoolctl.py "queue: cd /var ; ls -ltr"
```


3. Check Status of All Jobs

```bash
./taskspoolctl.py status:all
```

Example response:
```json
    {
      "queue_length": 0,
      "active_workers": 1,
      "max_concurrent_jobs": 3,
      "load_avg": [0.2, 0.3, 0.1],
      "last_job_id": 5,
      "jobs": [
        {
          "job_id": 4,
          "status": "completed",
          "exit_code": 0,
          "command": "hostname",
          "queued_time": "2025-04-17T10:15:03 EST",
          "run_time": "2025-04-17T10:15:04 EST"
        }
      ]
    }
```
4. Check Status of a Specific Job

```bash
 ./taskspoolctl.py "status: 3"
```


Permissions
-----------

Make sure only trusted users can access the UNIX socket. Use file permissions or socket ownership to restrict access.

License
-------

MIT License
