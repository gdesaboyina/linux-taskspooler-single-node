
# TaskSpooler

A lightweight task spooling system using Unix sockets for queuing and executing shell commands asynchronously. Useful for queuing system administration tasks or running background jobs in a controlled way.

## Components

### 1. taskspoold.py  Task Spooler Server

The server manages job execution using a Unix socket and processes commands in parallel (configurable). Each job's stdout/stderr and metadata are stored for querying.

### 2. taskspoolctl.py  Task Spooler Client

The client connects to the server using the Unix socket and allows you to:
- Submit new jobs
- View all jobs
- View a specific job's status and output

## Configuration

You can configure paths via environment variables:

| Variable Name         | Description                            | Default Value            |
|-----------------------|----------------------------------------|--------------------------|
| TASKSPOOL_SOCKET      | Unix socket path used by server/client | /tmp/taskspool.sock      |
| TASKSPOOL_LOG_DIR     | Directory for job logs (future use)    | /tmp/taskspool_logs      |
| TASKSPOOL_TEMP_DIR    | Temp directory for stdout/stderr files | /tmp/taskspool_temp      |

Example (Linux/macOS):

```bash
export TASKSPOOL_SOCKET=/tmp/mysock.sock
export TASKSPOOL_LOG_DIR=/var/log/taskspooler
export TASKSPOOL_TEMP_DIR=/var/tmp/taskspooler
```

## Getting Started

### 1. Start the Server

```bash
python3 taskspoold.py
```

The server will listen for incoming jobs on the socket specified in TASKSPOOL_SOCKET.

### 2. Queue a Command

```bash
python3 taskspoolctl.py "queue: ls -lh /var"
python3 taskspoolctl.py "queue: cd /var && ls -ltr"
python3 taskspoolctl.py "queue: cd /var ; ls -ltr"
```

You will receive a confirmation message like:

```json
{
  "message": "Job started: ls -lh /var"
}
```

### 3. View All Job Statuses

```bash
python3 taskspoolctl.py "status: all"
```

Sample output:
```json
{
  "queue_length": 0,
  "active_workers": 1,
  "max_concurrent_jobs": 3,
  "load_avg": [0.12, 0.34, 0.56],
  "last_job_id": 5,
  "jobs": [
    {
      "job_id": 3,
      "status": "completed",
      "exit_code": 0,
      "command": "ls -lh /var"
    }
  ]
}
```

### 4. View a Specific Job's Output

```bash
python3 taskspoolctl.py "status: 3"
```

Sample output:
```json
{
  "job_id": 3,
  "status": "completed",
  "exit_code": 0,
  "command": "ls -lh /var",
  "stdout": "total 12\ndrwxr-xr-x ...",
  "stderr": ""
}
```

## Features

- Queue and run shell commands
- View stdout and stderr for each job
- View current load, queue length, and job history
- Fully configurable via environment variables
- Lightweight and portable - just Python 3 and standard libraries

## Testing

You can test with commands that produce output:

```bash
python3 taskspoolctl.py "queue: echo 'Hello World'"
python3 taskspoolctl.py "queue: uname -a"
python3 taskspoolctl.py "queue: sleep 10"
```

Then check status:

```bash
python3 taskspoolctl.py "status: all"
```

## Future Improvements

- Persistent job storage
- Retry/timeout support
- Job cancellation
- Prioritization of jobs

## Cleanup

To remove all temp files and reset:
```bash
rm -f /tmp/taskspool.sock
rm -rf /tmp/taskspool_logs/*
rm -rf /tmp/taskspool_temp/*
```

## License

MIT License
