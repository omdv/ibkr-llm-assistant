"""Gunicorn configuration file for production deployment."""
import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8000"  # Listen on all interfaces
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1  # Recommended formula for CPU-bound apps
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = "-"  # stdout
errorlog = "-"   # stderr
loglevel = "info"

# Process naming
proc_name = "ibkr-mcp-server"

# SSL (uncomment and configure if using HTTPS)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Proxy settings
forwarded_allow_ips = "*"  # Trust X-Forwarded-* headers from Nginx
proxy_protocol = True
proxy_allow_ips = "*"  # Trust proxy protocol from Nginx

# Server hooks
def on_starting(server):
  """Log when server starts."""
  server.log.info("Starting IBKR MCP Server")

def on_exit(server):
  """Log when server exits."""
  server.log.info("Stopping IBKR MCP Server")
