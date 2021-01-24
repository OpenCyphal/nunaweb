"""
API endpoints for nunaserver.
"""
from nunaserver import settings
from nunaserver.utils.archive_utils import \
    fetch_remote_namespace, \
    unzip_to_directory, \
    allowed_file
from nunaserver.generator import generate_dsdl
from nunaserver.forms import UploadForm, ValidationError
from werkzeug.utils import secure_filename
from pathlib import Path
from celery.exceptions import TaskRevokedError
import tempfile
import flask
import os
api = flask.Blueprint("api", __name__)

@api.route("/", methods=["GET"])
def root():
    """
    Return 200 OK status with some server information.
    """
    return f"Nunaserver {settings.SERVER_VERSION}"

@api.route("/upload", methods=["POST"])
def upload():
    """
    Handle uploaded DSDL namespace repository archives.
    This expects either an already made zip archive uploaded
    as a file or a URL link to a zip archive.

    Frontend converts GitHub links into zip archives.

    Takes multipart/form-data (obviously, because we have a file upload).
    """
    arch_dir = Path(tempfile.mkdtemp(
        prefix="pyuavcan-cli-dsdl"))

    try:
        print(flask.request.form)
        form = UploadForm(flask.request.form)
    except ValidationError as e:
        print("valid")
        return flask.jsonify(e.errors)

    # TODO: Move this out to a celery task
    for file in form.archive_files:
        # Create temp file for zip archive
        fd, file_path = tempfile.mkstemp(".zip", "dsdl")
        fd.close()

        # Save and unzip
        file.save(file_path)
        unzip_to_directory(file_path, arch_dir)

        # Delete zip file
        os.unlink(file_path)
    for url in form.archive_urls:
        fetch_remote_namespace(url, arch_dir)

    (inner,) = [d for d in Path(arch_dir).iterdir() if d.is_dir()]  # Strip the outer layer, we don't need it
    assert isinstance(inner, Path)
    ns_dirs = [d for d in inner.iterdir() if d.is_dir() and not d.name.startswith(".")]

    out_dir = Path(tempfile.mkdtemp(prefix="nunavut-out"))

    task = generate_dsdl.delay(list(map(str, ns_dirs)),
                               flask.request.form["target_lang"],
                               str(out_dir))

    return flask.jsonify({
        "task_url": flask.url_for("api.taskstatus",
                                  task_id=task.id)}), 202

@api.route('/status/<task_id>')
def taskstatus(task_id):
    try:
        task = generate_dsdl.AsyncResult(task_id)
        if task.state == 'PENDING':
            # job did not start yet
            response = {
                'state': task.state,
                'current': 0,
                'total': 1,
                'status': 'Pending...'
            }
        elif task.state != 'FAILURE':
            response = {
                'state': task.state,
                'current': task.info.get('current', 0),
                'total': task.info.get('total', 1),
                'status': task.info.get('status', ''),
            }
            if 'result' in task.info:
                response['result'] = task.info['result']
        else:
            # something went wrong in the background job
            response = {
                'state': task.state,
                'current': 1,
                'total': 1,
                'status': str(task.info),  # this is the exception raised
            }
        return flask.jsonify(response)
    except AttributeError:
        return flask.jsonify({
            'state': 'CANCELED',
            'current': '0',
            'total': '1',
            'status': 'Task was canceled.'
        })

@api.route('/status/<task_id>/cancel')
def taskcancel(task_id):
    task = generate_dsdl.AsyncResult(task_id)
    task.revoke(terminate=True)

    return flask.jsonify({"response": "OK"}), 200
