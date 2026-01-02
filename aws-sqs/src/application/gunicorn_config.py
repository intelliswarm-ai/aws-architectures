"""Gunicorn configuration for production deployment."""

import multiprocessing
import os

# Server socket
bind = os.environ.get("GUNICORN_BIND", "0.0.0.0:8080")
backlog = 2048

# Worker processes
workers = int(os.environ.get("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests (helps with memory leaks)
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("LOG_LEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "banking-processor"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Hooks
def on_starting(server):
    """Called just before the master process is initialized."""
    pass


def on_reload(server):
    """Called when workers are reloaded."""
    pass


def when_ready(server):
    """Called just after the server is started."""
    pass


def worker_int(worker):
    """Called when a worker receives SIGINT or SIGQUIT."""
    pass


def worker_abort(worker):
    """Called when a worker receives SIGABRT."""
    pass


def pre_fork(server, worker):
    """Called just before a worker is forked."""
    pass


def post_fork(server, worker):
    """Called just after a worker has been forked."""
    # Start the transaction worker in each forked process
    from .worker import get_worker
    worker_instance = get_worker()
    worker_instance.start()


def child_exit(server, worker):
    """Called in the master process after a worker exits."""
    pass


def worker_exit(server, worker):
    """Called just after a worker has been exited."""
    from .worker import get_worker
    worker_instance = get_worker()
    worker_instance.stop()


def nworkers_changed(server, new_value, old_value):
    """Called just after the number of workers has been changed."""
    pass
