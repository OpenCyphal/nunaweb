"""
Utilities for nunaserver.
This includes utilities to fetch archives from Github, etc.
"""
import os
import http
import shutil
import typing
import logging
import zipfile
import tempfile
from pathlib import Path
import requests
from nunaserver.settings import ALLOWED_EXTENSIONS

logger = logging.getLogger(__name__)


def unzip_to_directory(file_path, arch_dir):
    with zipfile.ZipFile(file_path) as zf:
        zf.extractall(arch_dir)


def fetch_remote_namespace(url: str, arch_dir: Path):
    if not (url.startswith("http://") or url.startswith("https://")):
        raise RuntimeError("Not a valid URL.")

    logger.info(f"Downloading the archive from {url} into {arch_dir}...")
    if url.startswith("http://github.com") or url.startswith("https://github.com"):
        res = requests.get(f"{url}/archive/main.zip")

        if res.status_code == http.HTTPStatus.NOT_FOUND:
            res = requests.get(f"{url}/archive/master.zip")
            if res.status_code == http.HTTPStatus.NOT_FOUND:
                raise RuntimeError(
                    f"Server could not fetch Github namespace {url}. Please specify the zip archive manually."
                )
    elif url.endswith(".zip"):
        res = requests.get(url)
    else:
        raise RuntimeError("Only zip archives and Github are supported.")

    if res.status_code != http.HTTPStatus.OK:
        raise RuntimeError(
            f"Could not download the archive; HTTP error {res.status_code}"
        )

    fd, file_path = tempfile.mkstemp("dsdlarchive")

    with open(fd, "wb") as f:
        f.write(res.content)

    logger.info("Extracting the archive into %r...", arch_dir)
    unzip_to_directory(file_path, arch_dir)
    os.unlink(file_path)


def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(
                os.path.join(root, file),
                os.path.relpath(os.path.join(root, file), os.path.join(path, "..")),
            )


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
