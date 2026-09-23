web: cd backend && gunicorn app.main:app -c gunicorn.conf.py
worker: cd backend && PYTHONPATH=. python -m vector.worker
scheduler: cd backend && PYTHONPATH=. python -m app.indexing.scheduler
