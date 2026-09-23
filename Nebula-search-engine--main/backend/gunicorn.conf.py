import multiprocessing
import os

_backend_dir = os.path.dirname(os.path.abspath(__file__))
_app_env = os.getenv("APP_ENV", "production")
_workers_per_core = int(os.getenv("WORKERS_PER_CORE", "2"))
_max_workers = int(os.getenv("MAX_WORKERS", "8"))
_min_workers = int(os.getenv("MIN_WORKERS", "2"))

_calculated = max(_min_workers, min(_max_workers, multiprocessing.cpu_count() * _workers_per_core))
workers = _calculated if _app_env == "production" else 1

worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 120
graceful_timeout = 60
keepalive = 5
backlog = 2048

bind = os.getenv("GUNICORN_BIND", "0.0.0.0:8000")

pythonpath = _backend_dir
chdir = _backend_dir

accesslog = os.getenv("GUNICORN_ACCESS_LOG", "-")
errorlog = os.getenv("GUNICORN_ERROR_LOG", "-")
loglevel = os.getenv("GUNICORN_LOG_LEVEL", os.getenv("LOG_LEVEL", "info").lower())
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

reload = _app_env == "development"
reload_engine = "auto"

preload_app = _app_env == "production"

max_requests = int(os.getenv("GUNICORN_MAX_REQUESTS", "10000"))
max_requests_jitter = int(os.getenv("GUNICORN_MAX_REQUESTS_JITTER", "1000"))

limit_request_line = 8190
limit_request_fields = 100
limit_request_field_size = 8190

tmp_upload_dir = os.getenv("GUNICORN_TMP_DIR", None)

forwarded_allow_ips = os.getenv("GUNICORN_FORWARDED_IPS", "*")
proxy_protocol = os.getenv("GUNICORN_PROXY_PROTOCOL", "false").lower() == "true"

def pre_fork(server, worker):
    pass

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def pre_exec(server):
    server.log.info("Forked child, re-executing.")

def when_ready(server):
    server.log.info(
        "Nebula Search API starting — env=%s workers=%d class=%s bind=%s",
        _app_env,
        workers,
        worker_class,
        bind,
    )

def worker_int(worker):
    worker.log.info("Worker received INT or QUIT signal (pid: %s)", worker.pid)

def worker_abort(worker):
    worker.log.info("Worker received SIGABRT signal (pid: %s)", worker.pid)
