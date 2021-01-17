from nunaserver import settings
from nunaserver.views import api
from nunaserver.tasks import celery, make_celery, init_celery
from werkzeug.utils import secure_filename
from pathlib import Path
import sys
import logging
import tempfile
import flask
import os
from flask_cors import CORS

app = flask.Flask(__name__)
app.config["UPLOAD_FOLDER"] = settings.UPLOAD_FOLDER
app.config["OUT_FOLDER"] = settings.OUT_FOLDER
app.config["OUT_FILE_FOLDER"] = settings.OUT_FILE_FOLDER
CORS(app)

# Setup celery
init_celery(celery, app)

# Setup logging
fmt = '%(message)s'
logging.basicConfig(stream=sys.stderr, level=settings.LOG_LEVEL, format=fmt)
logging.info('Running %s using sys.prefix: %s',
Path(__file__).name, sys.prefix)

# Prep upload folder
if not os.path.isdir(settings.UPLOAD_FOLDER):
    os.mkdir(settings.UPLOAD_FOLDER)

# Prep outputs folder
if not os.path.isdir(settings.OUT_FOLDER):
    os.mkdir(settings.OUT_FOLDER)

# Prep zip outputs folder
if not os.path.isdir(settings.OUT_FILE_FOLDER):
    os.mkdir(settings.OUT_FILE_FOLDER)

app.register_blueprint(api)

if __name__ == "__main__":
    app.run(port=5000) # Dev server
