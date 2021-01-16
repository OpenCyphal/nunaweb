from nunaserver import settings
from nunaserver.utils import fetch_root_namespace_dirs, allowed_file
from werkzeug.utils import secure_filename
import flask
import os
from flask_cors import CORS

app = flask.Flask(__name__)
app.config["UPLOAD_FOLDER"] = settings.UPLOAD_FOLDER
CORS(app)

# Prep upload folder
if not os.path.isdir(settings.UPLOAD_FOLDER):
    os.mkdir(settings.UPLOAD_FOLDER)

@app.route("/", methods=["GET"])
def root():
    """
    Return 200 OK status with some server information.
    """
    return f"Nunaserver {settings.SERVER_VERSION}"

@app.route("/upload", methods=["POST"])
def upload():
    """
    Handle uploaded DSDL namespace repository archives.
    This expects either an already made zip archive uploaded
    as a file or a URL link to a zip archive.

    Frontend converts GitHub links into zip archives.

    Takes multipart/form-data (obviously, because we have a file upload).
    """
    if flask.request.form.get("archive_url"):
        ns_dirs = fetch_root_namespace_dirs(flask.request.form["archive_url"])
    else:
        file = flask.request.files["archive"]
        if file.filename == '':
            return flask.Response("No repository archive given.", status=400)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        else:
            return flask.Response("File type not allowed.", status=400)
        ns_dirs = fetch_root_namespace_dirs(
            os.path.join(app.config["UPLOAD_FOLDER"], filename))

    print(ns_dirs)
    return "ok"

if __name__ == "__main__":
    app.run(port=5000) # Dev server
