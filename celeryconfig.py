import os

broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
result_backend = os.environ.get("CELERY_RESULT_BACKEND", broker_url)
task_default_queue = "sim"
accept_content = ["json"]
task_serializer = "json"
result_serializer = "json"
timezone = "UTC"
enable_utc = True
