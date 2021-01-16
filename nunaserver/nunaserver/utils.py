"""
Utilities for nunaserver.
This includes utilities to fetch archives from Github, etc.
"""
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

def fetch_root_namespace_dirs(location: str) -> typing.List[Path]:
    if "://" in location:
        dirs = fetch_archive_dirs(location)
        logger.info(
            "Resource %r contains the following root namespace directories: %r", location, list(map(str, dirs))
        )
        return dirs
    elif location.endswith(".zip"):
        arch_dir = tempfile.mkdtemp(prefix="pyuavcan-cli-dsdl")
        with zipfile.ZipFile(location) as zf:
            zf.extractall(arch_dir)
        (inner,) = [d for d in Path(arch_dir).iterdir() if d.is_dir()]  # Strip the outer layer, we don't need it
        assert isinstance(inner, Path)
        return [d for d in inner.iterdir() if d.is_dir() and not d.name.startswith(".")]

    return [Path(location)]


def fetch_archive_dirs(archive_uri: str) -> typing.List[Path]:
    """
    Downloads an archive from the specified URI, unpacks it into a temporary directory, and returns the list of
    directories in the root of the unpacked archive.
    """

    # TODO: autodetect the type of the archive
    arch_dir = tempfile.mkdtemp(prefix="pyuavcan-cli-dsdl")
    arch_file = str(Path(arch_dir) / "dsdl.zip")

    logger.info("Downloading the archive from %r into %r...", archive_uri, arch_file)
    response = requests.get(archive_uri)
    if response.status_code != http.HTTPStatus.OK:
        raise RuntimeError(f"Could not download the archive; HTTP error {response.status_code}")
    with open(arch_file, "wb") as f:
        f.write(response.content)

    logger.info("Extracting the archive into %r...", arch_dir)
    with zipfile.ZipFile(arch_file) as zf:
        zf.extractall(arch_dir)

    (inner,) = [d for d in Path(arch_dir).iterdir() if d.is_dir()]  # Strip the outer layer, we don't need it

    assert isinstance(inner, Path)
    return [d for d in inner.iterdir() if d.is_dir() and not d.name.startswith(".")]

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
