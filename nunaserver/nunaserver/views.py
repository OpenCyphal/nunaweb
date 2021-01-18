from nunaserver import settings
from nunaserver.utils.archive_utils import fetch_root_namespace_dirs, allowed_file
from nunaserver.generator import generate_dsdl
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

    # TODO: This error handling is really gross.
    if flask.request.form.get("archive_url"):
        if flask.request.form["archive_url"] == "/archive/master.zip":
            return flask.Response("No archive URL given.", status=400)
        ns_dirs = fetch_root_namespace_dirs(flask.request.form["archive_url"], arch_dir)
    else:
        file = flask.request.files["archive"]
        if file.filename == '':
            return flask.Response("No repository archive given.", status=400)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(arch_dir / "dsdl.zip")
            ns_dirs = fetch_root_namespace_dirs(str(arch_dir / "dsdl.zip"), arch_dir)
        else:
            return flask.Response("File type not allowed.", status=400)

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
