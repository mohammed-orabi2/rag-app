# gunicorn_conf.py

# Bind server to port 8001
bind = "0.0.0.0:8001"

# Number of worker processes
workers = 4

# Use 'uvicorn' worker class for async apps (FastAPI/Starlette)
worker_class = "uvicorn.workers.UvicornWorker"

# Preload the app before forking workers
# This loads heavy models (e.g., embeddings) once, saving memory
preload_app = True

# Optional: tweak performance
timeout = 120
keepalive = 5
accesslog = "-"
errorlog = "-"
