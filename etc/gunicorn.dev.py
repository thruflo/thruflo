backlog = 2048              # The listen queue size for the server socket
bind = "unix:/tmp/gunicorn.sock"
daemon = False              # Whether work in the background
debug = True               # Some extra logging
keepalive = 30               # Time we wait for next connection (in seconds)
logfile = "log/gunicorn.log" 
loglevel = "debug"
pidfile = None              # Path to a PID file
workers = 1                 # Number of workers to initialize
umask = 0                   # Umask to set when daemonizing
user = None                 # Change process owner to user
group = None                # Change process group to group
proc_name = None            # Change the process name
spew=False                  # Display trace
timeout=30                  # Worker timeout
tmp_upload_dir = None       # Set path used to store temporary uploads
worker_class = "egg:gunicorn#gevent"    # The type of request processing to use
worker_connections=100     # Maximum number of simultaneous connections

after_fork=lambda server, worker: server.log.info(
        "Worker spawned (pid: %s)" % worker.pid)

before_fork=lambda server, worker: True

before_exec=lambda server: server.log.info("Forked child, reexecuting")

when_ready=lambda server: server.log.info("Gunicorn started.")
