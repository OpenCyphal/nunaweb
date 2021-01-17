"""
Global settings and constants read by Flask and other
parts of the server.
"""
import logging

# Server version
SERVER_VERSION="v1.0.0"

# settings for Flask
UPLOAD_FOLDER = "./uploads"
ALLOWED_EXTENSIONS = {"zip"}

# Celery
CELERY_RESULT_BACKEND = "redis://localhost"
CELERY_BROKER_URL = "redis://localhost:6379/0"

# Nunavut
OUT_FOLDER = "./uploads"
OUT_FILE_FOLDER = "./static"
# ^^^ DO NOT SET THIS TO SAME/SUBDIR OF OUT_FOLDER OR UPLOAD_FOLDER!
# Will be insecure.
# Serves static files from this directory (so user can download generated code).
# In production there will likely be a production server (e.g. nginx)
# serving these files.
# Care should be taken when configuring as to not accidentally expose other people's
# generated code.
OUT_SERVER_URL = "http://localhost:8000"
# ^^ Set this to production static file server URL

# Misc.
LOG_LEVEL = logging.WARNING
